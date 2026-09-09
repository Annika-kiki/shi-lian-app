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
  const values = points || []
  if (!values.length) return { labels: [], chartBars: [] }
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
    weightText: "",
    currentWeightText: "--",
    last30DaysText: "--",
    goalWeightText: "--",
    distanceText: "--",
    labels: [],
    chartBars: []
  },

  onLoad() {
    this.loadTrend()
  },

  loadTrend() {
    getBodyTrend().then((trend) => {
      const remoteChart = buildChart(trend.weights || [])
      const current = trend.current_weight_kg
      const target = trend.target_weight_kg
      const difference = trend.target_difference_kg
      this.setData({
        weightText: current == null ? "" : Number(current).toFixed(1),
        currentWeightText: current == null ? "--" : Number(current).toFixed(1),
        last30DaysText: trend.period_change_kg == null ? "--" : `${Number(trend.period_change_kg) > 0 ? "+" : ""}${Number(trend.period_change_kg).toFixed(1)}`,
        goalWeightText: target == null ? "--" : Number(target).toFixed(1),
        distanceText: difference == null ? "--" : Number(Math.abs(difference)).toFixed(1),
        labels: remoteChart.labels,
        chartBars: remoteChart.chartBars
      })
    }).catch((error) => {
      wx.showToast({ title: error.message || "体重数据加载失败", icon: "none" })
    })
  },

  onWeightInput(event) {
    this.setData({ weightText: event.detail.value })
  },

  goBack() {
    navigateBackOrRedirect("/pages/me/me")
  },

  recordWeight() {
    const value = Number(this.data.weightText)
    if (!Number.isFinite(value) || value <= 0 || value > 500) {
      wx.showToast({ title: "请输入有效体重", icon: "none" })
      return
    }
    recordWeight(this.data.weightText).then(() => {
      wx.showToast({
        title: "已保存体重",
        icon: "success"
      })
      this.loadTrend()
    }).catch((error) => {
      wx.showToast({
        title: error.message || "体重保存失败，请稍后重试",
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
