from lib.slack import Slack

import os
from dotenv import load_dotenv

def test_slack_message():
    load_dotenv()
    slack_channel = os.environ.get("SLACK_CHANNEL")
    slack_token = os.environ.get("SLACK_TOKEN")
    
    if not slack_channel or not slack_token:
        print("SLACK_CHANNEL or SLACK_TOKEN is not set in the environment variables.")
        return
    
    slack = Slack(slack_channel=slack_channel, slack_token=slack_token, bot_name="Test Bot")
    res = slack.send_message("This is a test message from the test_slack.py script.")
    assert res is True, "Failed to send message to Slack channel."