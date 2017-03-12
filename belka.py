from slackeventsapi import SlackEventAdapter
from slackclient import SlackClient
from flask import request
import validators
import requests
import os, re

import logging

logger = logging.getLogger()

logging.basicConfig(**{
    'level': logging.INFO
})

# Our app's Slack Event Adapter for receiving actions via the Events API
SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]
slack_events_adapter = SlackEventAdapter(SLACK_VERIFICATION_TOKEN, "/slack/events")

# Since SlackEventAdapter uses a standard Flask server, we can extend it to handle OAuth
# by simply adding a couple more route handlers.

# Slack App credentials for OAuth
SLACK_CLIENT_ID = os.environ["SLACK_CLIENT_ID"]
SLACK_CLIENT_SECRET = os.environ["SLACK_CLIENT_SECRET"]
SLACK_TEST_TOKEN = os.environ["SLACK_TEST_TOKEN"]
SLACK2ARENA_CHANNEL= os.environ["SLACK2ARENA_CHANNEL"]

ARENA_ACCESS_TOKEN = os.environ["ARENA_ACCESS_TOKEN"]
ARENA_POST_URL = os.environ["ARENA_POST_URL"]

CLIENT = SlackClient(SLACK_TEST_TOKEN)

# Now we'll set up some event listeners for our app to process and respond to
# Example responder to greetings
@slack_events_adapter.on("message")
def handle_message(event_data):
    handle_arena_link(event_data)
    # message = event_data["event"]
    # if message.get("subtype") is None and "hi" in message.get('text'):
    #     channel = message["channel"]
    #     message = "Hello <@%s>! :tada:" % message["user"]
    #     CLIENTS[team_id].api_call("chat.postMessage", channel=channel, text=message)

def handle_arena_link(event_data):

    slack_team_id = event_data["team_id"]
    message = event_data['event']
    channel_name = get_channel_name(message["channel"], slack_team_id)
    if (channel_name == SLACK2ARENA_CHANNEL) and message.get("subtype") is None:
        link_url = extract_url(message)

        if link_url is not None:
            response = requests.post(ARENA_POST_URL,
                headers = {
                        'Authorization': 'Bearer {}'.format(ARENA_ACCESS_TOKEN)},
                data = {'source': link_url}
            )


def extract_url(message):
    maybe_url = re.match('.*?<(.*?)[|>].*', message.get("text",""))
    if (maybe_url is not None) and validators.url(maybe_url.group(1)):
        logger.info("We have a link!")
        return maybe_url.group(1)
    else:
        return None

def get_channel_name(channel_id, team_id):
    r = CLIENT.api_call("channels.info", channel=channel_id)
    c = r.get("channel",{}).get("name")
    logger.info("We got a post in.... #{}".format(c))
    return c

# Once we have our addon routes and event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 3000
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 3000))
    slack_events_adapter.server.run(host='0.0.0.0', port=port)
