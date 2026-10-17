from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    nickname: str
    avatar: str = ""
    mock_openid: str

@router.post("/mock-login")
async def mock_login(req: LoginRequest):
    # 为了让你立刻测通，这里直接返回写死的 user_id = 1
    return {
        "code": 0,
        "data": {
            "user_id": 1,
            "nickname": req.nickname
        }
    }
