const { recordWorkout } = require("../../utils/mock")

Page({
  data: {
    workout: recordWorkout,
    sets: []
  },

  onLoad() {
    this.setData({
      sets: recordWorkout.sets.map((item) => ({ ...item }))
    })
  },

  toggleDone(event) {
    const index = event.currentTarget.dataset.index
    const sets = this.data.sets.slice()
    sets[index].done = !sets[index].done
    this.setData({ sets })
  },

  addSet() {
    const sets = this.data.sets.slice()
    sets.push({
      group: sets.length + 1,
      weight: 20,
      reps: 8,
      done: false
    })
    this.setData({ sets })
  },

  finishWorkout() {
    wx.showToast({
      title: "训练已完成",
      icon: "success"
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
