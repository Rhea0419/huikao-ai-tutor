"""错题本 — 收录错误题目，支持重做"""
import json, time
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

def add_error(username: str, subject: str, question: dict, user_answer: str):
    """添加一道错题"""
    err_dir = DATA_DIR / "users" / username / "errors"
    err_dir.mkdir(parents=True, exist_ok=True)
    err_file = err_dir / f"{subject}.json"
    
    errors = []
    if err_file.exists():
        errors = json.loads(err_file.read_text())
    
    # Check if already exists (by question text)
    for e in errors:
        if e["question"]["q"] == question.get("q", ""):
            e["attempts"] = e.get("attempts", 1) + 1
            e["last_wrong"] = time.strftime("%Y-%m-%d %H:%M:%S")
            e["user_answer"] = user_answer
            err_file.write_text(json.dumps(errors, ensure_ascii=False, indent=2))
            return
    
    errors.append({
        "question": question,
        "user_answer": user_answer,
        "correct_answer": question.get("ans", ""),
        "attempts": 1,
        "added_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_wrong": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mastered": False,
    })
    err_file.write_text(json.dumps(errors, ensure_ascii=False, indent=2))

def get_errors(username: str, subject: str = None) -> list[dict]:
    """获取错题"""
    err_dir = DATA_DIR / "users" / username / "errors"
    if not err_dir.exists():
        return []
    
    if subject:
        err_file = err_dir / f"{subject}.json"
        if not err_file.exists():
            return []
        return json.loads(err_file.read_text())
    else:
        # Get all subjects
        all_errors = []
        for f in err_dir.glob("*.json"):
            errors = json.loads(f.read_text())
            for e in errors:
                e["_subject"] = f.stem
            all_errors.extend(errors)
        return all_errors

def mark_mastered(username: str, subject: str, question_text: str):
    """标记错题已掌握"""
    err_dir = DATA_DIR / "users" / username / "errors"
    err_file = err_dir / f"{subject}.json"
    if not err_file.exists():
        return
    errors = json.loads(err_file.read_text())
    for e in errors:
        if e["question"].get("q", "") == question_text:
            e["mastered"] = True
            e["mastered_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    err_file.write_text(json.dumps(errors, ensure_ascii=False, indent=2))

def remove_error(username: str, subject: str, question_text: str):
    """删除一道错题"""
    err_dir = DATA_DIR / "users" / username / "errors"
    err_file = err_dir / f"{subject}.json"
    if not err_file.exists():
        return
    errors = json.loads(err_file.read_text())
    errors = [e for e in errors if e["question"].get("q", "") != question_text]
    err_file.write_text(json.dumps(errors, ensure_ascii=False, indent=2))
