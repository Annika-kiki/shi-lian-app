"""Development login contract; production uses verified WeChat identities."""
from sqlalchemy.exc import SQLAlchemyError
from backend.models.entities import User, UserProfile
from backend.services.auth import create_session_token


def mock_login_payload(db, settings, payload):
    if not isinstance(payload, dict):
        raise ValueError('请求体必须为JSON对象')
    nickname = payload.get('nickname', '练食记用户')
    avatar = payload.get('avatar', '')
    openid = payload.get('mock_openid')
    for label, value, limit, allow_empty in (
        ('nickname', nickname, 64, False), ('avatar', avatar, 512, True),
    ):
        if not isinstance(value, str) or len(value) > limit or (not allow_empty and not value.strip()):
            raise ValueError(f'{label}必须为{"非空" if not allow_empty else ""}字符串，最多{limit}字符')
    nickname = nickname.strip()
    if openid is None:
        openid = f'mock_{nickname}'
    if not isinstance(openid, str) or not openid.strip() or len(openid) > 128:
        raise ValueError('mock_openid必须为非空字符串，最多128字符')
    openid = openid.strip()
    try:
        user = db.query(User).filter_by(openid=openid).first()
        if user is None:
            user = User(openid=openid, nickname=nickname, avatar=avatar)
            db.add(user)
            db.flush()
        else:
            user.nickname, user.avatar = nickname, avatar
        if db.get(UserProfile, user.id) is None:
            db.add(UserProfile(user_id=user.id))
        result = {'code':0, 'data':{
            'user_id':user.id, 'nickname':user.nickname,
            'access_token':create_session_token(user.id, user.session_nonce, settings.session_secret, settings.session_ttl_seconds),
            'token_type':'Bearer', 'expires_in':settings.session_ttl_seconds,
        }}
        db.commit()
        return result
    except SQLAlchemyError:
        db.rollback()
        raise
