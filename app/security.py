import hashlib, secrets, time
from collections import defaultdict, deque
from fastapi import Header, HTTPException, Request
from sqlalchemy import select, insert
from .config import ADMIN_API_KEY, REQUIRE_API_KEY, DEFAULT_RATE_LIMIT
from .db import engine, api_keys, now_iso

_hits = defaultdict(deque)


def hash_key(k: str) -> str:
    return hashlib.sha256(k.encode()).hexdigest()


def create_key(owner: str, rate_limit: int = DEFAULT_RATE_LIMIT) -> str:
    raw = "sii_" + secrets.token_urlsafe(32)
    with engine.begin() as c:
        c.execute(insert(api_keys).values(key_hash=hash_key(raw), owner=owner,
                                          rate_limit=rate_limit, active=True, created_at=now_iso()))
    return raw


def _limit(ident: str, limit: int):
    now = time.time()
    q = _hits[ident]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        retry = int(60 - (now - q[0])) + 1
        raise HTTPException(429, "Rate limit exceeded", headers={"Retry-After": str(retry)})
    q.append(now)


async def require_key(request: Request, x_api_key: str = Header(default=None)):
    if ADMIN_API_KEY and x_api_key and secrets.compare_digest(x_api_key, ADMIN_API_KEY):
        return "admin"
    if not REQUIRE_API_KEY:
        _limit("ip:" + (request.client.host if request.client else "unknown"), DEFAULT_RATE_LIMIT)
        return "anonymous"
    if not x_api_key:
        raise HTTPException(401, "Missing X-API-Key header")
    with engine.connect() as c:
        row = c.execute(select(api_keys).where(api_keys.c.key_hash == hash_key(x_api_key))).first()
    if not row or not row.active:
        raise HTTPException(401, "Invalid API key")
    _limit("key:" + str(row.id), row.rate_limit or DEFAULT_RATE_LIMIT)
    return str(row.id)


async def require_admin(x_api_key: str = Header(default=None)):
    if not ADMIN_API_KEY or not x_api_key or not secrets.compare_digest(x_api_key, ADMIN_API_KEY):
        raise HTTPException(403, "Admin only (Berra)")
    return True
