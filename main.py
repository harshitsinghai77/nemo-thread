from app.tweet_thread import get_thread, save_thread
from app.deta_tweet import (
    get_thread_from_detabase,
    extract_thread_info,
    get_user,
    get_new_user_payload,
    create_new_user,
    get_user_twitter_handle,
    update_user_thread_list,
)

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="client"), name="static")

templates = Jinja2Templates(directory="client")

ROOT_URL = "https://qxq5l6.deta.dev/"


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse("<h1> Welcome to Twitter Blog </h1>")


@app.post("/create_user")
async def create_user(request: Request):
    user_info = await request.json()
    if not user_info:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "user_info not found"},
        )

    user_key = get_user_twitter_handle(user_info)
    user = get_user(user_key)
    if not user:
        key, new_user = get_new_user_payload(user_info)
        user_key = create_new_user(key=key, new_user=new_user)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"user_key": user_key},
    )


@app.post("/user_add_thread")
async def add_thread_to_user(request: Request):
    user_thread_details = await request.json()
    if not user_thread_details:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "user_thread_details not found"},
        )

    twitter_handler = user_thread_details["user_twitter_handler"]
    thread_info = user_thread_details["thread_info"]
    print("thread_info: ", thread_info)

    update_user_thread_list(key=twitter_handler, thread_info=thread_info)
    user_wall = ROOT_URL + "user/" + twitter_handler
    thread_link = ROOT_URL + "thread/" + thread_info["thread_url"]
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"user_wall": user_wall, "thread_link": thread_link},
    )


@app.get("/thread/{thread_id}", response_class=HTMLResponse)
async def get_thread_by_thread_id(request: Request, thread_id: str):

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


@app.get("/create_thread/{thread_id}/{thread_key}", response_class=HTMLResponse)
async def create_new_thread(thread_id: str, thread_key: str = None):
    if not thread_id:
        return HTMLResponse("<h1> No Thread id found </h1>")

    thread = None
    # check if thread already exists in detabase
    if thread_key:
        thread = get_thread_from_detabase(key=thread_key)
        thread_info = thread.get("thread_info") if thread else None

    if not thread:
        # if not, get thread and save it in detabase
        thread = await get_thread(thread_id)
        thread_info = extract_thread_info(thread[0])
        thread_key = save_thread(thread, thread_info)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"thread_key": thread_key, "thread_info": thread_info},
    )
