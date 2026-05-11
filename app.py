
import streamlit as st
import random, time, io, re, json
from collections import defaultdict
from pathlib import Path
from subjects import SUBJECTS, EXAM_SYLLABUS, POINTS_RULES
from question_bank import ALL_QUESTIONS
from auth import login, register, get_all_users
from persistence import (save_state, load_state, load_kb_proficiency,
                          save_uploaded_file, list_user_uploads, list_extracted_questions)
from doc_processor import process_upload

# 名言库
QUOTES = [
    "学而不思则罔，思而不学则殆。 — 孔子",
    "知识就是力量。 — 培根",
    "学习是终身的事业。 — 钱伟长",
    "不积跬步，无以至千里。 — 荀子",
    "温故而知新，可以为师矣。 — 孔子",
    "天才是百分之一的灵感加百分之九十九的汗水。 — 爱迪生",
    "读书破万卷，下笔如有神。 — 杜甫",
    "业精于勤，荒于嬉。 — 韩愈",
    "学如逆水行舟，不进则退。 — 《增广贤文》",
    "教育的根是苦的，但果实是甜的。 — 亚里士多德",
    "学习不在于学校，而在于一生。 — 爱因斯坦",
    "知之为知之，不知为不知，是知也。 — 孔子",
    "少壮不努力，老大徒伤悲。 — 《长歌行》",
    "博学之，审问之，慎思之，明辨之，笃行之。 — 《中庸》",
    "吾生也有涯，而知也无涯。 — 庄子",
]

st.set_page_config(page_title="会考AI学习管家", page_icon="📚", layout="wide",
                   initial_sidebar_state="expanded")

# ═══════════════════════════════════════
# CSS (full light-theme override)
# ═══════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');

/* ── Kill all dark ── */
.stApp, .main, .st-emotion-cache-0, section[data-testid="stSidebar"],
[data-testid="stAppViewContainer"], [data-testid="stHeader"],
[data-testid="stSidebarContent"], .block-container, .stMarkdown,
.element-container, .stVerticalBlock, div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"] { background: #FFFBF5 !important; }
.stApp, .stMarkdown, p, span, div, label, li, h1, h2, h3, h4, h5, h6,
[data-testid="stCaptionContainer"], [data-testid="stText"], code, pre,
.stRadio label, .stCheckbox label { color: #2D2420 !important; }
section[data-testid="stSidebar"] { background: #FFFAF0 !important; border-right: 2px solid #F5E6D3 !important; }

* { font-family: 'Nunito', 'PingFang SC', sans-serif !important; }
:root { --border: #F0E4D4; --muted: #A69888; --shadow: 0 4px 0 #E8D5C0, 0 6px 20px rgba(180,150,120,0.12); }

.fun-card {
    background: #FFF; border: 2px solid var(--border); border-radius: 20px; padding: 24px;
    box-shadow: var(--shadow); transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1);
}
.fun-card:hover { transform: translateY(-3px); box-shadow: 0 8px 0 #E8D5C0, 0 12px 30px rgba(180,150,120,0.18); }

.stButton > button {
    border-radius: 14px !important; font-weight: 700 !important; font-size: 0.9rem !important;
    padding: 10px 20px !important; transition: all 0.2s cubic-bezier(0.34,1.56,0.64,1) !important;
    border: 2px solid #E8D5C0 !important; background: #FFF !important; color: #2D2420 !important;
    box-shadow: 0 3px 0 #E8D5C0 !important;
}
.stButton > button:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 0 #E8D5C0 !important; background: #FFF8F0 !important; }
.stButton > button:active { transform: translateY(1px) !important; box-shadow: 0 1px 0 #E8D5C0 !important; }
.stButton > button[kind="primary"] { color: #FFF !important; border-color: transparent !important; }
.stButton > button[kind="primary"]:hover { filter: brightness(1.1); }

.qcard { background: #FFF; border: 2px solid #F0E4D4; border-radius: 20px; padding: 24px; box-shadow: var(--shadow); }
.fb-ok { background: #F0FFF4; border: 2px solid #A7F3D0; border-radius: 16px; padding: 16px; }
.fb-no { background: #FFF5F5; border: 2px solid #FECACA; border-radius: 16px; padding: 16px; }
.tag { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 700; }
.subkb {
    background: #FFF; border: 2px solid #F0E4D4; border-radius: 14px;
    padding: 18px 22px; margin: 10px 0; box-shadow: 0 2px 0 #F0E4D4;
}
.label-c { color: #A69888; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; }
.mastery-track { height: 8px; background: #F0E4D4; border-radius: 4px; overflow: hidden; }
.mastery-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }

@keyframes popIn { 0%{transform:scale(0.5);opacity:0}70%{transform:scale(1.1)}100%{transform:scale(1);opacity:1} }
.pop { animation: popIn 0.4s cubic-bezier(0.34,1.56,0.64,1); }

/* ── Login page ── */
.login-box {
    max-width: 420px; margin: 80px auto; text-align: center;
    background: #FFF; border: 2px solid #F0E4D4; border-radius: 24px;
    padding: 48px 36px; box-shadow: 0 8px 0 #E8D5C0, 0 12px 40px rgba(180,150,120,0.15);
}
.login-box input {
    border: 2px solid #F0E4D4 !important; border-radius: 12px !important;
    padding: 12px 16px !important; font-size: 1rem !important;
}

/* ── Admin table ── */
.admin-table { width: 100%; border-collapse: separate; border-spacing: 0; }
.admin-table th { background: #FFFAF0; padding: 12px 16px; text-align: left; font-weight: 700; border-bottom: 2px solid #E8D5C0; }
.admin-table td { padding: 10px 16px; border-bottom: 1px solid #F0E4D4; }

/* ── Upload fix: clear spacing ── */
.upload-section { margin: 16px 0; }
.upload-section .stFileUploader { margin: 8px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════
# Session Init
# ═══════════════════════════════════════
def init_session():
    for k, v in {
        "logged_in": False, "username": "", "is_admin": False,
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
        "login_mode": "login",
    }.items():
        if k not in st.session_state: st.session_state[k] = v

init_session()

# ═══════════════════════════════════════
# Auto-save hook
# ═══════════════════════════════════════
def maybe_save():
    if st.session_state.logged_in and not st.session_state.is_admin:
        save_state(st.session_state.username, st.session_state)

# ═══════════════════════════════════════
# Helpers
# ═══════════════════════════════════════
def cfg():
    s = st.session_state.subject
    if s and s in SUBJECTS: return SUBJECTS[s]
    return {"primary":"#2D2420","secondary":"#A69888","bg":"#FFFAF0","icon":"📚","emoji":"📚","gradient":"#2D2420"}

def get_subj_colors(subj):
    return {"化学":("#7C3AED","#EDE9FE","#A78BFA"),"生物":("#059669","#ECFDF5","#6EE7B7"),
            "历史":("#DC2626","#FEF2F2","#FCA5A5"),"地理":("#0284C7","#F0F9FF","#7DD3FC")}.get(subj,("#2D2420","#FFFAF0","#A69888"))

def add_pts(n): st.session_state.points += n; maybe_save()

def kb_pct(s,k):
    d=st.session_state.kb_proficiency[s][k]; return d["c"]/max(1,d["t"])

def kb_level(p):
    if p>=0.8: return "mastered","已经很棒啦 ⭐","#059669"
    if p>=0.5: return "ok","再加把劲 💪","#D97706"
    return "weak","需要加油 🔥","#DC2626"

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
            if end>0: out.append(f'<span class="label-c">{p[1:end]}</span> {p[end+1:]}')
            else: out.append(p)
        else: out.append(f'<span style="background:#FFF3CD;padding:2px 8px;border-radius:6px;font-weight:600;">{p}</span>')
    return "<br>".join(out)

def start_practice(ch_name):
    s=st.session_state.subject
    qs=[q for q in sub_qs(s) if q["chapter"]==ch_name]
    if not qs: qs=[q for q in sub_qs(s) if ch_name in q["chapter"] or q["chapter"] in ch_name]
    random.shuffle(qs)
    st.session_state.practice_chapter=ch_name; st.session_state.practice_questions=qs
    st.session_state.practice_idx=0; st.session_state.practice_answers={}
    st.session_state.practice_submitted=set()

def get_level():
    pts=st.session_state.points
    if pts>=2000: return 10,"🏆 学神","#7C3AED"
    if pts>=1000: return 8,"🌟 学霸","#3B82F6"
    if pts>=500: return 6,"📚 学者","#059669"
    if pts>=200: return 4,"🌱 学徒","#D97706"
    if pts>=50: return 2,"🐣 新手","#DC2626"
    return 1,"🌰 种子","#A69888"

def get_mascot(pts):
    if pts >= 1000: return "📚"
    if pts >= 500: return "🦊"
    if pts >= 200: return "🐱"
    if pts >= 50: return "🐤"
    return "🥚"

# ═══════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════
if not st.session_state.logged_in:
    # Center column
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("<br>", unsafe_allow_html=True)
        quote = random.choice(QUOTES)
        st.markdown(f"""
        <div style="text-align:center;padding:32px 0 16px;">
            <div style="font-size:1rem;color:#A69888;font-style:italic;padding:10px 18px;
                        background:#FFFAF0;border-radius:12px;border:1px solid #F0E4D4;
                        display:inline-block;max-width:480px;">
                💬 {quote}
            </div>
            <h1 style="font-weight:900;font-size:2rem;letter-spacing:-0.03em;margin-top:24px;">会考AI学习管家</h1>
            <p style="color:#A69888;font-size:1rem;">北京高中学业水平合格性考试</p>
        </div>
        """, unsafe_allow_html=True)

        mode = st.radio("", ["🔑 登录", "📝 注册"], horizontal=True)
        is_login = mode == "🔑 登录"

        username = st.text_input("用户名", placeholder="输入用户名", key="login_user")
        password = st.text_input("密码", type="password", placeholder="输入密码", key="login_pw")

        c1, c2 = st.columns([2, 1])
        with c1:
            if st.button("登录" if is_login else "注册", type="primary", use_container_width=True):
                if not username or not password:
                    st.error("请填写用户名和密码")
                elif is_login:
                    ok, msg, is_adm = login(username, password)
                    if ok:
                        st.session_state.logged_in = True; st.session_state.username = username
                        st.session_state.is_admin = is_adm
                        if not is_adm:
                            state = load_state(username)
                            for k, v in state.items():
                                if k in st.session_state: st.session_state[k] = v
                            st.session_state.kb_proficiency = load_kb_proficiency(username)
                        st.rerun()
                    else: st.error(msg)
                else:
                    ok, msg = register(username, password)
                    if ok: st.success(msg + "，请登录")
                    else: st.error(msg)
        with c2:
            st.caption("管理员: admin / admin123")

    st.stop()

# ═══════════════════════════════════════
# ADMIN PAGE
# ═══════════════════════════════════════
if st.session_state.is_admin:
    st.markdown('<h1 style="font-weight:900;">🛡️ 管理后台</h1>',unsafe_allow_html=True)

    users = get_all_users()
    st.markdown(f"### 📊 用户概览（共 {len(users)} 人）")

    if users:
        # Summary cards
        total_pts = sum(u.get("points",0) for u in users)
        total_q = sum(u.get("total_correct",0)+u.get("total_wrong",0) for u in users)
        cols = st.columns(4)
        cols[0].metric("👥 用户数", len(users))
        cols[1].metric("🏆 总积分", total_pts)
        cols[2].metric("📝 总做题", total_q)
        cols[3].metric("📤 总上传", sum(u.get("upload_count",0) for u in users))

        # Table
        st.markdown("""
        <table class="admin-table">
        <tr><th>用户</th><th>等级</th><th>积分</th><th>正确率</th><th>连击</th><th>上传</th><th>注册时间</th><th>最后登录</th></tr>
        """, unsafe_allow_html=True)
        for u in users:
            c = u.get("total_correct",0); w = u.get("total_wrong",0)
            rate = f"{c/(c+w)*100:.0f}%" if (c+w)>0 else "-"
            # Level
            pts = u.get("points",0)
            if pts >= 2000: lv = "🏆学神"
            elif pts >= 1000: lv = "🌟学霸"
            elif pts >= 500: lv = "📚学者"
            elif pts >= 200: lv = "🌱学徒"
            elif pts >= 50: lv = "🐣新手"
            else: lv = "🌰种子"
            st.markdown(f"""
            <tr>
                <td><strong>{u['username']}</strong></td>
                <td>{lv}</td>
                <td>{u.get('points',0)}</td>
                <td>{rate}</td>
                <td>🔥{u.get('max_streak',0)}</td>
                <td>📄{u.get('upload_count',0)}</td>
                <td>{u.get('created_at','-')}</td>
                <td>{u.get('last_login','-')}</td>
            </tr>
            """, unsafe_allow_html=True)
        st.markdown("</table>",unsafe_allow_html=True)

    if st.button("🚪 退出管理", use_container_width=True):
        st.session_state.logged_in = False; st.session_state.username = ""
        st.session_state.is_admin = False; st.rerun()
    st.stop()

# ═══════════════════════════════════════
# Sidebar (logged-in user)
# ═══════════════════════════════════════
with st.sidebar:
    lvl,lvl_name,lvl_color=get_level(); mascot=get_mascot(st.session_state.points)

    # User info
    st.markdown(f'<div class="mascot" style="font-size:3rem;">{mascot}</div>',unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center;">
        <div style="font-weight:800;">👤 {st.session_state.username}</div>
        <span class="tag" style="background:{lvl_color};color:#FFF;margin-top:4px;">Lv.{lvl} {lvl_name}</span>
    </div>
    <div style="text-align:center;margin:10px 0;">
        <div style="font-size:2rem;font-weight:900;">{st.session_state.points}<span style="font-size:0.85rem;color:#A69888;"> 分</span></div>
    </div>
    """,unsafe_allow_html=True)

    if st.session_state.streak >= 3:
        st.markdown(f'<div style="text-align:center;background:linear-gradient(135deg,#FF6B35,#F7C948);color:#FFF;border-radius:16px;padding:8px;font-weight:800;">🔥 {st.session_state.streak} 连击！</div>',unsafe_allow_html=True)

    st.divider()

    if st.session_state.subject:
        c=cfg()
        st.markdown(f"#### {c['icon']} {st.session_state.subject}")
        if st.button("← 返回首页",use_container_width=True): st.session_state.page="home"; st.session_state.subject=None; st.rerun()

    st.divider()
    if st.button("🚪 退出登录", use_container_width=True):
        maybe_save()
        st.session_state.logged_in=False; st.session_state.username=""
        st.session_state.is_admin=False; st.rerun()

# ═══════════════════════════════════════
# Home
# ═══════════════════════════════════════
if st.session_state.page=="home":
    st.markdown(f'<h1 style="font-weight:900;font-size:2rem;letter-spacing:-0.03em;">你好，{st.session_state.username}！</h1>',unsafe_allow_html=True)
    st.markdown('<p style="color:#A69888;margin-bottom:24px;">选择科目开始今天的学习吧 ✨</p>',unsafe_allow_html=True)

    cols=st.columns(4)
    for i,(subj,cfg_) in enumerate(SUBJECTS.items()):
        m=sum(1 for k in cfg_["kb"] if kb_pct(subj,k)>=0.8)
        tk=len(cfg_["kb"]); tq=len(sub_qs(subj)); pc,_,_=get_subj_colors(subj)
        with cols[i]:
            st.markdown(f"""
            <div style="background:{pc};border-radius:20px;padding:28px 16px;text-align:center;color:#FFF;box-shadow:0 6px 0 rgba(0,0,0,0.1),0 10px 30px rgba(0,0,0,0.08);transition:all 0.3s;">
                <div style="font-size:2.8rem;">{cfg_['icon']}</div>
                <h3 style="font-weight:800;margin:8px 0;color:#FFF;">{subj}</h3>
                <div style="background:rgba(255,255,255,0.2);border-radius:12px;padding:10px;margin-top:12px;">
                    <div style="color:#FFF;font-weight:700;font-size:1.3rem;">{m}/{tk}</div>
                    <div style="color:rgba(255,255,255,0.8);font-size:0.75rem;">{tq} 题</div>
                </div>
            </div>
            """,unsafe_allow_html=True)
            if st.button(f"🚀 {subj}",key=f"go_{subj}",use_container_width=True,type="primary"):
                st.session_state.page="subject"; st.session_state.subject=subj
                st.session_state.view="knowledge"; add_pts(2); st.rerun()

# ═══════════════════════════════════════
# Subject
# ═══════════════════════════════════════
elif st.session_state.page=="subject" and st.session_state.subject:
    s=st.session_state.subject; sc,sbg,ssec=get_subj_colors(s)

    st.markdown(f'<h1 style="font-weight:900;letter-spacing:-0.03em;">{SUBJECTS[s]["icon"]} {s}</h1>',unsafe_allow_html=True)

    views={"🧠 知识图谱":"knowledge","📝 练习":"practice","⏱️ 模拟考":"exam","📋 考纲":"syllabus","📤 上传":"upload"}
    cur_label=[k for k,v in views.items() if v==st.session_state.view][0]
    choice=st.radio("",list(views.keys()),horizontal=True,index=list(views.keys()).index(cur_label),label_visibility="collapsed")
    st.session_state.view=views[choice]; st.divider()

    # ═══ Knowledge ═══
    if st.session_state.view=="knowledge":
        st.markdown(f'<h3 style="font-weight:800;">🧠 知识图谱</h3>',unsafe_allow_html=True)
        for kb_name,kb_info in SUBJECTS[s]["kb"].items():
            pct=kb_pct(s,kb_name); lvl,label,lc=kb_level(pct); key=f"{s}_{kb_name}"
            is_open=key in st.session_state.expanded_kb
            if st.button(f"{'▾' if is_open else '▸'}  {kb_info['icon']}  {kb_name}",key=f"kb_{key}",
                         use_container_width=True,type="primary" if is_open else "secondary"):
                if is_open: st.session_state.expanded_kb.discard(key)
                else: st.session_state.expanded_kb.add(key)
                st.rerun()
            st.markdown(f'<div class="mastery-track"><div class="mastery-fill" style="width:{int(pct*100)}%;background:{lc};"></div></div>',unsafe_allow_html=True)
            st.caption(f"{label} · {kb_info.get('desc','')} · {len(kb_info['subs'])}子知识点")
            if is_open:
                for sk_name,sk_text in kb_info["subs"].items():
                    sp=max(0,min(1,pct+random.uniform(-0.06,0.06))); sl,slab,ssc=kb_level(sp)
                    st.markdown(f"""
                    <div class="subkb" style="border-left:4px solid {ssc};">
                        <div style="font-weight:700;margin-bottom:8px;display:flex;justify-content:space-between;">
                            <span>📌 {sk_name}</span><span style="color:{ssc};font-weight:700;">{slab}</span>
                        </div>
                        <div style="line-height:1.8;font-size:0.88rem;">{render_subkb(sk_text)}</div>
                    </div>""",unsafe_allow_html=True)
                if st.button(f"⚡ 去练习「{kb_name}」",key=f"kp_{key}",use_container_width=True,type="primary"):
                    start_practice(kb_name); st.session_state.view="practice"; st.rerun()

    # ═══ Practice ═══
    elif st.session_state.view=="practice":
        ch_title=st.session_state.practice_chapter or "选择章节"
        st.markdown(f'<h3 style="font-weight:800;">📝 练习 · {ch_title}</h3>',unsafe_allow_html=True)
        if not st.session_state.practice_questions:
            chaps=list(dict.fromkeys([q["chapter"] for q in sub_qs(s)]))
            cols=st.columns(3)
            for i,ch in enumerate(chaps):
                p=kb_pct(s,ch); _,lb,_=kb_level(p); qc=len([q for q in sub_qs(s) if q["chapter"]==ch])
                with cols[i%3]:
                    st.markdown(f'<div style="text-align:center;padding:14px;background:#FFF;border:2px solid #F0E4D4;border-radius:14px;margin-bottom:8px;"><strong>{ch}</strong><br><span style="color:#A69888;font-size:0.8rem;">{qc}题 · {p*100:.0f}%</span></div>',unsafe_allow_html=True)
                    if st.button(f"⚡ 开始",key=f"pch_{i}",use_container_width=True): start_practice(ch); st.rerun()
        qs=st.session_state.practice_questions; idx=st.session_state.practice_idx
        if qs and idx<len(qs):
            q=qs[idx]; qid=q["id"]; sub=qid in st.session_state.practice_submitted
            prev=st.session_state.practice_answers.get(qid,"")
            t1,t2=st.columns([4,1])
            with t1: st.progress(idx/len(qs),text=f"第{idx+1}/{len(qs)}题")
            with t2:
                if st.button("← 换",key="back_chap",use_container_width=True): st.session_state.practice_questions=[]; st.rerun()
            st.markdown(f'<div class="qcard"><strong>{idx+1}.</strong> {q["q"]} <span class="tag" style="background:{sbg};color:{sc};">{q["chapter"]}</span></div>',unsafe_allow_html=True)
            ch=st.radio("选择答案",q["opts"],index=q["opts"].index(prev) if prev in q["opts"] else None,key=f"pq_{qid}",disabled=sub)
            c1,c2=st.columns(2)
            with c1:
                if not sub and st.button("✅ 提交",key=f"ps_{qid}",use_container_width=True,type="primary"):
                    if ch: st.session_state.practice_answers[qid]=ch; st.session_state.practice_submitted.add(qid); ok=(ch[0]==q["ans"]); upd_kb(q["chapter"],ok)
                    if ok: st.session_state.total_correct+=1; st.session_state.streak+=1; st.session_state.max_streak=max(st.session_state.max_streak,st.session_state.streak); add_pts(10)
                    else: st.session_state.total_wrong+=1; st.session_state.streak=0; add_pts(2)
                    st.rerun()
            with c2:
                if sub and idx+1<len(qs) and st.button("👉 下一题",key=f"pn_{qid}",use_container_width=True): st.session_state.practice_idx+=1; st.rerun()
            if sub:
                ua=st.session_state.practice_answers.get(qid,"")[0] if st.session_state.practice_answers.get(qid) else ""
                if ua==q["ans"]: st.markdown(f'<div class="fb-ok">🎉 <strong>正确！</strong> +10分</div>',unsafe_allow_html=True)
                else: st.markdown(f'<div class="fb-no">😅 <strong>不对</strong> 答案:{q["ans"]} +2分</div>',unsafe_allow_html=True)
                st.info(q.get('exp',''))
        elif qs and idx>=len(qs):
            n=sum(1 for q in qs if st.session_state.practice_answers.get(q["id"],"") and st.session_state.practice_answers[q["id"]][0]==q["ans"])
            pct_done=n/len(qs)*100; ch=st.session_state.practice_chapter; cp=kb_pct(s,ch)
            st.balloons()
            emoji="🎉" if pct_done>=80 else "💪" if pct_done>=60 else "🔥"
            st.markdown(f'<div class="fun-card pop" style="text-align:center;"><div style="font-size:3rem;">{emoji}</div><div style="font-size:2.5rem;font-weight:900;">{n}/{len(qs)}</div><div style="color:#A69888;">正确率 {pct_done:.0f}%</div></div>',unsafe_allow_html=True)
            if cp>=0.9 and f"m_{s}_{ch}" not in st.session_state: st.session_state[f"m_{s}_{ch}"]=True; add_pts(100); st.success(f"🏆 「{ch}」精通 +100分！")
            c1,c2,c3=st.columns(3)
            with c1:
                if st.button("🔄 再来",use_container_width=True): start_practice(ch); st.rerun()
            with c2:
                if st.button("🧠 图谱",use_container_width=True): st.session_state.practice_questions=[]; st.session_state.view="knowledge"; st.rerun()
            with c3:
                if st.button("📋 换章节",use_container_width=True): st.session_state.practice_questions=[]; st.rerun()

    # ═══ Exam ═══
    elif st.session_state.view=="exam":
        st.markdown(f'<h3 style="font-weight:800;">⏱️ 模拟考试</h3>',unsafe_allow_html=True)
        aq=sub_qs(s); nq=min(20,len(aq))
        if not st.session_state.exam_started and not st.session_state.exam_submitted:
            st.markdown(f'<div class="fun-card" style="text-align:center;"><div style="font-size:3rem;">⏱️</div><h3>模拟考试</h3><p style="color:#A69888;">60分钟 · {nq}题 · 满分100 · 及格60</p></div>',unsafe_allow_html=True)
            if st.button("🚀 开始",type="primary",use_container_width=True):
                eq=random.sample(aq,min(nq,len(aq))); random.shuffle(eq)
                st.session_state.exam_questions=eq; st.session_state.exam_answers={}; st.session_state.exam_submitted_set=set()
                st.session_state.exam_started=True; st.session_state.exam_submitted=False; st.session_state.exam_start_time=time.time(); st.session_state.exam_idx=0; st.rerun()
        elif st.session_state.exam_started and not st.session_state.exam_submitted:
            eqs=st.session_state.exam_questions; tot=len(eqs); el=time.time()-st.session_state.exam_start_time; rem=max(0,3600-el)
            m,sec=int(rem//60),int(rem%60)
            t1,t2=st.columns([1,4])
            with t1: st.markdown(f'<div style="padding:16px;border-radius:14px;text-align:center;font-size:1.6rem;font-weight:900;background:{"#FEF2F2" if rem<600 else sbg};color:{"#DC2626" if rem<600 else sc};border:2px solid {"#FECACA" if rem<600 else ssec};">{m:02d}:{sec:02d}</div>',unsafe_allow_html=True)
            with t2: st.progress(len(st.session_state.exam_submitted_set)/tot,text=f"已完成 {len(st.session_state.exam_submitted_set)}/{tot}")
            if rem<=0: st.session_state.exam_submitted=True; st.session_state.exam_end_time=time.time(); st.rerun()
            ei=st.session_state.exam_idx
            if ei<tot:
                q=eqs[ei]; qid=q["id"]; sub=qid in st.session_state.exam_submitted_set
                prev=st.session_state.exam_answers.get(qid,"")
                st.markdown(f'<div class="qcard"><strong>{ei+1}.</strong> {q["q"]} <span class="tag" style="background:{sbg};color:{sc};">{q["chapter"]}</span></div>',unsafe_allow_html=True)
                ch=st.radio("",q["opts"],index=q["opts"].index(prev) if prev in q["opts"] else None,key=f"eq_{qid}",disabled=sub)
                c1,c2=st.columns(2)
                with c1:
                    if not sub and st.button("提交",key=f"es_{qid}"):
                        if ch: st.session_state.exam_answers[qid]=ch; st.session_state.exam_submitted_set.add(qid); st.rerun()
                with c2:
                    if st.button("跳过",key=f"esk_{ei}"): st.session_state.exam_idx=min(ei+1,tot-1); st.rerun()
            st.divider()
            if st.button("📝 交卷",type="primary",use_container_width=True): st.session_state.exam_submitted=True; st.session_state.exam_end_time=time.time(); st.rerun()
        if st.session_state.exam_submitted:
            eqs=st.session_state.exam_questions; tot=len(eqs); per=100//tot; corr=0
            for q in eqs:
                a=st.session_state.exam_answers.get(q["id"],""); l=a[0] if a else ""; ok=(l==q["ans"])
                if ok: corr+=1; st.session_state.total_correct+=1
                else: st.session_state.total_wrong+=1
                upd_kb(q["chapter"],ok)
            sc=corr*per; passed=sc>=60
            if passed: st.balloons(); add_pts(50)
            add_pts(corr*20//per if per else 0)
            scc="#059669" if passed else "#DC2626"
            st.markdown(f'<div class="fun-card pop" style="text-align:center;"><div style="font-size:3rem;">{"🎉" if passed else "💪"}</div><div style="font-size:3.5rem;font-weight:900;color:{scc};">{sc}<span style="font-size:1.3rem;">/100</span></div></div>',unsafe_allow_html=True)
            c1,c2=st.columns(2)
            with c1:
                if st.button("🔄 重新考",use_container_width=True): st.session_state.exam_started=False; st.session_state.exam_submitted=False; st.rerun()
            with c2:
                if st.button("🧠 图谱",use_container_width=True): st.session_state.exam_started=False; st.session_state.exam_submitted=False; st.session_state.view="knowledge"; st.rerun()

    # ═══ Syllabus ═══
    elif st.session_state.view=="syllabus":
        st.markdown(f'<h3 style="font-weight:800;">📋 考纲解析</h3>',unsafe_allow_html=True)
        st.markdown(f'<div class="fun-card">{EXAM_SYLLABUS.get(s,"")}</div>',unsafe_allow_html=True)
        for kn,ki in SUBJECTS[s]["kb"].items():
            st.markdown(f"**{ki['icon']} {kn}** · {ki.get('desc','')}")
            tags=" ".join([f'<span class="tag" style="background:{sbg};color:{sc};">{sn}</span>' for sn in ki["subs"]])
            st.markdown(tags,unsafe_allow_html=True)

    # ═══ Upload ═══
    elif st.session_state.view=="upload":
        st.markdown(f'<h3 style="font-weight:800;">📤 上传学习资料</h3>',unsafe_allow_html=True)

        # Pipeline explanation
        st.markdown(f"""
        <div class="fun-card" style="margin-bottom:20px;">
            <h4>🔍 文档识别入库流程</h4>
            <div style="font-size:0.88rem;color:#2D2420;line-height:1.9;">
                <p><strong>① 上传</strong> → 文件存储到 <code>data/users/{st.session_state.username}/uploads/</code></p>
                <p><strong>② 提取</strong> → PDF用pymupdf逐页提取文字 / Word用python-docx逐段提取</p>
                <p><strong>③ 解析</strong> → 正则匹配题干（含全角空格（　））+ 选项（A.B.C.D.）+ 答案</p>
                <p><strong>④ 归类</strong> → 关键词匹配科目（化学/生物/历史/地理）→ 匹配章节</p>
                <p><strong>⑤ 入库</strong> → 标注来源文件名 → 存入 <code>data/users/{st.session_state.username}/extracted/</code></p>
                <p style="color:{sc};font-weight:600;">📌 提取的题目自动标签：科目 + 章节 + 来源文档</p>
            </div>
        </div>
        """,unsafe_allow_html=True)

        # Upload area
        st.markdown('<div class="upload-section">',unsafe_allow_html=True)
        um = st.file_uploader("拖拽或点击上传 PDF / Word / TXT",
                              type=["pdf","docx","doc","txt"],
                              accept_multiple_files=True,
                              label_visibility="visible",
                              key="main_upload")
        st.markdown('</div>',unsafe_allow_html=True)

        if um:
            for f in um:
                with st.spinner(f"🔍 处理 {f.name}..."):
                    result = process_upload(st.session_state.username, f)

                if result.get("error"):
                    st.error(f"❌ {f.name}: {result['error']}")
                else:
                    st.success(f"✅ {f.name} 处理完成！")
                    st.json({
                        "文件名": result["filename"],
                        "大小": f"{result['size_kb']:.1f}KB",
                        "提取方式": result["text_method"],
                        "文本长度": f"{result['text_length']} 字符",
                        "检测科目": result["detected_subject"] or "未识别",
                        "检测章节": result["detected_chapter"] or "未分类",
                        "发现题目": result["questions_found"],
                        "入库题目": result["questions_saved"],
                        "存储路径": result["storage_path"],
                    })
                    add_pts(10)

        # Show existing uploads
        uploads = list_user_uploads(st.session_state.username)
        extracted = list_extracted_questions(st.session_state.username)
        if uploads or extracted:
            st.divider()
            if uploads:
                st.markdown("#### 📁 已上传文件")
                for u in uploads:
                    st.markdown(f"📄 `{u['name']}` ({u['size']/1024:.1f}KB)")
            if extracted:
                st.markdown("#### 📦 已提取题目")
                for e in extracted:
                    st.markdown(f"📋 `{e['file']}` — {e.get('subject','?')} · {len(e.get('questions',[]))}题 · 来源:{e.get('source','?')}")

# Auto-save on exit
maybe_save()
st.divider(); st.caption("会考AI学习管家 v6.0 · 多用户 · 数据持久化 · 文档智能入库")
