const { getReportSummary } = require("../../utils/api")

const fallbackReport = {
  averageScore: 0,
  rangeText: "近 7 天",
  trend: [],
  distribution: [],
  mealScores: [],
  summary: {
    mealCount: 0,
    workoutCount: 0,
    workoutMinutes: 0,
    workoutCalories: 0
  },
  suggestions: ["记录饮食和训练后，这里会生成你的阶段总结。"]
}

function formatDate(dateText) {
  const text = String(dateText || "")
  const match = text.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!match) return text
  return `${Number(match[2])}/${Number(match[3])}`
}

function normalizeReport(report, days) {
  if (!report) return fallbackReport
  const distribution = report.distribution || {}
  return {
    averageScore: Math.round(report.average_score || 0),
    rangeText: report.range ? `${formatDate(report.range.start)} - ${formatDate(report.range.end)}` : `近 ${days} 天`,
    trend: (report.trend || []).map((item) => ({
      date: formatDate(item.date),
      score: Math.round(item.score || 0),
      width: `${Math.min(100, Math.max(4, item.score || 0))}%`
    })),
    distribution: ["优秀", "良好", "一般", "较差"].map((label) => ({
      label,
      count: distribution[label] || 0,
      width: `${Math.min(100, Math.max(4, ((distribution[label] || 0) / days) * 100))}%`
    })),
    mealScores: (report.meal_scores || []).map((item) => ({
      label: item.label,
      score: Math.round(item.score || 0),
      detail: `${item.count || 0} 次 · 平均 ${item.avg_calories || 0} kcal · 蛋白质 ${item.avg_protein || 0} g`
    })),
    summary: {
      mealCount: report.summary && report.summary.meal_count || 0,
      workoutCount: report.summary && report.summary.workout_count || 0,
      workoutMinutes: report.summary && report.summary.workout_minutes || 0,
      workoutCalories: Math.round(report.summary && report.summary.workout_calories || 0)
    },
    suggestions: report.suggestions && report.suggestions.length ? report.suggestions : fallbackReport.suggestions
  }
}

Page({
  data: {
    days: 7,
    report: fallbackReport,
    loading: false
  },

  onShow() {
    this.loadReport()
  },

  loadReport() {
    this.setData({ loading: true })
    getReportSummary(this.data.days).then((report) => {
      this.setData({ report: normalizeReport(report, this.data.days) })
    }).catch(() => {
      this.setData({ report: fallbackReport })
    }).finally(() => {
      this.setData({ loading: false })
    })
  },

  setDays(event) {
    const days = Number(event.currentTarget.dataset.days) || 7
    this.setData({ days })
    this.loadReport()
  },

  goCalendar() {
    wx.navigateTo({ url: "/pages/calendar/calendar" })
  },

  goBody() {
    wx.navigateTo({ url: "/pages/body/body" })
  },

  onBottomNav(event) {
    wx.redirectTo({ url: event.detail.route })
  }
})
