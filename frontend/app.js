const { getUser } = require("./utils/user")

App({
  globalData: {
    userProfile: getUser()
  },

  onLaunch() {
    this.globalData.userProfile = getUser()
  },

  setUserProfile(profile) {
    this.globalData.userProfile = profile
  },

  getUserProfile() {
    return this.globalData.userProfile
  }
})
