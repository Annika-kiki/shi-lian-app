"""Server-side exchange of a temporary wx.login code."""

import httpx
from fastapi import HTTPException


CODE_TO_SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


def exchange_login_code(code: str, app_id: str, app_secret: str) -> str:
    try:
        response = httpx.get(
            CODE_TO_SESSION_URL,
            params={
                "appid": app_id,
                "secret": app_secret,
                "js_code": code,
                "grant_type": "authorization_code",
            },
            timeout=5.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "微信登录服务暂时不可用") from exc

    openid = payload.get("openid")
    if not openid:
        raise HTTPException(401, "微信登录凭证无效或已过期")
    return str(openid)
