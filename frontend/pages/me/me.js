const { getUser } = require("../../utils/user")
const { getMe, getTodayDashboard, getMonthlyStats } = require("../../utils/api")

function emptyProfile() {
  const user = getUser()
  return {
    avatar: user.avatar || "🍃",
    name: user.name || "用户",
    goal: user.goal || "未设置",
    height: user.height ? `${user.height} cm` : "--",
    weight: user.weight ? `${user.weight} kg` : "--",
    trainingCount: "--",
    streak: "--"
  }
}

Page({
  data: { me: emptyProfile() },

  onShow() {
    const now = new Date()
    this.setData({ me: emptyProfile() })
    Promise.all([
      getMe(),
      getTodayDashboard(),
      getMonthlyStats(now.getFullYear(), now.getMonth() + 1)
    ]).then(([account, dashboard, monthly]) => {
      const profile = account.profile || {}
      this.setData({
        me: {
          avatar: account.avatar || "🍃",
          name: account.nickname || "用户",
          goal: profile.goal_type || "未设置",
          height: profile.height_cm ? `${profile.height_cm} cm` : "--",
          weight: profile.current_weight_kg ? `${profile.current_weight_kg} kg` : "--",
          trainingCount: `${monthly.workout_count || 0} 次`,
          streak: `${dashboard.streak_days || 0} 天`
        }
      })
    }).catch((error) => {
      wx.showToast({ title: error.message || "数据加载失败", icon: "none" })
    })
  },

  editProfile() {
    wx.navigateTo({ url: "/pages/profile/profile" })
  },

  goBody() {
    wx.navigateTo({ url: "/pages/body/body" })
  },

  goTrainingHistory() {
    wx.redirectTo({ url: "/pages/calendar/calendar" })
  },

  goExerciseLibrary() {
    wx.redirectTo({ url: "/pages/training/home" })
  },

  goPrivacy() {
    wx.navigateTo({ url: "/pages/privacy/privacy" })
  },

  onBottomNav(event) {
    wx.redirectTo({ url: event.detail.route })
  }
})
