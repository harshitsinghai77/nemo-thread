import os
import tweepy


access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_key_secret = os.getenv("TWITTER_CONSUMER_KEY_SECRET")

auth = tweepy.OAuthHandler(consumer_key, consumer_key_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
# api.verify_credentials()

all_list = []


def respondToTweet():

    mentions = api.mentions_timeline(
        since_id=1594376053513867264, tweet_mode="extended"
    )
    if not mentions:
        return

    for mention in reversed(mentions):
        all_list.append(mention._json)

    import json

    with open("mention.json", "w") as json_file:
        json.dump(all_list, json_file)
