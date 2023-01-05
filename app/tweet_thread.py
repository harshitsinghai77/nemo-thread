import os

import tweepy
import aiohttp
import asyncio
from app.deta_tweet import save_thread_to_detabase, get_thread_key

bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

auth = tweepy.OAuth2BearerHandler(bearer_token)
api = tweepy.API(auth)

HEADERS = {"Authorization": f"Bearer {bearer_token}"}
THREAD_LIMIT = 40  # Thread usually consists of less than 40 tweets.


def get_all_tweets(tweet):
    screen_name = tweet.user.screen_name
    lastTweetId = tweet.id

    # initialize a list to hold all the tweepy Tweets
    allTweets = []

    # make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name=screen_name, count=200)
    allTweets.extend(new_tweets)

    # save the id of the oldest tweet less one
    oldest = allTweets[-1].id - 1

    # keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0 and oldest >= lastTweetId:
        print(f"getting tweets before {oldest}")
        # all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(
            screen_name=screen_name, count=200, max_id=oldest
        )
        # save most recent tweets
        allTweets.extend(new_tweets)
        # update the id of the oldest tweet less one
        oldest = allTweets[-1].id - 1
        print(f"...{len(allTweets)} tweets downloaded so far")

    outtweets = [tweet.id for tweet in allTweets]
    return outtweets


def print_thread(thread):
    for thread in thread:
        print(thread["full_text"])
        print("")


async def make_request(
    session, url="https://api.twitter.com/1.1/statuses/show.json", params={}
):
    async with session.get(url, params=params) as resp:
        tweet = await resp.json()
        return tweet


def get_original_thread(tweet_id):
    original_tweet = api.get_status(tweet_id, tweet_mode="extended")
    return original_tweet._json


async def get_all_tweets_in_thread(tweet_id):

    threads = []
    original_tweet = api.get_status(tweet_id, tweet_mode="extended")
    threads.append(original_tweet._json)

    all_tweets = get_all_tweets(original_tweet)

    if all_tweets[-1] > original_tweet.id:
        print("Not able to retrieve so older tweets")
        return threads

    end_index = all_tweets.index(original_tweet.id)
    start_index = max(end_index - THREAD_LIMIT, 0)
    fetch_tweet_lst = all_tweets[start_index:end_index]

    TCPConnector = aiohttp.TCPConnector(limit=50)
    async with aiohttp.ClientSession(
        headers=HEADERS, connector=TCPConnector
    ) as session:
        tasks = []
        for tweet in fetch_tweet_lst:
            tasks.append(
                asyncio.create_task(
                    make_request(
                        session, params={"id": tweet, "tweet_mode": "extended"}
                    )
                )
            )

        all_tweets = await asyncio.gather(*tasks)
        threads.extend(all_tweets)

    return threads


async def get_thread(tweet_id: int):

    all_tweets_in_thread = await get_all_tweets_in_thread(tweet_id)
    if not all_tweets_in_thread:
        return

    tweets_lookup = {
        tweet.get("in_reply_to_status_id"): tweet for tweet in all_tweets_in_thread
    }

    thread = [all_tweets_in_thread[0]]
    current_id = thread[-1]["id"]
    while tweets_lookup.get(current_id):
        thread.append(tweets_lookup[current_id])
        current_id = thread[-1]["id"]

    thread = get_embedded_tweets(thread)
    return thread


def save_thread(thread, thread_info):
    if not thread:
        return

    thread_key = get_thread_key(thread[0])
    return save_thread_to_detabase(thread_key, thread, thread_info)


def get_embedded_tweets(thread):
    for tweet in thread:
        all_embeds = []
        for url in tweet.get("entities").get("urls"):
            if "twitter.com" in url.get("expanded_url"):
                resp = api.get_oembed(url.get("expanded_url"))
                all_embeds.append(resp.get("html"))
        tweet["embed_htmls"] = all_embeds
    return thread
