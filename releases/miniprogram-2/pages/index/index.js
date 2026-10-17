const { getUser } = require("../../utils/user")
const { ensureLogin, setPrivacyConsent } = require("../../utils/api")

Page({
  data: { agreed: false, loggingIn: false },

  onLoad() {
    setPrivacyConsent(false)
    this.setData({ agreed: false })
  },

  onAgreementChange(event) {
    const agreed = event.detail.value.includes("agreed")
    this.setData({ agreed })
    setPrivacyConsent(agreed)
  },

  viewTerms() { wx.navigateTo({ url: "/pages/terms/terms" }) },
  viewPrivacy() { wx.navigateTo({ url: "/pages/privacy/privacy" }) },

  loginAndEnter(url) {
    if (!this.data.agreed) {
      wx.showToast({ title: "请先阅读并同意协议", icon: "none" })
      return
    }
    if (this.data.loggingIn) return
    setPrivacyConsent(true)
    this.setData({ loggingIn: true })
    ensureLogin(getUser()).then(() => wx.redirectTo({ url })).catch(() => {
      wx.showToast({ title: "云端登录失败，请稍后重试", icon: "none" })
    }).finally(() => this.setData({ loggingIn: false }))
  },

  goProfile() { this.loginAndEnter("/pages/profile/profile") },
  skip() { this.loginAndEnter("/pages/home/home") }
})
