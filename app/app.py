import os
import secrets
from urllib.parse import urlparse

from flask import Flask, render_template, request, redirect, url_for, abort, flash
import redis

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")

r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "mg-redis"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    decode_responses=True,
)

URL_KEY = "mg:url:{}"        # short code -> long URL
CLICK_KEY = "mg:clicks:{}"   # short code -> click count
RECENT_KEY = "mg:recent"     # list of recent codes (most recent first)
RECENT_LIMIT = 10
CODE_LEN = 6


def _valid_url(u: str) -> bool:
    try:
        p = urlparse(u)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False


def _new_code() -> str:
    for _ in range(8):
        code = secrets.token_urlsafe(CODE_LEN)[:CODE_LEN]
        if not r.exists(URL_KEY.format(code)):
            return code
    raise RuntimeError("could not allocate unique code")


@app.get("/")
def index():
    codes = r.lrange(RECENT_KEY, 0, RECENT_LIMIT - 1)
    recent = []
    for c in codes:
        long_url = r.get(URL_KEY.format(c))
        if long_url is None:
            continue
        clicks = int(r.get(CLICK_KEY.format(c)) or 0)
        recent.append({"code": c, "long": long_url, "clicks": clicks})
    return render_template("index.html", recent=recent)


@app.post("/shorten")
def shorten():
    long_url = (request.form.get("url") or "").strip()
    if not _valid_url(long_url):
        flash("Please enter a valid http(s) URL.")
        return redirect(url_for("index"))

    code = _new_code()
    r.set(URL_KEY.format(code), long_url)
    r.set(CLICK_KEY.format(code), 0)
    r.lpush(RECENT_KEY, code)
    r.ltrim(RECENT_KEY, 0, RECENT_LIMIT - 1)
    return redirect(url_for("index"))


@app.get("/x/<code>")
def follow(code):
    long_url = r.get(URL_KEY.format(code))
    if long_url is None:
        abort(404)
    r.incr(CLICK_KEY.format(code))
    return redirect(long_url, code=302)


@app.get("/health")
def health():
    try:
        r.ping()
        return {"status": "ok"}, 200
    except redis.RedisError as e:
        return {"status": "error", "detail": str(e)}, 500
