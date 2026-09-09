const { getCalendar, getMonthlyStats } = require("../../utils/api")

let markedDays = []

function buildMonth(year, month, selectedDay) {
  const first = new Date(year, month - 1, 1)
  const days = new Date(year, month, 0).getDate()
  const start = (first.getDay() + 6) % 7
  const cells = []
  for (let i = 0; i < start; i += 1) cells.push({})
  for (let day = 1; day <= days; day += 1) {
    cells.push({ day, marked: markedDays.includes(day), selected: day === selectedDay })
  }
  while (cells.length % 7) cells.push({})
  return cells
}

function dayLabel(year, month, day) {
  const now = new Date()
  const isToday = year === now.getFullYear() && month === now.getMonth() + 1 && day === now.getDate()
  return `${month} 月 ${day} 日${isToday ? " · 今天" : ""}`
}

Page({
  data: {
    year: 0,
    month: 0,
    monthLabel: "",
    selectedDayNumber: 0,
    selectedDay: "",
    selectedTitle: "请选择日期",
    selectedNote: "带圆点的日期表示有训练记录。",
    overview: { count: 0, duration: 0, top: "暂无训练" },
    history: [],
    cells: [],
    loading: true
  },

  onLoad() {
    const now = new Date()
    this.loadMonth(now.getFullYear(), now.getMonth() + 1, now.getDate())
  },

  loadMonth(year, month, selectedDay = 0) {
    this.setData({ loading: true })
    Promise.all([getCalendar(year, month), getMonthlyStats(year, month)])
      .then(([records, monthly]) => {
        markedDays = records.map((item) => Number(String(item.date).slice(-2)))
        const selectedRecord = records.find((item) => Number(String(item.date).slice(-2)) === selectedDay)
        this.setData({
          year,
          month,
          monthLabel: `${year} 年 ${month} 月`,
          selectedDayNumber: selectedDay,
          selectedDay: selectedDay ? dayLabel(year, month, selectedDay) : "",
          selectedTitle: selectedDay ? (selectedRecord ? "训练日" : "休息日") : "请选择日期",
          selectedNote: selectedRecord ? `${selectedRecord.sessions} 次训练 · ${selectedRecord.duration_min || 0} 分钟` : "带圆点的日期表示有训练记录。",
          cells: buildMonth(year, month, selectedDay),
          overview: {
            count: monthly.workout_count || 0,
            duration: monthly.total_duration_min || 0,
            top: monthly.most_trained_body_part || "暂无训练"
          },
          history: records.slice().reverse().map((item) => ({
            day: String(item.date).slice(5).replace("-", " 月 ") + " 日",
            name: `${item.sessions || 0} 次训练`,
            duration: `${item.duration_min || 0} 分钟`
          })),
          loading: false
        })
      })
      .catch((error) => {
        markedDays = []
        this.setData({
          year,
          month,
          monthLabel: `${year} 年 ${month} 月`,
          cells: buildMonth(year, month, selectedDay),
          history: [],
          overview: { count: 0, duration: 0, top: "暂不可用" },
          loading: false
        })
        wx.showToast({ title: error.message || "训练记录加载失败", icon: "none" })
      })
  },

  previousMonth() {
    const date = new Date(this.data.year, this.data.month - 2, 1)
    this.loadMonth(date.getFullYear(), date.getMonth() + 1)
  },

  nextMonth() {
    const date = new Date(this.data.year, this.data.month, 1)
    this.loadMonth(date.getFullYear(), date.getMonth() + 1)
  },

  selectDay(event) {
    const day = Number(event.currentTarget.dataset.day)
    if (!day) return
    const marked = markedDays.includes(day)
    this.setData({
      selectedDayNumber: day,
      selectedDay: dayLabel(this.data.year, this.data.month, day),
      selectedTitle: marked ? "训练日" : "休息日",
      selectedNote: marked ? "当天已有训练记录。" : "当天暂无训练记录。",
      cells: buildMonth(this.data.year, this.data.month, day)
    })
  },

  onBottomNav(event) {
    wx.redirectTo({ url: event.detail.route })
  }
})
