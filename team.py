import json
import os
import re
import sys
import time
import ast
import uuid
import math
import random
import string
import secrets
import hashlib
import base64
import threading
import argparse
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, quote
from dataclasses import dataclass
from typing import Any, Dict, Optional
import urllib.parse
import urllib.request
import urllib.error

from curl_cffi import requests

# ==========================================
# Tempmail.lol API (v2)/叫我小杨同学 Linuxdo
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_CONFIG: Dict[str, Any] = {
    "cdkey_file": "config/CDKEY.json",
    "code_file": "config/code.json",
    "code_results_file": "code_results.json",
    "teams_file": "teams.json",
    "output_root": ".",
    "target_type": "mother_count",
    "target_value": 0,
    "tempmail_base": "https://api.tempmail.lol/v2",
    "redeem_base_url": "https://yyl.ncet.top",
    "aisub_base_url": "https://sub.zenscaleai.com",
    "aisub_api_key": "sk_c1561e264e8b0b164d737603e696cba53e0040cc64fec55c",
    "subscribe_plan": "team",
    "oauth_redirect_uri": "http://localhost:1455/auth/callback",
    "oauth_scope": "openid email profile offline_access",
    "default_proxy": "",
    "default_sleep_min": 5,
    "default_sleep_max": 30
}


def _resolve_config_path(path_value: str) -> str:
    raw = str(path_value or "").strip()
    if not raw:
        return ""
    if os.path.isabs(raw):
        return raw
    return os.path.normpath(os.path.join(BASE_DIR, raw))


def load_config() -> Dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if not os.path.exists(CONFIG_PATH):
        return config
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            config.update(data)
    except Exception:
        return config
    return config


CONFIG = load_config()
TEMPMAIL_BASE = str(CONFIG.get("tempmail_base") or DEFAULT_CONFIG["tempmail_base"]).strip()
CURRENT_OUTPUT_DIR = ""


def _now_hms() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log_line(tag: str, message: str) -> None:
    print(f"[{_now_hms()}] {tag} {message}")


def log_info(message: str) -> None:
    log_line("INFO", message)


def log_ok(message: str) -> None:
    log_line(" OK ", message)


def log_warn(message: str) -> None:
    log_line("WARN", message)


def log_error(message: str) -> None:
    log_line("ERR ", message)


def log_section(title: str) -> None:
    bar = "=" * 18
    print(f"\n{bar} {title} {bar}")


def get_email_and_token(proxies: Any = None) -> tuple[str, str]:
    """创建 Tempmail.lol 邮箱并获取 token"""
    try:
        # 创建新的 inbox
        resp = requests.post(
            f"{TEMPMAIL_BASE}/inbox/create",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            json={},
            proxies=proxies,
            impersonate="chrome",
            timeout=15,
        )
        
        if resp.status_code not in (200, 201):
            log_error(f"Tempmail.lol 请求失败，状态码: {resp.status_code}")
            return "", ""
        
        data = resp.json()
        email = str(data.get("address", "")).strip()
        token = str(data.get("token", "")).strip()
        
        if not email or not token:
            log_error("Tempmail.lol 返回数据不完整")
            return "", ""
        
        return email, token
        
    except Exception as e:
        log_error(f"创建 Tempmail.lol 邮箱出错: {e}")
        return "", ""


def get_oai_code(token: str, email: str, proxies: Any = None) -> str:
    """使用 Tempmail.lol token 轮询获取验证码"""
    regex = r"(?<!\d)(\d{6})(?!\d)"
    seen_ids: set[int] = set()

    print(f"[*] 正在等待邮箱 {email} 的验证码...", end="", flush=True)

    for _ in range(40):
        print(".", end="", flush=True)
        try:
            # 获取邮件列表
            resp = requests.get(
                f"{TEMPMAIL_BASE}/inbox",
                params={"token": token},
                headers={"Accept": "application/json"},
                proxies=proxies,
                impersonate="chrome",
                timeout=15,
            )
            
            if resp.status_code != 200:
                time.sleep(3)
                continue

            data = resp.json()
            
            # 检查 inbox 是否过期
            if data is None or (isinstance(data, dict) and not data):
                print(" 邮箱已过期")
                return ""
            
            email_list = data.get("emails", []) if isinstance(data, dict) else []
            
            if not isinstance(email_list, list):
                time.sleep(3)
                continue

            for msg in email_list:
                if not isinstance(msg, dict):
                    continue
                
                # 使用 date 作为唯一标识（因为可能没有 id）
                msg_date = msg.get("date", 0)
                if not msg_date or msg_date in seen_ids:
                    continue
                seen_ids.add(msg_date)

                sender = str(msg.get("from", "")).lower()
                subject = str(msg.get("subject", ""))
                body = str(msg.get("body", ""))
                html = str(msg.get("html") or "")
                
                content = "\n".join([sender, subject, body, html])

                # 检查是否是目标邮件
                if "openai" not in sender and "openai" not in content.lower():
                    continue

                # 提取验证码
                m = re.search(regex, content)
                if m:
                    print(" 抓到啦! 验证码:", m.group(1))
                    return m.group(1)
                    
        except Exception as e:
            pass

        time.sleep(3)

    print(" 超时，未收到验证码")
    return ""


# ==========================================
# OAuth 授权与辅助函数
# ==========================================

AUTH_URL = "https://auth.openai.com/oauth/authorize"
TOKEN_URL = "https://auth.openai.com/oauth/token"
CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"

DEFAULT_REDIRECT_URI = str(CONFIG.get("oauth_redirect_uri") or DEFAULT_CONFIG["oauth_redirect_uri"])
DEFAULT_SCOPE = str(CONFIG.get("oauth_scope") or DEFAULT_CONFIG["oauth_scope"])


def _b64url_no_pad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _sha256_b64url_no_pad(s: str) -> str:
    return _b64url_no_pad(hashlib.sha256(s.encode("ascii")).digest())


def _random_state(nbytes: int = 16) -> str:
    return secrets.token_urlsafe(nbytes)


def _pkce_verifier() -> str:
    return secrets.token_urlsafe(64)


def _parse_callback_url(callback_url: str) -> Dict[str, str]:
    candidate = callback_url.strip()
    if not candidate:
        return {"code": "", "state": "", "error": "", "error_description": ""}

    if "://" not in candidate:
        if candidate.startswith("?"):
            candidate = f"http://localhost{candidate}"
        elif any(ch in candidate for ch in "/?#") or ":" in candidate:
            candidate = f"http://{candidate}"
        elif "=" in candidate:
            candidate = f"http://localhost/?{candidate}"

    parsed = urllib.parse.urlparse(candidate)
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    fragment = urllib.parse.parse_qs(parsed.fragment, keep_blank_values=True)

    for key, values in fragment.items():
        if key not in query or not query[key] or not (query[key][0] or "").strip():
            query[key] = values

    def get1(k: str) -> str:
        v = query.get(k, [""])
        return (v[0] or "").strip()

    code = get1("code")
    state = get1("state")
    error = get1("error")
    error_description = get1("error_description")

    if code and not state and "#" in code:
        code, state = code.split("#", 1)

    if not error and error_description:
        error, error_description = error_description, ""

    return {
        "code": code,
        "state": state,
        "error": error,
        "error_description": error_description,
    }


def _jwt_claims_no_verify(id_token: str) -> Dict[str, Any]:
    if not id_token or id_token.count(".") < 2:
        return {}
    payload_b64 = id_token.split(".")[1]
    pad = "=" * ((4 - (len(payload_b64) % 4)) % 4)
    try:
        payload = base64.urlsafe_b64decode((payload_b64 + pad).encode("ascii"))
        return json.loads(payload.decode("utf-8"))
    except Exception:
        return {}


def _decode_jwt_segment(seg: str) -> Dict[str, Any]:
    raw = (seg or "").strip()
    if not raw:
        return {}
    pad = "=" * ((4 - (len(raw) % 4)) % 4)
    try:
        decoded = base64.urlsafe_b64decode((raw + pad).encode("ascii"))
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        return {}


def _to_int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _generate_password(length: int = 12) -> str:
    """生成指定长度的随机密码（包含大小写字母和数字）"""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


VALIDATE_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://yyl.ncet.top/?",
    "sec-ch-ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
}

AISUB_API_KEY = str(CONFIG.get("aisub_api_key") or DEFAULT_CONFIG["aisub_api_key"]).strip()
AISUB_HEADERS = {
    "Authorization": f"Bearer {AISUB_API_KEY}",
    "Accept": "application/json",
}


class RetryWithNewAccount(Exception):
    """当前账号不可用，需要换号重试。"""

    pass


class StopScript(Exception):
    """满足停止条件，结束脚本。"""

    pass


def _code_file_path() -> str:
    return _resolve_config_path(str(CONFIG.get("code_file") or DEFAULT_CONFIG["code_file"]))


def _cdkey_file_path() -> str:
    return _resolve_config_path(str(CONFIG.get("cdkey_file") or DEFAULT_CONFIG["cdkey_file"]))


def _code_result_file_path() -> str:
    if CURRENT_OUTPUT_DIR:
        return os.path.join(CURRENT_OUTPUT_DIR, os.path.basename(str(CONFIG.get("code_results_file") or DEFAULT_CONFIG["code_results_file"])))
    return _resolve_config_path(str(CONFIG.get("code_results_file") or DEFAULT_CONFIG["code_results_file"]))


def _teams_file_path() -> str:
    return _resolve_config_path(str(CONFIG.get("teams_file") or DEFAULT_CONFIG["teams_file"]))


def _output_root_path() -> str:
    return _resolve_config_path(str(CONFIG.get("output_root") or DEFAULT_CONFIG["output_root"]))


def load_code_array() -> list[dict[str, Any]]:
    """读取配置指定的 code 文件，并解析其中的对象数组。"""
    code_file = _code_file_path()

    if not os.path.exists(code_file):
        log_warn(f"未找到 code 文件: {code_file}")
        return []

    try:
        with open(code_file, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    except Exception as e:
        log_error(f"读取 code 文件失败: {e}")
        return []

    if not raw:
        log_warn("code 文件为空")
        return []

    candidates = [raw]
    normalized = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', raw)
    normalized = re.sub(r"\bfalse\b", "false", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\btrue\b", "true", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bnull\b", "null", normalized, flags=re.IGNORECASE)
    candidates.append(normalized.replace("'", '"'))

    for candidate in candidates:
        try:
            data = json.loads(candidate)
            if isinstance(data, list):
                log_info(f"成功读取 code 数组，共 {len(data)} 项")
                return [item for item in data if isinstance(item, dict)]
        except Exception:
            pass

    try:
        python_like = raw.replace("false", "False").replace("true", "True").replace("null", "None")
        data = ast.literal_eval(python_like)
        if isinstance(data, list):
            log_info(f"成功读取 code 数组，共 {len(data)} 项")
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        pass

    log_error("code 文件内容不是可解析的数组格式")
    return []


def save_code_array(code_array: list[dict[str, Any]]) -> None:
    """将更新后的 code 数组写回 code 文件。"""
    code_file = _code_file_path()
    try:
        os.makedirs(os.path.dirname(code_file), exist_ok=True)
        normalized_array = []
        for item in code_array:
            if not isinstance(item, dict):
                continue
            normalized_array.append(
                {
                    "code": str(item.get("code") or "").strip(),
                    "use": _normalize_use_count(item.get("use")),
                }
            )
        with open(code_file, "w", encoding="utf-8") as f:
            json.dump(normalized_array, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(f"写回 code 文件失败: {e}")


def sync_code_file_from_cdkeys() -> None:
    """启动前将 CDKEY 文件中的未使用码补充到 code 文件。"""
    cdkey_file = _cdkey_file_path()
    if not cdkey_file or not os.path.exists(cdkey_file):
        return

    try:
        with open(cdkey_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        log_error(f"读取 CDKEY 文件失败: {e}")
        return

    codes: list[str] = []
    seen: set[str] = set()
    for line in lines:
        code = str(line or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        codes.append(code)

    if not codes:
        log_warn("CDKEY 文件为空，跳过同步")
        return

    existing_items = load_code_array()
    existing_codes = {
        str(item.get("code") or "").strip()
        for item in existing_items
        if isinstance(item, dict) and str(item.get("code") or "").strip()
    }

    added_count = 0
    merged_items = list(existing_items)
    for code in codes:
        if code in existing_codes:
            continue
        merged_items.append({"code": code, "use": 0})
        existing_codes.add(code)
        added_count += 1

    if added_count == 0:
        log_info("CDKEY 文件中的码已全部存在，跳过补充")
        return

    save_code_array(merged_items)
    log_info(f"已从 CDKEY 文件补充 {added_count} 个新码到 code 文件")


def load_code_result_map() -> dict[str, Dict[str, Any]]:
    """读取 code 对应的 validate 结果。"""
    result_file = _code_result_file_path()
    if not os.path.exists(result_file):
        return {}
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items() if isinstance(v, dict)}
    except Exception as e:
        log_error(f"读取 code_results 文件失败: {e}")
    return {}


def is_ready_validate_result(result: Any) -> bool:
    """只有已经拿到可用卡信息的缓存结果才允许复用。"""
    if not isinstance(result, dict):
        return False
    formatted_text = str(result.get("formatted_text") or "").strip()
    if formatted_text:
        return True
    response = result.get("response")
    return has_cards(response)


def save_code_result(code: str, result: Dict[str, Any]) -> None:
    """将 validate 结果写入单独文件。"""
    result_file = _code_result_file_path()
    data = load_code_result_map()
    data[code] = result
    try:
        os.makedirs(os.path.dirname(result_file), exist_ok=True)
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(f"写回 code_results 文件失败: {e}")


def create_run_output_dir() -> str:
    """创建本次运行的输出目录。"""
    now = datetime.now()
    dir_name = f"{now.year}年{now.month}月{now.day}日{now.strftime('%H:%M:%S')}"
    output_dir = os.path.join(_output_root_path(), dir_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def load_teams_entries(file_path: str) -> list[Dict[str, Any]]:
    """兼容读取单对象、对象数组或 {"teams": [...]} 格式。"""
    if not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []

    if isinstance(data, dict):
        teams = data.get("teams")
        if isinstance(teams, list):
            return [item for item in teams if isinstance(item, dict)]
        return [data]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    return []


def reset_teams_file(file_path: str) -> None:
    """初始化本次运行的 teams 汇总文件。"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"teams": []}, f, ensure_ascii=False, indent=2)


def append_team_entry(file_path: str, entry: Dict[str, Any]) -> None:
    """追加本次成功账号到 teams 汇总文件。"""
    teams = load_teams_entries(file_path)
    teams.append(entry)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump({"teams": teams}, f, ensure_ascii=False, indent=2)


def get_aisub_balance(proxies: Any = None) -> Dict[str, Any]:
    """查询 AISub 余额。"""
    try:
        aisub_base_url = str(CONFIG.get("aisub_base_url") or DEFAULT_CONFIG["aisub_base_url"]).rstrip("/")
        resp = requests.get(
            f"{aisub_base_url}/api/v1/balance",
            headers=AISUB_HEADERS,
            proxies=proxies,
            impersonate="chrome",
            timeout=20,
        )
        data: Any = resp.json() if resp.status_code == 200 else {"error": resp.text}
        return {
            "status_code": resp.status_code,
            "response": data,
        }
    except Exception as e:
        return {
            "status_code": 0,
            "response": {"error": str(e)},
        }


def ensure_aisub_balance(proxies: Any = None) -> int:
    """检查 AISub 余额，不足时停止脚本。"""
    balance_result = get_aisub_balance(proxies)
    balance_data = balance_result.get("response") or {}
    balance = 0
    if isinstance(balance_data, dict):
        try:
            balance = int(float(balance_data.get("balance") or 0))
        except (TypeError, ValueError):
            balance = 0

    remaining_times = balance // 30
    if balance_result.get("status_code") == 200 and remaining_times > 0:
        log_ok(f"AISub剩余次数 {remaining_times} 次")
        return remaining_times

    raise StopScript("AISub余额不足，请充值后再试")


def _normalize_use_count(value: Any) -> int:
    """将历史 use 字段统一转换为 0/1/2 计数。"""
    if isinstance(value, bool):
        return 2 if value else 0
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, count)


def get_next_unused_code() -> Optional[tuple[str, list[dict[str, Any]], int]]:
    """获取第一个 use < 2 的 code。"""
    code_array = load_code_array()
    for index, item in enumerate(code_array):
        code = str(item.get("code") or "").strip()
        use_count = _normalize_use_count(item.get("use"))
        item["use"] = use_count
        if code and use_count < 2:
            return code, code_array, index
    log_warn("code 文件中没有可用的 code")
    return None


def wait_for_next_unused_code() -> tuple[str, list[dict[str, Any]], int]:
    """获取可用 code；全部用完时停止脚本。"""
    next_code_info = get_next_unused_code()
    if next_code_info:
        return next_code_info
    raise StopScript("code 已全部用完，脚本停止")


def validate_redeem_code(code: str, proxies: Any = None) -> Dict[str, Any]:
    """请求兑换码校验接口；如未开卡则自动补全开卡流程。"""
    try:
        data = fetch_validate_payload(code, proxies)

        formatted_text = format_validate_response(data)
        result = {
            "requested_code": code,
            "status_code": 200,
            "response": data,
            "formatted_text": formatted_text,
        }
        if formatted_text:
            log_ok(f"卡信息 {formatted_text}")
        else:
            log_info(f"validate 接口结果: {json.dumps(result, ensure_ascii=False)}")
        return result
    except Exception as e:
        result = {
            "requested_code": code,
            "status_code": 0,
            "response": {"error": str(e)},
            "formatted_text": "",
        }
        log_error(f"validate 接口请求失败: {json.dumps(result, ensure_ascii=False)}")
        return result


def fetch_validate_payload(code: str, proxies: Any = None) -> Dict[str, Any]:
    """获取最终可用的卡片数据；未开卡时自动执行 redeem + task-status 轮询。"""
    validate_data = request_validate(code, proxies)
    if has_cards(validate_data):
        return validate_data

    validate_payload = validate_data.get("data") if isinstance(validate_data, dict) else {}
    if isinstance(validate_payload, dict) and validate_payload.get("valid") is True:
        redeem_data = request_redeem(code, proxies)
        if has_cards(redeem_data):
            return redeem_data

        redeem_payload = redeem_data.get("data") if isinstance(redeem_data, dict) else {}
        task_id = str((redeem_payload or {}).get("taskId") or "").strip()
        if not task_id:
            raise RuntimeError("redeem 成功但未返回 taskId")
        return wait_for_redeem_task(task_id, proxies)

    return validate_data


def request_validate(code: str, proxies: Any = None) -> Dict[str, Any]:
    """请求 validate 接口。"""
    redeem_base_url = str(CONFIG.get("redeem_base_url") or DEFAULT_CONFIG["redeem_base_url"]).rstrip("/")
    resp = requests.get(
        f"{redeem_base_url}/shop/shop/redeem/validate",
        params={"code": code},
        headers=VALIDATE_HEADERS,
        proxies=proxies,
        impersonate="chrome",
        timeout=20,
    )
    content_type = str(resp.headers.get("content-type", "")).lower()
    data: Any
    if "application/json" in content_type:
        data = resp.json()
    else:
        data = {"raw_text": resp.text}
    if resp.status_code != 200:
        raise RuntimeError(f"validate 请求失败: {resp.status_code}")
    if not isinstance(data, dict):
        raise RuntimeError("validate 返回不是 JSON 对象")
    payload = data.get("data") if isinstance(data, dict) else {}
    if isinstance(payload, dict):
        if has_cards(data):
            log_ok("validate 已返回卡信息")
        elif payload.get("valid") is True:
            log_info("validate 显示兑换码有效，准备开卡")
    return data


def request_redeem(code: str, proxies: Any = None) -> Dict[str, Any]:
    """请求 redeem 开卡。"""
    redeem_base_url = str(CONFIG.get("redeem_base_url") or DEFAULT_CONFIG["redeem_base_url"]).rstrip("/")
    headers = dict(VALIDATE_HEADERS)
    headers["content-type"] = "application/json"
    headers["origin"] = redeem_base_url
    visitor_id = f"visitor_{int(time.time() * 1000)}_{secrets.token_hex(4)}"
    resp = requests.post(
        f"{redeem_base_url}/shop/shop/redeem",
        headers=headers,
        json={
            "code": code,
            "contactEmail": "",
            "visitorId": visitor_id,
            "quantity": 1,
        },
        proxies=proxies,
        impersonate="chrome",
        timeout=20,
    )
    content_type = str(resp.headers.get("content-type", "")).lower()
    data: Any
    if "application/json" in content_type:
        data = resp.json()
    else:
        data = {"raw_text": resp.text}
    if resp.status_code != 200:
        raise RuntimeError(f"redeem 请求失败: {resp.status_code}")
    if not isinstance(data, dict):
        raise RuntimeError("redeem 返回不是 JSON 对象")
    payload = data.get("data") if isinstance(data, dict) else {}
    if isinstance(payload, dict):
        task_id = str(payload.get("taskId") or "").strip()
        order_no = str(payload.get("orderNo") or "").strip()
        log_info(f"redeem 已提交，orderNo={order_no} taskId={task_id}")
    return data


def request_redeem_task_status(task_id: str, proxies: Any = None) -> Dict[str, Any]:
    """查询 redeem task-status。"""
    redeem_base_url = str(CONFIG.get("redeem_base_url") or DEFAULT_CONFIG["redeem_base_url"]).rstrip("/")
    resp = requests.get(
        f"{redeem_base_url}/shop/shop/redeem/task-status/{task_id}",
        headers=VALIDATE_HEADERS,
        proxies=proxies,
        impersonate="chrome",
        timeout=20,
    )
    content_type = str(resp.headers.get("content-type", "")).lower()
    data: Any
    if "application/json" in content_type:
        data = resp.json()
    else:
        data = {"raw_text": resp.text}
    if resp.status_code != 200:
        raise RuntimeError(f"task-status 请求失败: {resp.status_code}")
    if not isinstance(data, dict):
        raise RuntimeError("task-status 返回不是 JSON 对象")
    return data


def wait_for_redeem_task(task_id: str, proxies: Any = None, retry_interval: int = 3) -> Dict[str, Any]:
    """轮询 task-status，直到拿到卡片。"""
    while True:
        task_data = request_redeem_task_status(task_id, proxies)
        if has_cards(task_data):
            return task_data

        payload = task_data.get("data") if isinstance(task_data, dict) else {}
        status = (payload or {}).get("status") if isinstance(payload, dict) else None
        progress = str((payload or {}).get("progress") or "").strip()
        if status == 2:
            return task_data
        if progress:
            log_info(f"开卡进行中: {progress}")
        time.sleep(retry_interval)


def has_cards(response_data: Any) -> bool:
    """判断响应中是否已经有卡片数据。"""
    if not isinstance(response_data, dict):
        return False
    data = response_data.get("data")
    if not isinstance(data, dict):
        return False
    cards = data.get("cards")
    return isinstance(cards, list) and len(cards) > 0


def is_exhausted_validate_response(response_data: Any) -> bool:
    """判断兑换码是否已使用完，需要切换下一张卡。"""
    if not isinstance(response_data, dict):
        return False
    data = response_data.get("data")
    if not isinstance(data, dict):
        return False

    message = str(data.get("message") or "").strip()
    remaining_quantity = data.get("remainingQuantity")
    is_used = data.get("isUsed")
    valid = data.get("valid")

    if "该兑换码已使用完" in message:
        return True
    if remaining_quantity == 0 and is_used is True:
        return True
    if valid is False and not has_cards(response_data):
        return True
    return False


def format_validate_response(response_data: Any) -> str:
    """将 validate 接口返回格式化为单行卡片信息。"""
    if not isinstance(response_data, dict):
        return ""

    data = response_data.get("data")
    if not isinstance(data, dict):
        return ""

    cards = data.get("cards")
    if not isinstance(cards, list) or not cards:
        return ""

    card = cards[0]
    if not isinstance(card, dict):
        return ""

    card_number = str(card.get("cardNumber") or "").strip()
    card_password = str(card.get("cardPassword") or "").strip()

    card_data_raw = card.get("cardData")
    card_data: Dict[str, Any] = {}
    if isinstance(card_data_raw, str) and card_data_raw.strip():
        try:
            parsed = json.loads(card_data_raw)
            if isinstance(parsed, dict):
                card_data = parsed
        except Exception:
            card_data = {}

    expiry = str(card_data.get("expiry") or "").strip()
    expiry_display = expiry
    if len(expiry) == 4 and expiry.isdigit():
        expiry_display = f"{expiry[:2]}/{expiry[2:]}"

    template = str(data.get("cardTemplate") or "").strip()
    address_text = ""
    if template:
        lines = [line.strip() for line in template.splitlines() if line.strip()]
        address = ""
        city = ""
        state = ""
        zipcode = ""
        country = ""
        for line in lines:
            if line.startswith("地址 "):
                address = line.replace("地址 ", "", 1).replace(",", ", ")
            elif line.startswith("城市 "):
                city = line.replace("城市 ", "", 1)
            elif line.startswith("州 "):
                state = line.replace("州 ", "", 1)
            elif line.startswith("邮编 "):
                zipcode = line.replace("邮编 ", "", 1)
            elif line.startswith("国家 "):
                country = line.replace("国家 ", "", 1)
        address_parts = [part for part in [address, city, state, zipcode, country] if part]
        address_text = ", ".join(address_parts)

    parts = [part for part in [card_number, expiry_display, card_password, address_text] if part]
    return " ".join(parts)


def wait_for_validate_result(code: str, proxies: Any = None, retry_interval: int = 5) -> Dict[str, Any]:
    """阻塞等待，直到 validate 接口返回 200。"""
    while True:
        result = validate_redeem_code(code, proxies)
        if result.get("status_code") == 200:
            return result
        log_warn(f"validate 失败，{retry_interval} 秒后重试")
        time.sleep(retry_interval)


def get_validate_context(proxies: Any = None) -> Dict[str, Any]:
    """根据 code.txt 中的 use 计数获取本轮要使用的 validate 结果。"""
    while True:
        code_value, code_array, code_index = wait_for_next_unused_code()
        item = code_array[code_index]
        use_count = _normalize_use_count(item.get("use"))
        result_map = load_code_result_map()
        last_result = result_map.get(code_value)

        if use_count == 0:
            if is_ready_validate_result(last_result):
                validate_result = last_result
            else:
                validate_result = wait_for_validate_result(code_value, proxies)
                save_code_result(code_value, validate_result)
        elif use_count == 1 and is_ready_validate_result(last_result):
            validate_result = last_result
            formatted_text = str(validate_result.get("formatted_text") or "").strip()
            if formatted_text:
                log_info(f"第二次复用当前 code 的 validate 结果: {formatted_text}")
            else:
                log_info(f"第二次复用当前 code 的 validate 结果: {json.dumps(validate_result, ensure_ascii=False)}")
        elif use_count == 1:
            log_warn("当前 code 缺少可复用的 validate 结果，重新请求 validate")
            validate_result = wait_for_validate_result(code_value, proxies)
            save_code_result(code_value, validate_result)
        else:
            item["use"] = 2
            save_code_array(code_array)
            log_info("当前 code 已达到最大使用次数，切换下一条")
            continue

        if is_exhausted_validate_response(validate_result.get("response")):
            item["use"] = 2
            save_code_array(code_array)
            log_warn(f"当前兑换码 {code_value} 已使用完，切换下一张卡")
            continue

        return {
            "code": code_value,
            "use_count": use_count,
            "code_array": code_array,
            "code_index": code_index,
            "validate_result": validate_result,
        }


def mark_code_used(code_array: list[dict[str, Any]], code_index: int, use_count: int) -> None:
    """在 subscribe 成功后递增当前 code 的 use 计数。"""
    code_array[code_index]["use"] = min(use_count + 1, 2)
    save_code_array(code_array)


def print_run_summary(
    *,
    registered_accounts: int,
    aisub_uses: int,
    cards_used: int,
    mother_accounts: int,
) -> None:
    """打印本次运行汇总。"""
    aisub_points = aisub_uses * 30
    child_accounts = mother_accounts * 5
    log_section("本次运行汇总")
    log_ok(f"注册了 {registered_accounts} 个号")
    log_ok(f"使用了 AISub {aisub_uses} 次")
    log_ok(f"使用了 AISub {aisub_points} 积分")
    log_ok(f"使用了 {cards_used} 张卡")
    log_ok(f"绑定成了 {mother_accounts} 个母号")
    log_ok(f"生成了 {child_accounts} 个子号")


def should_stop_for_target(
    *,
    registered_accounts: int,
    mother_accounts: int,
) -> bool:
    """根据配置的目标类型和数量决定是否停止。"""
    target_type = str(CONFIG.get("target_type") or DEFAULT_CONFIG["target_type"]).strip()
    try:
        target_value = int(CONFIG.get("target_value") or DEFAULT_CONFIG["target_value"])
    except (TypeError, ValueError):
        target_value = 0

    if target_value <= 0:
        return False

    current_value = 0
    target_label = ""
    if target_type == "register_count":
        current_value = registered_accounts
        target_label = "注册次数"
    elif target_type == "child_count":
        current_value = mother_accounts * 5
        target_label = "子号数"
    else:
        current_value = mother_accounts
        target_label = "母号数"

    if current_value >= target_value:
        log_info(f"已达到目标{target_label} {target_value}，脚本停止")
        return True
    return False


def subscribe_aisub(access_token: str, validate_result: Dict[str, Any], proxies: Any = None) -> Dict[str, Any]:
    """调用 AISub subscribe 接口。"""
    card_payload = str(validate_result.get("formatted_text") or "").strip()
    if not card_payload:
        card_payload = json.dumps(validate_result, ensure_ascii=False)
    log_info(f"AISub card 参数: {card_payload}")

    headers = dict(AISUB_HEADERS)
    headers["Content-Type"] = "application/json"

    try:
        aisub_base_url = str(CONFIG.get("aisub_base_url") or DEFAULT_CONFIG["aisub_base_url"]).rstrip("/")
        resp = requests.post(
            f"{aisub_base_url}/api/v1/subscribe",
            headers=headers,
            json={
                "access_token": access_token,
                "card": card_payload,
                "plan": str(CONFIG.get("subscribe_plan") or DEFAULT_CONFIG["subscribe_plan"]),
            },
            proxies=proxies,
            impersonate="chrome",
            timeout=20,
        )
        data: Any = resp.json() if resp.status_code == 200 else {"error": resp.text}
        result = {
            "status_code": resp.status_code,
            "response": data,
        }
        log_info(f"AISub subscribe 返回: {json.dumps(result, ensure_ascii=False)}")
        return result
    except Exception as e:
        result = {
            "status_code": 0,
            "response": {"success": False, "error": str(e)},
        }
        log_error(f"AISub subscribe 请求失败: {json.dumps(result, ensure_ascii=False)}")
        return result


def wait_for_subscribe_success(
    access_token: str,
    validate_result: Dict[str, Any],
    proxies: Any = None,
    retry_interval: int = 10,
) -> Dict[str, Any]:
    """阻塞等待 subscribe 成功。"""
    while True:
        subscribe_result = subscribe_aisub(access_token, validate_result, proxies)
        response_data = subscribe_result.get("response") or {}
        error_message = ""
        if isinstance(response_data, dict):
            error_message = str(response_data.get("error") or "").strip()
        if subscribe_result.get("status_code") == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
            return subscribe_result
        if "该账号需要额外验证（3DS）" in error_message:
            raise RetryWithNewAccount("该账号需要额外验证（3DS），切换下一个账号继续复用当前卡")
        log_warn(f"subscribe 未成功，{retry_interval} 秒后重试")
        time.sleep(retry_interval)


def _post_form(url: str, data: Dict[str, str], timeout: int = 30) -> Dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if resp.status != 200:
                raise RuntimeError(
                    f"token exchange failed: {resp.status}: {raw.decode('utf-8', 'replace')}"
                )
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        raise RuntimeError(
            f"token exchange failed: {exc.code}: {raw.decode('utf-8', 'replace')}"
        ) from exc


@dataclass(frozen=True)
class OAuthStart:
    auth_url: str
    state: str
    code_verifier: str
    redirect_uri: str


def generate_oauth_url(
    *, redirect_uri: str = DEFAULT_REDIRECT_URI, scope: str = DEFAULT_SCOPE
) -> OAuthStart:
    state = _random_state()
    code_verifier = _pkce_verifier()
    code_challenge = _sha256_b64url_no_pad(code_verifier)

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "login",
        "id_token_add_organizations": "true",
        "codex_cli_simplified_flow": "true",
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return OAuthStart(
        auth_url=auth_url,
        state=state,
        code_verifier=code_verifier,
        redirect_uri=redirect_uri,
    )


def submit_callback_url(
    *,
    callback_url: str,
    expected_state: str,
    code_verifier: str,
    redirect_uri: str = DEFAULT_REDIRECT_URI,
) -> str:
    cb = _parse_callback_url(callback_url)
    if cb["error"]:
        desc = cb["error_description"]
        raise RuntimeError(f"oauth error: {cb['error']}: {desc}".strip())

    if not cb["code"]:
        raise ValueError("callback url missing ?code=")
    if not cb["state"]:
        raise ValueError("callback url missing ?state=")
    if cb["state"] != expected_state:
        raise ValueError("state mismatch")

    token_resp = _post_form(
        TOKEN_URL,
        {
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code": cb["code"],
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        },
    )

    access_token = (token_resp.get("access_token") or "").strip()
    refresh_token = (token_resp.get("refresh_token") or "").strip()
    id_token = (token_resp.get("id_token") or "").strip()
    expires_in = _to_int(token_resp.get("expires_in"))

    claims = _jwt_claims_no_verify(id_token)
    email = str(claims.get("email") or "").strip()
    auth_claims = claims.get("https://api.openai.com/auth") or {}
    account_id = str(auth_claims.get("chatgpt_account_id") or "").strip()

    now = int(time.time())
    expired_rfc3339 = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime(now + max(expires_in, 0))
    )
    now_rfc3339 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))

    config = {
        "id_token": id_token,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "account_id": account_id,
        "last_refresh": now_rfc3339,
        "email": email,
        "type": "codex",
        "expired": expired_rfc3339,
    }

    return json.dumps(config, ensure_ascii=False, separators=(",", ":"))


# ==========================================
# 核心注册逻辑
# ==========================================


def run(proxy: Optional[str]) -> Optional[str]:
    proxies: Any = None
    if proxy:
        proxies = {"http": proxy, "https": proxy}

    s = requests.Session(proxies=proxies, impersonate="chrome")

    try:
        trace = s.get("https://cloudflare.com/cdn-cgi/trace", timeout=10)
        trace = trace.text
        loc_re = re.search(r"^loc=(.+)$", trace, re.MULTILINE)
        loc = loc_re.group(1) if loc_re else None
        print(f"[*] 当前 IP 所在地: {loc}")
        if loc == "CN" or loc == "HK":
            raise RuntimeError("检查代理哦w - 所在地不支持")
    except Exception as e:
        log_error(f"网络连接检查失败: {e}")
        return None

    email, dev_token = get_email_and_token(proxies)
    if not email or not dev_token:
        return None
    log_ok(f"成功获取 Tempmail.lol 邮箱与授权: {email}")

    oauth = generate_oauth_url()
    url = oauth.auth_url

    try:
        resp = s.get(url, timeout=15)
        did = s.cookies.get("oai-did")
        print(f"[*] Device ID: {did}")

        signup_body = f'{{"username":{{"value":"{email}","kind":"email"}},"screen_hint":"signup"}}'
        sen_req_body = f'{{"p":"","id":"{did}","flow":"authorize_continue"}}'

        sen_resp = requests.post(
            "https://sentinel.openai.com/backend-api/sentinel/req",
            headers={
                "origin": "https://sentinel.openai.com",
                "referer": "https://sentinel.openai.com/backend-api/sentinel/frame.html?sv=20260219f9f6",
                "content-type": "text/plain;charset=UTF-8",
            },
            data=sen_req_body,
            proxies=proxies,
            impersonate="chrome",
            timeout=15,
        )

        if sen_resp.status_code != 200:
            log_error(f"Sentinel 异常拦截，状态码: {sen_resp.status_code}")
            return None

        sen_token = sen_resp.json()["token"]
        sentinel = f'{{"p": "", "t": "", "c": "{sen_token}", "id": "{did}", "flow": "authorize_continue"}}'

        signup_resp = s.post(
            "https://auth.openai.com/api/accounts/authorize/continue",
            headers={
                "referer": "https://auth.openai.com/create-account",
                "accept": "application/json",
                "content-type": "application/json",
                "openai-sentinel-token": sentinel,
            },
            data=signup_body,
        )
        log_info(f"提交注册表单状态: {signup_resp.status_code}")

        # 生成密码
        password = _generate_password()
        log_info(f"生成密码: {password}")

        # 提交密码和邮箱
        register_body = json.dumps({
            "password": password,
            "username": email
        })

        pwd_resp = s.post(
            "https://auth.openai.com/api/accounts/user/register",
            headers={
                "referer": "https://auth.openai.com/create-account/password",
                "accept": "application/json",
                "content-type": "application/json",
            },
            data=register_body,
        )
        log_info(f"提交密码状态: {pwd_resp.status_code}")

        # 发送邮箱验证码
        otp_resp = s.get(
            "https://auth.openai.com/api/accounts/email-otp/send",
            headers={
                "referer": "https://auth.openai.com/create-account/password",
                "accept": "application/json",
            },
        )
        log_info(f"验证码发送状态: {otp_resp.status_code}")

        code = get_oai_code(dev_token, email, proxies)
        if not code:
            return None

        code_body = f'{{"code":"{code}"}}'
        code_resp = s.post(
            "https://auth.openai.com/api/accounts/email-otp/validate",
            headers={
                "referer": "https://auth.openai.com/email-verification",
                "accept": "application/json",
                "content-type": "application/json",
            },
            data=code_body,
        )
        log_info(f"验证码校验状态: {code_resp.status_code}")

        create_account_body = '{"name":"Neo","birthdate":"2000-02-20"}'
        create_account_resp = s.post(
            "https://auth.openai.com/api/accounts/create_account",
            headers={
                "referer": "https://auth.openai.com/about-you",
                "accept": "application/json",
                "content-type": "application/json",
            },
            data=create_account_body,
        )
        create_account_status = create_account_resp.status_code
        log_info(f"账户创建状态: {create_account_status}")

        if create_account_status != 200:
            print(create_account_resp.text)
            return None

        auth_cookie = s.cookies.get("oai-client-auth-session")
        if not auth_cookie:
            log_error("未能获取到授权 Cookie")
            return None

        auth_json = _decode_jwt_segment(auth_cookie.split(".")[0])
        workspaces = auth_json.get("workspaces") or []
        if not workspaces:
            log_error("授权 Cookie 里没有 workspace 信息")
            return None
        workspace_id = str((workspaces[0] or {}).get("id") or "").strip()
        if not workspace_id:
            log_error("无法解析 workspace_id")
            return None

        select_body = f'{{"workspace_id":"{workspace_id}"}}'
        select_resp = s.post(
            "https://auth.openai.com/api/accounts/workspace/select",
            headers={
                "referer": "https://auth.openai.com/sign-in-with-chatgpt/codex/consent",
                "content-type": "application/json",
            },
            data=select_body,
        )

        if select_resp.status_code != 200:
            log_error(f"选择 workspace 失败，状态码: {select_resp.status_code}")
            print(select_resp.text)
            return None

        continue_url = str((select_resp.json() or {}).get("continue_url") or "").strip()
        if not continue_url:
            log_error("workspace/select 响应里缺少 continue_url")
            return None

        current_url = continue_url
        for _ in range(6):
            final_resp = s.get(current_url, allow_redirects=False, timeout=15)
            location = final_resp.headers.get("Location") or ""

            if final_resp.status_code not in [301, 302, 303, 307, 308]:
                break
            if not location:
                break

            next_url = urllib.parse.urljoin(current_url, location)
            if "code=" in next_url and "state=" in next_url:
                return submit_callback_url(
                    callback_url=next_url,
                    code_verifier=oauth.code_verifier,
                    redirect_uri=oauth.redirect_uri,
                    expected_state=oauth.state,
                )
            current_url = next_url

        log_error("未能在重定向链中捕获到最终 Callback URL")
        return None

    except Exception as e:
        log_error(f"运行时发生错误: {e}")
        return None


def main() -> None:
    global CURRENT_OUTPUT_DIR
    parser = argparse.ArgumentParser(description="OpenAI 自动注册脚本 (Tempmail.lol 版本)")
    parser.add_argument(
        "--proxy", default=None, help="代理地址，如 http://127.0.0.1:7890"
    )
    parser.add_argument("--once", action="store_true", help="只运行一次")
    parser.add_argument(
        "--sleep-min",
        type=int,
        default=int(CONFIG.get("default_sleep_min") or DEFAULT_CONFIG["default_sleep_min"]),
        help="循环模式最短等待秒数",
    )
    parser.add_argument(
        "--sleep-max",
        type=int,
        default=int(CONFIG.get("default_sleep_max") or DEFAULT_CONFIG["default_sleep_max"]),
        help="循环模式最长等待秒数",
    )
    args = parser.parse_args()

    sleep_min = max(1, args.sleep_min)
    sleep_max = max(sleep_min, args.sleep_max)
    proxies: Any = None
    proxy_value = args.proxy or str(CONFIG.get("default_proxy") or "").strip() or None
    if proxy_value:
        proxies = {"http": proxy_value, "https": proxy_value}
    output_dir = create_run_output_dir()
    CURRENT_OUTPUT_DIR = output_dir
    teams_file = _teams_file_path()
    registered_accounts = 0
    aisub_uses = 0
    cards_used = 0
    mother_accounts = 0

    count = 0
    log_section("OpenAI Auto Registrar")
    log_info("Yasal's Seamless OpenAI Auto-Registrar Started for ZJH (Tempmail.lol Edition)")
    log_info(f"本次账号输出目录: {output_dir}")
    sync_code_file_from_cdkeys()
    try:
        ensure_aisub_balance(proxies)

        while True:
            count += 1
            log_section(f"开始第 {count} 次注册流程")

            try:
                ensure_aisub_balance(proxies)
                validate_context = get_validate_context(proxies)
                validate_result = validate_context["validate_result"]

                token_json = run(proxy_value)

                if token_json:
                    registered_accounts += 1
                    try:
                        t_data = json.loads(token_json)
                        fname_email = t_data.get("email", "unknown").replace("@", "_")
                    except Exception:
                        t_data = {}
                        fname_email = "unknown"

                    access_token = str(t_data.get("access_token") or "").strip()
                    if not access_token:
                        raise RuntimeError("token_json 中缺少 access_token")

                    subscribe_result = wait_for_subscribe_success(access_token, validate_result, proxies)
                    current_use_count = int(validate_context["use_count"])
                    mark_code_used(
                        validate_context["code_array"],
                        int(validate_context["code_index"]),
                        current_use_count,
                    )
                    aisub_uses += 1
                    if current_use_count == 0:
                        cards_used += 1

                    t_data["validate_result"] = validate_result
                    t_data["subscribe_result"] = subscribe_result

                    file_name = f"token_{fname_email}_{int(time.time())}.json"
                    file_path = os.path.join(output_dir, file_name)

                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(t_data, f, ensure_ascii=False, indent=2)
                    append_team_entry(teams_file, t_data)
                    mother_accounts += 1

                    log_ok(f"成功! Token 已保存至: {file_path}")
                    if should_stop_for_target(
                        registered_accounts=registered_accounts,
                        mother_accounts=mother_accounts,
                    ):
                        break
                else:
                    log_warn("本次注册失败")

            except RetryWithNewAccount as e:
                log_warn(str(e))
            except StopScript as e:
                log_warn(str(e))
                break
            except Exception as e:
                log_error(f"发生未捕获异常: {e}")

            if args.once:
                break

            wait_time = random.randint(sleep_min, sleep_max)
            log_info(f"休息 {wait_time} 秒")
            time.sleep(wait_time)
    finally:
        print_run_summary(
            registered_accounts=registered_accounts,
            aisub_uses=aisub_uses,
            cards_used=cards_used,
            mother_accounts=mother_accounts,
        )


if __name__ == "__main__":
    main()
