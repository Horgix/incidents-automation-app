from log import log


class IncidentsManager(object):
    def __init__(self):
        log.info("Initializing incidents manager...")
        # Slack
        # SMTP configuration
        # Elasticsearch
        # Cachet
        return

    def create_incident(self, priority, title, description):
        log.info(
            "Creating incident...:\n"
            "  Priority: {priority}\n"
            "  Title: {title}\n"
            "  Description: {description}"
            "".format(priority=priority, title=title,
                      description=description))
        log.info("Created incident successfully :)")

    def close_incident(self, event):
        log.info("Closing incident...")
        source = self.extract_event_infos(event)
        log.info("Source: " + str(source))
        log.info("Closed incident successfully :)")

    def list_incident_updates(self, event):
        log.info("Listing incident updates...")
        source = self.extract_event_infos(event)
        log.info("Source: " + str(source))

    def extract_event_infos(self, event):
        """
        Extract Slack event core infos (channel, user, message) from event
        """
        source_channel_id = event['channel']
        source_user_id = event['user']
        source_message = event['text']

        # Get real infos from Slack API
        # noinspection PyPep8
        # source_channel = self.slack.channels.info(channel=source_channel_id).body['channel']
        # source_user = self.slack.users.info(user=source_user_id).body['user']
        source_channel = source_channel_id
        source_user = source_user_id
        return {
            'channel': source_channel,
            'user': source_user,
            'message': source_message
        }
