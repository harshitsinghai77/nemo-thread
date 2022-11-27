from app.tweet_thread import get_thread, save_thread
from app.tweet_reply import process_twitter_mention, reply_to_tweet
from app.deta_tweet import (
    get_thread_from_detabase,
    extract_thread_info,
    get_user,
    get_new_user_payload,
    create_new_user,
    get_user_twitter_handle,
    update_user_thread_list,
    get_last_processed_id,
    add_last_processed_id,
    get_random_thread,
)
from app.constants import PROD_URL

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory="client"), name="static")

templates = Jinja2Templates(directory="client")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("landing-page/index.html", {"request": request})


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

    update_user_thread_list(key=twitter_handler, thread_info=thread_info)
    user_wall = PROD_URL + "/user/" + twitter_handler
    thread_link = PROD_URL + "/thread/" + thread_info["thread_url"]
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"user_wall": user_wall, "thread_link": thread_link},
    )


@app.post("/reply_to_user")
async def reply_to_user(request: Request):
    reply_user = await request.json()
    if not reply_user:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "reply_user dict not found "},
        )

    screen_name, thread_info, mention_id = (
        reply_user.get("screen_name"),
        reply_user.get("thread_info"),
        reply_user.get("mention_id"),
    )
    if not (screen_name and screen_name and mention_id):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "keys (screen_name, thread_info, mention_id) not found in request "
            },
        )

    reply_to_tweet(
        screen_name=screen_name, thread_info=thread_info, mention_id=mention_id
    )
    add_last_processed_id(str(mention_id))

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"success": True},
    )


@app.post("/process_mention")
async def process_mention(request: Request):
    mention = await request.json()
    if not mention:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "mention not found "},
        )

    await process_twitter_mention(mention)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"success": True},
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


@app.get("/last_processed_id")
async def last_processed_id():
    return get_last_processed_id()


@app.get("/thread/{thread_id}", response_class=HTMLResponse)
async def get_thread_by_thread_id(request: Request, thread_id: str):

    if not thread_id:
        return HTMLResponse("<h1> No Thread id found </h1>")

    thread = get_thread_from_detabase(thread_id)
    if not thread:
        return HTMLResponse("<h1> Invalid Thread id </h1>")
    thread = thread["data"]

    hero_post, all_posts = thread[0], thread[1:]
    related_thread = get_random_thread(n=4, shuffle=True) or []

    return templates.TemplateResponse(
        "post.html",
        {
            "request": request,
            "hero_post": hero_post,
            "all_posts": all_posts,
            "related_thread": related_thread,
        },
    )


@app.get("/feed", response_class=HTMLResponse)
async def get_user_wall(request: Request):

    all_threads = get_random_thread(shuffle=False) or []
    return templates.TemplateResponse(
        "feed.html",
        {"request": request, "threads": all_threads},
    )


@app.post("/check_nemo_twitter_handler")
async def check_user_exists(request: Request):
    twitter_handle = await request.json()
    print("twitter_handle: ", twitter_handle)
    if not twitter_handle:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "twitter_handle not found"},
        )

    twitter_handle = twitter_handle.get("twitter_handler")
    if not twitter_handle:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"success": False, "message": "Invalid entity"},
        )

    user = get_user(twitter_handle)
    success = True if user else False
    message = (
        "Account exists"
        if success
        else "Twitter Handler not registered with our account."
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"success": success, "message": message},
    )


@app.get("/user/{user_id}", response_class=HTMLResponse)
async def get_user_wall(request: Request, user_id: str):
    if not user_id:
        return HTMLResponse("<h1> No user Found </h1>")

    user = get_user(user_id)
    if not user:
        return HTMLResponse(
            "<h1> Twitter Handler not registered. <br /> You currently have no threads associated with your account. <br /> You will be automatically registered when you tag @focus_with_nemo in any twitter thread. <br /> <h2>Thanks for using Nemo 😊</h2< </h1>"
        )
    return templates.TemplateResponse(
        "posts.html",
        {"request": request, "user": user},
    )


@app.get("/home", response_class=HTMLResponse)
async def user_home(request: Request):
    return templates.TemplateResponse(
        "components/user-input.html",
        {"request": request},
    )
