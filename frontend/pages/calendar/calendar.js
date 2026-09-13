const { getCalendar, getMeals, getWorkoutSessions, getMe } = require("../../utils/api")

function pad(value) {
  const number = Number(value)
  return number < 10 ? `0${number}` : String(number)
}

function toDateKey(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function parseDateKey(dateKey) {
  const [year, month, day] = String(dateKey).split("-").map(Number)
  return new Date(year, month - 1, day)
}

function dateLabel(dateKey) {
  const date = parseDateKey(dateKey)
  return `${date.getMonth() + 1} 月 ${date.getDate()} 日`
}

function todayKey() {
  return toDateKey(new Date())
}

function monthLabel(year, month) {
  return `${year} 年 ${month} 月`
}

function buildMonth(year, month, records, selectedDate, loginDate) {
  const first = new Date(year, month - 1, 1)
  const last = new Date(year, month, 0)
  const days = last.getDate()
  const start = (first.getDay() + 6) % 7
  const recordMap = records.reduce((map, item) => {
    map[String(item.date)] = item
    return map
  }, {})
  const cells = []
  for (let i = 0; i < start; i += 1) cells.push({})
  for (let day = 1; day <= days; day += 1) {
    const date = `${year}-${pad(month)}-${pad(day)}`
    const record = recordMap[date]
    cells.push({
      day,
      date,
      started: date >= loginDate && date <= todayKey(),
      marked: Boolean(record && (record.sessions || record.meal_count)),
      training: Boolean(record && record.sessions),
      resting: Boolean(record && !record.sessions),
      selected: date === selectedDate
    })
  }
  while (cells.length % 7 !== 0) cells.push({})
  return cells
}

function buildOverview(records) {
  const trainingRecords = records.filter((item) => item.sessions > 0)
  const duration = trainingRecords.reduce((sum, item) => sum + (item.duration_min || 0), 0)
  const top = trainingRecords.length ? `${trainingRecords.length} 天有训练` : "暂无训练"
  return {
    count: trainingRecords.reduce((sum, item) => sum + (item.sessions || 0), 0),
    duration,
    top
  }
}

function buildDaySummary(date, calendarRecord, workouts, meals, loginDate) {
  if (date > todayKey()) {
    return {
      selectedDay: `${dateLabel(date)} · 未到日期`,
      selectedTitle: "未到日期",
      selectedNote: "未来日期暂不生成训练或饮食记录。",
      dailySummary: {
        workoutText: "未到日期",
        mealText: "未到日期"
      }
    }
  }
  if (date < loginDate) {
    return {
      selectedDay: `${dateLabel(date)} · 未开始记录`,
      selectedTitle: "未开始记录",
      selectedNote: "记录会从登录当天开始统计。",
      dailySummary: {
        workoutText: "未开始",
        mealText: "未开始"
      }
    }
  }
  const workoutCount = workouts.length
  const mealCount = meals.length
  const workoutMinutes = workouts.reduce((sum, item) => sum + (item.duration_min || 0), 0)
  const workoutCalories = Math.round(workouts.reduce((sum, item) => sum + (item.calories_kcal || 0), 0))
  const intakeCalories = Math.round(meals.reduce((sum, item) => sum + (item.calories_kcal || 0), 0))
  const isToday = date === todayKey()
  const title = workoutCount ? "训练日" : "休息日"
  const note = workoutCount
    ? `完成 ${workoutCount} 次训练，共 ${workoutMinutes} 分钟，约消耗 ${workoutCalories} kcal。`
    : "没有训练记录，记作休息日。"
  return {
    selectedDay: `${dateLabel(date)}${isToday ? " · 今天" : ""}`,
    selectedTitle: calendarRecord && calendarRecord.status || title,
    selectedNote: note,
    dailySummary: {
      workoutText: workoutCount ? `${workoutCount} 次 · ${workoutMinutes} 分钟 · ${workoutCalories} kcal` : "休息日",
      mealText: mealCount ? `${mealCount} 餐 · ${intakeCalories} kcal` : "暂无饮食"
    }
  }
}

function normalizeMeal(item) {
  return {
    id: item.id,
    title: `${item.meal_type || "饮食"} · ${item.name || "已记录"}`,
    detail: `${Math.round(item.calories_kcal || 0)} kcal · 蛋白质 ${Math.round(item.protein_g || 0)} g`
  }
}

function normalizeWorkout(item) {
  return {
    id: item.id,
    title: item.title || "训练记录",
    detail: `${item.duration_min || 0} 分钟 · ${Math.round(item.calories_kcal || 0)} kcal`
  }
}

Page({
  data: {
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    monthLabel: monthLabel(new Date().getFullYear(), new Date().getMonth() + 1),
    loginDate: todayKey(),
    selectedDate: todayKey(),
    selectedDay: `${dateLabel(todayKey())} · 今天`,
    selectedTitle: "休息日",
    selectedNote: "没有训练记录，记作休息日。",
    overview: { count: 0, duration: 0, top: "暂无训练" },
    dailySummary: { workoutText: "休息日", mealText: "暂无饮食" },
    dailyWorkouts: [],
    dailyMeals: [],
    cells: [],
    calendarRecords: []
  },

  onLoad() {
    const now = new Date()
    this.loadMonth(now.getFullYear(), now.getMonth() + 1, todayKey())
  },

  loadMonth(year, month, selectedDate) {
    getMe().then((me) => {
      const loginDate = String(me.created_date || todayKey())
      return getCalendar(year, month).then((records) => ({ records, loginDate }))
    }).then(({ records, loginDate }) => {
      const date = selectedDate || todayKey()
      this.setData({
        year,
        month,
        monthLabel: monthLabel(year, month),
        loginDate,
        selectedDate: date,
        calendarRecords: records,
        cells: buildMonth(year, month, records, date, loginDate),
        overview: buildOverview(records)
      })
      this.loadDay(date)
    }).catch(() => {
      const date = selectedDate || todayKey()
      this.setData({
        year,
        month,
        monthLabel: monthLabel(year, month),
        selectedDate: date,
        cells: buildMonth(year, month, [], date, this.data.loginDate)
      })
    })
  },

  loadDay(date) {
    const record = this.data.calendarRecords.find((item) => String(item.date) === date)
    if (date < this.data.loginDate || date > todayKey()) {
      this.setData(Object.assign({}, buildDaySummary(date, null, [], [], this.data.loginDate), {
        dailyWorkouts: [],
        dailyMeals: [],
        cells: buildMonth(this.data.year, this.data.month, this.data.calendarRecords, date, this.data.loginDate)
      }))
      return
    }
    Promise.all([
      getWorkoutSessions(date).catch(() => []),
      getMeals(date).catch(() => [])
    ]).then(([workouts, meals]) => {
      this.setData(Object.assign({}, buildDaySummary(date, record, workouts, meals, this.data.loginDate), {
        dailyWorkouts: workouts.map(normalizeWorkout),
        dailyMeals: meals.map(normalizeMeal),
        selectedDate: date,
        cells: buildMonth(this.data.year, this.data.month, this.data.calendarRecords, date, this.data.loginDate)
      }))
    })
  },

  selectDay(event) {
    const date = event.currentTarget.dataset.date
    if (!date) return
    this.loadDay(date)
  },

  prevMonth() {
    const previous = new Date(this.data.year, this.data.month - 2, 1)
    this.loadMonth(previous.getFullYear(), previous.getMonth() + 1, toDateKey(previous))
  },

  nextMonth() {
    const next = new Date(this.data.year, this.data.month, 1)
    this.loadMonth(next.getFullYear(), next.getMonth() + 1, toDateKey(next))
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
