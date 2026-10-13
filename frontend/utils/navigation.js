function navigateBackOrRedirect(fallbackUrl) {
  const pages = typeof getCurrentPages === "function" ? getCurrentPages() : []
  if (pages.length > 1) {
    wx.navigateBack({
      delta: 1,
      fail: () => {
        if (fallbackUrl) {
          wx.redirectTo({ url: fallbackUrl })
        }
      }
    })
    return
  }

  if (fallbackUrl) {
    wx.redirectTo({ url: fallbackUrl })
  }
}

module.exports = {
  navigateBackOrRedirect
}
