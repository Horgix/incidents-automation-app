from log import log
from slacker import Slacker, Error

from config import config

# ElasticSearch
from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
from aws_requests_auth import boto_utils


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
        # SMTP
        # Elasticsearch
        log.info("- Configuring Elasticsearch connection ...")
        self.es_index = config['elasticsearch']['index']
        try:
            # @formatter:off
            # noinspection PyPep8
            aws_auth = AWSRequestsAuth(
                aws_host    = config['elasticsearch']['host'],
                aws_region  = config['elasticsearch']['region'],
                aws_service = 'es',
                **boto_utils.get_credentials()
            )
            # noinspection PyPep8
            self.es = Elasticsearch(
                hosts   = [{'host': config['elasticsearch']['host'], 'port': 443}],
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
        # Cachet
        return

    def create_incident(self, priority, title, description):
        log.info(
            "Creating incident ...:\n"
            "  Priority: {priority}\n"
            "  Title: {title}\n"
            "  Description: {description}"
            "".format(priority=priority, title=title,
                      description=description))
        log.info("Created incident successfully :)")

    def close_incident(self, event):
        log.info("Closing incident ...")
        source = self.extract_event_infos(event)
        log.info("Source: " + str(source))
        log.info("Closed incident successfully :)")

    def list_incident_updates(self, event):
        log.info("Listing incident updates ...")
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

    def create_es_index(self, es_index):
        # === Wipe index
        # self.es.indices.delete(index=self.es_index)
        # === Create it again
        print("Creating index " + es_index + " ...")
        index_creation = self.es.indices.create(index=es_index, ignore=400)
        if 'acknowledged' in index_creation and index_creation['acknowledged']:
            print("... Index created")
        elif 'status' in index_creation and index_creation['status'] == 400:
            print("... Index already exists, continuing")
