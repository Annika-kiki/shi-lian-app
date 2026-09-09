const { saveUser, getUser } = require("../../utils/user")
const { ensureLogin, PRIVACY_AGREEMENT_VERSION } = require("../../utils/api")

function enterPage(url) {
  wx.redirectTo({ url })
}

function showLoginError(error) {
  wx.showToast({
    title: error.message || "登录失败，请检查网络后重试",
    icon: "none"
  })
}

Page({
  data: { agreed: false },

  toggleAgreement() {
    this.setData({ agreed: !this.data.agreed })
  },

  requireAgreement() {
    if (this.data.agreed) return true
    wx.showToast({ title: "请先阅读并同意协议", icon: "none" })
    return false
  },

  recordAgreement() {
    wx.setStorageSync("privacyAgreedVersion", PRIVACY_AGREEMENT_VERSION)
  },

  viewPrivacy() {
    wx.navigateTo({ url: "/pages/privacy/privacy?readOnly=1" })
  },

  viewTerms() {
    wx.navigateTo({ url: "/pages/terms/terms" })
  },

  goProfile() {
    if (!this.requireAgreement()) return
    this.recordAgreement()
    ensureLogin(getUser())
      .then(() => enterPage("/pages/profile/profile"))
      .catch(showLoginError)
  },

  skip() {
    if (!this.requireAgreement()) return
    this.recordAgreement()
    const user = saveUser(getUser())
    ensureLogin(user)
      .then(() => enterPage("/pages/home/home"))
      .catch(showLoginError)
  }
})
