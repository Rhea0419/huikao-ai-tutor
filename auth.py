"""用户认证模块"""
import json, hashlib, os, time
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
USERS_FILE = DATA_DIR / "users.json"
ADMIN_FILE = DATA_DIR / "admin.json"

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def _ensure_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text(json.dumps({}))
    if not ADMIN_FILE.exists():
        ADMIN_FILE.write_text(json.dumps({"admin": _hash("admin123")}))

def register(username: str, password: str) -> tuple[bool, str]:
    """注册新用户。返回 (成功, 消息)"""
    _ensure_files()
    users = json.loads(USERS_FILE.read_text())
    if username in users:
        return False, "用户名已存在"
    if len(username) < 2:
        return False, "用户名至少2个字符"
    if len(password) < 4:
        return False, "密码至少4个字符"
    users[username] = {
        "password": _hash(password),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2))
    # 创建用户数据目录
    (DATA_DIR / "users" / username / "uploads").mkdir(parents=True, exist_ok=True)
    return True, "注册成功"

def login(username: str, password: str) -> tuple[bool, str, bool]:
    """登录。返回 (成功, 消息, 是否管理员)"""
    _ensure_files()
    # 检查管理员
    admin = json.loads(ADMIN_FILE.read_text())
    if username in admin and admin[username] == _hash(password):
        return True, "管理员登录成功", True
    # 检查普通用户
    users = json.loads(USERS_FILE.read_text())
    if username not in users:
        return False, "用户不存在", False
    if users[username]["password"] != _hash(password):
        return False, "密码错误", False
    # 更新最后登录
    users[username]["last_login"] = time.strftime("%Y-%m-%d %H:%M:%S")
    USERS_FILE.write_text(json.dumps(users, ensure_ascii=False, indent=2))
    return True, "登录成功", False

def get_all_users() -> list[dict]:
    """获取所有用户信息（管理员用）"""
    _ensure_files()
    users = json.loads(USERS_FILE.read_text())
    result = []
    for uname, uinfo in users.items():
        user_dir = DATA_DIR / "users" / uname
        state_file = user_dir / "state.json"
        entry = {"username": uname, "created_at": uinfo.get("created_at",""),
                 "last_login": uinfo.get("last_login","")}
        if state_file.exists():
            state = json.loads(state_file.read_text())
            entry["points"] = state.get("points", 0)
            entry["total_correct"] = state.get("total_correct", 0)
            entry["total_wrong"] = state.get("total_wrong", 0)
            entry["max_streak"] = state.get("max_streak", 0)
        # 统计上传文件
        up_dir = user_dir / "uploads"
        if up_dir.exists():
            entry["upload_count"] = len(list(up_dir.iterdir()))
        result.append(entry)
    return result
