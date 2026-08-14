import praw
from pathlib import Path
from datetime import datetime
import configparser as ConfigParser
import logging.config


class reddit_output:
    def __init__(self, ini_file: Path, county_name: str):
        self.logger = logging.getLogger(__name__)
        try:
            config_file = ConfigParser.RawConfigParser()
            config_file.read(ini_file)

            self.client_id = config_file.get("reddit_output_settings", "client_id")
            self.client_secret = config_file.get("reddit_output_settings", "client_secret")
            self.username = config_file.get("reddit_output_settings", "username")
            self.password = config_file.get("reddit_output_settings", "password")
            self.useragent = config_file.get("reddit_output_settings", "password")
            #Get the county specific settings
            self.subreddits = config_file.get(county_name, "subreddits", fallback=None)
            self.flair_text = config_file.get(county_name, "flair_text", fallback=None)
            if self.subreddits is not None:
                self.subreddits = self.subreddits.split(',')
            self.logger.info(
                f"Using subreddits: {self.subreddits}"
            )
        except Exception as e:
            raise e

    def post(self, county: str, inspection_date: datetime, report_file: Path):
        self.logger.debug("Starting post for reddit output.")
        if self.subreddits is not None:
            try:
                reddit = praw.Reddit(client_id=self.client_id,
                                     client_secret=self.client_secret,
                                     user_agent='MySCRiversBot',
                                     password=self.password,
                                     username=self.username)

                title = f"{county} County Inspection Reports for {inspection_date.strftime('%Y-%m-%d')}"
                with open(report_file, 'r') as report_file:
                    output_text = report_file.read()
                    for sub in self.subreddits:
                        self.logger.info(f"Submitting to subreddit: {sub}")
                        subreddit = reddit.subreddit(sub)
                        flair_id = None
                        if self.flair_text is not None and len(self.flair_text) > 0:
                            for template in subreddit.flair.link_templates:
                                if template["text"].strip() == self.flair_text:
                                    flair_id = template["id"]
                                    flair_text = template["text"]
                                    break
                            if flair_id:
                                subreddit.submit(title, selftext=output_text, flair_id=flair_id, flair_text=flair_text)
                            else:
                                self.logger.error(f"No flair template: {self.flair_text} found for subreddit: {sub}")
                        else:
                            subreddit.submit(title, selftext=output_text)

            except Exception as e:
                self.logger.exception(e)
        else:
            self.logger.info(f"No subreddits configured for {county} county.")
        self.logger.info("Finished post for reddit output.")
