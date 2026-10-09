const catalog = require("./exercise-catalog.json")
const { request } = require("./api")
const PARTS = { chest: "胸部", back: "背部", shoulder: "肩部", arm: "手臂", leg: "臀腿", core: "核心" }

function normalize(item) {
  const local = catalog.find((entry) => entry.name === item.name)
  return {
    ...local, ...item,
    title: item.name, muscle: item.primary_muscle, level: item.difficulty,
    body_part: item.body_part === "腿部" ? "臀腿" : item.body_part,
    imageSrc: local ? local.imageSrc : "",
    slug: local ? local.slug : String(item.id),
    icon: ""
  }
}
function localList(part) {
  return catalog.filter((item) => !part || item.part === part).map(normalize)
}
function localExercise(id) {
  return catalog.find((item) => item.slug === String(id))
}
// Match by name, never assume database IDs are the same on every installation.
async function resolveExercise(id) {
  const local = localExercise(id)
  if (!local) return normalize(await request(`/api/exercises/${id}`))
  const items = await request(`/api/exercises?q=${encodeURIComponent(local.name)}`)
  const item = items.find((entry) => entry.name === local.name)
  if (!item) throw new Error("请重启后端以更新动作库")
  return normalize(item)
}
function mergeCatalog(items, part) {
  const merged = localList(part)
  items.map(normalize).forEach((item) => {
    if (item.body_part !== PARTS[part]) return
    const index = merged.findIndex((entry) => entry.name === item.name)
    if (index >= 0) merged[index] = item
    else merged.push(item)
  })
  return merged
}
module.exports = { PARTS, catalog, normalize, localList, localExercise, resolveExercise, mergeCatalog }
