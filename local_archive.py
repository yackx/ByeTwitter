"""Delete and unlike tweets from Twitter archive

Faster than using the Twitter API to retrieve tweet,
and to process large accounts were the retrieval limit is exceeded.
"""

import logging
import os
import signal
import sys

import orjson
import tweepy

from stats import Stats

is_verbose = True
do_unlike_tweets = False
do_delete_tweets = False
do_delete_direct_messages = True

stats = Stats()

account_id = os.getenv("TWITTER_ACCOUNT_ID")

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


def load_tweet_ids(archive_path):
    with open(f"{archive_path}/data/tweets.js", "r") as f:
        lines = "".join(f.readlines()).removeprefix("window.YTD.tweets.part0 = ")
        json = orjson.loads(lines)
        logging.info(f"Loaded {len(json)} archived tweets")
        return [tweet["tweet"]["id_str"] for tweet in json]


def delete_tweets(archive_path):
    def action(tweet_id):
        api.destroy_status(tweet_id)
        # API v2 always responds deleted: True even if tweet does not exist
        # resp = client.delete_tweet(tweet_id, user_auth=True)
        stats.count_deleted_tweets += 1

    perform_action(archive_path=archive_path, load_func=load_tweet_ids, action_func=action, action_name="Delete")


def load_liked_tweet_ids(archive_path):
    with open(f"{archive_path}/data/like.js", "r") as f:
        lines = "".join(f.readlines()).removeprefix("window.YTD.like.part0 = ")
        json = orjson.loads(lines)
        logging.info(f"Unlike {len(json)} tweets")
        return [tweet["like"]["tweetId"] for tweet in json]


def unlike_tweets(archive_path):
    def action(tweet_id):
        api.destroy_favorite(tweet_id)
        stats.count_unlike += 1

    perform_action(archive_path=archive_path, load_func=load_liked_tweet_ids, action_func=action, action_name="Unlike")


def load_message_ids(archive_path):
    with open(f"{archive_path}/data/direct-messages.js", "r") as f:
        lines = "".join(f.readlines()).removeprefix("window.YTD.direct_messages.part0 = ")
        json = orjson.loads(lines)
        logging.info(f"Loaded {len(json)} conversations")
        message_ids = []
        for conversation in json:
            for message in conversation["dmConversation"]["messages"]:
                try:
                    if message["messageCreate"]["senderId"] == account_id:
                        message_ids.append(message["messageCreate"]["id"])
                except KeyError:
                    # Sanity check. Sometimes the keys is different and can be ignored
                    try:
                        message["welcomeMessageCreate"]
                    except KeyError:
                        logging.error(f"Garbled keys in: {message}")
                        raise
        return message_ids


def delete_direct_messages(archive_path):
    def action(message_id):
        api.delete_direct_message(message_id)
        stats.count_deleted_dm += 1

    perform_action(archive_path=archive_path, load_func=load_message_ids, action_func=action, action_name="Delete DM")


def perform_action(*, archive_path, load_func, action_func, action_name):
    file_name = "./deleted_and_skipped.txt"
    if not os.path.exists(file_name):
        open(file_name, "w").close()
    with open(file_name, "r") as f:
        deleted_resource_ids = [line.strip() for line in f.readlines()]

    with open(file_name, "a") as f:
        for i, resource_id in enumerate(load_func(archive_path)):
            if resource_id in deleted_resource_ids:
                stats.count_skipped += 1
                logging.debug(f"Already processed {resource_id}")
            else:
                logging.info(f"{action_name} {resource_id}")
                try:
                    action_func(resource_id)
                except tweepy.errors.NotFound:
                    logging.info(f"Not found {resource_id}")
                    stats.count_not_found += 1
                except tweepy.errors.Forbidden as e:
                    logging.error(f"Forbidden {resource_id} -> {e.api_errors}")
                    stats.count_forbidden += 1
                except Exception:
                    logging.exception(f"Failed to process")
                    raise
                f.write(resource_id + "\n")
                f.flush()
            if i % 20 == 0:
                logging.info(stats)


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
    client.session.close()
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, sigint_handler)
    configure_logger()
    path = sys.argv[1]
    try:
        if do_unlike_tweets:
            unlike_tweets(path)
        if do_delete_tweets:
            delete_tweets(path)
        if do_delete_direct_messages:
            delete_direct_messages(path)
    finally:
        logging.info(stats)
