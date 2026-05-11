
import streamlit as st
import random, time, io
from collections import defaultdict
from subjects import SUBJECTS, EXAM_SYLLABUS, POINTS_RULES
from question_bank import ALL_QUESTIONS

st.set_page_config(page_title="会考AI学习管家", page_icon="🎓", layout="wide",
                   initial_sidebar_state="expanded")

# ===== CSS =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;600;700;900&display=swap');
* { font-family: 'Noto Sans SC', sans-serif; }
.stApp { background: #f1f5f9; }
section[data-testid="stSidebar"] { background: #ffffff; }
h1,h2,h3,h4,h5,p,span,div,label,li { color: #1e293b; }
.card {
    background: #ffffff; border-radius: 16px; padding: 22px; margin: 10px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
    border: 1px solid #e2e8f0;
}
.subkb-item {
    background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
    padding: 14px 18px; margin: 8px 0; font-size: 0.92em;
}
.subkb-item .label-c { color: #64748b; font-size: 0.78em; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.5px; }
.subkb-item .highlight { background: #fef3c7; padding: 1px 6px; border-radius: 4px; font-weight: 600; }
.qcard { background: #fff; border-radius: 14px; padding: 20px; margin: 10px 0;
         border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.fb-ok { background: #dcfce7; border: 1px solid #86efac; border-radius: 10px; padding: 12px; }
.fb-no { background: #fee2e2; border: 1px solid #fca5a5; border-radius: 10px; padding: 12px; }
.upload-box {
    border: 2px dashed #cbd5e1; border-radius: 16px; padding: 36px;
    text-align: center; background: #f8fafc; transition: all 0.2s;
}
.tag { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.78em;
       font-weight: 600; margin: 2px; }
.stButton > button { border-radius: 10px !important; font-weight: 600 !important; transition: all 0.15s !important; }
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# ===== Init =====
def init():
    for k, v in {
        "subject": None, "page": "home", "view": "knowledge",
        "points": 0, "streak": 0, "max_streak": 0,
        "total_correct": 0, "total_wrong": 0,
        "expanded_kb": set(),
        "practice_chapter": None, "practice_questions": [],
        "practice_idx": 0, "practice_answers": {}, "practice_submitted": set(),
        "practice_feedback": {},
        "exam_started": False, "exam_submitted": False,
        "exam_start_time": None, "exam_end_time": None,
        "exam_questions": [], "exam_answers": {}, "exam_submitted_set": set(), "exam_idx": 0,
        "kb_proficiency": defaultdict(lambda: defaultdict(lambda: {"c":0,"t":0})),
    }.items():
        if k not in st.session_state: st.session_state[k] = v

init()

# ===== Helpers =====
def cfg():
    s = st.session_state.subject
    if s and s in SUBJECTS: return SUBJECTS[s]
    return {"primary":"#64748b","secondary":"#94a3b8","bg":"#f8fafc","accent":"#6366f1",
            "gradient":"linear-gradient(135deg,#64748b,#94a3b8)","icon":"🎓","emoji":"📚"}

def add_pts(n): st.session_state.points += n

def kb_pct(s, k):
    d = st.session_state.kb_proficiency[s][k]; return d["c"]/max(1,d["t"])

def kb_level(p):
    if p>=0.8: return "mastered","熟练掌握","#16a34a"
    if p>=0.5: return "ok","一般掌握","#d97706"
    return "weak","不太掌握","#dc2626"

def upd_kb(chapter, ok):
    s = st.session_state.subject
    st.session_state.kb_proficiency[s][chapter]["t"] += 1
    if ok: st.session_state.kb_proficiency[s][chapter]["c"] += 1

def sub_qs(s): return ALL_QUESTIONS.get(s, [])

def render_subkb(text):
    parts = text.split("|"); out = []
    for p in parts:
        p = p.strip()
        if not p: continue
        if p.startswith("【"):
            end = p.find("】")
            if end>0:
                label = p[1:end]; rest = p[end+1:]
                out.append(f'<span class="label-c">{label}</span> <span>{rest}</span>')
            else: out.append(p)
        else: out.append(f'<span class="highlight">{p}</span>')
    return "<br>".join(out)

def start_practice(chapter_name):
    """初始化练习题"""
    s = st.session_state.subject
    qs = [q for q in sub_qs(s) if q["chapter"] == chapter_name]
    if not qs:
        # 如果没有精确匹配，尝试模糊匹配
        qs = [q for q in sub_qs(s) if chapter_name in q["chapter"] or q["chapter"] in chapter_name]
    random.shuffle(qs)
    st.session_state.practice_chapter = chapter_name
    st.session_state.practice_questions = qs
    st.session_state.practice_idx = 0
    st.session_state.practice_answers = {}
    st.session_state.practice_submitted = set()
    st.session_state.practice_feedback = {}

# ===== Sidebar =====
with st.sidebar:
    c = cfg()
    st.markdown("## 🎓 会考AI学习管家")
    st.markdown(f"""
    <div style="background:{c['gradient']};border-radius:14px;padding:16px;color:white;text-align:center;box-shadow:0 2px 12px rgba(0,0,0,0.1);margin-bottom:10px;">
        <div style="font-size:0.8em;opacity:0.9;">🏆 学习积分</div>
        <div style="font-size:2.2em;font-weight:900;">{st.session_state.points}</div>
        <div style="font-size:0.78em;opacity:0.85;">✅{st.session_state.total_correct} ❌{st.session_state.total_wrong} 🔥{st.session_state.max_streak}连击</div>
    </div>""", unsafe_allow_html=True)
    st.divider()

    if st.session_state.subject:
        st.markdown(f"### {c['icon']} {st.session_state.subject}")
        if st.button("🏠 返回首页", use_container_width=True):
            st.session_state.page = "home"; st.session_state.subject = None; st.rerun()
    else:
        st.info("选择科目开始→")

    st.divider()
    st.markdown("### 📤 上传资料")
    st.caption("PDF / Word / TXT")
    uf = st.file_uploader("拖拽或点击上传", type=["pdf","docx","doc","txt"],
                          accept_multiple_files=True, label_visibility="collapsed", key="sup")
    if uf:
        for f in uf: st.success(f"✅ {f.name}"); add_pts(5)
    st.divider()
    ans = st.session_state.total_correct + st.session_state.total_wrong
    st.caption(f"📊 {ans}题 | {st.session_state.total_correct/max(1,ans)*100:.0f}%")

# ===== Home =====
if st.session_state.page == "home":
    st.markdown('<h1 style="text-align:center;font-weight:900;margin:20px 0 8px;">🎓 北京高中学业水平合格性考试</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;font-size:1.1em;color:#64748b;margin-bottom:30px;">四科可选 · 每科独立知识图谱 · 积分激励</p>', unsafe_allow_html=True)
    cols = st.columns(4)
    for i, (subj, cfg_) in enumerate(SUBJECTS.items()):
        with cols[i]:
            m = sum(1 for k in cfg_["kb"] if kb_pct(subj, k) >= 0.8)
            tk = len(cfg_["kb"]); tq = len(sub_qs(subj))
            card = f"""<div style="background:{cfg_['gradient']};border-radius:18px;padding:26px 16px;text-align:center;color:white;box-shadow:0 6px 20px rgba(0,0,0,0.1);min-height:320px;display:flex;flex-direction:column;justify-content:space-between;">
            <div><div style="font-size:3em;">{cfg_['icon']}</div><h2 style="font-weight:900;margin:10px 0;font-size:1.6em;color:white;">{subj}</h2><p style="opacity:0.85;font-size:0.9em;color:white;">{cfg_['emoji']} 北京合格考</p></div>
            <div style="background:rgba(255,255,255,0.22);border-radius:12px;padding:10px;"><div style="font-size:0.8em;color:white;">知识掌握</div><div style="font-size:1.6em;font-weight:900;color:white;">{m}/{tk}</div><div style="font-size:0.7em;opacity:0.8;color:white;">题库{tq}题</div></div></div>"""
            st.markdown(card, unsafe_allow_html=True)
            if st.button(f"🚀 {subj}", key=f"go_{subj}", use_container_width=True, type="primary"):
                st.session_state.page = "subject"; st.session_state.subject = subj
                st.session_state.view = "knowledge"; add_pts(5); st.rerun()

# ===== Subject =====
elif st.session_state.page == "subject" and st.session_state.subject:
    s = st.session_state.subject; c = cfg()
    st.markdown(f'<h1 style="font-weight:900;color:{c["primary"]};">{c["icon"]} {s} — 北京合格考</h1>', unsafe_allow_html=True)

    # 用 segmented radio 代替 tabs —— 支持代码切换！
    views = {"🧠 知识图谱": "knowledge", "📝 练习": "practice",
             "⏱️ 模拟考": "exam", "📋 考纲": "syllabus", "📤 上传": "upload"}
    cur_label = [k for k,v in views.items() if v == st.session_state.view][0]
    choice = st.radio("导航", list(views.keys()), horizontal=True,
                      index=list(views.keys()).index(cur_label),
                      key="nav_radio", label_visibility="collapsed")
    st.session_state.view = views[choice]

    st.divider()

    # ---- 知识图谱 ----
    if st.session_state.view == "knowledge":
        st.markdown(f'<h3 style="color:{c["primary"]};">🧠 知识图谱 — 点击展开详细考点</h3>', unsafe_allow_html=True)
        st.caption("🟢熟练 🟡一般 🔴薄弱 | 展开后可点「去练习」做对应题目")

        for kb_name, kb_info in SUBJECTS[s]["kb"].items():
            pct = kb_pct(s, kb_name); lvl, label, lc = kb_level(pct); key = f"{s}_{kb_name}"
            arrow = "▼" if key in st.session_state.expanded_kb else "▶"
            btn = f"{arrow} {kb_info['icon']} {kb_name}  —  {label} ({pct*100:.0f}%)"

            if st.button(btn, key=f"kb_{key}", use_container_width=True,
                         type="primary" if key in st.session_state.expanded_kb else "secondary"):
                if key in st.session_state.expanded_kb: st.session_state.expanded_kb.discard(key)
                else: st.session_state.expanded_kb.add(key)
                st.rerun()

            if key in st.session_state.expanded_kb:
                st.caption(f"📖 {kb_info.get('desc','')}  |  含 {len(kb_info['subs'])} 个子知识点")
                for sk_name, sk_text in kb_info["subs"].items():
                    sp = pct + random.uniform(-0.06, 0.06); sp = max(0, min(1, sp))
                    sl, slab, sc = kb_level(sp)
                    html = render_subkb(sk_text)
                    st.markdown(f"""
                    <div class="subkb-item" style="border-left:3px solid {sc};">
                        <div style="font-weight:700;margin-bottom:6px;color:{sc};">📌 {sk_name} <span style="font-size:0.8em;">— {slab}</span></div>
                        <div style="line-height:1.7;">{html}</div>
                    </div>""", unsafe_allow_html=True)

                col_a, col_b = st.columns([1, 1])
                with col_a:
                    if st.button(f"📝 去练习「{kb_name}」", key=f"kp_{key}", use_container_width=True, type="primary"):
                        start_practice(kb_name)
                        st.session_state.view = "practice"
                        st.rerun()

    # ---- 练习 ----
    elif st.session_state.view == "practice":
        st.markdown(f'<h3 style="color:{c["primary"]};">📝 练习模式 — {st.session_state.practice_chapter or "选择章节"}</h3>', unsafe_allow_html=True)

        if not st.session_state.practice_questions:
            # 显示所有可练习的章节
            chaps = list(dict.fromkeys([q["chapter"] for q in sub_qs(s)]))
            st.markdown("#### 选择章节开始练习")
            st.caption("也可从「知识图谱」展开知识点后点「去练习」精准进入")

            cols = st.columns(3)
            for i, ch in enumerate(chaps):
                p = kb_pct(s, ch); _, lb, _ = kb_level(p)
                with cols[i % 3]:
                    q_count = len([q for q in sub_qs(s) if q["chapter"] == ch])
                    if st.button(f"{ch}  ({p*100:.0f}%)  [{q_count}题]",
                                 key=f"pch_{i}", use_container_width=True):
                        start_practice(ch)
                        st.rerun()

        # 做题
        qs = st.session_state.practice_questions; idx = st.session_state.practice_idx
        if qs and idx < len(qs):
            q = qs[idx]; qid = q["id"]; sub = qid in st.session_state.practice_submitted
            prev = st.session_state.practice_answers.get(qid, "")

            # 进度 + 返回按钮
            top_col1, top_col2 = st.columns([4, 1])
            with top_col1:
                st.progress(idx/len(qs), text=f"第 {idx+1}/{len(qs)} 题")
            with top_col2:
                if st.button("🔙 换章节", key=f"back_chap", use_container_width=True):
                    st.session_state.practice_questions = []
                    st.rerun()

            st.markdown(f'<div class="qcard"><strong>{idx+1}.</strong> {q["q"]}<br><span class="tag" style="background:{c["secondary"]};color:#1e293b;">{q["chapter"]}</span></div>', unsafe_allow_html=True)

            ch = st.radio("选择答案：", q["opts"],
                          index=q["opts"].index(prev) if prev in q["opts"] else None,
                          key=f"pq_{qid}", disabled=sub)

            ca, cb = st.columns(2)
            with ca:
                if not sub and st.button("✅ 提交", key=f"ps_{qid}", use_container_width=True):
                    if ch:
                        st.session_state.practice_answers[qid] = ch
                        st.session_state.practice_submitted.add(qid)
                        ok = (ch[0] == q["ans"])
                        upd_kb(q["chapter"], ok)
                        if ok:
                            st.session_state.total_correct += 1
                            st.session_state.streak += 1
                            st.session_state.max_streak = max(st.session_state.max_streak, st.session_state.streak)
                            add_pts(10)
                            if st.session_state.streak == 3: add_pts(15)
                            elif st.session_state.streak == 5: add_pts(30)
                        else:
                            st.session_state.total_wrong += 1
                            st.session_state.streak = 0
                            add_pts(2)
                        st.rerun()
                    else:
                        st.warning("请先选择一个答案")
            with cb:
                if sub and idx+1 < len(qs):
                    if st.button("➡️ 下一题", key=f"pn_{qid}", use_container_width=True):
                        st.session_state.practice_idx += 1
                        st.rerun()

            if sub:
                ua = st.session_state.practice_answers.get(qid, "")[0] if st.session_state.practice_answers.get(qid) else ""
                if ua == q["ans"]:
                    st.markdown(f'<div class="fb-ok">🎉 <strong>正确！</strong> +10分</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="fb-no">😅 <strong>错误</strong>（正确答案：{q["ans"]}）+2分</div>', unsafe_allow_html=True)
                st.info(f"💡 解析：{q['exp']}")

        elif qs and idx >= len(qs):
            n = sum(1 for q in qs if st.session_state.practice_answers.get(q["id"],"") and st.session_state.practice_answers[q["id"]][0] == q["ans"])
            st.balloons()
            pct_done = n/len(qs)*100
            st.success(f"🎉 练习完成！正确 {n}/{len(qs)}（{pct_done:.0f}%）")
            ch = st.session_state.practice_chapter; cp = kb_pct(s, ch)
            if cp >= 0.9 and f"m_{s}_{ch}" not in st.session_state:
                st.session_state[f"m_{s}_{ch}"] = True; add_pts(100)
                st.success(f"🏆 章节「{ch}」精通！+100分")

            # 根据结果推荐下一步
            if pct_done < 60:
                st.warning(f"💡 「{ch}」掌握度偏低，建议回到知识图谱重新学习考点后再练。")
            elif pct_done < 80:
                st.info(f"💡 「{ch}」还需加强，再做一组巩固。")
            else:
                st.success(f"💡 「{ch}」掌握良好！可以挑战其他薄弱章节。")

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🔄 再练一组", use_container_width=True):
                    start_practice(ch); st.rerun()
            with c2:
                if st.button("🧠 回知识图谱", use_container_width=True):
                    st.session_state.practice_questions = []; st.session_state.view = "knowledge"; st.rerun()
            with c3:
                if st.button("📋 换个章节", use_container_width=True):
                    st.session_state.practice_questions = []; st.rerun()

    # ---- 模拟考 ----
    elif st.session_state.view == "exam":
        st.markdown(f'<h3 style="color:{c["primary"]};">⏱️ 模拟考试</h3>', unsafe_allow_html=True)
        aq = sub_qs(s); nq = min(20, len(aq))
        if not st.session_state.exam_started and not st.session_state.exam_submitted:
            st.markdown(f"""<div class="card"><h4>📋 考试说明</h4><p>⏱️ 60分钟 | 📝 {nq}题 | 💯 100分 | ✅ 60分及格</p><p style="color:#94a3b8;">⚠️ 时间到自动交卷 · 提交后不可修改</p></div>""", unsafe_allow_html=True)
            if st.button("🚀 开始考试", type="primary", use_container_width=True):
                eq = random.sample(aq, min(nq, len(aq))); random.shuffle(eq)
                st.session_state.exam_questions = eq; st.session_state.exam_answers = {}
                st.session_state.exam_submitted_set = set(); st.session_state.exam_started = True
                st.session_state.exam_submitted = False; st.session_state.exam_start_time = time.time()
                st.session_state.exam_idx = 0; st.rerun()
        elif st.session_state.exam_started and not st.session_state.exam_submitted:
            eqs = st.session_state.exam_questions; tot = len(eqs)
            el = time.time() - st.session_state.exam_start_time; rem = max(0, 3600 - el)
            m, sec = int(rem//60), int(rem%60)
            tc2 = "#dc2626" if rem < 600 else c["primary"]
            tcl, prl = st.columns([1, 3])
            with tcl:
                st.markdown(f'<div style="background:{tc2};color:white;padding:12px;border-radius:12px;text-align:center;font-size:1.6em;font-weight:900;">⏰ {m:02d}:{sec:02d}</div>', unsafe_allow_html=True)
            with prl:
                st.progress(len(st.session_state.exam_submitted_set)/tot, text=f"{len(st.session_state.exam_submitted_set)}/{tot}")
            if rem <= 0: st.session_state.exam_submitted = True; st.session_state.exam_end_time = time.time(); st.rerun()
            ei = st.session_state.exam_idx
            if ei < tot:
                q = eqs[ei]; qid = q["id"]; sub = qid in st.session_state.exam_submitted_set
                prev = st.session_state.exam_answers.get(qid, "")
                st.markdown(f'<div class="qcard"><strong>{ei+1}.</strong> {q["q"]}<br><span class="tag" style="background:{c["secondary"]};color:#1e293b;">{q["chapter"]}</span></div>', unsafe_allow_html=True)
                ch = st.radio("选择：", q["opts"], index=q["opts"].index(prev) if prev in q["opts"] else None, key=f"eq_{qid}", disabled=sub)
                ca, cb = st.columns(2)
                with ca:
                    if not sub and st.button("提交", key=f"es_{qid}"):
                        if ch: st.session_state.exam_answers[qid] = ch; st.session_state.exam_submitted_set.add(qid); st.rerun()
                with cb:
                    if st.button("跳过", key=f"esk_{ei}"): st.session_state.exam_idx = min(ei+1, tot-1); st.rerun()
            st.divider()
            if st.button("📝 交卷", type="primary", use_container_width=True):
                st.session_state.exam_submitted = True; st.session_state.exam_end_time = time.time(); st.rerun()
        if st.session_state.exam_submitted:
            eqs = st.session_state.exam_questions; tot = len(eqs); per = 100//tot; corr = 0; results = []
            for q in eqs:
                a = st.session_state.exam_answers.get(q["id"], ""); l = a[0] if a else ""; ok = (l == q["ans"])
                if ok: corr += 1
                results.append({"q": q, "a": l or "未答", "ok": ok}); upd_kb(q["chapter"], ok)
                if ok: st.session_state.total_correct += 1; st.session_state.streak += 1
                else: st.session_state.total_wrong += 1; st.session_state.streak = 0
            sc = corr * per; passed = sc >= 60
            if passed: st.balloons(); add_pts(50)
            add_pts(corr * 20 // per if per else 0)
            scc = "#16a34a" if passed else "#dc2626"
            st.markdown(f'<div style="font-size:3em;font-weight:900;text-align:center;color:{scc};">{sc} 分</div>', unsafe_allow_html=True)
            st.markdown(f"### {'🎉 通过！' if passed else '💪 加油！'}")
            st.markdown(f"✅ {corr}/{tot} | ⏱️ {(st.session_state.exam_end_time-st.session_state.exam_start_time)/60:.1f}分")
            wrong = [r for r in results if not r["ok"]]
            if wrong:
                st.markdown("#### ❌ 错题")
                for r in wrong:
                    q = r["q"]
                    with st.expander(f"{q['chapter']} — {q['q'][:40]}..."):
                        st.write(f"你的答案: {r['a']} | 正确答案: {q['ans']}")
                        st.info(q['exp'])
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 重新考试", use_container_width=True):
                    st.session_state.exam_started = False; st.session_state.exam_submitted = False; st.rerun()
            with c2:
                if st.button("🧠 回知识图谱", use_container_width=True):
                    st.session_state.exam_started = False; st.session_state.exam_submitted = False
                    st.session_state.view = "knowledge"; st.rerun()

    # ---- 考纲 ----
    elif st.session_state.view == "syllabus":
        st.markdown(f'<h3 style="color:{c["primary"]};">📋 考纲解析</h3>', unsafe_allow_html=True)
        st.markdown(f"""<div class="card">{EXAM_SYLLABUS.get(s, '')}</div>""", unsafe_allow_html=True)
        st.divider(); st.markdown("### 📚 知识点清单")
        for kn, ki in SUBJECTS[s]["kb"].items():
            st.markdown(f"**{ki['icon']} {kn}** — {ki.get('desc','')}")
            tags = " ".join([f'<span class="tag" style="background:{c["bg"]};color:{c["primary"]};border:1px solid {c["secondary"]};">{sn}</span>' for sn in ki["subs"]])
            st.markdown(tags, unsafe_allow_html=True)

    # ---- 上传 ----
    elif st.session_state.view == "upload":
        st.markdown(f'<h3 style="color:{c["primary"]};">📤 上传学习资料</h3>', unsafe_allow_html=True)
        st.markdown(f"""<div class="upload-box"><div style="font-size:3em;">📤</div><h4>支持 PDF / Word / TXT</h4><p style="color:#94a3b8;">上传后自动解析内容</p></div>""", unsafe_allow_html=True)
        um = st.file_uploader("选择文件", type=["pdf","docx","doc","txt"], accept_multiple_files=True, label_visibility="collapsed", key="mup")
        if um:
            for f in um:
                st.success(f"✅ {f.name} ({f.size/1024:.0f}KB)"); add_pts(5)
                try:
                    if f.name.endswith('.pdf'):
                        import pymupdf; doc = pymupdf.open(stream=f.read(), filetype="pdf")
                        text = "".join([p.get_text() for p in doc]); st.text_area("预览", text[:500], height=120)
                    elif f.name.endswith(('.docx','.doc')):
                        import docx as pydocx; doc = pydocx.Document(io.BytesIO(f.read()))
                        text = "\\n".join([p.text for p in doc.paragraphs]); st.text_area("预览", text[:500], height=120)
                    elif f.name.endswith('.txt'):
                        text = f.read().decode('utf-8', errors='ignore'); st.text_area("预览", text[:500], height=120)
                except Exception as e: st.warning(str(e))

st.divider(); st.caption("🎓 北京会考AI学习管家 v3.1 | 强制浅色模式 | 数据参考：北京教育考试院")
