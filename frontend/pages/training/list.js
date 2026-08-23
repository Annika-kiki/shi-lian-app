const { getExerciseList } = require("../../utils/mock")

Page({
  data: {
    part: "chest",
    keyword: "",
    equipment: "全部",
    equipmentTabs: ["全部", "杠铃", "哑铃", "固定器械"],
    exercises: [],
    filteredExercises: [],
    title: "胸部动作"
  },

  onLoad(query) {
    const part = query.part || "chest"
    const exercises = getExerciseList(part)
    this.setData({
      part,
      exercises,
      filteredExercises: exercises,
      title: {
        chest: "胸部动作",
        back: "背部动作",
        shoulder: "肩部动作",
        arm: "手臂动作",
        leg: "腿臀动作",
        core: "核心动作"
      }[part] || "动作列表"
    })
  },

  setEquipment(event) {
    const equipment = event.currentTarget.dataset.value
    this.setData({ equipment }, () => this.updateFiltered())
  },

  onSearch(event) {
    this.setData({ keyword: event.detail.value }, () => this.updateFiltered())
  },

  openDetail(event) {
    const id = event.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/training/detail?id=${id}`
    })
  },

  updateFiltered() {
    const { exercises, equipment, keyword } = this.data
    const filteredExercises = exercises.filter((item) => {
      const equipmentMatch = equipment === "全部" || equipment === "all" || item.equipment.includes(equipment)
      const keywordMatch = !keyword || item.title.includes(keyword) || item.muscle.includes(keyword)
      return equipmentMatch && keywordMatch
    })
    this.setData({ filteredExercises })
  },

  onBottomNav(event) {
    wx.redirectTo({
      url: event.detail.route
    })
  }
})
