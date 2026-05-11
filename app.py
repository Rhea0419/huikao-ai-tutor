
import streamlit as st
import random, time, io, re, json
from collections import defaultdict
from pathlib import Path
from subjects import SUBJECTS, EXAM_SYLLABUS, POINTS_RULES
from question_bank import ALL_QUESTIONS
from auth import login, register, get_all_users
from persistence import (save_state, load_state, load_kb_proficiency, list_user_uploads, list_extracted_questions)
from doc_processor import process_upload

QUOTES = [
    "学而不思则罔，思而不学则殆。 — 孔子",
    "知识就是力量。 — 培根",
    "不积跬步，无以至千里。 — 荀子",
    "温故而知新，可以为师矣。 — 孔子",
    "天才是百分之一的灵感加百分之九十九的汗水。 — 爱迪生",
    "读书破万卷，下笔如有神。 — 杜甫",
    "业精于勤，荒于嬉。 — 韩愈",
    "学如逆水行舟，不进则退。 — 《增广贤文》",
    "学习不在于学校，而在于一生。 — 爱因斯坦",
    "知之为知之，不知为不知，是知也。 — 孔子",
    "少壮不努力，老大徒伤悲。 — 《长歌行》",
    "博学之，审问之，慎思之，明辨之，笃行之。 — 《中庸》",
]

st.set_page_config(page_title="会考AI学习管家", page_icon="📚", layout="wide",
                   initial_sidebar_state="expanded")

# ═══════════════════════════ CSS ═══════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700;900&display=swap');

:root {
    --blue: #3B82F6;
    --blue-light: #EFF6FF;
    --green: #10B981;
    --orange: #F59E0B;
    --red: #EF4444;
    --bg: #F3F4F6;
    --card: #FFFFFF;
    --text: #111827;
    --muted: #9CA3AF;
    --border: #E5E7EB;
    --radius: 16px;
    --shadow: 0 1px 3px rgba(0,0,0,.06);
    --shadow-card: 0 1px 3px rgba(0,0,0,.06),0 4px 12px rgba(0,0,0,.04);
}

/* ── Hide Streamlit toolbar/header junk ── */
[data-testid="stToolbar"], header[data-testid="stHeader"],
[data-testid="stDecoration"], #MainMenu, footer,
.stDeployButton, [data-testid="stAppViewToolbar"] { display: none !important; }

/* ── Global ── */
* { font-family: 'Noto Sans SC',system-ui,sans-serif !important; }
.stApp { background: var(--bg) !important; }
section[data-testid="stSidebar"] { background: #fff !important; border-right:1px solid var(--border) !important; }
h1,h2,h3,h4,p,span,div,label,li { color: var(--text); }

/* ── Cards ── */
.card {
    background:#fff;border-radius:var(--radius);padding:20px;
    box-shadow:var(--shadow-card);border:1px solid var(--border);
}

/* ── Buttons ── */
.stButton > button {
    border-radius:12px !important;font-weight:600 !important;font-size:.9rem !important;
    padding:10px 20px !important;transition:all .15s !important;
    border:1px solid var(--border) !important;background:#fff !important;color:var(--text) !important;
}
.stButton > button:hover { background:#F9FAFB !important;border-color:#D1D5DB !important; }
.stButton > button[kind="primary"] { background:var(--blue) !important;color:#fff !important;border-color:var(--blue) !important; }
.stButton > button[kind="primary"]:hover { background:#2563EB !important; }

/* ── Progress ── */
.stProgress>div{background:#E5E7EB!important;border-radius:6px!important;}
.stProgress>div>div{background:var(--blue)!important;border-radius:6px!important;}

/* ── Radio nav ── */
div[role="radiogroup"]{gap:4px;display:flex;}
div[role="radiogroup"] label{border-radius:10px!important;padding:8px 18px!important;font-weight:600!important;font-size:.88rem!important;}
div[role="radiogroup"] label:hover{background:#F3F4F6!important;}

/* ── Mastery bar ── */
.mbar{height:6px;background:#E5E7EB;border-radius:3px;overflow:hidden;margin:4px 0;}
.mfill{height:100%;border-radius:3px;transition:width .4s;}

/* ── Question ── */
.qcard{background:#fff;border-radius:var(--radius);padding:22px;box-shadow:var(--shadow);border:1px solid var(--border);}

/* ── Feedback ── */
.fb-ok{background:#ECFDF5;border:1px solid #A7F3D0;border-radius:12px;padding:14px;}
.fb-no{background:#FEF2F2;border:1px solid #FECACA;border-radius:12px;padding:14px;}

/* ── Sub knowledge ── */
.subkb{background:#fff;border:1px solid var(--border);border-radius:12px;padding:16px 20px;margin:8px 0;box-shadow:var(--shadow);}
.lbl{color:var(--muted);font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;}

/* ── Tags ── */
.tag{display:inline-block;padding:3px 10px;border-radius:12px;font-size:.75rem;font-weight:600;}
</style>
""",unsafe_allow_html=True)

# ═══════════════════════════ Init ═══════════════════════════
def init():
    for k,v in {
        "logged_in":False,"username":"","is_admin":False,
        "subject":None,"page":"home","view":"knowledge",
        "points":0,"streak":0,"max_streak":0,"total_correct":0,"total_wrong":0,
        "expanded_kb":set(),
        "practice_chapter":None,"practice_questions":[],
        "practice_idx":0,"practice_answers":{},"practice_submitted":set(),
        "exam_started":False,"exam_submitted":False,
        "exam_start_time":None,"exam_end_time":None,
        "exam_questions":[],"exam_answers":{},"exam_submitted_set":set(),"exam_idx":0,
        "kb_proficiency":defaultdict(lambda:defaultdict(lambda:{"c":0,"t":0})),
    }.items():
        if k not in st.session_state:st.session_state[k]=v
init()

def maybe_save():
    if st.session_state.logged_in and not st.session_state.is_admin:
        save_state(st.session_state.username,st.session_state)

# ═══════════════════════════ Helpers ═══════════════════════════
def cfg():
    s=st.session_state.subject
    if s and s in SUBJECTS:return SUBJECTS[s]
    return {"primary":"#3B82F6","icon":"📚","gradient":"#3B82F6"}

def subj_color(subj):
    return {"化学":("#8B5CF6","#F5F3FF"),"生物":("#10B981","#ECFDF5"),
            "历史":("#F59E0B","#FFFBEB"),"地理":("#3B82F6","#EFF6FF")}.get(subj,("#3B82F6","#EFF6FF"))

def add_pts(n):st.session_state.points+=n;maybe_save()
def kb_pct(s,k):
    d=st.session_state.kb_proficiency[s][k];return d["c"]/max(1,d["t"])
def kb_level(p):
    if p>=.8:return"mastered","熟练","#10B981"
    if p>=.5:return"ok","一般","#F59E0B"
    return"weak","薄弱","#EF4444"
def upd_kb(ch,ok):
    s=st.session_state.subject
    st.session_state.kb_proficiency[s][ch]["t"]+=1
    if ok:st.session_state.kb_proficiency[s][ch]["c"]+=1
def sub_qs(s):return ALL_QUESTIONS.get(s,[])
def render_subkb(text):
    parts=text.split("|");out=[]
    for p in parts:
        p=p.strip()
        if not p:continue
        if p.startswith("【"):
            end=p.find("】")
            if end>0:out.append(f'<span class="lbl">{p[1:end]}</span> {p[end+1:]}')
            else:out.append(p)
        else:out.append(f'<span style="background:#FEF3C7;padding:2px 8px;border-radius:4px;font-weight:600;">{p}</span>')
    return"<br>".join(out)
def start_practice(ch_name):
    s=st.session_state.subject
    qs=[q for q in sub_qs(s) if q["chapter"]==ch_name]
    if not qs:qs=[q for q in sub_qs(s) if ch_name in q["chapter"] or q["chapter"] in ch_name]
    random.shuffle(qs)
    st.session_state.practice_chapter=ch_name;st.session_state.practice_questions=qs
    st.session_state.practice_idx=0;st.session_state.practice_answers={}
    st.session_state.practice_submitted=set()

def get_mascot(pts):
    if pts>=1000:return"📚"
    if pts>=500:return"🦊"
    if pts>=200:return"🐱"
    if pts>=50:return"🐤"
    return"🥚"

# ═══════════════════════════ LOGIN ═══════════════════════════
if not st.session_state.logged_in:
    _,center,_=st.columns([1,2,1])
    with center:
        st.markdown("<br>",unsafe_allow_html=True)
        quote=random.choice(QUOTES)
        st.markdown(f"""
        <div style="text-align:center;padding:32px 0 16px;">
            <div style="font-size:.95rem;color:var(--muted);font-style:italic;padding:10px 18px;
                        background:var(--blue-light);border-radius:12px;border:1px solid #DBEAFE;
                        display:inline-block;max-width:480px;">💬 {quote}</div>
            <h1 style="font-weight:900;font-size:2rem;margin-top:24px;">会考AI学习管家</h1>
            <p style="color:var(--muted);">北京高中学业水平合格性考试</p>
        </div>""",unsafe_allow_html=True)
        mode=st.radio("",["🔑 登录","📝 注册"],horizontal=True)
        is_login=mode=="🔑 登录"
        username=st.text_input("用户名",placeholder="输入用户名")
        password=st.text_input("密码",type="password",placeholder="输入密码")
        if st.button("登录" if is_login else"注册",type="primary",use_container_width=True):
            if not username or not password:st.error("请填写用户名和密码")
            elif is_login:
                ok,msg,is_adm=login(username,password)
                if ok:
                    st.session_state.logged_in=True;st.session_state.username=username;st.session_state.is_admin=is_adm
                    if not is_adm:
                        s=load_state(username)
                        for k,v in s.items():
                            if k in st.session_state:st.session_state[k]=v
                        st.session_state.kb_proficiency=load_kb_proficiency(username)
                    st.rerun()
                else:st.error(msg)
            else:
                ok,msg=register(username,password)
                if ok:st.success(msg+"，请登录")
                else:st.error(msg)
    st.stop()

# ═══════════════════════════ ADMIN ═══════════════════════════
if st.session_state.is_admin:
    st.markdown('<h1 style="font-weight:900;">🛡️ 管理后台</h1>',unsafe_allow_html=True)
    users=get_all_users()
    st.markdown(f"### 📊 用户概览（{len(users)}人）")
    if users:
        tp=sum(u.get("points",0)for u in users)
        tq=sum(u.get("total_correct",0)+u.get("total_wrong",0)for u in users)
        c1,c2,c3,c4=st.columns(4)
        c1.metric("👥 用户",len(users));c2.metric("🏆 积分",tp);c3.metric("📝 做题",tq)
        c4.metric("📤 上传",sum(u.get("upload_count",0)for u in users))
        for u in users:
            c=u.get("total_correct",0);w=u.get("total_wrong",0)
            rate=f"{c/(c+w)*100:.0f}%"if(c+w)>0 else"-"
            pts=u.get("points",0)
            if pts>=1000:lv="🌟学霸"
            elif pts>=500:lv="📚学者"
            elif pts>=200:lv="🌱学徒"
            elif pts>=50:lv="🐣新手"
            else:lv="🌰种子"
            st.markdown(f"**{u['username']}** | {lv} | {u.get('points',0)}分 | 正确率{rate} | 🔥{u.get('max_streak',0)}连击 | 📄{u.get('upload_count',0)}上传")
    if st.button("🚪 退出管理",use_container_width=True):
        st.session_state.logged_in=False;st.session_state.username="";st.session_state.is_admin=False;st.rerun()
    st.stop()

# ═══════════════════════════ Sidebar ═══════════════════════════
with st.sidebar:
    mascot=get_mascot(st.session_state.points)
    pts=st.session_state.points
    if pts>=1000:lv,ln="🌟","学霸"
    elif pts>=500:lv,ln="📚","学者"
    elif pts>=200:lv,ln="🌱","学徒"
    elif pts>=50:lv,ln="🐣","新手"
    else:lv,ln="🌰","种子"

    st.markdown(f'<div style="text-align:center;font-size:2.5rem;margin:8px 0;">{mascot}</div>',unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center;margin-bottom:12px;">
        <span style="font-weight:800;">👤 {st.session_state.username}</span><br>
        <span style="font-size:.8rem;color:var(--muted);">{lv} {ln}</span>
        <div style="font-size:1.8rem;font-weight:900;margin:8px 0;">{st.session_state.points}<span style="font-size:.85rem;color:var(--muted);">分</span></div>
    </div>""",unsafe_allow_html=True)
    if st.session_state.streak>=3:
        st.markdown(f'<div style="text-align:center;background:linear-gradient(135deg,#F97316,#FBBF24);color:#fff;border-radius:12px;padding:6px;font-weight:700;">🔥 {st.session_state.streak}连击</div>',unsafe_allow_html=True)
    st.divider()
    if st.session_state.subject:
        st.markdown(f"#### {SUBJECTS[st.session_state.subject]['icon']} {st.session_state.subject}")
        if st.button("← 返回首页",use_container_width=True):
            st.session_state.page="home";st.session_state.subject=None;st.rerun()
    st.divider()
    if st.button("🚪 退出",use_container_width=True):
        maybe_save();st.session_state.logged_in=False;st.session_state.username="";st.rerun()

# ═══════════════════════════ Home ═══════════════════════════
if st.session_state.page=="home":
    st.markdown(f'<h1 style="font-weight:900;font-size:1.6rem;">你好，{st.session_state.username} 👋</h1>',unsafe_allow_html=True)
    st.markdown('<p style="color:var(--muted);margin-bottom:20px;">选择科目开始今天的学习</p>',unsafe_allow_html=True)
    cols=st.columns(4)
    for i,(subj,cfg_)in enumerate(SUBJECTS.items()):
        m=sum(1 for k in cfg_["kb"] if kb_pct(subj,k)>=.8)
        tk=len(cfg_["kb"]);tq=len(sub_qs(subj))
        sc,_=subj_color(subj)
        with cols[i]:
            st.markdown(f"""
            <div class="card" style="text-align:center;padding:24px 16px;border-top:3px solid {sc};">
                <div style="font-size:2.5rem;">{cfg_['icon']}</div>
                <h3 style="font-weight:700;font-size:1.1rem;margin:8px 0;">{subj}</h3>
                <div style="color:var(--muted);font-size:.8rem;">{m}/{tk} 章节掌握 · {tq}题</div>
            </div>""",unsafe_allow_html=True)
            if st.button(f"进入{subj}",key=f"go_{subj}",use_container_width=True,type="primary"):
                st.session_state.page="subject";st.session_state.subject=subj
                st.session_state.view="knowledge";add_pts(2);st.rerun()

# ═══════════════════════════ Subject ═══════════════════════════
elif st.session_state.page=="subject" and st.session_state.subject:
    s=st.session_state.subject;sc,sbg=subj_color(s)
    st.markdown(f'<h1 style="font-weight:900;font-size:1.5rem;">{SUBJECTS[s]["icon"]} {s}</h1>',unsafe_allow_html=True)
    views={"🧠 知识图谱":"knowledge","📝 练习":"practice","⏱️ 模拟考":"exam","📋 考纲":"syllabus","📤 上传":"upload"}
    cur=[k for k,v in views.items() if v==st.session_state.view][0]
    c=st.radio("",list(views.keys()),horizontal=True,index=list(views.keys()).index(cur),label_visibility="collapsed")
    st.session_state.view=views[c];st.divider()

    # ═══ Knowledge ═══
    if st.session_state.view=="knowledge":
        st.markdown('<h3 style="font-weight:700;">🧠 知识图谱</h3>',unsafe_allow_html=True)
        for kb_name,kb_info in SUBJECTS[s]["kb"].items():
            pct=kb_pct(s,kb_name);lvl,label,lc=kb_level(pct);key=f"{s}_{kb_name}"
            is_open=key in st.session_state.expanded_kb
            if st.button(f"{'▾' if is_open else'▸'} {kb_info['icon']} {kb_name}",key=f"kb_{key}",use_container_width=True,
                         type="primary" if is_open else"secondary"):
                if is_open:st.session_state.expanded_kb.discard(key)
                else:st.session_state.expanded_kb.add(key)
                st.rerun()
            st.markdown(f'<div class="mbar"><div class="mfill" style="width:{int(pct*100)}%;background:{lc};"></div></div>',unsafe_allow_html=True)
            st.caption(f"{label} · {kb_info.get('desc','')}")
            if is_open:
                for sk_name,sk_text in kb_info["subs"].items():
                    sp=max(0,min(1,pct+random.uniform(-.06,.06)));sl,slab,ssc=kb_level(sp)
                    st.markdown(f"""<div class="subkb" style="border-left:3px solid {ssc};"><div style="font-weight:700;margin-bottom:6px;display:flex;justify-content:space-between;"><span>📌 {sk_name}</span><span style="color:{ssc};font-weight:700;font-size:.8rem;">{slab}</span></div><div style="line-height:1.8;font-size:.88rem;">{render_subkb(sk_text)}</div></div>""",unsafe_allow_html=True)
                if st.button(f"⚡ 去练习「{kb_name}」",key=f"kp_{key}",use_container_width=True,type="primary"):
                    start_practice(kb_name);st.session_state.view="practice";st.rerun()

    # ═══ Practice ═══
    elif st.session_state.view=="practice":
        st.markdown(f'<h3 style="font-weight:700;">📝 练习 · {st.session_state.practice_chapter or"选择章节"}</h3>',unsafe_allow_html=True)
        if not st.session_state.practice_questions:
            chaps=list(dict.fromkeys([q["chapter"]for q in sub_qs(s)]))
            cols=st.columns(3)
            for i,ch in enumerate(chaps):
                p=kb_pct(s,ch);qc=len([q for q in sub_qs(s) if q["chapter"]==ch])
                with cols[i%3]:
                    st.markdown(f'<div class="card" style="text-align:center;padding:14px;"><strong>{ch}</strong><br><span style="color:var(--muted);font-size:.82rem;">{qc}题 · {p*100:.0f}%</span></div>',unsafe_allow_html=True)
                    if st.button("⚡ 开始",key=f"pch_{i}",use_container_width=True):start_practice(ch);st.rerun()
        qs=st.session_state.practice_questions;idx=st.session_state.practice_idx
        if qs and idx<len(qs):
            q=qs[idx];qid=q["id"];sub=qid in st.session_state.practice_submitted
            prev=st.session_state.practice_answers.get(qid,"")
            t1,t2=st.columns([4,1])
            with t1:st.progress(idx/len(qs),text=f"第{idx+1}/{len(qs)}题")
            with t2:
                if st.button("← 换",key="back_chap",use_container_width=True):
                    st.session_state.practice_questions=[];st.rerun()
            st.markdown(f'<div class="qcard"><strong>{idx+1}.</strong> {q["q"]} <span class="tag" style="background:{sbg};color:{sc};">{q["chapter"]}</span></div>',unsafe_allow_html=True)
            ch=st.radio("选择答案",q["opts"],index=q["opts"].index(prev) if prev in q["opts"] else None,key=f"pq_{qid}",disabled=sub)
            c1,c2=st.columns(2)
            with c1:
                if not sub and st.button("✅ 提交",key=f"ps_{qid}",use_container_width=True,type="primary"):
                    if ch:
                        st.session_state.practice_answers[qid]=ch;st.session_state.practice_submitted.add(qid)
                        ok=(ch[0]==q["ans"]);upd_kb(q["chapter"],ok)
                        if ok:st.session_state.total_correct+=1;st.session_state.streak+=1;st.session_state.max_streak=max(st.session_state.max_streak,st.session_state.streak);add_pts(10)
                        else:st.session_state.total_wrong+=1;st.session_state.streak=0;add_pts(2)
                        st.rerun()
            with c2:
                if sub and idx+1<len(qs) and st.button("👉 下一题",key=f"pn_{qid}",use_container_width=True):
                    st.session_state.practice_idx+=1;st.rerun()
            if sub:
                ua=st.session_state.practice_answers.get(qid,"")[0] if st.session_state.practice_answers.get(qid) else""
                if ua==q["ans"]:st.markdown('<div class="fb-ok">🎉 <strong>正确！</strong> +10分</div>',unsafe_allow_html=True)
                else:st.markdown(f'<div class="fb-no">😅 <strong>不对</strong> 答案:{q["ans"]} +2分</div>',unsafe_allow_html=True)
                st.info(q.get('exp',''))
        elif qs and idx>=len(qs):
            n=sum(1 for q in qs if st.session_state.practice_answers.get(q["id"],"")and st.session_state.practice_answers[q["id"]][0]==q["ans"])
            pct_done=n/len(qs)*100;ch=st.session_state.practice_chapter;cp=kb_pct(s,ch)
            st.balloons()
            emoji="🎉" if pct_done>=80 else"💪" if pct_done>=60 else"🔥"
            st.markdown(f'<div class="card" style="text-align:center;"><div style="font-size:2.5rem;">{emoji}</div><div style="font-size:2rem;font-weight:900;">{n}/{len(qs)}</div><div style="color:var(--muted);">正确率 {pct_done:.0f}%</div></div>',unsafe_allow_html=True)
            if cp>=.9 and f"m_{s}_{ch}" not in st.session_state:st.session_state[f"m_{s}_{ch}"]=True;add_pts(100);st.success(f"🏆 「{ch}」精通 +100分！")
            c1,c2,c3=st.columns(3)
            with c1:
                if st.button("🔄 再来",use_container_width=True):start_practice(ch);st.rerun()
            with c2:
                if st.button("🧠 图谱",use_container_width=True):st.session_state.practice_questions=[];st.session_state.view="knowledge";st.rerun()
            with c3:
                if st.button("📋 换章节",use_container_width=True):st.session_state.practice_questions=[];st.rerun()

    # ═══ Exam ═══
    elif st.session_state.view=="exam":
        st.markdown('<h3 style="font-weight:700;">⏱️ 模拟考试</h3>',unsafe_allow_html=True)
        aq=sub_qs(s);nq=min(20,len(aq))
        if not st.session_state.exam_started and not st.session_state.exam_submitted:
            st.markdown(f'<div class="card" style="text-align:center;"><div style="font-size:3rem;">⏱️</div><h3>模拟考试 · {s}</h3><p style="color:var(--muted);">60分钟 · {nq}题 · 满分100 · 及格60</p></div>',unsafe_allow_html=True)
            if st.button("🚀 开始考试",type="primary",use_container_width=True):
                eq=random.sample(aq,min(nq,len(aq)));random.shuffle(eq)
                st.session_state.exam_questions=eq;st.session_state.exam_answers={};st.session_state.exam_submitted_set=set()
                st.session_state.exam_started=True;st.session_state.exam_submitted=False
                st.session_state.exam_start_time=time.time();st.session_state.exam_idx=0;st.rerun()
        elif st.session_state.exam_started and not st.session_state.exam_submitted:
            eqs=st.session_state.exam_questions;tot=len(eqs);el=time.time()-st.session_state.exam_start_time;rem=max(0,3600-el)
            m,sec=int(rem//60),int(rem%60)
            t1,t2=st.columns([1,4])
            with t1:st.markdown(f'<div style="padding:14px;border-radius:12px;text-align:center;font-size:1.4rem;font-weight:900;background:{"#FEF2F2" if rem<600 else sbg};color:{"#EF4444" if rem<600 else sc};border:1px solid {"#FECACA" if rem<600 else"#E5E7EB"};">{m:02d}:{sec:02d}</div>',unsafe_allow_html=True)
            with t2:st.progress(len(st.session_state.exam_submitted_set)/tot,text=f"已完成 {len(st.session_state.exam_submitted_set)}/{tot}")
            if rem<=0:st.session_state.exam_submitted=True;st.session_state.exam_end_time=time.time();st.rerun()
            ei=st.session_state.exam_idx
            if ei<tot:
                q=eqs[ei];qid=q["id"];sub=qid in st.session_state.exam_submitted_set
                prev=st.session_state.exam_answers.get(qid,"")
                st.markdown(f'<div class="qcard"><strong>{ei+1}.</strong> {q["q"]} <span class="tag" style="background:{sbg};color:{sc};">{q["chapter"]}</span></div>',unsafe_allow_html=True)
                ch=st.radio("",q["opts"],index=q["opts"].index(prev) if prev in q["opts"] else None,key=f"eq_{qid}",disabled=sub)
                c1,c2=st.columns(2)
                with c1:
                    if not sub and st.button("提交",key=f"es_{qid}"):
                        if ch:st.session_state.exam_answers[qid]=ch;st.session_state.exam_submitted_set.add(qid);st.rerun()
                with c2:
                    if st.button("跳过",key=f"esk_{ei}"):st.session_state.exam_idx=min(ei+1,tot-1);st.rerun()
            st.divider()
            if st.button("📝 交卷",type="primary",use_container_width=True):
                st.session_state.exam_submitted=True;st.session_state.exam_end_time=time.time();st.rerun()
        if st.session_state.exam_submitted:
            eqs=st.session_state.exam_questions;tot=len(eqs);per=100//tot;corr=0
            for q in eqs:
                a=st.session_state.exam_answers.get(q["id"],"");l=a[0] if a else"";ok=(l==q["ans"])
                if ok:corr+=1;st.session_state.total_correct+=1
                else:st.session_state.total_wrong+=1
                upd_kb(q["chapter"],ok)
            sc=corr*per;passed=sc>=60
            if passed:st.balloons();add_pts(50)
            add_pts(corr*20//per if per else 0)
            scc="#10B981" if passed else"#EF4444"
            st.markdown(f'<div class="card" style="text-align:center;"><div style="font-size:3rem;">{"🎉" if passed else"💪"}</div><div style="font-size:3rem;font-weight:900;color:{scc};">{sc}<span style="font-size:1.2rem;">/100</span></div></div>',unsafe_allow_html=True)
            c1,c2=st.columns(2)
            with c1:
                if st.button("🔄 重考",use_container_width=True):st.session_state.exam_started=False;st.session_state.exam_submitted=False;st.rerun()
            with c2:
                if st.button("🧠 图谱",use_container_width=True):st.session_state.exam_started=False;st.session_state.exam_submitted=False;st.session_state.view="knowledge";st.rerun()

    # ═══ Syllabus ═══
    elif st.session_state.view=="syllabus":
        st.markdown('<h3 style="font-weight:700;">📋 考纲解析</h3>',unsafe_allow_html=True)
        st.markdown(f'<div class="card">{EXAM_SYLLABUS.get(s,"")}</div>',unsafe_allow_html=True)
        for kn,ki in SUBJECTS[s]["kb"].items():
            st.markdown(f"**{ki['icon']} {kn}** · {ki.get('desc','')}")
            tags=" ".join([f'<span class="tag" style="background:{sbg};color:{sc};">{sn}</span>' for sn in ki["subs"]])
            st.markdown(tags,unsafe_allow_html=True)

    # ═══ Upload ═══
    elif st.session_state.view=="upload":
        st.markdown('<h3 style="font-weight:700;">📤 上传学习资料</h3>',unsafe_allow_html=True)

        um = st.file_uploader(
            "",
            type=["pdf","docx","doc","txt"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="main_up"
        )

        if um:
            for f in um:
                with st.spinner(f"处理 {f.name}..."):
                    result = process_upload(st.session_state.username, f)
                if result.get("error"):
                    st.error(f"❌ {f.name}: {result['error']}")
                else:
                    st.success(f"✅ {f.name} 处理完成")
                    st.markdown(f"""
                    <div class="card" style="font-size:.88rem;">
                        <strong>检测科目：</strong>{result.get('detected_subject') or '未识别'}<br>
                        <strong>匹配章节：</strong>{result.get('detected_chapter') or '未分类'}<br>
                        <strong>发现题目：</strong>{result.get('questions_found',0)} 题<br>
                        <strong>存储路径：</strong><code>{result.get('storage_path','')}</code>
                    </div>""",unsafe_allow_html=True)
                    add_pts(10)

        uploads=list_user_uploads(st.session_state.username)
        if uploads:
            st.divider()
            st.markdown("#### 📁 已上传")
            for u in uploads:
                st.markdown(f"📄 `{u['name']}` ({u['size']/1024:.1f}KB)")

maybe_save()
