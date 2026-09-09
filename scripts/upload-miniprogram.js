const path = require("path")
const fs = require("fs")
const { execFileSync } = require("child_process")
const packageJson = require("../package.json")

const appid = process.env.WECHAT_APP_ID
const privateKeyPath = process.env.MINIPROGRAM_PRIVATE_KEY_PATH
const description = process.env.RELEASE_DESCRIPTION
const confirmed = process.env.CONFIRM_WECHAT_UPLOAD === "yes"
const releaseCommit = process.env.RELEASE_COMMIT

if (!confirmed) {
  throw new Error("Upload blocked: set CONFIRM_WECHAT_UPLOAD=yes only after the owner approves this upload")
}
if (!appid || !privateKeyPath || !description || !releaseCommit) {
  throw new Error("WECHAT_APP_ID, MINIPROGRAM_PRIVATE_KEY_PATH, RELEASE_DESCRIPTION and RELEASE_COMMIT are required")
}
if (appid !== "wx26dfe00bf5f3258b") {
  throw new Error("WECHAT_APP_ID does not match the approved production AppID")
}
if (!/^\d+\.\d+\.\d+$/.test(packageJson.version)) {
  throw new Error("package.json version must use numeric SemVer (for example 1.2.3)")
}
if (!description.trim() || description.length > 200) {
  throw new Error("RELEASE_DESCRIPTION must contain 1-200 characters")
}

const repositoryRoot = path.resolve(__dirname, "..")
const currentCommit = execFileSync("git", ["rev-parse", "HEAD"], {
  cwd: repositoryRoot,
  encoding: "utf8"
}).trim()
if (!/^[0-9a-f]{40}$/.test(releaseCommit) || releaseCommit !== currentCommit) {
  throw new Error("RELEASE_COMMIT must exactly match the checked-out Git commit")
}
const dirtyFiles = execFileSync("git", ["status", "--porcelain"], {
  cwd: repositoryRoot,
  encoding: "utf8"
}).trim()
if (dirtyFiles) {
  throw new Error("Upload blocked: the Git worktree must be clean")
}

const resolvedPrivateKeyPath = path.resolve(privateKeyPath)
if (fs.lstatSync(resolvedPrivateKeyPath).isSymbolicLink()) {
  throw new Error("MINIPROGRAM_PRIVATE_KEY_PATH must not be a symbolic link")
}
const keyStat = fs.statSync(resolvedPrivateKeyPath)
if (!keyStat.isFile()) {
  throw new Error("MINIPROGRAM_PRIVATE_KEY_PATH must point to a regular file")
}
if (process.platform !== "win32" && (keyStat.mode & 0o077) !== 0) {
  throw new Error("Private key permissions are too broad; use chmod 600")
}

// Load the upload tool only after every local safety guard has passed. This
// limits exposure to its legacy transitive dependencies during normal checks.
const ci = require("miniprogram-ci")

const project = new ci.Project({
  appid,
  type: "miniProgram",
  projectPath: path.resolve(__dirname, "../frontend"),
  privateKeyPath: resolvedPrivateKeyPath,
  ignores: ["node_modules/**/*"]
})

async function upload() {
  await ci.upload({
    project,
    version: packageJson.version,
    desc: description,
    setting: {
      es6: true,
      minify: true,
      minifyJS: true,
      minifyWXML: true,
      minifyWXSS: true
    }
  })
}

upload().catch((error) => {
  console.error(`Upload failed: ${error.message}`)
  process.exitCode = 1
})
