import os

import tweepy
import aiohttp
import asyncio

from app.constants import ROOT_URL

access_token = os.getenv("TWITTER_ACCESS_TOKEN", "MY_TWITTER_ACCESS_TOKEN")
access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "MY_TWITTER_ACCESS_TOKEN_SECRET")
consumer_key = os.getenv("TWITTER_CONSUMER_KEY", "MY_TWITTER_CONSUMER_KEY")
consumer_key_secret = os.getenv("TWITTER_CONSUMER_KEY_SECRET", "MY_TWITTER_CONSUMER_KEY_SECRET")

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


async def process_twitter_mention(mention):

    thread_key = get_thread_key(mention)
    thread_id = mention.get("in_reply_to_status_id")

    thread_url = f"{ROOT_URL}/create_thread/{thread_id}/{thread_key}"
    create_user_url = f"{ROOT_URL}/create_user"
    user = mention.get("user")

    async with aiohttp.ClientSession() as session:
        # Process thread and create new user in a parallel request
        tasks = [
            asyncio.create_task(get_request(session, url=thread_url)),
            asyncio.create_task(post_request(session, url=create_user_url, data=user)),
        ]

        all_requests = await asyncio.gather(*tasks)

        # Add thread to user's thread list
        thread_info, user = all_requests
        thread_info_req = await post_request(
            session,
            f"{ROOT_URL}/user_add_thread",
            data={"user_twitter_handler": user["user_key"], **thread_info},
        )

        # Reply to the user
        reply_to_user_data = {
            "screen_name": mention["user"]["screen_name"],
            "thread_info": thread_info_req,
            "mention_id": mention["id"],
        }
        await post_request(
            session,
            f"{ROOT_URL}/reply_to_user",
            data=reply_to_user_data,
        )


def get_reply_text(screen_name, thread_info):
    return f"""
        Hey @{screen_name}, Thanks for using Nemo. \n\nHere's your thread: {thread_info['thread_link']} \n\nYou can check all your saved threads here: {thread_info['user_wall']}
    """


def reply_to_tweet(screen_name, thread_info, mention_id):
    reply_text = get_reply_text(screen_name, thread_info)
    api.update_status(status=reply_text, in_reply_to_status_id=mention_id)
