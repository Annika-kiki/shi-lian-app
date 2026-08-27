function navigateBackOrRedirect(fallbackUrl) {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    wx.navigateBack({ delta: 1 })
    return
  }

  if (fallbackUrl) {
    wx.redirectTo({ url: fallbackUrl })
  }
}

module.exports = {
  navigateBackOrRedirect
}
