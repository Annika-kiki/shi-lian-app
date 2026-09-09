const assert = require("assert")
const path = require("path")
const { spawnSync } = require("child_process")

const repositoryRoot = path.resolve(__dirname, "..")
const uploadScript = path.join(repositoryRoot, "scripts", "upload-miniprogram.js")

function run(extraEnv) {
  return spawnSync(process.execPath, [uploadScript], {
    cwd: repositoryRoot,
    env: { PATH: process.env.PATH, ...extraEnv },
    encoding: "utf8"
  })
}

let result = run({})
assert.notStrictEqual(result.status, 0)
assert.match(result.stderr, /set CONFIRM_WECHAT_UPLOAD=yes/)

result = run({
  CONFIRM_WECHAT_UPLOAD: "yes",
  WECHAT_APP_ID: "wrong-appid",
  MINIPROGRAM_PRIVATE_KEY_PATH: "/does/not/exist",
  RELEASE_DESCRIPTION: "test",
  RELEASE_COMMIT: "0".repeat(40)
})
assert.notStrictEqual(result.status, 0)
assert.match(result.stderr, /does not match the approved production AppID/)

console.log("Upload safety guard checks passed.")
