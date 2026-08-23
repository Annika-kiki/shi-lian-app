const DEFAULT_USER = {
  name: "用户",
  avatar: "🍃",
  goal: "减脂",
  gender: "女",
  age: "21",
  height: "165",
  weight: "56.5",
  targetWeight: "53.0"
}

function readStoredUser() {
  try {
    return wx.getStorageSync("userProfile") || wx.getStorageSync("profileForm") || {}
  } catch (error) {
    return {}
  }
}

function normalizeUser(user = {}) {
  return {
    ...DEFAULT_USER,
    ...readStoredUser(),
    ...user
  }
}

function saveUser(user = {}) {
  const next = normalizeUser(user)
  wx.setStorageSync("userProfile", next)
  return next
}

function getUser() {
  return normalizeUser()
}

module.exports = {
  DEFAULT_USER,
  getUser,
  saveUser,
  normalizeUser
}
