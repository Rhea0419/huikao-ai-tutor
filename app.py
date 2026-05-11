
import streamlit as st
import random
import time
from datetime import datetime
from collections import defaultdict
from subjects import SUBJECTS, EXAM_SYLLABUS, POINTS_RULES
from question_bank import ALL_QUESTIONS, SUBJECT_CHAPTERS

st.set_page_config(
    page_title="会考AI学习管家", page_icon="🎓", layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# ===== 浅色主题关键 CSS =====
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700;900&display=swap');
    * { font-family: 'Noto Sans SC', sans-serif; }

    /* 强制浅色主题 */
    .stApp { background: #f8f9fa !important; }
    .main .block-container { background: #f8f9fa; }
    section[data-testid="stSidebar"] { background: #ffffff; }

    /* 全局文字色 */
    .stApp, .stMarkdown, p, div, span, label { color: #2d3436; }
    h1, h2, h3, h4 { color: #2d3436; }

    /* 卡片样式 */
    .subject-card {
        border-radius: 20px; padding: 30px; text-align: center; cursor: pointer;
        transition: all 0.3s; margin: 10px; box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .subject-card:hover { transform: translateY(-5px); box-shadow: 0 12px 40px rgba(0,0,0,0.2); }

    /* 知识点节点 */
    .kb-node {
        padding: 14px 18px; margin: 6px 0; border-radius: 12px;
        border: 1.5px solid #e0e0e0; background: white;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04); cursor: pointer;
        transition: all 0.2s;
    }
    .kb-node:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .kb-mastered { border-left: 4px solid #27ae60; }
    .kb-ok { border-left: 4px solid #f39c12; }
    .kb-weak { border-left: 4px solid #e74c3c; }

    .sub-kb {
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 14px; margin: 3px 0 3px 20px; border-radius: 8px;
        background: #fafafa; border: 1px solid #eee;
    }

    .question-card {
        background: white; border-radius: 16px; padding: 22px; margin: 12px 0;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    }

    .feedback-ok {
        background: #d4edda; color: #155724; padding: 14px; border-radius: 10px;
    }
    .feedback-no {
        background: #f8d7da; color: #721c24; padding: 14px; border-radius: 10px;
    }

    .upload-zone {
        border: 3px dashed #ccc; border-radius: 20px; padding: 40px; text-align: center;
        transition: all 0.3s; background: white;
    }
    .upload-zone:hover { border-color: #6c5ce7; background: #f8f7ff; }

    .tag {
        display: inline-block; padding: 4px 12px; border-radius: 20px;
        font-size: 0.82em; font-weight: bold; margin: 2px;
    }

    /* 积分样式 */
    .points-badge {
        display: inline-block; background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white; padding: 6px 16px; border-radius: 20px; font-weight: 900;
        font-size: 1.1em; box-shadow: 0 2px 8px rgba(245,87,108,0.3);
    }
</style>
""", unsafe_allow_html=True)

# ===== 初始化 =====
def init():
    defaults = {
        "subject": None, "page": "home",
        "subject_tab": "knowledge",
        "points": 0, "streak": 0, "max_streak": 0,
        "total_correct": 0, "total_wrong": 0,
        "expanded_kb": set(),
        "practice_chapter": None, "practice_questions": [],
        "practice_idx": 0, "practice_answers": {}, "practice_submitted": set(),
        "exam_started": False, "exam_submitted": False,
        "exam_start_time": None, "exam_end_time": None,
        "exam_questions": [], "exam_answers": {}, "exam_submitted_set": set(),
        "exam_idx": 0,
        "kb_proficiency": defaultdict(lambda: defaultdict(lambda: {"correct": 0, "total": 0})),
        "history": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init()

# ===== 工具函数 =====
def get_subject(): 
    return st.session_state.subject

def get_theme():
    s = get_subject()
    if s and s in SUBJECTS:
        return SUBJECTS[s]
    return {"color_primary": "#636e72", "color_secondary": "#b2bec3",
            "color_bg": "#f5f6fa", "color_accent": "#6c5ce7",
            "color_gradient": "linear-gradient(135deg, #636e72, #b2bec3)",
            "icon": "🎓", "emoji": "📚"}

def add_points(n, reason=""):
    st.session_state.points += n
    st.session_state.history.append(f"+{n} {'— '+reason if reason else ''}")

def calc_kb_pct(subj, kb):
    d = st.session_state.kb_proficiency[subj][kb]
    if d["total"] == 0: return 0
    return d["correct"] / d["total"]

def kb_level(pct):
    if pct >= 0.8: return "mastered", "熟练掌握", "#27ae60"
    elif pct >= 0.5: return "ok", "一般掌握", "#f39c12"
    return "weak", "不太掌握", "#e74c3c"

def update_kb(ch, correct):
    st.session_state.kb_proficiency[get_subject()][ch]["total"] += 1
    if correct:
        st.session_state.kb_proficiency[get_subject()][ch]["correct"] += 1

def get_questions(subj):
    return ALL_QUESTIONS.get(subj, [])

# ===== 侧边栏 =====
with st.sidebar:
    st.markdown("## 🎓 会考AI学习管家")
    theme = get_theme()

    # 积分
    st.markdown(f"""
    <div style="background:{theme['color_gradient']};border-radius:18px;padding:16px 20px;color:white;text-align:center;box-shadow:0 4px 16px rgba(0,0,0,0.15);margin-bottom:12px;">
        <div style="font-size:0.8em;opacity:0.9;">🏆 学习积分</div>
        <div style="font-size:2.4em;font-weight:900;">{st.session_state.points}</div>
        <div style="font-size:0.8em;opacity:0.85;">
            ✅{st.session_state.total_correct} ❌{st.session_state.total_wrong} 🔥{st.session_state.max_streak}连击
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if get_subject():
        st.markdown(f"### {theme['icon']} {get_subject()}")
        if st.button("🏠 返回首页", use_container_width=True):
            st.session_state.page = "home"
            st.session_state.subject = None
            st.rerun()
    else:
        st.info("👆 选择科目开始学习")

    st.divider()
    st.markdown("### 📤 上传资料")
    st.caption("支持 PDF / Word")
    uploaded_files = st.file_uploader("上传文件", type=["pdf","docx","doc"], accept_multiple_files=True,
                                      label_visibility="collapsed", key="side_up")
    if uploaded_files:
        for f in uploaded_files:
            st.success(f"✅ {f.name}")
            add_points(5, f"上传: {f.name}")

    st.divider()
    ans_count = st.session_state.total_correct + st.session_state.total_wrong
    pct = st.session_state.total_correct / max(1, ans_count) * 100
    st.caption(f"📊 {ans_count}题 | 正确率 {pct:.0f}%")

# ========== 首页 ==========
if st.session_state.page == "home":
    st.markdown('<h1 style="text-align:center;font-weight:900;margin:20px 0 10px;">🎓 北京高中学业水平合格性考试</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;font-size:1.15em;color:#636e72;margin-bottom:30px;">选择科目，开启会考学习之旅 ✨</p>', unsafe_allow_html=True)

    cols = st.columns(4)
    for i, (subj, cfg) in enumerate(SUBJECTS.items()):
        with cols[i]:
            mastered = sum(1 for k in cfg["kb_points"] if calc_kb_pct(subj, k) >= 0.8)
            total_kb = len(cfg["kb_points"])
            total_q = len(get_questions(subj))

            card = f"""
            <div style="background:{cfg['color_gradient']};border-radius:20px;padding:28px 18px;
                        text-align:center;color:white;box-shadow:0 8px 30px rgba(0,0,0,0.12);
                        min-height:340px;display:flex;flex-direction:column;justify-content:space-between;">
                <div>
                    <div style="font-size:3.2em;">{cfg['icon']}</div>
                    <h2 style="font-weight:900;margin:12px 0;font-size:1.7em;color:white;">{subj}</h2>
                    <p style="opacity:0.85;font-size:0.9em;color:white;">{cfg['emoji']} 北京合格考</p>
                </div>
                <div style="background:rgba(255,255,255,0.22);border-radius:14px;padding:12px;margin-top:8px;">
                    <div style="font-size:0.85em;color:white;">知识点掌握</div>
                    <div style="font-size:1.8em;font-weight:900;color:white;">{mastered}/{total_kb}</div>
                    <div style="font-size:0.75em;opacity:0.85;color:white;">题库 {total_q} 题</div>
                </div>
            </div>
            """
            st.markdown(card, unsafe_allow_html=True)
            if st.button(f"开始学习 {subj}", key=f"enter_{subj}", use_container_width=True, type="primary"):
                st.session_state.page = "subject"
                st.session_state.subject = subj
                st.session_state.subject_tab = "knowledge"
                add_points(POINTS_RULES["daily_login"], "每日登录")
                st.rerun()

# ========== 科目页面 ==========
elif st.session_state.page == "subject" and get_subject():
    subj = get_subject()
    cfg = SUBJECTS[subj]
    tc = cfg["color_primary"]

    st.markdown(f'<h1 style="font-weight:900;color:{tc};">{cfg["icon"]} {subj} — 北京合格考</h1>', unsafe_allow_html=True)

    t1, t2, t3, t4, t5 = st.tabs(["🧠 知识图谱", "📝 练习", "⏱️ 模拟考", "📋 考纲", "📤 上传"])

    # ===== Tab 1: 知识图谱 =====
    with t1:
        st.markdown(f'<h3 style="color:{tc};">🧠 知识图谱</h3>', unsafe_allow_html=True)
        st.caption("点击知识点展开子知识点 | 🟢熟练 🟡一般 🔴薄弱")

        for kb_name, kb_info in cfg["kb_points"].items():
            pct = calc_kb_pct(subj, kb_name)
            lvl, label, lc = kb_level(pct)
            kb_key = f"{subj}_{kb_name}"

            # 用 button 代替 expander —— 保证可点击
            arrow = "▼" if kb_key in st.session_state.expanded_kb else "▶"
            btn_label = f"{arrow} {kb_info['icon']} {kb_name}  —  {label}  ({pct*100:.0f}%)"

            col_btn, col_bar = st.columns([5, 1])
            with col_btn:
                if st.button(btn_label, key=f"kb_btn_{kb_key}", use_container_width=True):
                    if kb_key in st.session_state.expanded_kb:
                        st.session_state.expanded_kb.discard(kb_key)
                    else:
                        st.session_state.expanded_kb.add(kb_key)
                    st.rerun()

            # 展开内容
            if kb_key in st.session_state.expanded_kb:
                st.caption(f"包含 {len(kb_info['subs'])} 个子知识点")
                for sub_kb in kb_info["subs"]:
                    sp = pct + random.uniform(-0.08, 0.08)
                    sp = max(0, min(1, sp))
                    sl, slab, sc = kb_level(sp)
                    st.markdown(f"""
                    <div class="sub-kb">
                        <span>📌 {sub_kb}</span>
                        <span style="color:{sc};font-weight:bold;font-size:0.85em;">{slab}</span>
                    </div>
                    """, unsafe_allow_html=True)

                if st.button(f"📝 练习「{kb_name}」", key=f"kb_prac_{kb_key}", use_container_width=True):
                    st.session_state.practice_chapter = kb_name
                    st.session_state.practice_questions = [q for q in get_questions(subj) if q["chapter"] == kb_name]
                    random.shuffle(st.session_state.practice_questions)
                    st.session_state.practice_idx = 0
                    st.session_state.practice_answers = {}
                    st.session_state.practice_submitted = set()
                    st.session_state.subject_tab = "practice"
                    st.rerun()

    # ===== Tab 2: 练习 =====
    with t2:
        st.markdown(f'<h3 style="color:{tc};">📝 练习模式</h3>', unsafe_allow_html=True)

        if not st.session_state.practice_questions:
            chapters = list(dict.fromkeys([q["chapter"] for q in get_questions(subj)]))
            st.markdown("#### 选择章节")
            cols = st.columns(3)
            for i, ch in enumerate(chapters):
                pct = calc_kb_pct(subj, ch)
                _, label, _ = kb_level(pct)
                with cols[i % 3]:
                    if st.button(f"{label}\n{ch} ({pct*100:.0f}%)", key=f"pch_{i}", use_container_width=True):
                        st.session_state.practice_chapter = ch
                        st.session_state.practice_questions = [q for q in get_questions(subj) if q["chapter"] == ch]
                        random.shuffle(st.session_state.practice_questions)
                        st.session_state.practice_idx = 0
                        st.session_state.practice_answers = {}
                        st.session_state.practice_submitted = set()
                        st.rerun()

        qs = st.session_state.practice_questions
        idx = st.session_state.practice_idx
        if qs and idx < len(qs):
            q = qs[idx]
            qid = q["id"]
            ok = qid in st.session_state.practice_submitted
            prev = st.session_state.practice_answers.get(qid, "")

            st.progress(idx/len(qs), text=f"{idx+1}/{len(qs)}")
            st.markdown(f'<div class="question-card"><strong>{idx+1}.</strong> {q["q"]}<br><span class="tag" style="background:{cfg["color_secondary"]};color:white;">{q["chapter"]}</span></div>', unsafe_allow_html=True)

            choice = st.radio("选择答案：", q["opts"],
                              index=q["opts"].index(prev) if prev in q["opts"] else None,
                              key=f"pq_{qid}", disabled=ok)

            c1, c2 = st.columns(2)
            with c1:
                if not ok and st.button("✅ 提交", key=f"ps_{qid}", use_container_width=True):
                    if choice:
                        st.session_state.practice_answers[qid] = choice
                        st.session_state.practice_submitted.add(qid)
                        correct = (choice[0] == q["ans"])
                        update_kb(q["chapter"], correct)
                        if correct:
                            st.session_state.total_correct += 1
                            st.session_state.streak += 1
                            st.session_state.max_streak = max(st.session_state.max_streak, st.session_state.streak)
                            add_points(POINTS_RULES["practice_correct"], "答对")
                            if st.session_state.streak == 3: add_points(15, "3连击!")
                            elif st.session_state.streak == 5: add_points(30, "5连击!")
                        else:
                            st.session_state.total_wrong += 1
                            st.session_state.streak = 0
                            add_points(2, "再接再厉")
                        st.rerun()
                    else:
                        st.warning("请选择答案")
            with c2:
                if ok and idx+1 < len(qs) and st.button("➡️ 下一题", key=f"pn_{qid}", use_container_width=True):
                    st.session_state.practice_idx += 1
                    st.rerun()

            if ok:
                ua = st.session_state.practice_answers.get(qid, "")[0] if st.session_state.practice_answers.get(qid) else ""
                if ua == q["ans"]:
                    st.markdown(f'<div class="feedback-ok">🎉 <strong>正确！</strong></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="feedback-no">😅 <strong>错误</strong>（答案：{q["ans"]}）</div>', unsafe_allow_html=True)
                st.info(f"💡 {q['exp']}")

        elif qs and idx >= len(qs):
            n = sum(1 for q in qs if st.session_state.practice_answers.get(q["id"],"") and st.session_state.practice_answers[q["id"]][0] == q["ans"])
            st.balloons()
            st.success(f"🎉 完成！{n}/{len(qs)} ({n/len(qs)*100:.0f}%)")
            ch = st.session_state.practice_chapter
            chp = calc_kb_pct(subj, ch)
            if chp >= 0.9 and f"m_{subj}_{ch}" not in st.session_state:
                st.session_state[f"m_{subj}_{ch}"] = True
                add_points(100, f"掌握: {ch}")
                st.success(f"🏆 章节「{ch}」精通！+100分")
            if st.button("🔄 再来", use_container_width=True):
                st.session_state.practice_questions = []
                st.rerun()

    # ===== Tab 3: 模拟考 =====
    with t3:
        st.markdown(f'<h3 style="color:{tc};">⏱️ 模拟考试</h3>', unsafe_allow_html=True)
        all_qs = get_questions(subj)
        n_qs = min(20, len(all_qs))

        if not st.session_state.exam_started and not st.session_state.exam_submitted:
            st.markdown(f"""
            <div style="background:{cfg['color_bg']};border-radius:16px;padding:22px;margin:12px 0;">
                <h4>📋 考试说明</h4>
                <p>⏱️ 60分钟 | 📝 {n_qs}题 | 💯 100分 | ✅ 60分及格</p>
                <p>⚠️ 时间到自动交卷 | 提交后不可改</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚀 开始考试", type="primary", use_container_width=True):
                exam_qs = random.sample(all_qs, min(n_qs, len(all_qs)))
                random.shuffle(exam_qs)
                st.session_state.exam_questions = exam_qs
                st.session_state.exam_answers = {}
                st.session_state.exam_submitted_set = set()
                st.session_state.exam_started = True
                st.session_state.exam_submitted = False
                st.session_state.exam_start_time = time.time()
                st.session_state.exam_idx = 0
                st.rerun()

        elif st.session_state.exam_started and not st.session_state.exam_submitted:
            eqs = st.session_state.exam_questions
            total = len(eqs)
            elapsed = time.time() - st.session_state.exam_start_time
            rem = max(0, 3600 - elapsed)
            mins, secs = int(rem//60), int(rem%60)

            tcol, pcol = st.columns([1, 3])
            with tcol:
                tc2 = "#e74c3c" if rem < 600 else tc
                st.markdown(f'<div style="background:{tc2};color:white;padding:14px;border-radius:14px;text-align:center;font-size:1.7em;font-weight:900;">⏰ {mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)
            with pcol:
                done = len(st.session_state.exam_submitted_set)
                st.progress(done/total, text=f"{done}/{total}")

            if rem <= 0:
                st.session_state.exam_submitted = True
                st.session_state.exam_end_time = time.time()
                st.rerun()

            ei = st.session_state.exam_idx
            if ei < total:
                q = eqs[ei]
                qid = q["id"]
                sub = qid in st.session_state.exam_submitted_set
                prev = st.session_state.exam_answers.get(qid, "")

                st.markdown(f'<div class="question-card"><strong>{ei+1}.</strong> {q["q"]}<br><span class="tag" style="background:{cfg["color_secondary"]};color:white;">{q["chapter"]}</span></div>', unsafe_allow_html=True)

                choice = st.radio("选择：", q["opts"],
                                  index=q["opts"].index(prev) if prev in q["opts"] else None,
                                  key=f"eq_{qid}", disabled=sub)

                c1, c2 = st.columns(2)
                with c1:
                    if not sub and st.button("提交", key=f"es_{qid}"):
                        if choice:
                            st.session_state.exam_answers[qid] = choice
                            st.session_state.exam_submitted_set.add(qid)
                            st.rerun()
                with c2:
                    if st.button("跳过", key=f"esk_{ei}"):
                        st.session_state.exam_idx = min(ei+1, total-1)
                        st.rerun()

            st.divider()
            if st.button("📝 交卷", type="primary", use_container_width=True):
                st.session_state.exam_submitted = True
                st.session_state.exam_end_time = time.time()
                st.rerun()

        if st.session_state.exam_submitted:
            eqs = st.session_state.exam_questions
            total = len(eqs)
            per = 100 // total
            corr = 0
            results = []
            for q in eqs:
                a = st.session_state.exam_answers.get(q["id"], "")
                l = a[0] if a else ""
                ok = (l == q["ans"])
                if ok: corr += 1
                results.append({"q": q, "ans": l or "未答", "ok": ok})
                update_kb(q["chapter"], ok)
                if ok:
                    st.session_state.total_correct += 1
                    st.session_state.streak += 1
                    st.session_state.max_streak = max(st.session_state.max_streak, st.session_state.streak)
                else:
                    st.session_state.total_wrong += 1
                    st.session_state.streak = 0

            score = corr * per
            passed = score >= 60
            if passed:
                st.balloons()
                add_points(50, "模拟考通过!")
            add_points(corr * 20 // per, "考试得分")

            sc = "#27ae60" if passed else "#e74c3c"
            st.markdown(f'<div style="font-size:3em;font-weight:900;text-align:center;color:{sc};">{score} 分</div>', unsafe_allow_html=True)
            st.markdown(f"### {'🎉 通过！' if passed else '💪 加油！'}")
            st.markdown(f"✅ {corr}/{total} | ⏱️ {(st.session_state.exam_end_time - st.session_state.exam_start_time)/60:.1f}分")

            wrong = [r for r in results if not r["ok"]]
            if wrong:
                st.markdown("#### ❌ 错题")
                for r in wrong:
                    q = r["q"]
                    with st.expander(f"{q['chapter']} — {q['q'][:40]}..."):
                        st.write(f"你的: {r['ans']} | 正确: {q['ans']}")
                        st.info(q['exp'])

            if st.button("🔄 重新考", use_container_width=True):
                st.session_state.exam_started = False
                st.session_state.exam_submitted = False
                st.rerun()

    # ===== Tab 4: 考纲 =====
    with t4:
        st.markdown(f'<h3 style="color:{tc};">📋 考纲解析</h3>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:{cfg['color_bg']};border-radius:16px;padding:24px;">
            {EXAM_SYLLABUS.get(subj, '')}
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.markdown("### 📚 知识点清单")
        for kb_name, kb_info in cfg["kb_points"].items():
            st.markdown(f"**{kb_info['icon']} {kb_name}**")
            tags_html = " ".join([f'<span class="tag" style="background:{cfg["color_secondary"]};color:white;">{s}</span>' for s in kb_info["subs"]])
            st.markdown(tags_html, unsafe_allow_html=True)

    # ===== Tab 5: 上传 =====
    with t5:
        st.markdown(f'<h3 style="color:{tc};">📤 上传学习资料</h3>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="upload-zone">
            <div style="font-size:3em;">📤</div>
            <h4>支持 PDF / Word / TXT</h4>
            <p style="color:#888;">上传后自动解析内容</p>
        </div>
        """, unsafe_allow_html=True)
        up_main = st.file_uploader("选择文件", type=["pdf","docx","doc","txt"],
                                    accept_multiple_files=True, label_visibility="collapsed", key="main_up")
        if up_main:
            for f in up_main:
                st.success(f"✅ {f.name} ({f.size/1024:.0f}KB)")
                add_points(5, f"上传: {f.name}")
                try:
                    import io
                    if f.name.endswith('.pdf'):
                        import pymupdf
                        doc = pymupdf.open(stream=f.read(), filetype="pdf")
                        text = "".join([p.get_text() for p in doc])
                        st.text_area("预览", text[:400], height=120)
                    elif f.name.endswith(('.docx','.doc')):
                        import docx as pydocx
                        doc = pydocx.Document(io.BytesIO(f.read()))
                        text = "\\n".join([p.text for p in doc.paragraphs])
                        st.text_area("预览", text[:400], height=120)
                    elif f.name.endswith('.txt'):
                        text = f.read().decode('utf-8', errors='ignore')
                        st.text_area("预览", text[:400], height=120)
                except Exception as e:
                    st.warning(f"解析: {e}")

st.divider()
st.caption("🎓 北京会考AI学习管家 Demo v2.1 | 数据参考：北京教育考试院 + 高中课程标准")
