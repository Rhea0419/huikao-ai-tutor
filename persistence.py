"""数据持久化模块 — 按用户隔离存储"""
import json, os, time
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

def _user_dir(username: str) -> Path:
    d = DATA_DIR / "users" / username
    d.mkdir(parents=True, exist_ok=True)
    return d

def save_state(username: str, session_state: dict):
    """保存可序列化的 session state"""
    state = {
        "points": session_state.get("points", 0),
        "streak": session_state.get("streak", 0),
        "max_streak": session_state.get("max_streak", 0),
        "total_correct": session_state.get("total_correct", 0),
        "total_wrong": session_state.get("total_wrong", 0),
        "subject": session_state.get("subject"),
        "view": session_state.get("view"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (_user_dir(username) / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2))

    # 保存知识点熟练度
    kb = session_state.get("kb_proficiency")
    if kb and isinstance(kb, defaultdict):
        kb_serializable = {}
        for subj, chapters in kb.items():
            kb_serializable[subj] = dict(chapters)
        (_user_dir(username) / "kb_proficiency.json").write_text(
            json.dumps(kb_serializable, ensure_ascii=False, indent=2))

def load_state(username: str) -> dict:
    """加载用户状态"""
    state_file = _user_dir(username) / "state.json"
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {}

def load_kb_proficiency(username: str) -> defaultdict:
    """加载知识点熟练度"""
    kb_file = _user_dir(username) / "kb_proficiency.json"
    if kb_file.exists():
        data = json.loads(kb_file.read_text())
        return defaultdict(lambda: defaultdict(lambda: {"c":0,"t":0}), data)
    return defaultdict(lambda: defaultdict(lambda: {"c":0,"t":0}))

def save_uploaded_file(username: str, file_obj) -> str:
    """保存上传文件，返回存储路径"""
    up_dir = _user_dir(username) / "uploads"
    up_dir.mkdir(parents=True, exist_ok=True)
    file_path = up_dir / file_obj.name
    file_path.write_bytes(file_obj.getvalue())
    return str(file_path)

def save_extracted_questions(username: str, source_file: str, subject: str, questions: list):
    """保存从文档提取的题目"""
    ext_dir = _user_dir(username) / "extracted"
    ext_dir.mkdir(parents=True, exist_ok=True)
    out_file = ext_dir / f"{Path(source_file).stem}_questions.json"
    data = {
        "source": source_file,
        "subject": subject,
        "extracted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "questions": questions,
    }
    out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return str(out_file)

def list_user_uploads(username: str) -> list:
    """列出用户上传的文件"""
    up_dir = _user_dir(username) / "uploads"
    if not up_dir.exists(): return []
    return [{"name": f.name, "size": f.stat().st_size, "path": str(f), "time": f.stat().st_mtime}
            for f in up_dir.iterdir() if f.is_file()]

def list_extracted_questions(username: str) -> list:
    """列出已提取的题目文件"""
    ext_dir = _user_dir(username) / "extracted"
    if not ext_dir.exists(): return []
    result = []
    for f in ext_dir.glob("*_questions.json"):
        data = json.loads(f.read_text())
        data["file"] = f.name
        result.append(data)
    return result
