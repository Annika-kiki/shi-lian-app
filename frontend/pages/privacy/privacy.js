const { deleteAccount } = require("../../utils/api")

Page({
  data: { showDelete: true },

  onLoad(query) {
    this.setData({ showDelete: query.readOnly !== "1" })
  },

  goBack() {
    const pages = getCurrentPages()
    if (pages.length > 1) {
      wx.navigateBack({ delta: 1 })
    } else {
      wx.redirectTo({ url: "/pages/me/me" })
    }
  },

  deleteAccount() {
    wx.showModal({
      title: "注销账号",
      content: "注销后，个人资料、体重、饮食、收藏和训练记录将被删除且无法恢复。确定继续吗？",
      confirmText: "确认注销",
      confirmColor: "#c0392b",
      success: (result) => {
        if (!result.confirm) return
        wx.showLoading({ title: "正在注销" })
        deleteAccount().then(() => {
          wx.showToast({ title: "账号已注销", icon: "success" })
          setTimeout(() => wx.reLaunch({ url: "/pages/index/index" }), 800)
        }).catch((error) => {
          wx.showToast({ title: error.message || "注销失败", icon: "none" })
        }).finally(() => wx.hideLoading())
      }
    })
  }
})
