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

# We'll store the SlackClient instances for each team in a
# dictionary, so we can have multiple teams authed
CLIENTS = {}

# Our app's Slack Event Adapter for receiving actions via the Events API
SLACK_VERIFICATION_TOKEN = os.environ["SLACK_VERIFICATION_TOKEN"]
slack_events_adapter = SlackEventAdapter(SLACK_VERIFICATION_TOKEN, "/slack/events")

# Since SlackEventAdapter uses a standard Flask server, we can extend it to handle OAuth
# by simply adding a couple more route handlers.

# Slack App credentials for OAuth
SLACK_CLIENT_ID = os.environ["SLACK_CLIENT_ID"]
SLACK_CLIENT_SECRET = os.environ["SLACK_CLIENT_SECRET"]
SLACK_TEST_TOKEN = os.environ["SLACK_TEST_TOKEN"]

ARENA_ACCESS_TOKEN = os.environ["ARENA_ACCESS_TOKEN"]

CLIENT = SlackClient(SLACK_TEST_TOKEN)

# This route renders the installation page with 'Add to Slack' button.
@slack_events_adapter.server.route("/", methods=["GET"])
def pre_install():
    add_to_slack = """
        <a href="https://slack.com/oauth/authorize?scope=bot&client_id=%s">
            <img alt="Add to Slack" src="https://platform.slack-edge.com/img/add_to_slack.png"/>
        </a>
    """ % SLACK_CLIENT_ID
    return add_to_slack


# This route is called by Slack after the user installs our app. It will
# exchange the temporary authorization code Slack sends for an OAuth token
# which we'll save on the bot object to use later.
# To let the user know what's happened it will also render a thank you page.
@slack_events_adapter.server.route("/auth/slack/callback", methods=["GET"])
def thanks():

    # Get the OAuth code to pass into the token request
    auth_code = request.args.get('code')

    # Create a temporary Slack client to make the OAuth request.
    # This client doesn't need a token.
    slack_client = SlackClient("")

    # Ask Slack for a bot token, using the auth code we received
    auth_response = slack_client.api_call(
        "oauth.access",
        client_id=SLACK_CLIENT_ID,
        client_secret=SLACK_CLIENT_SECRET,
        code=auth_code
    )

    # Grab the user's team info and token from the OAuth response
    team_id = auth_response.get("team_id")
    team_name = auth_response.get("team_name")
    bot_token = auth_response["bot"].get("bot_access_token")
    logger.info("bot_token {}".format(bot_token))

    # Create a SlackClient for your bot to use for Web API requests
    CLIENTS[team_id] = SlackClient(bot_token)
    return "Your app has been installed on <b>%s</b>" % team_name


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
    post_url = 'http://api.are.na/v2/channels/tnn-test/blocks'

    slack_team_id = event_data["team_id"]
    message = event_data['event']
    channel_name = get_channel_name(message["channel"], slack_team_id)
    if channel_name in ("hellobots"):
        link_url = extract_url(message)

        if link_url is not None:
            logger.info(link_url)
            response = requests.post(post_url,
                headers = {
                        'Authorization': 'Bearer {}'.format(ARENA_ACCESS_TOKEN)},
                data = {'source': link_url}
            )


def extract_url(message):
    if message.get("subtype") is None:
        maybe_url = re.match('.*?<(.*?)>.*', message.get("text",""))
        if (maybe_url is not None) and validators.url(maybe_url.group(1)):
            logger.info("We have a link!")
            return maybe_url.group(1)
        else:
            return None
    else:
        return None

def get_channel_name(channel_id, team_id):
    r = CLIENT.api_call("channels.info", channel=channel_id)
    c = r.get("channel",{}).get("name")
    logger.info("We got a post in.... #{}".format(c))
    return c

# Once we have our addon routes and event listeners configured, we can start the
# Flask server with the default `/events` endpoint on port 3000
port = int(os.environ.get('PORT', 3000))
slack_events_adapter.start(port=port)
