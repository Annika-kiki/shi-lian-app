from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class LoginRequest(BaseModel):
    nickname: str
    avatar: str = ""
    mock_openid: str

@router.post("/mock-login")
async def mock_login(req: LoginRequest):
    return {
        "code": 0,
        "data": {
            "user_id": 1,
            "nickname": req.nickname
        }
    }
