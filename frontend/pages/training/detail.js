const { localExercise, normalize, resolveExercise } = require("../../utils/exercises")
const { ensureLogin, request, showApiError } = require("../../utils/api")
const { navigationBehavior } = require("../../utils/navigation")

Page({
  behaviors: [navigationBehavior],
  data: {
    exercise: null,
    favorite: false,
    loading: true,
    error: "",
    imageError: false,
    stages: [0, 1],
    detail: { steps: [] }
  },

  showExercise(exercise) {
    this.setData({
      exercise, loading: false, error: "", imageError: false,
      detail: {
        part: `${exercise.body_part} · ${exercise.equipment}`,
        main: exercise.primary_muscle,
        assist: exercise.secondary_muscle,
        steps: String(exercise.steps || "").split(/[；。]/).filter(Boolean),
        notes: exercise.cautions,
        imageSrc: exercise.imageSrc
      }
    })
  },

  async onLoad(query) {
    const id = query.id || "barbell-bench-press"
    const local = localExercise(id)
    if (local) this.showExercise(normalize(local))
    try {
      this.showExercise(await resolveExercise(id))
    } catch (error) {
      if (!local) this.setData({ loading: false, error: "动作暂时无法加载，请返回动作库重试" })
    }
  },

  onImageError() {
    this.setData({ imageError: true })
  },

  previewImage() {
    if (!this.data.detail.imageSrc || this.data.imageError) return
    wx.previewImage({ current: this.data.detail.imageSrc, urls: [this.data.detail.imageSrc] })
  },

  async getOnlineExercise() {
    if (!this.data.exercise) throw new Error("请先选择动作")
    if (typeof this.data.exercise.id === "number") return this.data.exercise
    const exercise = await resolveExercise(this.data.exercise.slug)
    this.setData({ exercise })
    return exercise
  },

  async startRecord() {
    try {
      const exercise = await this.getOnlineExercise()
      wx.navigateTo({ url: `/pages/training/record?id=${exercise.id}` })
    } catch (error) { showApiError(error) }
  },

  async toggleFavorite() {
    try {
      const exercise = await this.getOnlineExercise()
      await ensureLogin()
      const next = !this.data.favorite
      await request(`/api/exercises/${exercise.id}/favorite`, { method: next ? "POST" : "DELETE" })
      this.setData({ favorite: next })
      wx.showToast({ title: next ? "已收藏" : "已取消收藏", icon: "none" })
    } catch (error) { showApiError(error) }
  },

  onBottomNav(event) {
    wx.redirectTo({ url: event.detail.route })
  }
})
