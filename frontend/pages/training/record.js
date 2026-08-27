const { recordWorkout } = require("../../utils/mock")
const { getExercise, createWorkoutSession, addWorkoutSet, completeWorkoutSession } = require("../../utils/api")
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


function cloneSets(sets) {
  return sets.map((item) => ({ ...item }))
}

function buildWorkoutFromExercise(exercise) {
  return {
    name: exercise && exercise.title || recordWorkout.name,
    part: exercise && exercise.detail && exercise.detail.main || exercise && exercise.muscle || recordWorkout.part,
    startedAt: new Date().toTimeString().slice(0, 5),
    kcal: exercise && exercise.kcal || recordWorkout.kcal
  }
}

Page({
  data: {
    workout: recordWorkout,
    sets: cloneSets(recordWorkout.sets),
    exercise: null,
    exerciseId: ""
  },

  onLoad(query) {
    const stored = wx.getStorageSync("currentWorkoutExercise") || {}
    const exerciseId = String(query.id || stored.id || "")
    if (!exerciseId || exerciseId === "bench") {
      this.setData({
        workout: recordWorkout,
        sets: cloneSets(recordWorkout.sets),
        exerciseId: exerciseId || ""
      })
      return
    }

    this.setData({ exerciseId })
    getExercise(exerciseId)
      .then((exercise) => {
        this.setData({
          exercise,
          workout: buildWorkoutFromExercise(exercise),
          sets: [
            { group: 1, weight: 20, reps: 12, done: true },
            { group: 2, weight: 25, reps: 10, done: true },
            { group: 3, weight: 25, reps: 10, done: false },
            { group: 4, weight: 25, reps: 8, done: false }
          ]
        })
      })
      .catch(() => {
        this.setData({
          workout: recordWorkout,
          sets: cloneSets(recordWorkout.sets)
        })
      })
  },

  goBack() {
    navigateBackOrRedirect("/pages/training/detail?id=" + (this.data.exerciseId || "bench"))
  },

  toggleDone(event) {
    const index = event.currentTarget.dataset.index
    const sets = cloneSets(this.data.sets)
    sets[index].done = !sets[index].done
    this.setData({ sets })
  },

  addSet() {
    const sets = cloneSets(this.data.sets)
    sets.push({
      group: sets.length + 1,
      weight: sets.length >= 2 ? sets[sets.length - 1].weight : 20,
      reps: 8,
      done: false
    })
    this.setData({ sets })
  },

  async finishWorkout() {
    const exercise = this.data.exercise
    if (!exercise) {
      wx.showToast({
        title: "后端未启动，已保留页面数据",
        icon: "none"
      })
      return
    }

    wx.showLoading({ title: "保存中" })
    try {
      const session = await createWorkoutSession({
        title: this.data.workout.name || exercise.title,
        duration_min: Math.max(20, this.data.sets.length * 5)
      })

      for (const item of this.data.sets) {
        await addWorkoutSet(session.id, {
          exercise_id: Number(exercise.id),
          set_no: Number(item.group),
          weight_kg: Number(item.weight),
          reps: Number(item.reps),
          completed: !!item.done
        })
      }

      await completeWorkoutSession(session.id)
      wx.showToast({
        title: "训练已保存",
        icon: "success"
      })
    } catch (error) {
      wx.showToast({
        title: "后端未启动，已保留页面数据",
        icon: "none"
      })
    } finally {
      wx.hideLoading()
    }
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
