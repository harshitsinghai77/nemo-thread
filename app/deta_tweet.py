import os
import random
from datetime import datetime

from deta import Deta

PROJECT_KEY = os.getenv("DETA_PROJECT_KEY")
deta = Deta(project_key=PROJECT_KEY)


def getdetabase(db_name):
    return deta.Base(db_name)


DETA_BASE_LAST_MENTION = getdetabase("nemo_twitter_last_processed_mention")
DETA_BASE_THREAD = getdetabase("nemo_twitter_thread")
DETA_BASE_TWITTER_USER = getdetabase("nemo_twitter_user")
DETA_DRIVE = deta.Drive("family_documents")

REALLY_REALLY_BIG_NUMBER = 8.64e15


def get_thread_key(thread):
    if not thread:
        return
    screen_name = thread["user"]["screen_name"].replace(" ", "_").lower()
    key = screen_name + "_" + thread["id_str"]
    return key


def get_last_mentioned_key():
    """For context why keys are generated like this: https://github.com/orgs/deta/discussions/344#discussioncomment-3263320"""
    return str(REALLY_REALLY_BIG_NUMBER - datetime.now().timestamp())


def add_last_processed_id(processed_id):
    last_mentioned_key = get_last_mentioned_key()
    DETA_BASE_LAST_MENTION.put(
        data={"processed_id": processed_id, "timestamp": str(datetime.now())},
        key=last_mentioned_key,
    )


def get_last_processed_id():
    res = DETA_BASE_LAST_MENTION.fetch(query={}, limit=1)
    all_items = res.items[-1] if res.items else None
    return all_items


def get_user_twitter_handle(user_info):
    return user_info.get("screen_name")


def get_new_user_payload(user_info):
    if not user_info:
        return None, None

    screen_name = get_user_twitter_handle(user_info)
    new_user = {
        "twitter_handle": screen_name,
        "name": user_info.get("name"),
        "description": user_info.get("description"),
        "threads": [],
        "location": user_info.get("location"),
        "profile_image_url": user_info.get("profile_image_url_https"),
        "profile_banner_url": user_info.get("profile_banner_url"),
        "profile_use_background_image": user_info.get("profile_use_background_image"),
    }

    if new_user.get("profile_image_url"):
        new_user["profile_image_url"] = new_user["profile_image_url"].replace(
            "_normal", "_400x400"
        )

    return screen_name, new_user


def extract_thread_info(thread_post):
    if not thread_post:
        return

    thread_meta = {
        "title": thread_post["full_text"],
        "thread_url": get_thread_key(thread_post),
        "author": thread_post["user"]["name"],
        "twitter_handler": thread_post["user"]["screen_name"],
        "post_image_url": thread_post["user"]["profile_image_url_https"].replace(
            "_normal", "_400x400"
        ),
        "created_at": str(datetime.now().strftime("%Y-%m-%d %I:%M %p")),
    }
    return thread_meta


def save_thread_to_detabase(key, thread, thread_info):
    if not (thread and key and thread_info):
        return

    raw_thread = {"data": thread, "thread_info": thread_info}
    DETA_BASE_THREAD.put(raw_thread, key=key)
    return key


def get_thread_from_detabase(key):
    if not key:
        return
    return DETA_BASE_THREAD.get(key)


def create_new_user(key, new_user):
    if not new_user:
        return

    # check if user already exist:
    user = get_user(key)
    if user:
        return user.get("twitter_handle")

    DETA_BASE_TWITTER_USER.put(new_user, key=key)
    return key


def get_user(key):
    if not key:
        return

    return DETA_BASE_TWITTER_USER.get(key)


def update_user_thread_list(key, thread_info):
    update = {"threads": DETA_BASE_TWITTER_USER.util.append(thread_info)}
    DETA_BASE_TWITTER_USER.update(update, key)


def get_random_thread(n=100, shuffle=False):
    thread = DETA_BASE_THREAD.fetch(query=None, limit=1000)
    thread_items = thread.items
    if shuffle:
        thread_items = [random.choice(thread_items) for _ in range(n)]

    all_thread = list(map(lambda x: x["thread_info"], thread_items))
    return all_thread


def fetch_document(document_name):
    """Fetch and return the document from Deta Drive."""
    return DETA_DRIVE.get(document_name)


def list_documents():
    """List all the documents in the Deta Drive."""
    return DETA_DRIVE.list(limit=1000)
