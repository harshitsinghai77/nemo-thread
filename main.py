from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.sqlite.dbContextManager import SqliteContextManager
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
    fetch_document,
    list_documents,
)
from app.constants import PROD_URL
from app.event_validation import Action
from cron.cron_job import fetch_tweet_mentions

app = FastAPI()
app.mount("/static", StaticFiles(directory="client"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="client")

# on FastAPI startup using sqlite3, create table html_cache
@app.on_event("startup")
async def startup():
    with SqliteContextManager() as cursor:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS html_cache (thread_id TEXT PRIMARY KEY, html TEXT)"
        )


def insert_html_to_sqlite_cache_db(thread_id: str, html_content: str):
    with SqliteContextManager() as cursor:
        cursor.execute(
            "INSERT INTO html_cache (thread_id, html) VALUES (?, ?)",
            (thread_id, html_content),
        )


def get_html_from_sqlite_cache_db(thread_id: str):
    with SqliteContextManager() as cursor:
        cursor.execute("SELECT html FROM html_cache WHERE thread_id = ?", (thread_id,))
        html = cursor.fetchone()
        if html:
            html_bytes = html[0]
            return html_bytes.decode("utf-8")


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

    html_str = get_html_from_sqlite_cache_db(thread_id)
    if html_str:
        return HTMLResponse(html_str)

    thread = thread["data"]
    hero_post, all_posts = thread[0], thread[1:]
    related_thread = get_random_thread(n=4, shuffle=True) or []

    html = templates.TemplateResponse(
        "post.html",
        {
            "request": request,
            "hero_post": hero_post,
            "all_posts": all_posts,
            "related_thread": related_thread,
        },
    )
    insert_html_to_sqlite_cache_db, thread_id, html.body
    return html


@app.get("/feed", response_class=HTMLResponse)
async def get_user_wall(request: Request):

    # all_threads = get_random_thread(shuffle=False) or []
    all_threads = []
    return templates.TemplateResponse(
        "feed.html",
        {"request": request, "threads": all_threads},
    )


@app.post("/check_nemo_twitter_handler")
async def check_user_exists(request: Request):
    twitter_handle = await request.json()
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


@app.get("/document/cdn/{document_id}")
async def cdn(document_id: str):
    """Serve documents from DetaDrive CDN"""
    document = fetch_document(document_id)
    if not document:
        return JSONResponse({"message": "Document not found"}, status_code=404)
    headers = {"Cache-Control": "public, max-age=86400"}
    return Response(
        content=document.read(),
        media_type="application/octet-stream",
        headers=headers,
    )


@app.get("/all-documents")
async def get_list_of_documents():
    """List all documents available in the drive"""
    return list_documents()


@app.post("/__space/v0/actions")
async def cron_job(action: Action):
    if action.event.id == "fetch_tweet_mentions":
        print("Starting cron job")
        await fetch_tweet_mentions()
        print("Ending cron job")
