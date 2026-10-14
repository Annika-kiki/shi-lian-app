const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const source = fs.readFileSync(require('node:path').join(__dirname, '../frontend/utils/api.js'), 'utf8')
const target = 'prod-d4gls6f9gaef2c320/flask-3xwi'
function setup(storage = {}, responder = () => ({ statusCode: 200, data: { code: 0, data: {} } })) {
  storage.privacyAgreedVersion = "2026-09-05"
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
  vm.runInNewContext(source, {wx,module,require: () => ({getUser:()=>({}),calculateNutritionTargets:()=>({dailyCalorieTarget:1800,proteinTargetG:90,carbTargetG:200,fatTargetG:50})})})
  return {api:module.exports,calls,init,storage,get logins(){return logins}}
}
;(async () => {
  for (const storage of [{userId:3},{userId:3,accessToken:'old',cloudAuthTarget:'wrong'},{userId:3,accessToken:'old',cloudAuthTarget:target}]) {
    const x=setup(storage)
    await Promise.all([x.api.ensureLogin(),x.api.getMe(),x.api.getTodayDashboard()])
    assert.equal(x.logins,1)
    assert.equal(x.init[0].env,'prod-d4gls6f9gaef2c320')
    const login=x.calls[0]
    assert.equal(login.method,'POST');assert.equal(JSON.stringify(login.data),'{}')
    assert.equal(login.header.Authorization,undefined)
    for(const c of x.calls){assert.equal(c.config.env,'prod-d4gls6f9gaef2c320');assert.equal(c.header['X-WX-SERVICE'],'flask-3xwi');assert.equal(c.header['X-User-Id'],undefined)}
    assert.equal(x.calls[1].header.Authorization,'Bearer token1')
  }
  const x=setup({},o=>o.header.Authorization==='Bearer token1'?{statusCode:401,data:{message:'expired'}}:{statusCode:200,data:{code:0,data:{}}})
  await x.api.ensureLogin()
  await Promise.all([x.api.getMe(),x.api.getTodayDashboard()])
  assert.equal(x.logins,2)
  const y=setup({},()=>({statusCode:401,data:{message:'expired'}}))
  await assert.rejects(y.api.getMe());assert.equal(y.logins,2);assert.equal(y.calls.length,4)
  const z=setup();await z.api.saveProfile({name:'新昵称',avatar:'local-avatar',gender:'女',age:21,height:165,weight:56,targetWeight:53,goal:'减脂'})
  const data=z.calls.at(-1).data;assert.equal(data.nickname,'新昵称');assert.equal(data.avatar,undefined);assert.equal(data.height_cm,165)
  console.log('PASS: cloud env/service, login body, cache migration, concurrent login, concurrent 401 refresh, bounded retry, profile contract')
})().catch(e=>{console.error(e);process.exitCode=1})
