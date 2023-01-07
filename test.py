# import asyncio
# from cron.cron_job import fetch_tweet_mentions

# asyncio.run(fetch_tweet_mentions())

# Loop through all the files in the folder ../family-files and upload them to Deta Drive
# import os
# from deta import Deta

# PROJECT_KEY = os.getenv("DETA_PROJECT_KEY")
# deta = Deta(project_key=PROJECT_KEY)
# DETA_DRIVE = deta.Drive("family_documents")

# for file in os.listdir("./family-files"):
#     print("file: ", file)
#     DETA_DRIVE.put(file, path="./family-files/" + file)
