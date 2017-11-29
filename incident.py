from enum import Enum
import json
from datetime import datetime
from jira.exceptions import JIRAError

from config import config
from log import log

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


class DumbEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.strftime('%Y-%m-%dT%H:%M:%S%z')
        if isinstance(o, IncidentState) or isinstance(o, IncidentPriority):
            return o.value
        return o.__str__()


class IncidentState(Enum):
    ONGOING = "Ongoing"
    CLOSED  = "Closed"


class IncidentPriority(Enum):
    ORANGE  = "orange"
    RED     = "red"


class Incident(object):
    def __init__(self, incident_id=0, priority=IncidentPriority.RED,
                 title="Undefined", description="Undefined"):
        print("Creating incident " + str(incident_id) + " ...")
        self.state          = IncidentState.ONGOING
        self.id             = incident_id
        self.title          = title
        self.description    = description
        self.priority       = IncidentPriority(priority)
        self.slack_channel  = "incident-" + str(self.id)
        self.slack_channel_id  = None
        self.opening_time   = datetime.now()
        self.closing_time   = None
        self.starting_time  = datetime.now()  # TODO : Make this set-able
        self.ending_time    = None
        self.updates        = []
        self.jira_issue     = config['jira']['project'] + "-" + str(self.id)
        self.cachet_id      = None
        print("Created incident")

    def close(self):
        from app import incidents
        print("Closing incident " + str(self.id) + " ... ")
        self.state          = IncidentState.CLOSED
        self.closing_time   = datetime.now()
        self.ending_time    = self.closing_time
        self.send_to_es()
        log.debug("Sending confirmation to Slack ...")
        incidents.slack.chat.post_message(
            channel = self.slack_channel,
            text    = '',
            as_user = True,
            attachments = [
                {
                    "text": "Closing this incident, good job :+1:",
                    "color": "good",
                    "mrkdwn_in": ["text"],
                    "short": False,
                    "fields": [
                        {
                            "title": "Jira Issue",
                            "value": "<{jira_server}/browse/{jira_issue}"
                                     "|{jira_issue}>".format(
                                        jira_server=config['jira']['host'],
                                        jira_issue=self.jira_issue),
                            "short": True
                        },
                        {
                            "title": "State",
                            "value": self.state.value,
                            "short": True
                        }
                    ]
                }
            ]
        )
        log.debug("Sent confirmation to Slack")
        self.list_updates()
        log.debug("Updating Jira issue ...")
        try:
            incidents.jira.transition_issue(self.jira_issue, "1002")
        except JIRAError:
            pass
        log.debug("Updated Jira issue")
        log.debug("Updating Cachet ...")
        # FIXME self.declare_to_cachet()
        log.debug("Updated Cachet")

    def set_description(self, new_description):
        log.debug("Updating description for incident " + str(self.id) + " ... ")
        from app import incidents
        self.description = new_description
        self.send_to_es()
        log.debug("Updated description")
        log.debug("Sending confirmation to Slack ...")
        incidents.slack.channels.set_purpose(
            channel = self.slack_channel_id,
            purpose = "Incident " + self.priority.value.upper() + " " +
                      str(self.id) + " - Incident management room\n\n" +
                      new_description
        )
        print("Sent confirmation to Slack")

    def add_update(self, message, user):
        log.info("Adding update ...")
        from app import incidents
        date = datetime.now()
        self.updates.append({'message': message, 'author': user, 'date': date})
        log.debug("Ack Slack")
        incidents.slack.chat.post_message(
            channel = self.slack_channel,
            text    = '',
            as_user = True,
            attachments = [
                {
                    "text": "Just logged a new update for this incident." +
                            " The message was: " + message,
                    "mrkdwn_in": ["text"]
                }
            ]
        )
        self.send_to_es()
        log.debug("Adding comment to Jira")
        incidents.jira.add_comment(self.jira_issue, message)

    def list_updates(self):
        print("Listing updates for incident " + str(self.id) + " ... ")
        from app import incidents
        incidents.slack.chat.post_message(
            channel = self.slack_channel,
            text    = 'Here are the updates for this incident:\n```' +
                      '\n'.join([
                                    self.format_update(update, idx)
                                    for idx, update in enumerate(self.updates)]) + '```',
            as_user = True
        )
        print("Sent updates to Slack")

    def get_color(self):
        """Get color code from incident priority"""
        if self.priority == IncidentPriority.ORANGE:
            return "#ffa500"
        elif self.priority == IncidentPriority.RED:
            return "#ff2600"

    def send_to_es(self):
        """Send incident to ElasticSearch"""
        from app import incidents
        log.debug("Sending incident to ES ...")
        incidents.es.index(
            index = incidents.es_index,
            doc_type="incident",
            id = self.id,
            body = self.serialize()
        )
        print("Sent incident to ES")
        print("Refreshing ES index ...")
        incidents.es.indices.refresh(index=incidents.es_index)
        print("Refreshed index")

    @staticmethod
    def format_update(update, idx):
        """Format an update for Slack"""
        if 'author' in update:
            author_str = " - <@" + update['author']['id'] + ">"
        else:
            author_str = ""
        return "Update n°{number} ({date}{author}) - {message|".format(
                    number = str(idx + 1),
                    date = update['date'].strftime("%Y-%m-%d %H:%M:%S"),
                    author = author_str,
                    message = update['message']
        )

    def serialize(self):
        return json.dumps(self.__dict__, indent=4,
                          cls=DumbEncoder, ensure_ascii=False)

    def unserialize(self, source_json):
        log.debug("Unserializing incident from json ...")
        log.debug(source_json)
        self.__dict__ = source_json
        self.opening_time = datetime.strptime(self.opening_time, DATE_FORMAT)
        self.starting_time = datetime.strptime(self.starting_time, DATE_FORMAT)
        self.priority = IncidentPriority(self.priority)
        self.state = IncidentState(self.state)
        if self.state == IncidentState.CLOSED:
            self.closing_time = datetime.strptime(self.closing_time,
                                                  DATE_FORMAT)
        for idx, update in enumerate(self.updates):
            self.updates[idx]['date'] = datetime.strptime(update['date'],
                                                          DATE_FORMAT)
        # print(self.serialize())
        print("... unserialized")
        return self
