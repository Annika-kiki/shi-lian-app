const { bodyTrend } = require("../../utils/mock")
const { getBodyTrend, recordWeight } = require("../../utils/api")
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


function buildChart(points) {
  const values = points.length ? points : bodyTrend.points.map((value, index) => ({
    weight_kg: value,
    date: bodyTrend.labels[index]
  }))
  const weights = values.map((item) => item.weight_kg)
  const max = Math.max(...weights)
  const min = Math.min(...weights)
  const range = max - min || 1
  const count = Math.max(values.length - 1, 1)
  const leftStep = 90 / count

  return {
    labels: values.map((item) => String(item.date).slice(5).replace("-", "/")),
    chartBars: values.map((item, index) => ({
      height: 70 + ((max - item.weight_kg) / range) * 150,
      left: `${5 + index * leftStep}%`,
      value: Number(item.weight_kg).toFixed(1)
    }))
  }
}

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
    const chart = buildChart([])
    this.setData({
      labels: chart.labels,
      chartBars: chart.chartBars
    })
    getBodyTrend().then((trend) => {
      const remoteChart = buildChart(trend.weights || [])
      this.setData({
        weightText: Number(trend.current_weight_kg || bodyTrend.currentWeight).toFixed(1),
        last30DaysText: Number(trend.period_change_kg || 0).toFixed(1),
        distanceText: Number(trend.target_difference_kg || bodyTrend.distance).toFixed(1),
        labels: remoteChart.labels,
        chartBars: remoteChart.chartBars
      })
    }).catch(() => {})
  },

  onWeightInput(event) {
    this.setData({ weightText: event.detail.value })
  },

  goBack() {
    navigateBackOrRedirect("/pages/me/me")
  },

  recordWeight() {
    recordWeight(this.data.weightText).then(() => {
      wx.showToast({
        title: "已保存体重",
        icon: "success"
      })
    }).catch(() => {
      wx.showToast({
        title: "后端未启动，已保留页面数据",
        icon: "none"
      })
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
