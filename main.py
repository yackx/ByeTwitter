import dataclasses
import logging
import os
import signal
import sys

import orjson
import tweepy


@dataclasses.dataclass()
class Stats:
    count_deleted: int = 0
    count_not_found: int = 0


stats = Stats()

# API v2
client = tweepy.Client(
        consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
        consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
)

# API v1
auth = tweepy.OAuthHandler(os.environ["TWITTER_CONSUMER_KEY"], os.environ["TWITTER_CONSUMER_SECRET"])
auth.set_access_token(os.environ["TWITTER_ACCESS_TOKEN"], os.environ["TWITTER_ACCESS_TOKEN_SECRET"])
api = tweepy.API(auth)


def load_tweets(archive_path):
    with open(f"{archive_path}/data/tweet.js", "r") as f:
        lines = "".join(f.readlines()).removeprefix("window.YTD.tweet.part0 = ")
        json = orjson.loads(lines)
        for tweet in json:
            yield tweet["tweet"]["id_str"]


def delete_tweets(archive_path):
    # for tweet_id in ["1602331721638232064"]:
    for tweet_id in load_tweets(archive_path):
        logging.info(f"Delete tweet {tweet_id}")
        try:
            api.destroy_status(tweet_id)
            # API v2 always responds deleted: True even if tweet does not exist
            # resp = client.delete_tweet(tweet_id, user_auth=True)
        except tweepy.errors.NotFound:
            stats.count_not_found += 1
        except Exception:
            logging.exception(f"Failed to delete tweet")
            raise
    logging.info(str(stats))


def configure_logger():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


def sigint_handler(sig, frame):
    logging.warning('Interrupted')
    logging.info(stats)
    client.session.close()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    configure_logger()
    path = sys.argv[1]
    delete_tweets(path)
