const { getUser, saveUser } = require("../../utils/user")

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

  saveAndStart() {
    const userProfile = saveUser(this.data)
    const app = getApp()
    app.setUserProfile(userProfile)
    wx.redirectTo({
      url: "/pages/home/home"
    })
  }
})
