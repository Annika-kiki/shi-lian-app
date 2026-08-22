"""Exercise content database and simple, explainable training-plan generator."""

EXERCISES = [
    {"id":"chest-01","name":"杠铃卧推","muscle":"胸","equipment":"杠铃","level":"中级","pattern":"推","steps":["肩胛后缩并贴紧凳面","杠铃下降至胸部中下方","呼气推起且手腕保持中立"],"warning":"新手需要保护者或使用安全架"},
    {"id":"chest-02","name":"哑铃上斜卧推","muscle":"胸","equipment":"哑铃","level":"中级","pattern":"推","steps":["上斜凳调至约30度","哑铃下降至上胸两侧","沿弧线向上推起"],"warning":"避免凳面角度过高导致肩部代偿"},
    {"id":"chest-03","name":"跪姿俯卧撑","muscle":"胸","equipment":"徒手","level":"新手","pattern":"推","steps":["膝盖着地并收紧核心","胸口靠近地面","推起时身体保持直线"],"warning":"不要塌腰或耸肩"},
    {"id":"back-01","name":"高位下拉","muscle":"背","equipment":"固定器械","level":"新手","pattern":"拉","steps":["胸口微微抬起","肘部向下向后拉","控制重量缓慢还原"],"warning":"不要用身体后仰甩动重量"},
    {"id":"back-02","name":"坐姿划船","muscle":"背","equipment":"固定器械","level":"新手","pattern":"拉","steps":["保持脊柱中立","肩胛骨先后收再拉肘","停顿后控制还原"],"warning":"避免圆肩和含胸"},
    {"id":"back-03","name":"单臂哑铃划船","muscle":"背","equipment":"哑铃","level":"中级","pattern":"拉","steps":["支撑侧保持稳定","肘部贴近身体向髋部拉","顶端收紧背部"],"warning":"躯干不要旋转"},
    {"id":"leg-01","name":"高脚杯深蹲","muscle":"腿臀","equipment":"哑铃","level":"新手","pattern":"蹲","steps":["双脚略宽于肩","膝盖跟随脚尖方向","髋膝同时伸展站起"],"warning":"脚跟保持着地"},
    {"id":"leg-02","name":"罗马尼亚硬拉","muscle":"腿臀","equipment":"哑铃","level":"中级","pattern":"髋铰链","steps":["膝盖微屈","髋部向后推并保持背部中立","臀腿发力站起"],"warning":"重量贴近腿部，不要弓背"},
    {"id":"leg-03","name":"保加利亚分腿蹲","muscle":"腿臀","equipment":"徒手/哑铃","level":"中级","pattern":"单腿","steps":["后脚放在凳上","前腿控制下降","前脚发力站起"],"warning":"保持骨盆稳定"},
    {"id":"shoulder-01","name":"坐姿哑铃推举","muscle":"肩","equipment":"哑铃","level":"中级","pattern":"推","steps":["核心收紧贴稳靠背","哑铃从耳侧推起","控制下降"],"warning":"避免腰部过度反弓"},
    {"id":"shoulder-02","name":"哑铃侧平举","muscle":"肩","equipment":"哑铃","level":"新手","pattern":"外展","steps":["肘部微屈","手臂抬至接近肩高","慢速下降"],"warning":"不要耸肩或借力摆动"},
    {"id":"core-01","name":"平板支撑","muscle":"核心","equipment":"徒手","level":"新手","pattern":"抗伸展","steps":["肘部位于肩下","夹紧臀部并收紧腹部","保持自然呼吸"],"warning":"腰部不要下塌"},
    {"id":"core-02","name":"死虫式","muscle":"核心","equipment":"徒手","level":"新手","pattern":"抗伸展","steps":["腰背贴地","对侧手脚缓慢伸展","回到起点后换边"],"warning":"动作范围以腰背不离地为准"},
]

ILLUSTRATIONS = {
    "chest-01": {"url": "/assets/exercises/barbell-bench-press.png", "active_muscles": ["胸大肌", "肱三头肌", "三角肌前束"]},
    "back-01": {"url": "/assets/exercises/lat-pulldown.png", "active_muscles": ["背阔肌", "肱二头肌", "菱形肌"]},
    "leg-01": {"url": "/assets/exercises/goblet-squat.png", "active_muscles": ["股四头肌", "臀大肌", "核心"]},
    "core-01": {"url": "/assets/exercises/forearm-plank.png", "active_muscles": ["腹横肌", "腹直肌", "臀大肌"]},
}

GOAL_REPS = {"减脂": "10–15", "增肌": "8–12", "保持健康": "10–12"}
SPECIAL_REPS = {"core-01": "30–45 秒", "core-02": "每侧 10–12"}


def list_exercises(muscle=None, equipment=None):
    items = [{**item, "illustration": ILLUSTRATIONS.get(item["id"])} for item in EXERCISES]
    if muscle:
        items = [x for x in items if x["muscle"] == muscle]
    if equipment:
        items = [x for x in items if equipment in x["equipment"]]
    return items


def generate_plan(goal="减脂", level="新手", days=3, equipment=None):
    if goal not in GOAL_REPS:
        raise ValueError("目标支持：减脂、增肌、保持健康")
    if level not in ("新手", "中级"):
        raise ValueError("训练水平支持：新手、中级")
    if not isinstance(days, int) or not 2 <= days <= 5:
        raise ValueError("每周训练天数应在 2–5 天")
    pool = [x for x in EXERCISES if not equipment or equipment in x["equipment"] or x["equipment"] == "徒手"]
    splits = [
        ("全身 A", ["腿臀", "胸", "背", "核心"]),
        ("全身 B", ["腿臀", "肩", "背", "核心"]),
        ("上肢", ["胸", "背", "肩", "核心"]),
        ("下肢与核心", ["腿臀", "腿臀", "核心", "背"]),
        ("全身巩固", ["腿臀", "胸", "背", "核心"]),
    ]
    sessions = []
    used = set()
    for index in range(days):
        title, muscles = splits[index]
        chosen = []
        for muscle in muscles:
            candidates = [x for x in pool if x["muscle"] == muscle]
            level_matches = [x for x in candidates if x["level"] == level]
            preferred = level_matches or candidates
            pick = next((x for x in preferred if x["id"] not in used), preferred[0] if preferred else None)
            if pick:
                chosen.append({"id": pick["id"], "name": pick["name"], "muscle": pick["muscle"],
                               "sets": 3, "reps": SPECIAL_REPS.get(pick["id"], GOAL_REPS[goal]),
                               "rest_seconds": 60 if goal == "减脂" else 90})
                used.add(pick["id"])
        sessions.append({"day": index + 1, "name": title, "estimated_minutes": 45, "exercises": chosen})
    return {"goal": goal, "level": level, "days_per_week": days,
            "principle": "先掌握动作，再逐周小幅增加次数或重量；疼痛时停止训练。", "sessions": sessions}
