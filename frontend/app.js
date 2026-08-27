const { getUser } = require("./utils/user")
const { ensureLogin } = require("./utils/api")

App({
  globalData: {
    userProfile: getUser()
  },

  onLaunch() {
    this.globalData.userProfile = getUser()
    ensureLogin(this.globalData.userProfile).catch(() => {})
  },

  setUserProfile(profile) {
    this.globalData.userProfile = profile
  },

  getUserProfile() {
    return this.globalData.userProfile
  }
})
