const { calendarData } = require("../../utils/mock")
const { getCalendar } = require("../../utils/api")

let markedDays = [2, 4, 6, 9, 12, 15]

function buildMonth(year, month) {
  const first = new Date(year, month - 1, 1)
  const last = new Date(year, month, 0)
  const days = last.getDate()
  const start = (first.getDay() + 6) % 7
  const cells = []
  for (let i = 0; i < start; i += 1) cells.push({})
  for (let day = 1; day <= days; day += 1) {
    cells.push({
      day,
      marked: markedDays.includes(day),
      selected: day === 17
    })
  }
  while (cells.length < 35) cells.push({})
  return cells
}

Page({
  data: {
    monthLabel: calendarData.monthLabel,
    selectedDay: calendarData.selectedDay,
    selectedTitle: calendarData.selectedTitle,
    selectedNote: calendarData.selectedNote,
    overview: calendarData.overview,
    history: calendarData.history,
    cells: []
  },

  onLoad() {
    const now = new Date()
    const year = now.getFullYear()
    const month = now.getMonth() + 1
    getCalendar(year, month).then((records) => {
      markedDays = records.map((item) => Number(String(item.date).slice(-2)))
      this.setData({
        monthLabel: `${year} 年 ${month} 月`,
        cells: buildMonth(year, month),
        overview: {
          count: records.length,
          duration: records.reduce((sum, item) => sum + (item.duration_min || 0), 0),
          top: records.length ? "已完成训练" : "暂无训练"
        },
        history: records.map((item) => ({
          day: String(item.date).slice(5).replace("-", " 月 ") + " 日",
          name: "训练记录",
          duration: `${item.duration_min || 0} min`
        }))
      })
    }).catch(() => {})
    this.setData({
      cells: buildMonth(2026, 8)
    })
  },

  selectDay(event) {
    const day = event.currentTarget.dataset.day
    if (!day) return
    const marked = markedDays.includes(day)
    this.setData({
      selectedDay: `8 月 ${day} 日${day === 17 ? " · 今天" : ""}`,
      selectedTitle: marked ? "训练日" : "休息日",
      selectedNote: marked ? "完成了一次训练，记得补水和拉伸。" : "保持充足睡眠，为下次训练恢复体力。",
      cells: this.data.cells.map((cell) => ({ ...cell, selected: cell.day === day }))
    })
  },

  openDetail() {
    wx.navigateTo({
      url: "/pages/training/detail?id=bench"
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
