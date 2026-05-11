"""自定义题库 — 按上传文件管理题目集合"""
import json, os, time, re, io
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent / "data"

def get_custom_banks(username: str, subject: str) -> list:
    """获取用户某科目的所有自定义题库"""
    bank_dir = DATA_DIR / "users" / username / "custom_banks" / subject
    if not bank_dir.exists():
        return []
    banks = []
    for f in bank_dir.glob("*.json"):
        data = json.loads(f.read_text())
        data["_file"] = f.name
        banks.append(data)
    banks.sort(key=lambda b: b.get("created_at", ""), reverse=True)
    return banks

def save_custom_bank(username: str, subject: str, source_file: str, questions: list):
    """保存一个上传文件的题目集合为自定义题库"""
    bank_dir = DATA_DIR / "users" / username / "custom_banks" / subject
    bank_dir.mkdir(parents=True, exist_ok=True)
    
    safe_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fff]', '_', Path(source_file).stem)
    bank_file = bank_dir / f"{safe_name}_{int(time.time())}.json"
    
    data = {
        "source": source_file,
        "subject": subject,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "question_count": len(questions),
        "questions": questions,
    }
    bank_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return str(bank_file)

def load_custom_bank(username: str, subject: str, filename: str):
    """加载指定自定义题库"""
    bank_file = DATA_DIR / "users" / username / "custom_banks" / subject / filename
    if not bank_file.exists():
        return None
    return json.loads(bank_file.read_text())
