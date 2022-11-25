import os
import json

import tweepy
import aiohttp
import asyncio

access_token = os.getenv("TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
consumer_key_secret = os.getenv("TWITTER_CONSUMER_KEY_SECRET")

auth = tweepy.OAuthHandler(consumer_key, consumer_key_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
# api.verify_credentials()

all_list = []

BASE_URL = "http://127.0.0.1:8000"


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


async def respondToTweet():

    # mentions = api.mentions_timeline(
    #     since_id=1596202726559731712, tweet_mode="extended"
    # )
    # if not mentions:
    #     return

    # for mention in reversed(mentions):
    #     all_list.append(mention._json)

    # with open("mention.json", "w") as json_file:
    #     json.dump(all_list, json_file)

    # exit()

    with open("mention.json", "r") as json_file:
        mention = json.load(json_file)

    mention = mention[0]

    thread_key = get_thread_key(mention)
    thread_id = mention.get("in_reply_to_status_id")
    thread_url = f"{BASE_URL}/create_thread/{thread_id}/{thread_key}"
    create_user_url = f"{BASE_URL}/create_user"
    user = mention.get("user")

    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(get_request(session, url=thread_url)),
            asyncio.create_task(post_request(session, url=create_user_url, data=user)),
        ]

        all_requests = await asyncio.gather(*tasks)
        print("all_requests: ", all_requests)

        thread_info, user = all_requests
        get_url = await post_request(
            session,
            f"{BASE_URL}/user_add_thread",
            data={"user_twitter_handler": user["user_key"], **thread_info},
        )

        print("get_url", get_url)

    # print("mention: ", mention)
