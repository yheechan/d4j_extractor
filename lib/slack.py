
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class Slack:
    """
    Slack class to send messages to a Slack channel
    """
    def __init__(self, slack_channel=None, slack_token=None, bot_name="Un-Named Bot"):
        self.client = WebClient(token=slack_token)
        self.channel_name = slack_channel
        self.deactivated = False
        if slack_token is None:
            self.deactivated = True
        self.bot_name = bot_name

    def send_message(self, msg):
        if self.deactivated:
            return False
        try:
            res = self.client.chat_postMessage(
                channel=self.channel_name,
                text=msg,
                username=self.bot_name
            )
            return res["ok"]
        except SlackApiError as e:
            print(f"Error sending message: {e.response['error']}")
