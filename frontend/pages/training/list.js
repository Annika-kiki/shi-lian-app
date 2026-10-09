const { PARTS, localList, mergeCatalog } = require("../../utils/exercises")
const { request } = require("../../utils/api")
const { navigationBehavior } = require("../../utils/navigation")

Page({
  behaviors: [navigationBehavior],
  data: {
    part: "chest",
    keyword: "",
    equipment: "全部",
    equipmentTabs: ["全部", "杠铃", "哑铃", "固定器械", "绳索", "徒手"],
    exercises: [],
    filteredExercises: [],
    title: "胸部动作"
  },

  async onLoad(query) {
    const part = PARTS[query.part] ? query.part : "chest"
    const exercises = localList(part)
    this.setData({ part, exercises, filteredExercises: exercises, title: `${PARTS[part]}动作` })
    try {
      const items = await request("/api/exercises")
      this.setData({ exercises: mergeCatalog(items, part) }, () => this.updateFiltered())
    } catch (error) {
      // The bundled catalog and illustrations remain available offline.
    }
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
      const keywordMatch = !keyword || item.title.includes(keyword) || item.muscle.includes(keyword) || item.equipment.includes(keyword)
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
