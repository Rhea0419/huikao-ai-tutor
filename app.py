
import streamlit as st
import random, time, io
from collections import defaultdict
from subjects import SUBJECTS, EXAM_SYLLABUS, POINTS_RULES
from question_bank import ALL_QUESTIONS

st.set_page_config(page_title="会考AI学习管家", page_icon="🎓", layout="wide",
                   initial_sidebar_state="expanded")

# ═══════════════════════════════════════
# shadcn/ui inspired design system
# ═══════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #fafafa;
    --card: #ffffff;
    --border: #e5e7eb;
    --text: #18181b;
    --muted: #71717a;
    --radius: 12px;
    --radius-sm: 8px;
    --shadow: 0 1px 2px rgba(0,0,0,.04), 0 1px 3px rgba(0,0,0,.06);
    --shadow-md: 0 4px 6px rgba(0,0,0,.04), 0 2px 4px rgba(0,0,0,.04);
}

* { font-family: 'Inter', system-ui, sans-serif; }
.stApp { background: var(--bg); }
section[data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--border); }
h1,h2,h3,h4,h5,h6 { color: var(--text); font-weight: 700; letter-spacing: -0.02em; }
p,span,div,label,li { color: var(--text); }

/* ── Cards ── */
.card {
    background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 24px; box-shadow: var(--shadow);
}
.card-sm { padding: 16px; }

/* ── Buttons ── */
.stButton > button {
    border-radius: var(--radius-sm) !important; font-weight: 500 !important;
    font-size: 0.875rem !important; padding: 8px 16px !important;
    transition: all 0.15s ease !important; letter-spacing: -0.01em !important;
    border: 1px solid var(--border) !important; background: #fff !important; color: var(--text) !important;
}
.stButton > button:hover {
    background: #f4f4f5 !important; border-color: #d4d4d8 !important;
    transform: translateY(-1px); box-shadow: var(--shadow-md);
}
.stButton > button:active { transform: translateY(0); }

/* ── Primary button ── */
.stButton > button[kind="primary"] {
    background: #18181b !important; color: #fff !important; border-color: #18181b !important;
}
.stButton > button[kind="primary"]:hover {
    background: #27272a !important;
}

/* ── Radio (nav bar) ── */
div[role="radiogroup"] { gap: 4px; display: flex; }
div[role="radiogroup"] label {
    border-radius: var(--radius-sm) !important; padding: 8px 16px !important;
    font-weight: 500 !important; font-size: 0.875rem !important;
    transition: all 0.15s ease !important;
}
div[role="radiogroup"] label:hover { background: #f4f4f5 !important; }

/* ── Progress ── */
.stProgress > div > div { background: #18181b !important; border-radius: 4px !important; }
.stProgress > div { background: #e5e7eb !important; border-radius: 4px !important; }

/* ── Question card ── */
.qcard {
    background: var(--card); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 24px; box-shadow: var(--shadow);
}
.qcard:hover { box-shadow: var(--shadow-md); }

/* ── Feedback ── */
.fb-ok { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: var(--radius-sm); padding: 14px 18px; }
.fb-no { background: #fef2f2; border: 1px solid #fecaca; border-radius: var(--radius-sm); padding: 14px 18px; }

/* ── Knowledge sub-items ── */
.subkb {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius-sm); padding: 16px 20px; margin: 8px 0;
    box-shadow: var(--shadow); transition: all 0.15s ease;
}
.subkb:hover { box-shadow: var(--shadow-md); }
.label-c { color: var(--muted); font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; }

/* ── Tags ── */
.tag { display: inline-block; padding: 2px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 500; }

/* ── Upload ── */
.upload-box {
    border: 2px dashed var(--border); border-radius: var(--radius); padding: 40px;
    text-align: center; background: var(--card); transition: all 0.15s ease;
}
.upload-box:hover { border-color: #a1a1aa; background: #fafafa; }

/* ── Subject card (home) ── */
.subject-card {
    border-radius: 16px; padding: 28px 20px; text-align: center; cursor: pointer;
    transition: all 0.2s ease; box-shadow: var(--shadow); border: 1px solid var(--border);
    background: var(--card);
}
.subject-card:hover { transform: translateY(-3px); box-shadow: 0 12px 24px rgba(0,0,0,.08); }

/* ── Timer ── */
.timer { letter-spacing: -0.02em; font-feature-settings: "tnum"; font-variant-numeric: tabular-nums; }

/* ── Animations ── */
@keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.6; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.animate-in { animation: fadeIn 0.3s ease; }
.animate-slide { animation: slideUp 0.3s ease; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# Init
# ═══════════════════════════════════════
def init():
    for k, v in {
        "subject": None, "page": "home", "view": "knowledge",
        "points": 0, "streak": 0, "max_streak": 0,
        "total_correct": 0, "total_wrong": 0,
        "expanded_kb": set(),
        "practice_chapter": None, "practice_questions": [],
        "practice_idx": 0, "practice_answers": {}, "practice_submitted": set(),
        "exam_started": False, "exam_submitted": False,
        "exam_start_time": None, "exam_end_time": None,
        "exam_questions": [], "exam_answers": {}, "exam_submitted_set": set(), "exam_idx": 0,
        "kb_proficiency": defaultdict(lambda: defaultdict(lambda: {"c":0,"t":0})),
    }.items():
        if k not in st.session_state: st.session_state[k] = v

init()

# ═══════════════════════════════════════
# Helpers
# ═══════════════════════════════════════
def cfg():
    s = st.session_state.subject
    if s and s in SUBJECTS: return SUBJECTS[s]
    return {"primary":"#18181b","secondary":"#71717a","bg":"#fafafa","accent":"#3b82f6",
            "icon":"🎓","emoji":"📚","gradient":"#18181b"}

def add_pts(n): st.session_state.points += n

def kb_pct(s,k):
    d=st.session_state.kb_proficiency[s][k]; return d["c"]/max(1,d["t"])

def kb_level(p):
    if p>=0.8: return "mastered","熟练掌握","#16a34a"
    if p>=0.5: return "ok","一般掌握","#d97706"
    return "weak","不太掌握","#dc2626"

def upd_kb(ch,ok):
    s=st.session_state.subject
    st.session_state.kb_proficiency[s][ch]["t"]+=1
    if ok: st.session_state.kb_proficiency[s][ch]["c"]+=1

def sub_qs(s): return ALL_QUESTIONS.get(s,[])

def render_subkb(text):
    parts=text.split("|"); out=[]
    for p in parts:
        p=p.strip()
        if not p: continue
        if p.startswith("【"):
            end=p.find("】")
            if end>0: out.append(f'<span class="label-c">{p[1:end]}</span> <span>{p[end+1:]}</span>')
            else: out.append(p)
        else: out.append(f'<span style="background:#fef3c7;padding:1px 6px;border-radius:4px;font-weight:500;">{p}</span>')
    return "<br>".join(out)

def start_practice(ch_name):
    s=st.session_state.subject
    qs=[q for q in sub_qs(s) if q["chapter"]==ch_name]
    if not qs: qs=[q for q in sub_qs(s) if ch_name in q["chapter"] or q["chapter"] in ch_name]
    random.shuffle(qs)
    st.session_state.practice_chapter=ch_name; st.session_state.practice_questions=qs
    st.session_state.practice_idx=0; st.session_state.practice_answers={}
    st.session_state.practice_submitted=set()

def subject_accent(subj):
    """shadcn-inspired color per subject"""
    m={
        "化学": {"bg":"#f5f3ff","text":"#7c3aed","border":"#ddd6fe","bar":"#a78bfa"},
        "生物": {"bg":"#ecfdf5","text":"#059669","border":"#a7f3d0","bar":"#6ee7b7"},
        "历史": {"bg":"#fef2f2","text":"#dc2626","border":"#fecaca","bar":"#fca5a5"},
        "地理": {"bg":"#f0f9ff","text":"#0284c7","border":"#bae6fd","bar":"#7dd3fc"},
    }
    return m.get(subj,m["化学"])

# ═══════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════
with st.sidebar:
    st.markdown("### 🎓 会考AI学习管家")
    c=cfg(); ac=subject_accent(st.session_state.subject or "化学")

    # Points badge
    st.markdown(f"""
    <div style="background:{c['primary']};border-radius:12px;padding:18px;color:#fff;margin-bottom:12px;box-shadow:var(--shadow);">
        <div style="font-size:0.75rem;opacity:0.8;font-weight:500;text-transform:uppercase;letter-spacing:0.05em;">学习积分</div>
        <div style="font-size:2.2rem;font-weight:800;line-height:1.2;letter-spacing:-0.03em;">{st.session_state.points}</div>
        <div style="font-size:0.75rem;opacity:0.8;margin-top:2px;">
            ✅ {st.session_state.total_correct}  ❌ {st.session_state.total_wrong}  🔥 {st.session_state.max_streak}连击
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.subject:
        st.markdown(f"#### {c['icon']} {st.session_state.subject}")
        if st.button("← 返回首页", use_container_width=True):
            st.session_state.page="home"; st.session_state.subject=None; st.rerun()

    st.divider()
    st.markdown("#### 📤 上传资料")
    uf=st.file_uploader("PDF / Word / TXT",type=["pdf","docx","doc","txt"],
                        accept_multiple_files=True,label_visibility="collapsed")
    if uf:
        for f in uf: st.success(f"✅ {f.name}"); add_pts(5)

    st.divider()
    ans=st.session_state.total_correct+st.session_state.total_wrong
    st.caption(f"📊 共练习 {ans} 题 · 正确率 {st.session_state.total_correct/max(1,ans)*100:.0f}%")

# ═══════════════════════════════════════
# Home
# ═══════════════════════════════════════
if st.session_state.page=="home":
    st.markdown('<h1 style="font-weight:800;letter-spacing:-0.03em;margin:16px 0 4px;">北京高中学业水平合格性考试</h1>',unsafe_allow_html=True)
    st.markdown('<p style="color:var(--muted);font-size:0.95rem;margin-bottom:28px;">四科可选 · 知识图谱 · 积分激励 · 模拟考试</p>',unsafe_allow_html=True)

    cols=st.columns(4)
    for i,(subj,cfg_) in enumerate(SUBJECTS.items()):
        m=sum(1 for k in cfg_["kb"] if kb_pct(subj,k)>=0.8)
        tk=len(cfg_["kb"]); tq=len(sub_qs(subj))
        with cols[i]:
            st.markdown(f"""
            <div class="subject-card animate-in" style="animation-delay:{i*0.05}s;">
                <div style="font-size:2.8rem;margin-bottom:4px;">{cfg_['icon']}</div>
                <h3 style="font-weight:700;margin:8px 0;font-size:1.15rem;letter-spacing:-0.02em;">{subj}</h3>
                <p style="color:var(--muted);font-size:0.8rem;margin:0;">{cfg_['emoji']} 北京合格考</p>
                <div style="margin-top:14px;padding:10px;background:var(--bg);border-radius:8px;">
                    <span style="font-size:0.7rem;color:var(--muted);">知识掌握</span>
                    <div style="font-weight:700;font-size:1.3rem;letter-spacing:-0.02em;">{m}/{tk}</div>
                    <span style="font-size:0.7rem;color:var(--muted);">{tq} 题</span>
                </div>
            </div>
            """,unsafe_allow_html=True)
            if st.button(f"进入{subj}",key=f"go_{subj}",use_container_width=True,type="primary"):
                st.session_state.page="subject"; st.session_state.subject=subj
                st.session_state.view="knowledge"; add_pts(5); st.rerun()

# ═══════════════════════════════════════
# Subject
# ═══════════════════════════════════════
elif st.session_state.page=="subject" and st.session_state.subject:
    s=st.session_state.subject; c=cfg(); ac=subject_accent(s)

    st.markdown(f'<h1 style="font-weight:800;letter-spacing:-0.03em;">{c["icon"]} {s}<span style="color:var(--muted);font-weight:400;font-size:0.85rem;margin-left:8px;">北京合格考</span></h1>',unsafe_allow_html=True)

    # Navigation
    views={"🧠 知识图谱":"knowledge","📝 练习":"practice","⏱️ 模拟考":"exam","📋 考纲":"syllabus","📤 上传":"upload"}
    cur_label=[k for k,v in views.items() if v==st.session_state.view][0]
    choice=st.radio("",list(views.keys()),horizontal=True,index=list(views.keys()).index(cur_label),label_visibility="collapsed")
    st.session_state.view=views[choice]
    st.divider()

    # ═══ Knowledge ═══
    if st.session_state.view=="knowledge":
        st.markdown(f'<h3 style="font-weight:700;letter-spacing:-0.02em;">🧠 知识图谱</h3>',unsafe_allow_html=True)
        st.caption("点击展开详细考点 · 展开后可做对应练习题")

        for kb_name,kb_info in SUBJECTS[s]["kb"].items():
            pct=kb_pct(s,kb_name); lvl,label,lc=kb_level(pct); key=f"{s}_{kb_name}"
            arrow="▾" if key in st.session_state.expanded_kb else "▸"

            # Mastery indicator dot
            bar_w=int(pct*100)
            btn=f"{arrow}  {kb_info['icon']}  {kb_name}"
            sub_text=f"{label} · {pct*100:.0f}%"

            col1,col2=st.columns([5,1])
            with col1:
                btn_type="primary" if key in st.session_state.expanded_kb else "secondary"
                if st.button(btn,key=f"kb_{key}",use_container_width=True,type=btn_type):
                    if key in st.session_state.expanded_kb: st.session_state.expanded_kb.discard(key)
                    else: st.session_state.expanded_kb.add(key)
                    st.rerun()

            # Thin progress bar under the button
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:8px;margin:-6px 0 4px;padding-left:12px;">
                <div style="flex:1;height:3px;background:#e5e7eb;border-radius:2px;">
                    <div style="width:{bar_w}%;height:100%;background:{lc};border-radius:2px;transition:width 0.3s;"></div>
                </div>
                <span style="font-size:0.7rem;color:{lc};font-weight:600;white-space:nowrap;">{sub_text}</span>
            </div>
            """,unsafe_allow_html=True)

            if key in st.session_state.expanded_kb:
                st.markdown(f'<p style="color:var(--muted);font-size:0.8rem;margin:4px 0 8px 20px;">📖 {kb_info.get("desc","")} · {len(kb_info["subs"])} 个子知识点</p>',unsafe_allow_html=True)
                for sk_name,sk_text in kb_info["subs"].items():
                    sp=pct+random.uniform(-0.06,0.06); sp=max(0,min(1,sp))
                    sl,slab,sc=kb_level(sp)
                    html=render_subkb(sk_text)
                    st.markdown(f"""
                    <div class="subkb animate-slide" style="border-left:3px solid {sc};">
                        <div style="font-weight:600;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
                            <span>📌 {sk_name}</span>
                            <span style="font-size:0.75rem;color:{sc};font-weight:600;">{slab}</span>
                        </div>
                        <div style="line-height:1.75;font-size:0.875rem;">{html}</div>
                    </div>
                    """,unsafe_allow_html=True)

                if st.button(f"→ 练习「{kb_name}」",key=f"kp_{key}",use_container_width=True,type="primary"):
                    start_practice(kb_name); st.session_state.view="practice"; st.rerun()

    # ═══ Practice ═══
    elif st.session_state.view=="practice":
        ch_title=st.session_state.practice_chapter or "选择章节"
        st.markdown(f'<h3 style="font-weight:700;letter-spacing:-0.02em;">📝 练习 · {ch_title}</h3>',unsafe_allow_html=True)

        if not st.session_state.practice_questions:
            chaps=list(dict.fromkeys([q["chapter"] for q in sub_qs(s)]))
            cols=st.columns(3)
            for i,ch in enumerate(chaps):
                p=kb_pct(s,ch); _,lb,_=kb_level(p); qc=len([q for q in sub_qs(s) if q["chapter"]==ch])
                with cols[i%3]:
                    st.markdown(f"""
                    <div class="card card-sm" style="text-align:center;margin-bottom:8px;">
                        <div style="font-size:0.7rem;color:var(--muted);text-transform:uppercase;letter-spacing:0.05em;">{lb}</div>
                        <div style="font-weight:600;font-size:0.95rem;margin:4px 0;">{ch}</div>
                        <div style="font-size:0.75rem;color:var(--muted);">{qc} 题 · {p*100:.0f}%</div>
                    </div>
                    """,unsafe_allow_html=True)
                    if st.button(f"开始练习",key=f"pch_{i}",use_container_width=True):
                        start_practice(ch); st.rerun()

        qs=st.session_state.practice_questions; idx=st.session_state.practice_idx
        if qs and idx<len(qs):
            q=qs[idx]; qid=q["id"]; sub=qid in st.session_state.practice_submitted
            prev=st.session_state.practice_answers.get(qid,"")

            # Top bar
            t1,t2=st.columns([4,1])
            with t1: st.progress(idx/len(qs),text=f"第 {idx+1} / {len(qs)} 题")
            with t2:
                if st.button("← 换章节",key="back_chap",use_container_width=True):
                    st.session_state.practice_questions=[]; st.rerun()

            # Question
            st.markdown(f"""
            <div class="qcard">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                    <span style="font-weight:700;font-size:1.05rem;">{idx+1}. {q["q"]}</span>
                    <span class="tag" style="background:{ac["bg"]};color:{ac["text"]};">{q["chapter"]}</span>
                </div>
            </div>
            """,unsafe_allow_html=True)

            ch=st.radio("选择答案",q["opts"],index=q["opts"].index(prev) if prev in q["opts"] else None,key=f"pq_{qid}",disabled=sub)

            c1,c2=st.columns(2)
            with c1:
                if not sub and st.button("提交答案",key=f"ps_{qid}",use_container_width=True,type="primary"):
                    if ch:
                        st.session_state.practice_answers[qid]=ch; st.session_state.practice_submitted.add(qid)
                        ok=(ch[0]==q["ans"]); upd_kb(q["chapter"],ok)
                        if ok: st.session_state.total_correct+=1; st.session_state.streak+=1; st.session_state.max_streak=max(st.session_state.max_streak,st.session_state.streak); add_pts(10)
                        else: st.session_state.total_wrong+=1; st.session_state.streak=0; add_pts(2)
                        st.rerun()
                    else: st.warning("请选择答案")
            with c2:
                if sub and idx+1<len(qs) and st.button("下一题 →",key=f"pn_{qid}",use_container_width=True):
                    st.session_state.practice_idx+=1; st.rerun()

            if sub:
                ua=st.session_state.practice_answers.get(qid,"")[0] if st.session_state.practice_answers.get(qid) else ""
                if ua==q["ans"]:
                    st.markdown(f'<div class="fb-ok animate-in">✓ <strong>正确</strong> +10分</div>',unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="fb-no animate-in">✗ <strong>错误</strong> · 正确答案 {q["ans"]} · +2分</div>',unsafe_allow_html=True)
                st.info(f"💡 {q['exp']}")

        elif qs and idx>=len(qs):
            n=sum(1 for q in qs if st.session_state.practice_answers.get(q["id"],"") and st.session_state.practice_answers[q["id"]][0]==q["ans"])
            pct_done=n/len(qs)*100; ch=st.session_state.practice_chapter; cp=kb_pct(s,ch)
            st.balloons()
            st.markdown(f"""
            <div class="card animate-in" style="text-align:center;">
                <div style="font-size:3rem;font-weight:800;letter-spacing:-0.03em;">{n}<span style="font-size:1.5rem;color:var(--muted);">/{len(qs)}</span></div>
                <div style="font-size:1.1rem;font-weight:600;color:{"#16a34a" if pct_done>=60 else "#dc2626"};margin:8px 0;">
                    {"🎉 完成！" if pct_done>=60 else "💪 继续努力"}
                </div>
                <p style="color:var(--muted);">正确率 {pct_done:.0f}%</p>
            </div>
            """,unsafe_allow_html=True)

            if cp>=0.9 and f"m_{s}_{ch}" not in st.session_state:
                st.session_state[f"m_{s}_{ch}"]=True; add_pts(100)
                st.success(f"🏆 「{ch}」章节精通 +100分！")

            c1,c2,c3=st.columns(3)
            with c1:
                if st.button("再来一组",use_container_width=True): start_practice(ch); st.rerun()
            with c2:
                if st.button("回知识图谱",use_container_width=True):
                    st.session_state.practice_questions=[]; st.session_state.view="knowledge"; st.rerun()
            with c3:
                if st.button("换章节",use_container_width=True): st.session_state.practice_questions=[]; st.rerun()

    # ═══ Exam ═══
    elif st.session_state.view=="exam":
        st.markdown('<h3 style="font-weight:700;letter-spacing:-0.02em;">⏱️ 模拟考试</h3>',unsafe_allow_html=True)
        aq=sub_qs(s); nq=min(20,len(aq))
        if not st.session_state.exam_started and not st.session_state.exam_submitted:
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:2rem;margin-bottom:8px;">⏱️</div>
                <h4 style="font-weight:600;">模拟考试说明</h4>
                <p style="color:var(--muted);">60分钟 · {nq}道选择题 · 满分100 · 及格60</p>
                <p style="color:var(--muted);font-size:0.8rem;">时间到自动交卷 · 提交后不可修改</p>
            </div>
            """,unsafe_allow_html=True)
            if st.button("开始考试",type="primary",use_container_width=True):
                eq=random.sample(aq,min(nq,len(aq))); random.shuffle(eq)
                st.session_state.exam_questions=eq; st.session_state.exam_answers={}
                st.session_state.exam_submitted_set=set(); st.session_state.exam_started=True
                st.session_state.exam_submitted=False; st.session_state.exam_start_time=time.time()
                st.session_state.exam_idx=0; st.rerun()

        elif st.session_state.exam_started and not st.session_state.exam_submitted:
            eqs=st.session_state.exam_questions; tot=len(eqs)
            el=time.time()-st.session_state.exam_start_time; rem=max(0,3600-el)
            m,sec=int(rem//60),int(rem%60)
            tc="#dc2626" if rem<600 else "#18181b"
            t1,t2=st.columns([1,4])
            with t1:
                st.markdown(f'<div style="background:{tc};color:#fff;padding:16px;border-radius:10px;text-align:center;font-size:1.5rem;font-weight:700;letter-spacing:-0.02em;" class="timer">{m:02d}:{sec:02d}</div>',unsafe_allow_html=True)
            with t2:
                st.progress(len(st.session_state.exam_submitted_set)/tot,text=f"已完成 {len(st.session_state.exam_submitted_set)}/{tot} 题")
            if rem<=0: st.session_state.exam_submitted=True; st.session_state.exam_end_time=time.time(); st.rerun()

            ei=st.session_state.exam_idx
            if ei<tot:
                q=eqs[ei]; qid=q["id"]; sub=qid in st.session_state.exam_submitted_set
                prev=st.session_state.exam_answers.get(qid,"")
                st.markdown(f'<div class="qcard"><strong>{ei+1}.</strong> {q["q"]}<br><span class="tag" style="background:{ac["bg"]};color:{ac["text"]};margin-top:8px;">{q["chapter"]}</span></div>',unsafe_allow_html=True)
                ch=st.radio("选择",q["opts"],index=q["opts"].index(prev) if prev in q["opts"] else None,key=f"eq_{qid}",disabled=sub)
                c1,c2=st.columns(2)
                with c1:
                    if not sub and st.button("提交",key=f"es_{qid}"):
                        if ch: st.session_state.exam_answers[qid]=ch; st.session_state.exam_submitted_set.add(qid); st.rerun()
                with c2:
                    if st.button("跳过",key=f"esk_{ei}"): st.session_state.exam_idx=min(ei+1,tot-1); st.rerun()
            st.divider()
            if st.button("交卷",type="primary",use_container_width=True):
                st.session_state.exam_submitted=True; st.session_state.exam_end_time=time.time(); st.rerun()

        if st.session_state.exam_submitted:
            eqs=st.session_state.exam_questions; tot=len(eqs); per=100//tot; corr=0; results=[]
            for q in eqs:
                a=st.session_state.exam_answers.get(q["id"],""); l=a[0] if a else ""; ok=(l==q["ans"])
                if ok: corr+=1
                results.append({"q":q,"a":l or "未答","ok":ok}); upd_kb(q["chapter"],ok)
                if ok: st.session_state.total_correct+=1; st.session_state.streak+=1
                else: st.session_state.total_wrong+=1; st.session_state.streak=0
            sc=corr*per; passed=sc>=60
            if passed: st.balloons(); add_pts(50)
            add_pts(corr*20//per if per else 0)
            scc="#16a34a" if passed else "#dc2626"
            st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div style="font-size:3.5rem;font-weight:800;letter-spacing:-0.03em;color:{scc};">{sc}<span style="font-size:1.5rem;">/100</span></div>
                <div style="font-size:1.1rem;font-weight:600;margin:8px 0;">{'🎉 通过！' if passed else '💪 继续加油'}</div>
                <p style="color:var(--muted);">✅ {corr}/{tot} · ⏱️ {(st.session_state.exam_end_time-st.session_state.exam_start_time)/60:.1f}分</p>
            </div>
            """,unsafe_allow_html=True)

            wrong=[r for r in results if not r["ok"]]
            if wrong:
                for r in wrong:
                    q=r["q"]
                    with st.expander(f"{q['chapter']} · {q['q'][:40]}..."):
                        st.write(f"你的答案: {r['a']}   正确答案: {q['ans']}")
                        st.info(q['exp'])
            c1,c2=st.columns(2)
            with c1:
                if st.button("重新考试",use_container_width=True): st.session_state.exam_started=False; st.session_state.exam_submitted=False; st.rerun()
            with c2:
                if st.button("回知识图谱",use_container_width=True): st.session_state.exam_started=False; st.session_state.exam_submitted=False; st.session_state.view="knowledge"; st.rerun()

    # ═══ Syllabus ═══
    elif st.session_state.view=="syllabus":
        st.markdown(f'<h3 style="font-weight:700;">📋 考纲解析</h3>',unsafe_allow_html=True)
        st.markdown(f'<div class="card">{EXAM_SYLLABUS.get(s,"")}</div>',unsafe_allow_html=True)
        st.divider()
        for kn,ki in SUBJECTS[s]["kb"].items():
            st.markdown(f"**{ki['icon']} {kn}** · {ki.get('desc','')}")
            tags=" ".join([f'<span class="tag" style="background:{ac["bg"]};color:{ac["text"]};">{sn}</span>' for sn in ki["subs"]])
            st.markdown(tags,unsafe_allow_html=True)

    # ═══ Upload ═══
    elif st.session_state.view=="upload":
        st.markdown(f'<h3 style="font-weight:700;">📤 上传资料</h3>',unsafe_allow_html=True)
        st.markdown('<div class="upload-box"><div style="font-size:2.5rem;">📤</div><p style="font-weight:500;">拖拽或点击上传</p><p style="color:var(--muted);font-size:0.85rem;">PDF · Word · TXT</p></div>',unsafe_allow_html=True)
        um=st.file_uploader("选择文件",type=["pdf","docx","doc","txt"],accept_multiple_files=True,label_visibility="collapsed")
        if um:
            for f in um:
                st.success(f"✅ {f.name} ({f.size/1024:.0f}KB)"); add_pts(5)
                try:
                    if f.name.endswith('.pdf'):
                        import pymupdf; doc=pymupdf.open(stream=f.read(),filetype="pdf")
                        text="".join([p.get_text() for p in doc]); st.text_area("预览",text[:500],height=120)
                    elif f.name.endswith(('.docx','.doc')):
                        import docx as pydocx; doc=pydocx.Document(io.BytesIO(f.read()))
                        text="\\n".join([p.text for p in doc.paragraphs]); st.text_area("预览",text[:500],height=120)
                    elif f.name.endswith('.txt'):
                        text=f.read().decode('utf-8',errors='ignore'); st.text_area("预览",text[:500],height=120)
                except Exception as e: st.warning(str(e))

st.divider()
st.caption("会考AI学习管家 v4.0 · shadcn/ui design system")
