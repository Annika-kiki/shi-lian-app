import logging
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.api.router import router
from backend.config.settings import settings
from backend.database.seed import init_db

logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(message)s")
app = FastAPI(title="食练周期 API", version="0.1.0", description="健身饮食与训练记录 MVP")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(","), allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
@app.on_event("startup")
def startup(): init_db()
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
app.mount("/assets/exercises", StaticFiles(directory=Path(__file__).resolve().parents[1] / "frontend/assets/exercises"), name="exercise-images")
app.include_router(router)
@app.get("/health")
def health(): return {"code":0,"message":"ok","data":{"status":"healthy"}}
