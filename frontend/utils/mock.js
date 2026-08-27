const { calculateNutritionTargets } = require("./user")

const navItems = [
  { label: "首页", icon: "⌂", route: "/pages/home/home" },
  { label: "饮食", icon: "◔", route: "/pages/food/home" },
  { label: "训练", icon: "◆", route: "/pages/training/home" },
  { label: "记录", icon: "▦", route: "/pages/calendar/calendar" },
  { label: "我的", icon: "☺", route: "/pages/me/me" }
]

const profile = {
  name: "用户",
  goal: "减脂",
  days: 16,
  height: 165,
  weight: 55.2,
  targetWeight: 53.0,
  monthlyTraining: 6,
  streak: 16
}

const mockTargets = calculateNutritionTargets(profile)

const homeSummary = {
  date: "8月17日 · 星期一",
  greeting: "晚上好，用户",
  kcal: 1260,
  workout: 45,
  protein: { current: 68, target: mockTargets.proteinTargetG },
  carbs: { current: 130, target: mockTargets.carbTargetG },
  fat: { current: 35, target: mockTargets.fatTargetG }
}

const meals = [
  { label: "早餐", icon: "🍳", kcal: 380, detail: "燕麦牛奶 · 水煮蛋 · 香蕉" },
  { label: "午餐", icon: "🍱", kcal: 620, detail: "杂粮饭 · 鸡胸肉 · 西兰花" },
  { label: "晚餐", icon: "🌙", kcal: "尚未记录", detail: "建议补充蛋白与蔬菜" }
]

const recipePlans = [
  {
    id: "1",
    name: "番茄鸡胸荞麦面",
    minutes: 18,
    kcal: 510,
    protein: 44,
    fat: 16,
    tags: ["高蛋白", "均衡"],
    ingredients: [
      { name: "鸡胸肉", amount: "150 g" },
      { name: "番茄", amount: "200 g" },
      { name: "荞麦面", amount: "120 g" }
    ],
    steps: ["荞麦面先煮熟过凉", "鸡胸肉煎熟切片，番茄炒出汁", "把面和鸡胸肉拌入番茄酱汁即可"]
  },
  {
    id: "2",
    name: "三文鱼烤盘蔬菜",
    minutes: 25,
    kcal: 490,
    protein: 38,
    fat: 20,
    tags: ["低脂", "少油"],
    ingredients: [
      { name: "三文鱼", amount: "140 g" },
      { name: "菜花", amount: "180 g" },
      { name: "胡萝卜", amount: "120 g" }
    ],
    steps: ["三文鱼和蔬菜切好后平铺在烤盘里", "撒盐、黑胡椒和少量橄榄油", "烤至表面微焦后直接出炉"]
  },
  {
    id: "3",
    name: "虾仁蒸蛋碗",
    minutes: 15,
    kcal: 430,
    protein: 35,
    fat: 14,
    tags: ["快手", "清爽"],
    ingredients: [
      { name: "虾仁", amount: "120 g" },
      { name: "鸡蛋", amount: "2 个" },
      { name: "白菜", amount: "120 g" }
    ],
    steps: ["鸡蛋打散加温水，先蒸到半凝固", "放入虾仁和白菜继续蒸熟", "出锅后淋少量芝麻油即可"]
  },
  {
    id: "4",
    name: "牛肉土豆焖锅",
    minutes: 28,
    kcal: 560,
    protein: 42,
    fat: 22,
    tags: ["饱足", "高蛋白"],
    ingredients: [
      { name: "牛肉", amount: "140 g" },
      { name: "土豆", amount: "160 g" },
      { name: "洋葱", amount: "80 g" }
    ],
    steps: ["牛肉先煎香，土豆和洋葱切块备用", "加入少量热水，小火焖煮到土豆软糯", "收汁后出锅，风味更浓郁"]
  },
  {
    id: "5",
    name: "豆腐菌菇汤",
    minutes: 20,
    kcal: 380,
    protein: 30,
    fat: 12,
    tags: ["清爽", "少油"],
    ingredients: [
      { name: "北豆腐", amount: "180 g" },
      { name: "香菇", amount: "120 g" },
      { name: "金针菇", amount: "100 g" }
    ],
    steps: ["香菇和金针菇先煮出鲜味", "加入豆腐块，小火煮几分钟", "最后淋少量芝麻油，清汤就完成了"]
  }
]

const ingredientChips = [
  "鸡胸肉",
  "鸡蛋",
  "牛肉",
  "三文鱼",
  "虾仁",
  "北豆腐",
  "米饭",
  "糙米饭",
  "燕麦",
  "红薯",
  "西兰花",
  "番茄"
]
const calorieOptions = ["约400 kcal", "约500 kcal", "约600 kcal"]
const tasteOptions = ["少油", "高蛋白", "15 分钟内"]

const bodyParts = [
  { label: "胸", icon: "◉", part: "chest" },
  { label: "背", icon: "◇", part: "back" },
  { label: "肩", icon: "△", part: "shoulder" },
  { label: "手臂", icon: "⚡", part: "arm" },
  { label: "腿臀", icon: "∧", part: "leg" },
  { label: "核心", icon: "◎", part: "core" }
]

const exercises = [
  {
    id: "bench",
    title: "杠铃卧推",
    muscle: "胸大肌",
    equipment: "杠铃",
    level: "中级",
    part: "chest",
    icon: "🏋️"
  },
  {
    id: "incline",
    title: "上斜哑铃卧推",
    muscle: "上胸",
    equipment: "哑铃",
    level: "中级",
    part: "chest",
    icon: "💪"
  },
  {
    id: "machine",
    title: "坐姿推胸",
    muscle: "胸大肌",
    equipment: "固定器械",
    level: "新手",
    part: "chest",
    icon: "🎯"
  }
]

const exerciseDetail = {
  bench: {
    title: "杠铃卧推",
    part: "胸部 · 杠铃",
    main: "胸大肌",
    assist: "肱三头肌",
    steps: ["双脚踩实，肩胛骨向后收紧", "杠铃下降至胸部中下方", "呼气推起，手肘不要完全锁死"],
    notes: "保持手腕中立；新手建议有人保护。"
  }
}

const trainingSummary = {
  focus: "胸部 + 肱三头肌",
  moves: 6,
  minutes: 55,
  recent: {
    title: "胸部训练",
    date: "8月15日",
    detail: "6 个动作 · 52 分钟 · 4,280 kg"
  }
}

const recordWorkout = {
  name: "杠铃卧推",
  part: "胸部",
  startedAt: "18:42",
  kcal: 126,
  sets: [
    { group: 1, weight: 20, reps: 12, done: true },
    { group: 2, weight: 25, reps: 10, done: true },
    { group: 3, weight: 25, reps: 10, done: false },
    { group: 4, weight: 25, reps: 8, done: false }
  ]
}

const calendarData = {
  monthLabel: "2026 年 8 月",
  selectedDay: "8 月 17 日 · 今天",
  selectedTitle: "休息日",
  selectedNote: "保持充足睡眠，为下次训练恢复体力。",
  overview: { count: 6, duration: 286, top: "胸部 · 3 次" },
  history: [{ day: "8 月 15 日", name: "腿部训练", duration: "52 min" }]
}

const bodyTrend = {
  currentWeight: 55.2,
  last30Days: -1.3,
  goalWeight: 53.0,
  distance: 2.2,
  points: [57.1, 56.5, 56.0, 55.8, 55.1, 54.4, 55.2],
  labels: ["7/19", "7/26", "8/3", "8/7", "8/10", "8/14", "8/17"]
}

const me = {
  avatar: "🌿",
  name: profile.name,
  goal: profile.goal,
  height: `${profile.height} cm`,
  weight: `${profile.weight} kg`,
  trainingCount: `${profile.monthlyTraining} 次`,
  streak: `${profile.streak} 天`
}

function getExerciseList(part) {
  if (!part || part === "all") return exercises
  return exercises.filter((item) => item.part === part)
}

function getExerciseById(id) {
  return exercises.find((item) => item.id === id) || exercises[0]
}

function getRecipeById(id) {
  return recipePlans.find((item) => item.id === id) || recipePlans[0]
}

module.exports = {
  navItems,
  profile,
  homeSummary,
  meals,
  recipePlans,
  ingredientChips,
  calorieOptions,
  tasteOptions,
  bodyParts,
  exercises,
  exerciseDetail,
  trainingSummary,
  recordWorkout,
  calendarData,
  bodyTrend,
  me,
  getExerciseList,
  getExerciseById,
  getRecipeById
}
