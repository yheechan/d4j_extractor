from lib.database import Database
from lib.slack import Slack

import os
from dotenv import load_dotenv

class ExtractorEngine:
    def __init__(self):
        load_dotenv()
        self.os_copy = os.environ.copy()
        self.slack = Slack(
            slack_channel=self.os_copy.get("SLACK_CHANNEL"),
            slack_token=self.os_copy.get("SLACK_TOKEN"),
            bot_name="Extractor Engine",
        )

        self.db = Database(
            host=self.os_copy.get("DB_HOST"),
            port=self.os_copy.get("DB_PORT"),
            user=self.os_copy.get("DB_USER"),
            password=self.os_copy.get("DB_PASSWORD"),
            database=self.os_copy.get("DB"),
            slack_channel=self.os_copy.get("SLACK_CHANNEL"),
            slack_token=self.os_copy.get("SLACK_TOKEN"),
        )

        self.server_home = self.os_copy.get("SERVER_HOME")

    def run(self):
        pass