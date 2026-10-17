const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const root = path.join(__dirname, '../releases/miniprogram-2')
const target = 'prod-d4gls6f9gaef2c320/flask-3xwi'
function setup(storage = {}, responder = () => ({ statusCode: 200, data: { code: 0, data: {} } })) {
  const calls = [], init = []
  let logins = 0
  const wx = {
    getStorageSync: k => storage[k], setStorageSync: (k,v) => {storage[k]=v}, removeStorageSync: k => {delete storage[k]},
    cloud: {init: o => init.push(o), callContainer: async o => {
      calls.push(o)
      if (o.path === '/api/auth/cloud-login') {
        logins++
        return {statusCode:200,data:{code:0,data:{user_id:9,access_token:`token${logins}`}}}
      }
      return responder(o)
    }}
  }
  const module = {exports:{}}
  vm.runInNewContext(fs.readFileSync(path.join(root,'utils/api.js'),'utf8'), {wx,module,require: () => ({getUser:()=>({}),calculateNutritionTargets:()=>({dailyCalorieTarget:1800,proteinTargetG:90,carbTargetG:200,fatTargetG:50})})})
  return {api:module.exports,calls,init,storage,get logins(){return logins}}
}
async function authChecks() {
  for (const storage of [{userId:3},{userId:3,accessToken:'old',cloudAuthTarget:'wrong'},{userId:3,accessToken:'old',cloudAuthTarget:target}]) {
    const x=setup(storage)
    await assert.rejects(x.api.ensureLogin(),/协议/)
    await assert.rejects(x.api.getMe(),/协议/)
    assert.equal(x.calls.length,0)
    x.api.setPrivacyConsent(true)
    await Promise.all([x.api.ensureLogin(),x.api.getMe(),x.api.getTodayDashboard()])
    assert.equal(x.logins,1)
    assert.equal(x.init[0].env,'prod-d4gls6f9gaef2c320')
    const login=x.calls[0]
    assert.equal(login.method,'POST');assert.equal(JSON.stringify(login.data),'{}')
    assert.equal(login.header.Authorization,undefined)
    for(const c of x.calls){assert.equal(c.config.env,'prod-d4gls6f9gaef2c320');assert.equal(c.header['X-WX-SERVICE'],'flask-3xwi');assert.equal(c.header['X-User-Id'],undefined)}
    assert.equal(x.calls[1].header.Authorization,'Bearer token1')
    x.api.setPrivacyConsent(false)
    await assert.rejects(x.api.getMe(),/协议/)
  }
  const x=setup({},o=>o.header.Authorization==='Bearer token1'?{statusCode:401,data:{message:'expired'}}:{statusCode:200,data:{code:0,data:{}}})
  x.api.setPrivacyConsent(true);await x.api.ensureLogin()
  await Promise.all([x.api.getMe(),x.api.getTodayDashboard()]);assert.equal(x.logins,2)
  const y=setup({},()=>({statusCode:401,data:{message:'expired'}}))
  y.api.setPrivacyConsent(true);await assert.rejects(y.api.getMe());assert.equal(y.logins,2);assert.equal(y.calls.length,4)
  const z=setup();z.api.setPrivacyConsent(true)
  await z.api.saveProfile({name:'新昵称',avatar:'local-avatar',gender:'女',age:21,height:165,weight:56,targetWeight:53,goal:'减脂'})
  const data=z.calls.at(-1).data;assert.equal(data.nickname,'新昵称');assert.equal(data.avatar,undefined);assert.equal(data.height_cm,165)
  await z.api.parseFood('鸡胸肉150g');assert.equal(z.calls.at(-1).path,'/api/food/parse')
  await z.api.quickLogFull({text:'鸡胸肉150g',meal_type:'午餐'});assert.equal(z.calls.at(-1).path,'/api/quick-log')
}
async function deployedCompatibilityChecks() {
  const item={id:3,name:'鸡胸肉',aliases:'鸡胸,鸡肉',calories_kcal_per_100g:133,protein_g:24.6,carb_g:0,fat_g:5}
  const x=setup({},o=>o.path==='/api/food/parse'?{statusCode:404,data:{}}:{statusCode:200,data:{code:0,data:o.path.startsWith('/api/ingredients')?[item]:{id:1}}})
  x.api.setPrivacyConsent(true)
  const result=await x.api.parseFood('鸡胸肉150g')
  assert.equal(result.ingredient_id,3);assert.equal(result.protein_g,36.9);assert.equal(result.kcal,199.5)
  await x.api.parseFood('150克鸡胸')
  assert.equal(x.calls.filter(o=>o.path==='/api/food/parse').length,1,'remember unsupported endpoint')
  await x.api.quickLogFull({...result,meal_type:'晚餐',text:'鸡胸肉150g'})
  const saved=x.calls.at(-1);assert.equal(saved.path,'/api/meals');assert.equal(saved.data.meal_type,'晚餐');assert.equal(saved.data.ingredients[0].amount_g,150)
  await assert.rejects(x.api.parseFood('2个鸡蛋'),/克数/)
  await assert.rejects(x.api.parseFood('鸡胸肉0g'),/克数/)
  const y=setup({},()=>({statusCode:503,data:{message:'unavailable'}}));y.api.setPrivacyConsent(true)
  await assert.rejects(y.api.parseFood('鸡胸肉150g'),/unavailable/)
  assert.equal(y.calls.some(o=>o.path.startsWith('/api/ingredients')),false,'do not conceal server failures')
}

async function homeChecks() {
  let page, confirmed=false, writes=[], navigation=[], parseCalls=0, sportCalls=0, dashboardFails=false
  const api={getTodayDashboard:async()=>{if(dashboardFails) throw Error("401 session expired"); return ({daily_calorie_target:1800,intake_calories_kcal:600,nutrition:{protein:{consumed:42,target:90},carb:{consumed:70,target:200},fat:{consumed:15,target:50}}})},getMeals:async()=>[{meal_type:'午餐',calories_kcal:200},{meal_type:'午餐',calories_kcal:300}],getTodayInsight:async()=>({diet_score:80,advice:['测试建议']}),parseFood:async()=>{parseCalls++;return {matched:true,food_name:'鸡胸肉',quantity_g:150,kcal:177,protein_g:36.9,carbs_g:.9,fat_g:2.9}},quickLogFull:async data=>writes.push(data),quickLog:async()=>sportCalls++}
  const wx={showToast:()=>{},showLoading:()=>{},hideLoading:()=>{},showModal:o=>o.success({confirm:confirmed}),redirectTo:o=>navigation.push(o.url),setStorageSync:()=>{}}
  vm.runInNewContext(fs.readFileSync(path.join(root,'pages/home/home.js'),'utf8'),{Page:p=>page=p,wx,require:p=>p.endsWith('/api')?api:p.endsWith('/meal')?{getMealSummary:()=>({items:[]})}:{getUser:()=>({name:'测试用户'}),calculateNutritionTargets:()=>({dailyCalorieTarget:1800,proteinTargetG:90,carbTargetG:200,fatTargetG:50})}})
  page.setData=v=>Object.assign(page.data,v)
  await page.loadMeals()
  assert.equal(page.data.summary.protein.current,42);assert.equal(page.data.summary.carbs.current,70)
  assert.equal(page.data.meals[1].kcal,500)
  page.onBottomNav({detail:{route:'/pages/me/me'}});assert.equal(navigation[0],'/pages/me/me')
  page.data.quickInput='鸡胸肉150g';await page.saveQuickLog();assert.equal(writes.length,0,'cancel must not save')
  confirmed=true;page.data.mealTypeIndex=2
  await Promise.all([page.saveQuickLog(),page.saveQuickLog()]);assert.equal(writes.length,1,'parallel click must save once');assert.equal(writes[0].meal_type,'晚餐')
  page.data.quickInput='蛙泳40分钟';await page.saveQuickLog();assert.equal(sportCalls,1);assert.equal(parseCalls,2)
  dashboardFails=true;await page.loadMeals();assert.match(page.data.loadError,/session expired/)
}
;(async()=>{await authChecks();await deployedCompatibilityChecks();await homeChecks();console.log('PASS: consent, stale/foreign caches, concurrent login/401, bounded retry, profile/food contracts, nested nutrition, meal totals, navigation, cancel/save/double-click, sport logging, visible errors')})().catch(e=>{console.error(e);process.exitCode=1})
