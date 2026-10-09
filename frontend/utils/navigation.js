const navigationBehavior = Behavior({
  methods: {
    goBack() {
      const pages = getCurrentPages()
      if (pages.length > 1) {
        wx.navigateBack({ delta: 1 })
        return
      }
      const current = pages[0] && pages[0].route
      wx.redirectTo({ url: current === "pages/home/home" ? "/pages/index/index" : "/pages/home/home" })
    }
  }
})

module.exports = { navigationBehavior }
