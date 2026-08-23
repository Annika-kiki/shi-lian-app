const { getExerciseById, exerciseDetail } = require("../../utils/mock")

const DEFAULT_VIDEO =
  "../../assets/videos/mov_bbb.mp4"

Page({
  data: {
    exercise: getExerciseById("bench"),
    detail: {
      ...exerciseDetail.bench,
      videoSrc: DEFAULT_VIDEO
    }
  },

  onLoad(query) {
    const exercise = getExerciseById(query.id || "bench")
    const detail = exerciseDetail[exercise.id] || exerciseDetail.bench
    this.setData({
      exercise,
      detail: {
        ...detail,
        videoSrc: detail.videoSrc || DEFAULT_VIDEO
      }
    })
  },

  startRecord() {
    wx.navigateTo({
      url: "/pages/training/record"
    })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
