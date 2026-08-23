const { bodyTrend } = require("../../utils/mock")

Page({
  data: {
    weightText: bodyTrend.currentWeight.toFixed(1),
    last30DaysText: bodyTrend.last30Days.toFixed(1),
    goalWeightText: bodyTrend.goalWeight.toFixed(1),
    distanceText: bodyTrend.distance.toFixed(1),
    labels: bodyTrend.labels,
    chartBars: []
  },

  onLoad() {
    const max = Math.max(...bodyTrend.points)
    const min = Math.min(...bodyTrend.points)
    const range = max - min || 1
    const count = Math.max(bodyTrend.points.length - 1, 1)
    const leftStep = 90 / count
    this.setData({
      chartBars: bodyTrend.points.map((value, index) => ({
        height: 70 + ((max - value) / range) * 150,
        left: `${5 + index * leftStep}%`,
        value: value.toFixed(1)
      }))
    })
  },

  recordWeight() {
    wx.showToast({
      title: "已保存体重",
      icon: "success"
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
