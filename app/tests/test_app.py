import fakeredis
import pytest

import app as shortener


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(shortener, "r", fakeredis.FakeRedis(decode_responses=True))
    shortener.app.config["TESTING"] = True
    return shortener.app.test_client()


def shorten(client, url):
    client.post("/shorten", data={"url": url})
    return shortener.r.lrange(shortener.RECENT_KEY, 0, 0)[0]


def test_shorten_stores_url_and_lists_it(client):
    code = shorten(client, "https://example.com/a/very/long/path")
    assert len(code) == shortener.CODE_LEN
    assert shortener.r.get(f"mg:url:{code}") == "https://example.com/a/very/long/path"
    assert b"example.com/a/very/long/path" in client.get("/").data


def test_short_link_redirects_and_counts_clicks(client):
    code = shorten(client, "https://example.com")
    for _ in range(2):
        resp = client.get(f"/x/{code}")
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://example.com"
    assert shortener.r.get(f"mg:clicks:{code}") == "2"


@pytest.mark.parametrize("bad", ["", "not a url", "ftp://example.com", "javascript:alert(1)"])
def test_invalid_urls_are_rejected(client, bad):
    client.post("/shorten", data={"url": bad})
    assert shortener.r.llen(shortener.RECENT_KEY) == 0


def test_unknown_code_returns_404(client):
    assert client.get("/x/nope42").status_code == 404


def test_recent_list_keeps_only_the_last_ten(client):
    for i in range(12):
        shorten(client, f"https://example.com/{i}")
    assert shortener.r.llen(shortener.RECENT_KEY) == shortener.RECENT_LIMIT


def test_health_reports_ok(client):
    assert client.get("/health").status_code == 200
