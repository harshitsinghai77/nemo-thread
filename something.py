import asyncio
import time
from app.tweet_reply import respondToTweet

start = time.perf_counter()
asyncio.run(respondToTweet())
end = time.perf_counter()
print("Total time take", end - start)
