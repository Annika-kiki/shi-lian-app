const { calendarData } = require("../../utils/mock")

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
      marked: [2, 4, 6, 9, 12, 15].includes(day),
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
    this.setData({
      cells: buildMonth(2026, 8)
    })
  },

  selectDay(event) {
    const day = event.currentTarget.dataset.day
    if (!day) return
    const marked = [2, 4, 6, 9, 12, 15].includes(day)
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
