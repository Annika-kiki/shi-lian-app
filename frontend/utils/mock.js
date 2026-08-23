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

const homeSummary = {
  date: "8月17日 · 星期一",
  greeting: "晚上好，用户",
  kcal: 1260,
  workout: 45,
  protein: { current: 68, target: 100 },
  carbs: { current: 130, target: 200 },
  fat: { current: 35, target: 50 }
}

const meals = [
  { label: "早餐", icon: "🥣", kcal: 380, detail: "燕麦牛奶 · 水煮蛋 · 香蕉" },
  { label: "午餐", icon: "🍱", kcal: 620, detail: "杂粮饭 · 番茄鸡胸肉 · 西兰花" },
  { label: "晚餐", icon: "🌙", kcal: "尚未记录", detail: "建议补充蛋白与蔬菜" }
]

const recipePlans = [
  {
    id: "1",
    name: "番茄鸡胸滑蛋",
    minutes: 20,
    kcal: 520,
    protein: 48,
    fat: 20,
    tags: ["高蛋白", "少油"],
    ingredients: [
      { name: "鸡胸肉", amount: "150 g" },
      { name: "鸡蛋", amount: "2 个" },
      { name: "西红柿", amount: "200 g" }
    ],
    steps: ["鸡胸肉切块腌制", "鸡蛋炒至半熟盛出", "番茄炒出汁，加入鸡胸肉和鸡蛋"]
  },
  {
    id: "2",
    name: "西兰花鸡胸烘蛋",
    minutes: 25,
    kcal: 485,
    protein: 42,
    fat: 18,
    tags: ["高蛋白", "低脂"],
    ingredients: [
      { name: "鸡胸肉", amount: "120 g" },
      { name: "鸡蛋", amount: "2 个" },
      { name: "西兰花", amount: "180 g" }
    ],
    steps: ["西兰花焯水", "鸡胸肉煎熟切块", "蛋液混合后烘烤至定型"]
  },
  {
    id: "3",
    name: "番茄鸡胸暖沙拉",
    minutes: 15,
    kcal: 450,
    protein: 36,
    fat: 14,
    tags: ["快手", "轻负担"],
    ingredients: [
      { name: "鸡胸肉", amount: "160 g" },
      { name: "番茄", amount: "1 个" },
      { name: "西兰花", amount: "120 g" }
    ],
    steps: ["鸡胸肉煎熟", "蔬菜焯水后过冷", "拌匀后淋少量酱汁"]
  }
]

const ingredientChips = ["鸡胸肉", "西红柿", "鸡蛋", "西兰花"]
const calorieOptions = ["约 400 kcal", "约 500 kcal", "约 600 kcal"]
const tasteOptions = ["少油", "高蛋白", "15 分钟内"]

const bodyParts = [
  { label: "胸", icon: "◉", part: "chest" },
  { label: "背", icon: "◇", part: "back" },
  { label: "肩", icon: "△", part: "shoulder" },
  { label: "手臂", icon: "≋", part: "arm" },
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
    icon: "🏋"
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
    icon: "⚙"
  },
  {
    id: "fly",
    title: "绳索夹胸",
    muscle: "胸大肌",
    equipment: "龙门架",
    level: "中级",
    part: "chest",
    icon: "↔"
  },
  {
    id: "back-row",
    title: "器械划船",
    muscle: "背阔肌",
    equipment: "器械",
    level: "新手",
    part: "back",
    icon: "⟷"
  },
  {
    id: "shoulder-press",
    title: "哑铃推举",
    muscle: "三角肌",
    equipment: "哑铃",
    level: "中级",
    part: "shoulder",
    icon: "▲"
  }
]

const exerciseDetail = {
  bench: {
    title: "杠铃卧推",
    part: "胸部 · 杠铃",
    main: "胸大肌",
    assist: "肱三头肌",
    steps: ["双脚踩稳，肩胛骨向后收紧", "杠铃下降至胸部中下方", "呼气推起，手肘不要完全锁死"],
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
  avatar: "🍃",
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
