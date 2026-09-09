const CLOUD_SERVICES = {
  // The current environment is staging. Production stays intentionally blank
  // until a separate environment has been created and approved.
  trial: { env: "prod-d4g1s6f9gaef2c320", service: "flask-3xwi" },
  release: { env: "", service: "" }
}

function getEnvVersion() {
  try {
    return wx.getAccountInfoSync().miniProgram.envVersion || "develop"
  } catch (error) {
    return "develop"
  }
}

function getApiBase() {
  const envVersion = getEnvVersion()
  if (envVersion === "develop") {
    return wx.getStorageSync("apiBaseUrl") || "http://127.0.0.1:8001"
  }

  throw new Error(`${envVersion} 环境必须通过微信云托管调用后端`)
}

function getTransportConfig() {
  const envVersion = getEnvVersion()
  if (envVersion === "develop") return { type: "http", base: getApiBase() }
  const cloud = CLOUD_SERVICES[envVersion]
  if (!cloud || !cloud.env || !cloud.service) {
    throw new Error(`${envVersion} 环境尚未配置微信云托管服务`)
  }
  return { type: "cloud", ...cloud }
}

module.exports = { getApiBase, getEnvVersion, getTransportConfig }
