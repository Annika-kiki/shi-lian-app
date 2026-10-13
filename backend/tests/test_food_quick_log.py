import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import SQLAlchemyError
from backend.main import app
from backend.api import food as food_api
from backend.api.router import current_user
from backend.database.session import Base, get_db
from backend.models.entities import User
from backend.models.food import Food, ConfirmedMeal
from backend.services.food import invalidate_catalog

@pytest.fixture
def setup(monkeypatch):
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        db.add(User(id=1, session_nonce='test'))
        db.add_all([Food(name='鸡胸脯肉', aliases=' 鸡胸肉 ; ;鸡胸 ', kcal_per_100g=118,
                         protein_per_100g=24.6, carbs_per_100g=.6, fat_per_100g=1.9, default_quantity_g=120, unit='份'),
                    Food(name='7号酸奶', aliases='酸奶', kcal_per_100g=70, protein_per_100g=4,
                         carbs_per_100g=8, fat_per_100g=2, default_quantity_g=200, unit='杯'),
                    Food(name='100%麦片_原味', kcal_per_100g=100,protein_per_100g=1,carbs_per_100g=1,fat_per_100g=1)])
        db.commit()
    def dependency():
        with factory() as db: yield db
    monkeypatch.setattr(food_api, 'SessionLocal', factory)
    app.dependency_overrides[get_db] = dependency
    invalidate_catalog()
    yield TestClient(app, raise_server_exceptions=False), factory
    app.dependency_overrides.clear()
    invalidate_catalog()
    engine.dispose()

@pytest.mark.parametrize('text,quantity', [('150g鸡胸肉',150),('鸡胸肉150克',150),('150 G 鸡胸肉',150),
                                          ('12.5g鸡胸肉',12.5),('鸡胸肉',120),('2份鸡胸肉',240),('7号酸奶',200)])
def test_parse(setup,text,quantity):
    client,_=setup
    response=client.post('/api/food/parse',json={'text':text})
    assert response.status_code==200
    data=response.json()['data']
    assert data['matched'] and data['quantity_g']==quantity
    if quantity==150:
        assert (data['kcal'],data['protein_g'],data['carbs_g'],data['fat_g'])==(177,36.9,.9,2.9)

@pytest.mark.parametrize('text', ['',None,12,[], '150g', '0g鸡胸肉','-1g鸡胸肉','nang鸡胸肉',
                                '1e999g鸡胸肉','2碗鸡胸肉','2杯螺蛳粉','1g2g鸡胸肉'])
def test_invalid_parse(setup,text):
    assert setup[0].post('/api/food/parse',json={'text':text}).status_code==400

def test_unmatched_search_probe(setup):
    client,_=setup
    data=client.post('/api/food/parse',json={'text':'150g螺蛳粉'}).json()['data']
    assert data==dict(matched=False,food_name='螺蛳粉',quantity_g=150,kcal=200,protein_g=10,carbs_g=20,fat_g=8,confidence=0)
    assert client.get('/api/food/search?q=鸡胸肉').json()['data'][0]['name']=='鸡胸脯肉'
    assert client.get('/api/food/search?q=').json()['data']==[]
    assert len(client.get('/api/food/search?q=%').json()['data'])==1
    assert len(client.get('/api/food/search?q=_').json()['data'])==1
    response=client.get('/__tcb_probe__')
    assert response.status_code==200 and response.text=='ok'

BODY=dict(text='150g鸡胸肉',food_name='鸡胸脯肉',meal_type='午餐',quantity_g=150,kcal=177,protein_g=36.9,carbs_g=.9,fat_g=2.9)

def test_save_auth_validation_rollback(setup,monkeypatch):
    client,factory=setup
    assert client.post('/api/quick-log',headers={'X-User-Id':'1'},json=BODY).status_code==401
    app.dependency_overrides[current_user]=lambda: User(id=1)
    response=client.post('/api/quick-log',json=BODY)
    assert response.status_code==200
    assert response.json()['data']['created_at'].endswith('Z')
    with factory() as db:
        assert db.get(ConfirmedMeal,response.json()['data']['id']).user_id==1
    for field,value in [('quantity_g',0),('quantity_g',-1),('kcal',-1),('fat_g','nan'),('food_name',''),('meal_type',None)]:
        assert client.post('/api/quick-log',json={**BODY,field:value}).status_code==400
    missing=BODY.copy();missing.pop('kcal')
    assert client.post('/api/quick-log',json=missing).status_code==400
    db=factory()
    rolled=[]
    original=db.rollback
    def rollback(): rolled.append(True);original()
    monkeypatch.setattr(db,'rollback',rollback)
    monkeypatch.setattr(db,'commit',lambda: (_ for _ in ()).throw(SQLAlchemyError('test failure')))
    def dependency(): yield db
    app.dependency_overrides[get_db]=dependency
    assert client.post('/api/quick-log',json=BODY).status_code==503
    assert rolled
    db.close()
    with factory() as check:
        assert len(check.scalars(select(ConfirmedMeal)).all())==1

def test_import(setup,tmp_path):
    from openpyxl import Workbook
    from backend.database.import_foods import COLUMNS,import_foods
    _,factory=setup
    path=tmp_path/'foods.xlsx'
    workbook=Workbook();sheet=workbook.active;sheet.title='common_foods_356'
    sheet.append(COLUMNS);sheet.append(['新食物',None,None,100,None,None,None,None,None]);workbook.save(path)
    with factory() as db:
        result=import_foods(db,path);assert result['added']==1 and result['committed']
        assert import_foods(db,path)['skipped']==1
        sheet.cell(2,4,101);workbook.save(path)
        assert import_foods(db,path)['updated']==1
        sheet.append(['坏数据',None,None,-1,None,None,None,None,None]);workbook.save(path)
        result=import_foods(db,path);assert result['errors']==1 and not result['committed']

def test_catalog_cache_and_fuzzy(setup,monkeypatch):
    from backend.services import food
    _,factory=setup
    with factory() as db:
        calls=[]
        execute=db.execute
        def counted(*args,**kwargs): calls.append(1);return execute(*args,**kwargs)
        monkeypatch.setattr(db,'execute',counted)
        assert food.parse(db,'鸡胸脯肉')['confidence']==1
        assert food.parse(db,'鸡胸脯')['matched']
        assert food.parse(db,'鸡胸铺肉')['matched']
        assert len(calls)==1
        assert food.parse(db,'螺蛳粉')['quantity_g']==100
        assert food.parse(db,'1杯酸奶')['quantity_g']==200

@pytest.mark.parametrize('payload',[None,[],{'text':'鸡胸肉','kcal':1}, {**BODY,'kcal':10**1000}])
def test_bad_confirmed_bodies(setup,payload):
    app.dependency_overrides[current_user]=lambda: User(id=1)
    assert setup[0].post('/api/quick-log',json=payload).status_code==400

def test_nonfinite_validation():
    from backend.services.food import numeric
    for value in (float('nan'),float('inf'),-float('inf'),True):
        with pytest.raises(ValueError):numeric(value,'value')
