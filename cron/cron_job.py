import os
import requests

import tweepy
import asyncio
import aiohttp

from app.constants import ROOT_URL

access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_key_secret = os.getenv("TWITTER_CONSUMER_KEY_SECRET")

auth = tweepy.OAuthHandler(consumer_key, consumer_key_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
# api.verify_credentials()

PROCESS_MENTION_URL = ROOT_URL + "/process_mention"


async def post_request(session, url, data):
    async with session.post(url, json=data) as resp:
        tweet = await resp.json()
        return tweet


async def fetch_tweet_mentions():

    req_last_mention_id = requests.get(ROOT_URL + "/last_processed_id")
    last_mention_id = req_last_mention_id.json()
    if last_mention_id:
        last_mention_id = last_mention_id["processed_id"]

    all_mentions = []
    while True:
        mention = api.mentions_timeline(since_id=last_mention_id, tweet_mode="extended")
        if not mention:
            break

        all_list = [mention._json for mention in reversed(mention)]
        all_mentions.extend(all_list)

        last_mention_id = all_mentions[-1]["id"]

    # with open("mention.json", "w") as json_file:
    #     json.dump(all_mentions, json_file)

    # with open("mention.json", "r") as json_file:
    #     mention = json.load(json_file)

    async with aiohttp.ClientSession() as session:
        mention_task = []
        for mention in all_mentions:
            mention_task.append(
                asyncio.create_task(
                    post_request(session, url=PROCESS_MENTION_URL, data=mention)
                )
            )

        all_resp = await asyncio.gather(*mention_task)
        print("all_resp: ", all_resp)
