import json
import time
import asyncio
from app.tweet_thread import get_thread, save_thread
from app.tweet_reply import respondToTweet
from app.deta_tweet import (
    get_thread_from_detabase,
    get_user,
)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="client"), name="static")

templates = Jinja2Templates(directory="client")


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse("<h1> Welcome to Twitter Blog </h1>")


@app.get("/thread/{thread_id}", response_class=HTMLResponse)
async def display_thread(request: Request, thread_id: str):

    if not thread_id:
        return HTMLResponse("<h1> No Thread id found </h1>")

    thread = get_thread_from_detabase(thread_id)
    if not thread:
        return HTMLResponse("<h1> Invalid Thread id </h1>")
    thread = thread["data"]

    hero_post = thread[0]
    all_posts = thread[1:]

    return templates.TemplateResponse(
        "post.html",
        {"request": request, "hero_post": hero_post, "all_posts": all_posts},
    )


@app.get("/user/{user_id}", response_class=HTMLResponse)
async def get_user_wall(request: Request, user_id: str):
    if not user_id:
        return HTMLResponse("<h1> No Thread id found </h1>")

    user = get_user(user_id)
    return templates.TemplateResponse(
        "posts.html",
        {"request": request, "user": user},
    )


@app.get("/fetch_thread/{thread_id}", response_class=HTMLResponse)
async def fetch_thread(thread_id: str):
    if not thread_id:
        return HTMLResponse("<h1> No Thread id found </h1>")

    thread = await get_thread(thread_id)
    key = save_thread(thread)
    return key
