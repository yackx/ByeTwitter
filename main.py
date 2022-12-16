"""Delete and unlike tweets """

import logging
import os
import signal
import sys

import tweepy

from stats import Stats

dry_run = False
is_verbose = False
is_delete_tweets = False
is_unlike_tweets = True

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


def delete_tweets():
    def action(tweet_id):
        api.destroy_status(tweet_id)
        # API v2 always responds deleted: True even if tweet does not exist
        # resp = client.delete_tweet(tweet_id, user_auth=True)
        stats.count_deleted += 1

    perform_action(cursor_func=api.user_timeline, action_func=action, action_name="delete")


def unlike_tweets():
    def action(tweet_id):
        api.destroy_favorite(tweet_id)
        stats.count_unlike += 1

    perform_action(cursor_func=api.get_favorites, action_func=action, action_name="unlike")


def perform_action(*, cursor_func, action_func, action_name):
    logging.info("Retrieving tweets")
    for i, tweet in enumerate(tweepy.Cursor(cursor_func).items()):
        logging.debug(f"{action_name} {tweet.id} {tweet.created_at}")
        if not dry_run:
            try:
                action_func(tweet.id)
            except Exception:
                logging.exception(f"Failed to perform action {action_name}")
                raise
        if i % 20 == 0:
            logging.info(stats)


def configure_logger():
    root = logging.getLogger()
    root.setLevel(logging.INFO if not is_verbose else logging.DEBUG)
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
    try:
        if is_unlike_tweets:
            unlike_tweets()
        if is_delete_tweets:
            delete_tweets()
    finally:
        logging.info(stats)
