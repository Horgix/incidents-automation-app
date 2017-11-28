# Slack
from slacker import Slacker
from slacker import Error as SlackerError
# JIRA
from jira import JIRA
# ElasticSearch
from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
from aws_requests_auth import boto_utils

from log import log
from config import config
from incident import Incident, IncidentPriority


class IncidentsManager(object):
    def __init__(self):
        log.info("Initializing incidents manager ...")
        # Slack
        self.slack_channel = config['slack']['channel']
        self.slack = Slacker(config['slack']['self']['token'])
        self.slack_self_user = config['slack']['self']
        self.slack_fake_user = Slacker(config['slack']['fake_user']['token'])
        self.apiai_user = self.slack_fake_user.users.info(
            user=config['slack']['apiai_user']['id']).body['user']
        # TODO SMTP
        # Elasticsearch
        log.info("Connecting to Elasticsearch ...")
        self.es_index = config['elasticsearch']['index']
        try:
            # @formatter:off
            aws_auth = AWSRequestsAuth(
                aws_host    = config['elasticsearch']['host'],
                aws_region  = config['elasticsearch']['region'],
                aws_service = 'es',
                **boto_utils.get_credentials()
            )
            self.es = Elasticsearch(
                hosts   = [{'host': config['elasticsearch']['host'],
                            'port': 443}],
                http_auth           = aws_auth,
                use_ssl             = True,
                verify_certs        = True,
                connection_class    = RequestsHttpConnection
            )
            # @formatter:on
        except:
            log.error("Couldn't connect to Elasticsearch")
        try:
            self.create_es_index(self.es_index)
        except:
            log.error("Couldn't create Elasticsearch index")
        # Jira
        log.info("Connecting to Jira ...")
        self.jira = JIRA(
            {'server': config['jira']['host']},
            basic_auth=(config['jira']['user'], config['jira']['password'])
        )
        self.jira_project = config['jira']['project']
        # TODO Cachet
        return

    def create_incident(self, priority, title, description):
        log.info("Starting to create incident ...")
        jira_issue = self.jira.create_issue(
            project     = self.jira_project,
            issuetype   = {'name': 'Incident'},
            summary     = title,
            description = description)
        incident_id = int(str(jira_issue)[len(self.jira_project)+1:])
        log.debug("got incident id " + str(incident_id))
        incident = Incident(
            incident_id,
            priority    = IncidentPriority(priority),
            title       = title,
            description = description)
        incident.send_to_es()
        # log.debug(incident.serialize())
        self.create_slack_channel(incident)
        # Resend it now that is has a Slack channel ID
        incident.send_to_es()
        self.post_new_incident_announce_on_slack(incident)
        # TODO post incident summary to Slack dedicated channel
        # TODO send email
        # TODO declare to Cachet
        log.info("Created incident successfully :)")

    def close_incident(self, event):
        log.info("Closing incident ...")
        source = self.extract_event_infos(event)
        log.info("Source: " + str(source))
        # TODO find incident from channel
        # TODO unserialize event
        # TODO close incident for real
        log.info("Closed incident successfully :)")

    def list_incident_updates(self, event):
        log.info("Listing incident updates ...")
        source = self.extract_event_infos(event)
        # TODO find incident from channel
        # TODO unserialize event
        # TODO list updates for real
        log.info("Source: " + str(source))

    def extract_event_infos(self, event):
        """
        Extract Slack event core infos (channel, user, message) from event
        """
        source_channel_id = event['channel']
        source_user_id = event['user']
        source_message = event['text']

        # Get real infos from Slack API
        source_channel = self.slack.channels.info(channel=source_channel_id).body['channel']
        source_user = self.slack.users.info(user=source_user_id).body['user']
        return {
            'channel': source_channel,
            'user': source_user,
            'message': source_message
        }

    def create_es_index(self, es_index):
        # === Wipe index
        # self.es.indices.delete(index=self.es_index)
        # === Create it again
        log.info("Creating index " + es_index + " ...")
        index_creation = self.es.indices.create(index=es_index, ignore=400)
        if 'acknowledged' in index_creation and index_creation['acknowledged']:
            log.info("... Index created")
        elif 'status' in index_creation and index_creation['status'] == 400:
            log.info("... Index already exists, continuing")

    def invite_user_to_channel(self, user, user_id, channel, channel_id):
        log.debug("Inviting user {user} to new Slack channel {channel} ..."
                  .format(user=user, channel=channel))
        try:
            self.slack_fake_user.channels.invite(
                channel = channel_id,
                user = user_id
            )
        except SlackerError as e:
            if str(e) == "already_in_channel":
                log.debug("User {user} already in channel {channel} ; continuing ..."
                          .format(user=user, channel=channel))
                pass

    # TODO : set channel topic and description
    def create_slack_channel(self, incident):
        # Create channel
        log.info("Creating Slack channel " + incident.slack_channel + "...")
        try:
            channel = self.slack_fake_user.channels.create(
                name=incident.slack_channel).body['channel']
            log.debug("... created Slack channel with ID " + channel['id'])
        except SlackerError as e:
            if str(e) == "name_taken":
                log.debug("... channel already exists, searching the existing one")
                channels_list = self.slack.channels.list().body['channels']
                channel = [chan for chan in channels_list if chan['name'] == incident.slack_channel]
                if len(channel) != 1:
                    raise Exception("Failed to lookup channel that should exist")
                channel = channel[0]
                log.debug("... existing channel found,  continuing using channel " + channel['id'])
                pass
            else:
                raise e
        incident.slack_channel_id = channel['id']

        # Join channel
        log.debug("Fake user joining channel ...")
        self.slack_fake_user.channels.join(name=channel['name'])
        log.debug("... joined channel")

        # Invite Dialogflow user
        log.debug("Inviting Dialogflow user to incident channel ...")
        self.invite_user_to_channel(
            user=self.apiai_user['name'],
            user_id=self.apiai_user['id'],
            channel=incident.slack_channel,
            channel_id=incident.slack_channel_id
        )
        log.debug("Invited user")

        # Invite App user
        log.debug("Inviting self (app) user to incident channel ...")
        self.invite_user_to_channel(
            user=self.slack_self_user['name'],
            user_id=self.slack_self_user['id'],
            channel=incident.slack_channel,
            channel_id=incident.slack_channel_id
        )
        log.debug("Invited user")

        # Define purpose and title
        log.debug("... defining channel purpose")
        self.slack.channels.set_purpose(
            channel = incident.slack_channel_id,
            purpose = "Incident " + incident.priority.value.upper() + " " +
                      str(incident.id) + " - Incident management room"
        )
        log.debug("... defined channel purpose")
        log.debug("... defining channel title")
        self.slack.channels.set_topic(
            channel = incident.slack_channel_id,
            topic = incident.title
        )
        log.debug("... defined channel title")

    def post_new_incident_announce_on_slack(self, incident):
        log.debug("Posting new incident announce ...")
        self.slack.chat.post_message(
            channel=self.slack_channel,
            text='',
            as_user=True,
            attachments=[
                {
                    "text": ":warning: New incident opened: *" +
                            incident.slack_channel + "* :warning:",
                    "color": incident.get_color(),
                    "mrkdwn_in": ["text"],
                    "fields": [
                        {"title": "Title", "value": str(incident.title), "short": False},
                        {"title": "State", "value": incident.state.value, "short": True},
                        {"title": "ID", "value": str(incident.id), "short": True},
                        {"title": "Priority", "value": incident.priority.value, "short": True},
                        {"title": "Jira Issue",
                         "value": "<{jira_server}/browse/{jira_issue}|{jira_issue}>".format(
                             jira_server=config['jira']['host'],
                             jira_issue=incident.jira_issue),
                         "short": True},
                        {"title": "Description", "value": str(incident.description), "short": False}
                    ]
                },
                {
                    "text": "Please join channel <#" + incident.slack_channel_id + ">",
                    "mrkdwn_in": ["text"],
                    "color": incident.get_color()
                }
            ])
        log.debug("Posted new incident announce")

    def post_new_incident_summary(self, incident):
        log.debug("Posting new incident summary ...")
        self.slack.chat.post_message(
            channel=incident.slack_channel,
            text='',
            as_user=True,
            attachments=[
                {
                    "text": ":warning: Welcome to this new code handling channel\n" +
                            "As a reminder, here are the informations so far:",
                    "mrkdwn_in": ["text"],
                    "fields": [
                        {"title": "Title", "value": str(incident.title), "short": False},
                        {"title": "State", "value": incident.state.value, "short": True},
                        {"title": "ID", "value": str(incident.id), "short": True},
                        {"title": "Priority", "value": incident.priority.value, "short": True},
                        {"title": "Jira Issue",
                         "value": "<{jira_server}/browse/{jira_issue}|{jira_issue}>".format(
                             jira_server=config['jira']['host'],
                             jira_issue=incident.jira_issue),
                         "short": True},
                        {"title": "Description", "value": str(incident.description), "short": False}
                    ]
                }
            ])
        log.debug("Posted new incident summary")
