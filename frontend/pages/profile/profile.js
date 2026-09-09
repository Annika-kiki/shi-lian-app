const { getUser, saveUser } = require("../../utils/user")
const { saveProfile } = require("../../utils/api")

Page({
  data: {
    name: "用户",
    goal: "减脂",
    gender: "女",
    age: "21",
    height: "165",
    weight: "56.5",
    targetWeight: "53.0"
  },

  onLoad() {
    this.setData(getUser())
  },

  setGoal(event) {
    this.setData({ goal: event.currentTarget.dataset.value })
  },

  setGender(event) {
    this.setData({ gender: event.currentTarget.dataset.value })
  },

  onNameInput(event) {
    this.setData({ name: event.detail.value })
  },

  onAgeInput(event) {
    this.setData({ age: event.detail.value })
  },

  onHeightInput(event) {
    this.setData({ height: event.detail.value })
  },

  onWeightInput(event) {
    this.setData({ weight: event.detail.value })
  },

  onTargetWeightInput(event) {
    this.setData({ targetWeight: event.detail.value })
  },

  goBack() {
    const pages = getCurrentPages()
    if (pages.length > 1) {
      wx.navigateBack({ delta: 1 })
    } else {
      wx.redirectTo({ url: "/pages/index/index" })
    }
  },

  saveAndStart() {
    const age = Number(this.data.age)
    if (!Number.isFinite(age) || age < 14) {
      wx.showModal({
        title: "暂不支持",
        content: "食练周期首版仅面向14周岁以上用户。",
        showCancel: false
      })
      return
    }
    const userProfile = { ...this.data, age: String(age) }
    const app = getApp()
    wx.showLoading({ title: "保存中" })
    saveProfile(userProfile).then(() => {
      const savedProfile = saveUser(userProfile)
      app.setUserProfile(savedProfile)
      wx.redirectTo({
        url: "/pages/home/home"
      })
    }).catch((error) => {
      wx.showToast({
        title: error.message || "保存失败，请稍后重试",
        icon: "none"
      })
    }).finally(() => {
      wx.hideLoading()
    })
  }
})
