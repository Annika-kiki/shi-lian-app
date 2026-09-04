const { getExerciseList } = require("../../utils/mock")
const { getExercises } = require("../../utils/api")
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


function titleForPart(part) {
  return {
    chest: "胸部动作",
    back: "背部动作",
    shoulder: "肩部动作",
    arm: "手臂动作",
    leg: "腿臀动作",
    core: "核心动作"
  }[part] || "动作列表"
}

Page({
  data: {
    part: "chest",
    keyword: "",
    equipment: "全部",
    equipmentTabs: ["全部", "杠铃", "哑铃", "固定器械", "徒手", "绳索"],
    exercises: [],
    filteredExercises: [],
    title: "胸部动作"
  },

  onLoad(query) {
    const part = query.part || "chest"
    this.setData({
      part,
      title: titleForPart(part)
    })
    this.loadExercises(part)
  },

  loadExercises(part) {
    const fallback = getExerciseList(part)
    this.setData({
      exercises: fallback,
      filteredExercises: fallback
    })
    getExercises(part).then((remoteExercises) => {
      this.setData({
        exercises: remoteExercises,
        filteredExercises: remoteExercises
      }, () => this.updateFiltered())
    }).catch(() => {
      this.updateFiltered()
    })
  },

  goBack() {
    navigateBackOrRedirect("/pages/training/home")
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
      const equipmentMatch = equipment === "全部" || equipment === "all" || String(item.equipment || "").includes(equipment)
      const keywordMatch = !keyword || String(item.title || "").includes(keyword) || String(item.muscle || "").includes(keyword) || String(item.equipment || "").includes(keyword)
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
