from types import SimpleNamespace
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import Base, get_db
from backend.models.entities import User, UserProfile
import backend.api.router as router

@pytest.fixture
def isolated(monkeypatch):
    engine=create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory=sessionmaker(bind=engine)
    def get_session():
        with factory() as db:yield db
    app.dependency_overrides[get_db]=get_session
    monkeypatch.setattr(router,'settings',SimpleNamespace(app_env='development',session_secret='test-secret',session_ttl_seconds=3600))
    import backend.main as main
    main.rate_limit_buckets.clear()
    yield TestClient(app),factory
    app.dependency_overrides.clear()
    engine.dispose()

BODY={'nickname':'练食记用户','avatar':'','mock_openid':'mock_练食记用户'}

def test_contract_reuses_identity(isolated):
    client,factory=isolated
    first=client.post('/api/auth/mock-login',json=BODY)
    assert first.status_code==200
    data=first.json()['data']
    assert first.json()['code']==0 and data['nickname']=='练食记用户'
    assert data['user_id']>0 and data['access_token']
    second=client.post('/api/auth/mock-login',json={**BODY,'nickname':'新昵称'})
    assert second.json()['data']['user_id']==data['user_id']
    assert second.json()['data']['nickname']=='新昵称'
    with factory() as db:
        assert len(db.scalars(select(User)).all())==1
        assert db.get(UserProfile,data['user_id']) is not None
    response=client.get('/api/users/me',headers={'Authorization':f"Bearer {data['access_token']}"})
    assert response.status_code==200
    assert client.get('/api/users/me',headers={'X-User-Id':str(data['user_id'])}).status_code==401

@pytest.mark.parametrize('payload',[[],None,{'nickname':''},{'nickname':123},{'avatar':42},{'mock_openid':''},{'mock_openid':[]},{'nickname':'a'*65}])
def test_invalid_request(isolated,payload):
    response=isolated[0].post('/api/auth/mock-login',json=payload)
    assert response.status_code==400
    assert response.json()['code']==-1 and response.json()['message']

def test_invalid_json_and_content_type(isolated):
    client,_=isolated
    for content,headers in [('bad',{'Content-Type':'application/json'}),('{}',{'Content-Type':'text/plain'})]:
        response=client.post('/api/auth/mock-login',content=content,headers=headers)
        assert response.status_code==400 and response.json()['code']==-1

@pytest.mark.parametrize('environment',['staging','production'])
def test_deployed_error_contract(isolated,monkeypatch,environment):
    monkeypatch.setattr(router,'settings',SimpleNamespace(app_env=environment))
    response=isolated[0].post('/api/auth/mock-login',json=BODY)
    assert response.status_code==404 and response.json()['code']==-1
    assert '微信登录' in response.json()['message']

def test_database_rollback(isolated,monkeypatch):
    client,factory=isolated
    db=factory();rolled=[];rollback=db.rollback
    def rollback_spy():rolled.append(True);rollback()
    monkeypatch.setattr(db,'rollback',rollback_spy)
    def failing_commit():raise SQLAlchemyError('private database failure')
    monkeypatch.setattr(db,'commit',failing_commit)
    def session():yield db
    app.dependency_overrides[get_db]=session
    response=client.post('/api/auth/mock-login',json=BODY)
    assert response.status_code==503 and response.json()['code']==-1
    assert 'private database failure' not in response.text
    assert rolled
    db.close()
    with factory() as check:assert check.scalars(select(User)).all()==[]

def test_rate_limit_error_contract(isolated,monkeypatch):
    import backend.main as main
    monkeypatch.setattr(main,'settings',SimpleNamespace(sensitive_rate_limit_per_minute=1))
    client,_=isolated
    assert client.post('/api/auth/mock-login',json=BODY).status_code==200
    response=client.post('/api/auth/mock-login',json=BODY)
    assert response.status_code==429
    assert response.json()=={'code':-1,'message':'请求过于频繁，请稍后重试'}
    main.rate_limit_buckets.clear()
