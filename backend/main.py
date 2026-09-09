import logging
from contextlib import asynccontextmanager
from collections import defaultdict, deque
from time import monotonic
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from backend.api.router import router
from backend.config.settings import settings, validate_production_settings
from backend.database.seed import init_db
from backend.database.session import engine
from sqlalchemy import text

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_settings()
    if not settings.is_deployed:
        init_db()
    yield


app = FastAPI(
    title="食练周期 API",
    version="0.1.0",
    description="健身饮食与训练记录",
    lifespan=lifespan,
    docs_url=None if settings.is_deployed else "/docs",
    redoc_url=None if settings.is_deployed else "/redoc",
    openapi_url=None if settings.is_deployed else "/openapi.json",
)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
configured_hosts = [host.strip() for host in settings.allowed_hosts.split(",") if host.strip()]
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=list(dict.fromkeys(configured_hosts + ["127.0.0.1", "localhost"])),
)

rate_limit_buckets = defaultdict(deque)
rate_limited_paths = {
    "/api/auth/wechat-login",
    "/api/auth/cloud-login",
    "/api/auth/mock-login",
    "/api/recipes/generate",
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if request.url.path in rate_limited_paths:
        now = monotonic()
        client_host = request.client.host if request.client else "unknown"
        bucket = rate_limit_buckets[(client_host, request.url.path)]
        while bucket and bucket[0] <= now - 60:
            bucket.popleft()
        if len(bucket) >= settings.sensitive_rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": "60", "Cache-Control": "no-store"},
                content={"code": 429, "message": "请求过于频繁，请稍后重试", "data": {}},
            )
        bucket.append(now)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 1024 * 1024:
                return JSONResponse(status_code=413, content={"code": 413, "message": "请求内容过大", "data": {}})
        except ValueError:
            return JSONResponse(status_code=400, content={"code": 400, "message": "Content-Length 无效", "data": {}})
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response
@app.exception_handler(HTTPException)
async def http_errors(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"code": exc.status_code, "message": str(exc.detail), "data": {}})
@app.exception_handler(RequestValidationError)
async def validation_errors(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"code": 422, "message": "请求参数校验失败", "data": {"errors": exc.errors()}})
@app.exception_handler(Exception)
async def errors(request:Request, exc:Exception):
    if hasattr(exc,"status_code"): return JSONResponse(status_code=exc.status_code,content={"code":exc.status_code,"message":str(exc.detail),"data":{}})
    logging.exception("Unhandled API error"); return JSONResponse(status_code=500,content={"code":500,"message":"服务器内部错误","data":{}})
app.include_router(router)
@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(503, "数据库不可用") from exc
    return {"code":0,"message":"ok","data":{"status":"healthy"}}
