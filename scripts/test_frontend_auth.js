// Keep the repository verification entry point, exercising both the legacy
// frontend cloud client and the current importable release project.
const { spawnSync } = require('node:child_process')
const path = require('node:path')
for (const suite of ['test_cloud_frontend_auth.cjs', 'test_release_integration.cjs']) {
  const result = spawnSync(process.execPath, [path.join(__dirname, suite)], { stdio: 'inherit' })
  if (result.error) throw result.error
  if (result.status !== 0) process.exit(result.status || 1)
}
