import os
import json
import requests

import tweepy
import aiohttp
import asyncio

from app.constants import ROOT_URL

access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_key_secret = os.getenv("TWITTER_CONSUMER_KEY_SECRET")

auth = tweepy.OAuthHandler(consumer_key, consumer_key_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
# api.verify_credentials()


def get_thread_key(thread):
    if not thread:
        return
    screen_name = thread["in_reply_to_screen_name"].replace(" ", "_").lower()
    key = screen_name + "_" + thread["in_reply_to_status_id_str"]
    return key


async def get_request(session, url):
    async with session.get(url) as resp:
        tweet = await resp.json()
        return tweet


async def post_request(session, url, data):
    async with session.post(url, json=data) as resp:
        tweet = await resp.json()
        return tweet


async def process_mention(mention):

    thread_key = get_thread_key(mention)
    thread_id = mention.get("in_reply_to_status_id")

    thread_url = f"{ROOT_URL}/create_thread/{thread_id}/{thread_key}"
    create_user_url = f"{ROOT_URL}/create_user"
    user = mention.get("user")

    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(get_request(session, url=thread_url)),
            asyncio.create_task(post_request(session, url=create_user_url, data=user)),
        ]

        all_requests = await asyncio.gather(*tasks)
        # print("all_requests: ", all_requests)

        thread_info, user = all_requests
        thread_info_req = await post_request(
            session,
            f"{ROOT_URL}/user_add_thread",
            data={"user_twitter_handler": user["user_key"], **thread_info},
        )

        reply_to_user_data = {
            "screen_name": mention["user"]["screen_name"],
            "thread_info": thread_info_req,
            "mention_id": mention["id"],
        }
        resp = await post_request(
            session,
            f"{ROOT_URL}/reply_to_user",
            data=reply_to_user_data,
        )
        print("resp", resp)


async def respondToTweet():

    req_last_mention_id = requests.get(ROOT_URL + "/last_processed_id")
    last_mention_id = req_last_mention_id.json()
    if last_mention_id:
        last_mention_id = last_mention_id["processed_id"]

    all_mentions = []
    # mention = api.mentions_timeline(since_id=last_mention_id, tweet_mode="extended")
    while True:
        mention = api.mentions_timeline(since_id=last_mention_id, tweet_mode="extended")
        if not mention:
            break

        all_list = [mention._json for mention in reversed(mention)]
        all_mentions.extend(all_list)

        last_mention_id = all_mentions[-1]["id"]
        print("last_mention_id: ", last_mention_id)

    # exit()

    # all_list = [mention._json for mention in reversed(mention)]

    with open("mention_1.json", "w") as json_file:
        json.dump(all_mentions, json_file)

    # exit()

    # with open("mention.json", "r") as json_file:
    #     mention = json.load(json_file)

    print("all_mentions: ", len(all_mentions))
    for mention in all_mentions:
        await process_mention(mention)
