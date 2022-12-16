import asyncio
from cron.cron_job import fetch_tweet_mentions

asyncio.run(fetch_tweet_mentions())
