import json
import os
import re
import sys
import time
import ast
import math
import random
import string
import secrets
import hashlib
import base64
import threading
import argparse
import importlib.util
import pprint
import tty
import termios
import unicodedata
import html
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, quote
from dataclasses import dataclass
from typing import Any, Dict, Optional
import urllib.parse
import urllib.request
import urllib.error

from curl_cffi import requests

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except Exception:
    Console = None
    Panel = None
    Table = None
    Text = None
    RICH_AVAILABLE = False

# ==========================================
# Tempmail.lol API (v2)/叫我小杨同学 Linuxdo
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
CONFIG_PY_PATH = os.path.join(CONFIG_DIR, "config.py")
DEFAULT_CONFIG: Dict[str, Any] = {
    "cdkey_file": "config/cdkeys.json",
    "code_file": "config/redeem_codes.json",
    "code_results_file": "code_results.json",
    "teams_file": "data/team_accounts.json",
    "output_root": "",
    "target_type": "mother_count",
    "target_value": 0,
    "tempmail_base": "https://api.tempmail.lol/v2",
    "tempmail_plus_api": "https://tempmail.plus/api",
    "npcmail_base": "https://dash.xphdfs.me",
    "gptmail_base": "https://mail.chatgpt.org.uk/api",
    "junmail_base": "https://mail.zhujunpeng.cc.cd",
    "tm_email_provider": "gptmail",
    "tm_npcmail_apikey": "",
    "gptmail_api_key": "gpt-test",
    "junmail_api_key": "",
    "register_type": "team",
    "tm_reg_prefix": "",
    "tm_reg_domain": "",
    "tm_local_email_file": "data/local_graph_accounts.txt",
    "tm_local_email_cursor": 0,
    "tm_use_cd": False,
    "tm_custom_domains": [],
    "tm_tm_addr": "",
    "tm_tm_epin": "",
    "redeem_base_url": "https://yyl.ncet.top",
    "aisub_base_url": "https://sub.zenscaleai.com",
    "aisub_api_key": "sk_c1561e264e8b0b164d737603e696cba53e0040cc64fec55c",
    "subscribe_plan": "team",
    "card_max_use_count": 2,
    "subscribe_retry_new_account_enabled": True,
    "subscribe_retry_new_account_limit": 50,
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
    if os.path.exists(CONFIG_PY_PATH):
        try:
            spec = importlib.util.spec_from_file_location("team_config", CONFIG_PY_PATH)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                data = getattr(module, "CONFIG", None)
                if isinstance(data, dict):
                    config.update(data)
                    return config
        except Exception:
            return config
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


def save_config() -> None:
    config_dir = os.path.dirname(CONFIG_PY_PATH)
    os.makedirs(config_dir, exist_ok=True)
    with open(CONFIG_PY_PATH, "w", encoding="utf-8") as f:
        f.write("CONFIG = ")
        f.write(pprint.pformat(CONFIG, sort_dicts=False, width=100))
        f.write("\n")


CONFIG = load_config()
TEMPMAIL_BASE = str(CONFIG.get("tempmail_base") or DEFAULT_CONFIG["tempmail_base"]).strip()
TEMPMAIL_PLUS_API = str(CONFIG.get("tempmail_plus_api") or DEFAULT_CONFIG["tempmail_plus_api"]).strip()
NPCMAIL_BASE = str(CONFIG.get("npcmail_base") or DEFAULT_CONFIG["npcmail_base"]).strip().rstrip("/")
GPTMAIL_BASE = str(CONFIG.get("gptmail_base") or DEFAULT_CONFIG["gptmail_base"]).strip().rstrip("/")
CURRENT_OUTPUT_DIR = ""

FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
    "Thomas", "Charles", "Mary", "Patricia", "Jennifer", "Linda", "Barbara",
    "Elizabeth", "Susan", "Jessica", "Sarah", "Karen", "Emma", "Olivia", "Ava",
    "Sophia", "Isabella", "Liam", "Noah", "Oliver", "Elijah", "Lucas",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
    "Harris", "Clark",
]
STARTUP_BANNER = r"""
    _    _   _ _____ ___    _____ _____    _    __  __ 
   / \  | | | |_   _/ _ \  |_   _| ____|  / \  |  \/  |
  / _ \ | | | | | || | | |   | | |  _|   / _ \ | |\/| |
 / ___ \| |_| | | || |_| |   | | | |___ / ___ \| |  | |
/_/   \_\\___/  |_| \___/    |_| |_____/_/   \_\_|  |_|
"""
ANSI_RESET = "\033[0m"
ANSI_DIM = "\033[2m"
ANSI_BOLD = "\033[1m"
ANSI_MENU = "\033[38;5;110m"
MENU_OPTIONS = ["开始运行", "注册类型", "生成账户数", "配置中心", "退出程序"]
CONSOLE = Console() if RICH_AVAILABLE else None

LOG_STYLES = {
    "INFO": "bold cyan",
    " OK ": "bold green",
    "WARN": "bold yellow",
    "ERR ": "bold red",
}

EMAIL_PROVIDER_LABELS: Dict[str, str] = {
    "npcmail": "NPCMail",
    "gptmail": "GPTMail",
    "junmail": "JunMail",
    "xiaomajiang": "临时邮箱(仅可做测试使用,封号严重)",
    "local_graph": "本地Outlook邮箱",
    "tempmail": "TempMail",
}

REGISTER_TYPE_LABELS: Dict[str, str] = {
    "normal": "普号",
    "team": "Team",
}


def _now_hms() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _fmt_local_dt(dt: datetime) -> str:
    return dt.strftime("%Y年%-m月%-d日%H:%M:%S") if os.name != "nt" else dt.strftime("%Y年%m月%d日%H:%M:%S")


def _fmt_duration(total_seconds: float) -> str:
    seconds = max(0, int(total_seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}小时{minutes}分{secs}秒"
    if minutes > 0:
        return f"{minutes}分{secs}秒"
    return f"{secs}秒"


def log_line(tag: str, message: str) -> None:
    line = f"[{_now_hms()}] {tag} {message}"
    if RICH_AVAILABLE and CONSOLE:
        style = LOG_STYLES.get(tag, "white")
        CONSOLE.print(f"[dim][{_now_hms()}][/dim] ", end="")
        CONSOLE.print(f"[{style}]{tag}[/] {message}")
        return
    print(line)


def log_info(message: str) -> None:
    log_line("INFO", message)


def log_ok(message: str) -> None:
    log_line(" OK ", message)


def log_warn(message: str) -> None:
    log_line("WARN", message)


def log_error(message: str) -> None:
    log_line("ERR ", message)


def log_section(title: str) -> None:
    if RICH_AVAILABLE and CONSOLE:
        CONSOLE.rule(f"[bold cyan]{title}[/bold cyan]")
        return
    bar = "=" * 18
    print(f"\n{bar} {title} {bar}")


def _request_json(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Any = None,
    data: Any = None,
    proxies: Any = None,
    timeout: int = 15,
) -> Any:
    resp = requests.request(
        method=method,
        url=url,
        headers=headers,
        params=params,
        json=json_body,
        data=data,
        proxies=proxies,
        impersonate="chrome",
        timeout=timeout,
    )
    try:
        payload = resp.json()
    except Exception as exc:
        raise RuntimeError(f"响应解析失败: HTTP {resp.status_code}") from exc
    if resp.status_code < 200 or resp.status_code >= 300:
        if isinstance(payload, dict):
            detail = payload.get("error") or payload.get("message") or payload.get("detail")
        else:
            detail = None
        raise RuntimeError(str(detail or f"HTTP {resp.status_code}"))
    return payload


def _email_provider_label(provider: Any) -> str:
    key = str(provider or "").strip().lower()
    return EMAIL_PROVIDER_LABELS.get(key, str(provider or "").strip() or "未知")


def _register_type_key(value: Any = None) -> str:
    key = str(CONFIG.get("register_type") if value is None else value or "").strip().lower()
    if key not in REGISTER_TYPE_LABELS:
        return "team"
    return key


def _register_type_label(value: Any = None) -> str:
    key = _register_type_key(value)
    return REGISTER_TYPE_LABELS.get(key, "Team")


def _extract_verification_code(content: str) -> str:
    text = str(content or "")
    match = re.search(r"\b(\d{6})\b", text)
    if match:
        return match.group(1)
    match = re.search(r"\b(\d{4,8})\b", text)
    if match:
        return match.group(1)
    return ""


def _strip_html(text: str) -> str:
    raw = str(text or "")
    if not raw:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", raw)
    cleaned = html.unescape(cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _collect_text_fragments(value: Any, depth: int = 0, limit: int = 80) -> list[str]:
    if value is None or limit <= 0 or depth > 4:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, (int, float, bool)):
        return [str(value)]

    fragments: list[str] = []
    if isinstance(value, dict):
        preferred_keys = (
            "subject",
            "from",
            "sender",
            "address",
            "full_address",
            "text",
            "plain",
            "plain_text",
            "body",
            "body_text",
            "body_plain",
            "bodyPreview",
            "content",
            "html",
            "html_content",
            "snippet",
            "intro",
            "preview",
            "raw",
            "source",
            "data",
        )
        visited: set[str] = set()
        for key in preferred_keys:
            if key not in value:
                continue
            visited.add(key)
            fragments.extend(_collect_text_fragments(value.get(key), depth + 1, limit - len(fragments)))
            if len(fragments) >= limit:
                return fragments[:limit]
        for key, nested in value.items():
            if key in visited:
                continue
            fragments.extend(_collect_text_fragments(nested, depth + 1, limit - len(fragments)))
            if len(fragments) >= limit:
                break
        return fragments[:limit]

    if isinstance(value, list):
        for item in value[:20]:
            fragments.extend(_collect_text_fragments(item, depth + 1, limit - len(fragments)))
            if len(fragments) >= limit:
                break
        return fragments[:limit]

    return []


def _stringify_message_payload(payload: Any) -> str:
    fragments = _collect_text_fragments(payload)
    if not fragments:
        return ""
    return _strip_html(" ".join(fragments))


def _looks_like_openai_message(content: str) -> bool:
    lowered = str(content or "").lower()
    return "openai" in lowered or "chatgpt" in lowered


def _generate_password(length: int = 16) -> str:
    chars = string.ascii_letters + string.digits + "!@#$%"
    password_chars = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%"),
    ]
    while len(password_chars) < max(length, 4):
        password_chars.append(secrets.choice(chars))
    random.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def _generate_profile() -> Dict[str, Any]:
    current_year = datetime.now().year
    birth_year = current_year - 18 - random.randint(0, 29)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    return {
        "first_name": random.choice(FIRST_NAMES),
        "last_name": random.choice(LAST_NAMES),
        "birthdate": f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}",
    }


def _random_prefix(length: int = 12) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _load_custom_domains() -> list[str]:
    raw = CONFIG.get("tm_custom_domains", [])
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
        return [part.strip() for part in re.split(r"[\n,;]+", stripped) if part.strip()]
    return []


def _local_email_file_path() -> str:
    return _resolve_config_path(str(CONFIG.get("tm_local_email_file") or DEFAULT_CONFIG["tm_local_email_file"]))


def _parse_local_graph_account_line(line: str) -> Optional[Dict[str, Any]]:
    raw = str(line or "").strip()
    if not raw:
        return None
    parts = [part.strip() for part in raw.split("----")]
    if len(parts) < 4:
        return None
    account: Dict[str, Any] = {
        "email": parts[0],
        "email_password": parts[1],
        "client_id": parts[2],
        "refresh_token": parts[3],
    }
    if len(parts) >= 5 and parts[4]:
        expire_time_str = parts[4]
        for fmt in ("%Y年%m月%d日", "%Y-%m-%d"):
            try:
                account["refresh_expires_at"] = datetime.strptime(expire_time_str, fmt).timestamp()
                break
            except ValueError:
                continue
    return account


def _load_local_graph_accounts() -> list[Dict[str, Any]]:
    path = _local_email_file_path()
    if not os.path.exists(path):
        raise RuntimeError(f"本地邮箱文件不存在: {path}")
    accounts: list[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            parsed = _parse_local_graph_account_line(line)
            if parsed is None:
                if line.strip():
                    log_warn(f"跳过格式无效的本地邮箱账号，第 {line_no} 行")
                continue
            accounts.append(parsed)
    if not accounts:
        raise RuntimeError("本地邮箱文件中没有可用账号")
    return accounts


def _create_local_graph_mailbox_context() -> Dict[str, Any]:
    accounts = _load_local_graph_accounts()
    cursor = max(0, _to_int(CONFIG.get("tm_local_email_cursor")))
    index = cursor % len(accounts)
    selected = dict(accounts[index])
    CONFIG["tm_local_email_cursor"] = cursor + 1
    save_config()
    profile = _generate_profile()
    selected.update(
        {
            "email_provider": "local_graph",
            "custom_domain": False,
            "password": _generate_password(),
            **profile,
        }
    )
    return selected


def _refresh_graph_access_token(client_id: str, refresh_token: str, proxies: Any = None) -> str:
    if not client_id or not refresh_token:
        return ""
    resp = requests.post(
        "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": "https://graph.microsoft.com/.default",
        },
        proxies=proxies,
        impersonate="chrome",
        timeout=30,
    )
    if resp.status_code != 200:
        try:
            payload = resp.json()
        except Exception:
            payload = resp.text
        raise RuntimeError(f"Graph 刷新 access_token 失败: HTTP {resp.status_code} {payload}")
    try:
        payload = resp.json()
    except Exception as exc:
        raise RuntimeError("Graph access_token 响应解析失败") from exc
    return str(payload.get("access_token") or "").strip()


def _fetch_graph_mail_code(mailbox: Dict[str, Any], proxies: Any = None) -> str:
    client_id = str(mailbox.get("client_id") or "").strip()
    refresh_token = str(mailbox.get("refresh_token") or "").strip()
    access_token = str(mailbox.get("graph_access_token") or "").strip()
    if not access_token:
        access_token = _refresh_graph_access_token(client_id, refresh_token, proxies)
        mailbox["graph_access_token"] = access_token
    if not access_token:
        return ""

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    resp = requests.get(
        "https://graph.microsoft.com/v1.0/me/messages",
        headers=headers,
        params={
            "$top": 10,
            "$select": "id,subject,from,receivedDateTime,bodyPreview",
            "$orderby": "receivedDateTime desc",
        },
        proxies=proxies,
        impersonate="chrome",
        timeout=15,
    )
    if resp.status_code != 200:
        return ""
    try:
        payload = resp.json()
    except Exception:
        return ""
    messages = payload.get("value") if isinstance(payload, dict) else None
    if not isinstance(messages, list):
        return ""

    for message in messages:
        if not isinstance(message, dict):
            continue
        sender = str(message.get("from", {}).get("emailAddress", {}).get("address") or "")
        subject = str(message.get("subject") or "")
        preview = str(message.get("bodyPreview") or "")
        combined = " ".join([sender, subject, preview]).lower()
        if "openai" not in combined and "chatgpt" not in combined:
            continue

        detail_id = str(message.get("id") or "").strip()
        content = " ".join([subject, preview])
        if detail_id:
            detail_resp = requests.get(
                f"https://graph.microsoft.com/v1.0/me/messages/{quote(detail_id)}",
                headers=headers,
                params={"$select": "body,subject,from,bodyPreview"},
                proxies=proxies,
                impersonate="chrome",
                timeout=15,
            )
            if detail_resp.status_code == 200:
                try:
                    detail = detail_resp.json()
                except Exception:
                    detail = {}
                body = detail.get("body") if isinstance(detail, dict) else {}
                body_content = _strip_html((body or {}).get("content") or "")
                content = " ".join(
                    [
                        str((detail or {}).get("subject") or subject),
                        str((detail or {}).get("bodyPreview") or preview),
                        body_content,
                    ]
                )
        code = _extract_verification_code(content)
        if code:
            return code
    return ""


def _npcmail_request(method: str, endpoint: str, *, body: Any = None, proxies: Any = None) -> Any:
    api_key = str(CONFIG.get("tm_npcmail_apikey") or "").strip()
    if not api_key:
        raise RuntimeError("请先配置 NPCmail 密钥")
    return _request_json(
        method,
        f"{NPCMAIL_BASE}{endpoint}",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json_body=body,
        proxies=proxies,
    )


def _gptmail_request(method: str, endpoint: str, *, body: Any = None, proxies: Any = None) -> Any:
    api_key = str(CONFIG.get("gptmail_api_key") or "gpt-test").strip()
    if not api_key:
        raise RuntimeError("请先配置 GPTMail 密钥")
    payload = _request_json(
        method,
        f"{GPTMAIL_BASE}{endpoint}",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        json_body=body,
        proxies=proxies,
    )
    if not isinstance(payload, dict) or payload.get("success") is not True:
        detail = payload.get("error") if isinstance(payload, dict) else None
        raise RuntimeError(str(detail or "GPTMail 请求失败"))
    return payload.get("data")


def _junmail_headers() -> Dict[str, str]:
    api_key = str(CONFIG.get("junmail_api_key") or "").strip()
    if not api_key:
        raise RuntimeError("请先配置 JunMail API Key")
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _junmail_request(
    method: str,
    endpoint: str,
    *,
    body: Any = None,
    params: Optional[Dict[str, Any]] = None,
    proxies: Any = None,
) -> Any:
    base_url = str(CONFIG.get("junmail_base") or DEFAULT_CONFIG["junmail_base"]).strip().rstrip("/")
    if not base_url:
        raise RuntimeError("请先配置 JunMail Base URL")
    return _request_json(
        method,
        f"{base_url}{endpoint}",
        headers=_junmail_headers(),
        params=params,
        json_body=body,
        proxies=proxies,
    )


def _create_junmail_mailbox(address: str = "", domain: str = "", proxies: Any = None) -> Dict[str, str]:
    body: Dict[str, Any] = {}
    if address:
        body["address"] = address
    if domain:
        body["domain"] = domain
    payload = _junmail_request("POST", "/api/mailboxes", body=body, proxies=proxies)
    mailbox = payload.get("mailbox") if isinstance(payload, dict) else None
    if not isinstance(mailbox, dict):
        raise RuntimeError("JunMail 创建邮箱失败")
    mailbox_id = str(mailbox.get("id") or "").strip()
    full_address = str(mailbox.get("full_address") or mailbox.get("address") or "").strip()
    if not mailbox_id or not full_address:
        raise RuntimeError("JunMail 返回邮箱信息不完整")
    return {"mailbox_id": mailbox_id, "email": full_address}


def _fetch_junmail_code(mailbox_id: str, proxies: Any = None) -> str:
    if not mailbox_id:
        return ""
    payload = _junmail_request(
        "GET",
        f"/api/mailboxes/{quote(mailbox_id)}/emails",
        params={"page": 1, "size": 20},
        proxies=proxies,
    )
    messages = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(messages, list):
        return ""

    for message in messages:
        if not isinstance(message, dict):
            continue
        summary_content = _stringify_message_payload(message)
        code = _extract_verification_code(summary_content)
        if code and (len(code) == 6 or _looks_like_openai_message(summary_content)):
            return code
        email_id = str(message.get("id") or "").strip()
        if not email_id:
            continue
        detail = _junmail_request(
            "GET",
            f"/api/mailboxes/{quote(mailbox_id)}/emails/{quote(email_id)}",
            proxies=proxies,
        )
        detail_content = _stringify_message_payload(detail)
        code = _extract_verification_code(detail_content)
        if code and (len(code) == 6 or _looks_like_openai_message(detail_content)):
            return code
    return ""


def _tempmail_plus_request(endpoint: str, *, proxies: Any = None) -> Any:
    return _request_json(
        "GET",
        f"{TEMPMAIL_PLUS_API}{endpoint}",
        headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
        proxies=proxies,
    )


def _create_tempmail_lol_inbox(proxies: Any = None) -> Dict[str, str]:
    payload = _request_json(
        "POST",
        f"{TEMPMAIL_BASE}/inbox/create",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json_body={},
        proxies=proxies,
    )
    if not isinstance(payload, dict):
        raise RuntimeError("Tempmail.lol 创建邮箱失败")
    address = str(payload.get("address") or "").strip()
    token = str(payload.get("token") or "").strip()
    if not address or not token:
        raise RuntimeError("Tempmail.lol 返回邮箱或 token 为空")
    return {"email": address, "token": token}


def _fetch_tempmail_lol_code(token: str, proxies: Any = None) -> str:
    if not token:
        return ""
    payload = _request_json(
        "GET",
        f"{TEMPMAIL_BASE}/inbox?token={quote(token)}",
        headers={"Accept": "application/json"},
        proxies=proxies,
    )
    messages = payload.get("emails") if isinstance(payload, dict) else None
    if not isinstance(messages, list):
        return ""
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = " ".join(
            [
                str(message.get("from") or ""),
                str(message.get("subject") or ""),
                str(message.get("body") or ""),
                str(message.get("html") or ""),
            ]
        )
        if "openai" not in content.lower():
            continue
        code = _extract_verification_code(content)
        if code:
            return code
    return ""


def create_registration_email_context(proxies: Any = None) -> Dict[str, Any]:
    profile = _generate_profile()
    context: Dict[str, Any] = {
        "password": _generate_password(),
        **profile,
    }

    use_custom_domain = bool(CONFIG.get("tm_use_cd"))
    custom_domains = _load_custom_domains()
    reg_prefix = str(CONFIG.get("tm_reg_prefix") or "").strip()
    reg_domain = str(CONFIG.get("tm_reg_domain") or "").strip()

    if use_custom_domain and custom_domains:
        receiver_addr = str(CONFIG.get("tm_tm_addr") or "").strip()
        if not receiver_addr:
            raise RuntimeError("已启用自定义域名模式，但未配置 TempMail 取件邮箱")
        selected_domain = random.choice(custom_domains)
        prefix = reg_prefix or _random_prefix(12)
        context.update(
            {
                "email": f"{prefix}@{selected_domain}",
                "email_provider": "tempmail",
                "custom_domain": True,
                "tm_addr": receiver_addr,
                "tm_epin": str(CONFIG.get("tm_tm_epin") or "").strip(),
            }
        )
        return context

    provider = str(CONFIG.get("tm_email_provider") or "gptmail").strip().lower()
    if provider == "npcmail":
        body: Dict[str, Any] = {"count": 1, "expiryDays": 30}
        if reg_domain:
            body["domain"] = reg_domain
        if reg_prefix:
            body["prefix"] = reg_prefix
        payload = _npcmail_request("POST", "/api/public/batch-create-emails", body=body, proxies=proxies)
        emails = payload.get("emails") if isinstance(payload, dict) else None
        if not isinstance(emails, list) or not emails:
            raise RuntimeError("NPCmail 创建邮箱失败")
        email_obj = emails[0] if isinstance(emails[0], dict) else {}
        address = str(email_obj.get("address") or "").strip()
        if not address:
            raise RuntimeError("NPCmail 返回邮箱为空")
        context.update({"email": address, "email_provider": "npcmail", "custom_domain": False})
        return context

    if provider == "xiaomajiang":
        inbox = _create_tempmail_lol_inbox(proxies)
        context.update(
            {
                "email": inbox["email"],
                "email_provider": "xiaomajiang",
                "custom_domain": False,
                "tm_token": inbox["token"],
            }
        )
        return context

    if provider == "junmail":
        mailbox = _create_junmail_mailbox(reg_prefix, reg_domain, proxies)
        context.update(
            {
                "email": mailbox["email"],
                "email_provider": "junmail",
                "custom_domain": False,
                "junmail_mailbox_id": mailbox["mailbox_id"],
            }
        )
        return context

    if provider == "local_graph":
        return _create_local_graph_mailbox_context()

    body = {}
    if reg_prefix:
        body["prefix"] = reg_prefix
    if reg_domain:
        body["domain"] = reg_domain
    payload = _gptmail_request("POST" if body else "GET", "/generate-email", body=body or None, proxies=proxies)
    if not isinstance(payload, dict):
        raise RuntimeError("GPTMail 创建邮箱失败")
    address = str(payload.get("email") or "").strip()
    if not address:
        raise RuntimeError("GPTMail 返回邮箱为空")
    context.update({"email": address, "email_provider": "gptmail", "custom_domain": False})
    return context


def _fetch_gptmail_code(email: str, proxies: Any = None) -> str:
    payload = _gptmail_request("GET", f"/emails?email={quote(email)}", proxies=proxies)
    messages = payload if isinstance(payload, list) else payload.get("emails") if isinstance(payload, dict) else []
    if not isinstance(messages, list):
        return ""
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = " ".join(
            [
                str(message.get("content") or ""),
                str(message.get("html_content") or ""),
                str(message.get("subject") or ""),
            ]
        )
        code = _extract_verification_code(content)
        if code:
            return code
    return ""


def _fetch_npcmail_code(email: str, proxies: Any = None) -> str:
    payload = _npcmail_request(
        "POST",
        "/api/public/extract-codes",
        body={"addresses": [email]},
        proxies=proxies,
    )
    if isinstance(payload, list) and payload:
        first = payload[0] if isinstance(payload[0], dict) else {}
        return str(first.get("code") or "").strip()
    if isinstance(payload, dict):
        for key in ("codes", "data"):
            items = payload.get(key)
            if isinstance(items, list) and items:
                first = items[0] if isinstance(items[0], dict) else {}
                code = str(first.get("code") or "").strip()
                if code:
                    return code
    return ""


def _fetch_tempmail_plus_code(address: str, epin: str = "", proxies: Any = None) -> str:
    inbox = _tempmail_plus_request(f"/mails?email={quote(address)}&epin={quote(epin)}", proxies=proxies)
    mail_list = inbox.get("mail_list") if isinstance(inbox, dict) else None
    if not isinstance(mail_list, list) or not mail_list:
        return ""
    mail = mail_list[0] if isinstance(mail_list[0], dict) else {}
    mail_id = mail.get("mail_id")
    if not mail_id:
        return ""
    detail = _tempmail_plus_request(
        f"/mails/{mail_id}?email={quote(address)}&epin={quote(epin)}",
        proxies=proxies,
    )
    content = " ".join(
        [
            str(detail.get("text") or ""),
            str(detail.get("html") or ""),
            str(detail.get("subject") or mail.get("subject") or ""),
        ]
    )
    return _extract_verification_code(content)


def get_oai_code(mailbox: Dict[str, Any], proxies: Any = None) -> str:
    email = str(mailbox.get("email") or "").strip()
    provider = str(mailbox.get("email_provider") or "gptmail").strip().lower()
    receiver_addr = str(mailbox.get("tm_addr") or "").strip()
    receiver_epin = str(mailbox.get("tm_epin") or "").strip()
    tempmail_lol_token = str(mailbox.get("tm_token") or "").strip()

    log_info(f"等待验证码: {email}")
    for attempt in range(60):
        try:
            if mailbox.get("custom_domain") and receiver_addr:
                code = _fetch_tempmail_plus_code(receiver_addr, receiver_epin, proxies)
            elif provider == "npcmail":
                code = _fetch_npcmail_code(email, proxies)
            elif provider == "xiaomajiang":
                code = _fetch_tempmail_lol_code(tempmail_lol_token, proxies)
            elif provider == "junmail":
                code = _fetch_junmail_code(str(mailbox.get("junmail_mailbox_id") or "").strip(), proxies)
            elif provider == "local_graph":
                code = _fetch_graph_mail_code(mailbox, proxies)
            else:
                code = _fetch_gptmail_code(email, proxies)
            if code:
                log_ok(f"收到验证码: {code}")
                return code
        except Exception:
            pass
        if attempt < 59:
            time.sleep(3)
    log_warn("验证码超时")
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

def _aisub_headers() -> Dict[str, str]:
    api_key = str(CONFIG.get("aisub_api_key") or DEFAULT_CONFIG["aisub_api_key"]).strip()
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }


class RetryWithNewAccount(Exception):
    """当前账号不可用，需要换号重试。"""

    pass


class StopScript(Exception):
    """满足停止条件，结束脚本。"""

    pass


class SkipCurrentCode(Exception):
    """当前兑换码无法继续使用，需要跳过。"""

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


def load_code_array(quiet: bool = False) -> list[dict[str, Any]]:
    """读取 CDKEY 文件，兼容字符串数组、对象数组和纯文本格式。"""
    code_file = _cdkey_file_path()

    if not os.path.exists(code_file):
        log_warn(f"未找到 CDKEY 文件: {code_file}")
        return []

    try:
        with open(code_file, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    except Exception as e:
        log_error(f"读取 CDKEY 文件失败: {e}")
        return []

    if not raw:
        log_warn("CDKEY 文件为空")
        return []

    def _normalize_loaded_code_items(data: Any) -> list[dict[str, Any]]:
        if isinstance(data, dict):
            for key in ("cdkeys", "codes", "items", "data"):
                nested = data.get(key)
                if isinstance(nested, list):
                    data = nested
                    break
        if not isinstance(data, list):
            return []
        normalized_items: list[dict[str, Any]] = []
        seen_codes: set[str] = set()
        for item in data:
            if isinstance(item, dict):
                code = str(item.get("code") or "").strip()
                use_count = _normalize_use_count(item.get("use"))
            else:
                code = str(item or "").strip()
                use_count = 0
            if not code or code in seen_codes:
                continue
            seen_codes.add(code)
            normalized_items.append({"code": code, "use": use_count})
        return normalized_items

    def _looks_like_code_container(data: Any) -> bool:
        if isinstance(data, list):
            return True
        if isinstance(data, dict):
            return any(isinstance(data.get(key), list) for key in ("cdkeys", "codes", "items", "data"))
        return False

    candidates = [raw]
    normalized = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', raw)
    normalized = re.sub(r"\bfalse\b", "false", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\btrue\b", "true", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bnull\b", "null", normalized, flags=re.IGNORECASE)
    candidates.append(normalized.replace("'", '"'))

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except Exception:
            continue
        items = _normalize_loaded_code_items(data)
        if items or _looks_like_code_container(data):
            if not quiet:
                log_info(f"成功读取 CDKEY 数组，共 {len(items)} 项")
            return items

    try:
        python_like = raw.replace("false", "False").replace("true", "True").replace("null", "None")
        data = ast.literal_eval(python_like)
        items = _normalize_loaded_code_items(data)
        if items or _looks_like_code_container(data):
            if not quiet:
                log_info(f"成功读取 CDKEY 数组，共 {len(items)} 项")
            return items
    except Exception:
        pass

    plain_codes = _extract_code_lines(raw)
    if plain_codes:
        items = [{"code": code, "use": 0} for code in plain_codes]
        if not quiet:
            log_info(f"成功读取 CDKEY 文本，共 {len(items)} 项")
        return items

    log_error("CDKEY 文件内容不是可解析的数组或文本格式")
    return []


def save_code_array(code_array: list[dict[str, Any]]) -> None:
    """将更新后的 CDKEY 数组写回 CDKEY 文件。"""
    code_file = _cdkey_file_path()
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
        log_error(f"写回 CDKEY 文件失败: {e}")


def _load_plain_codes(file_path: str) -> list[str]:
    if not file_path or not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception:
        return []
    return _extract_code_lines(raw)


def _extract_code_lines(raw_text: str) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for part in re.split(r"[\s,;，；]+", str(raw_text or "").strip()):
        code = str(part or "").strip()
        if not code or code in seen:
            continue
        seen.add(code)
        items.append(code)
    return items


def _save_plain_codes(file_path: str, codes: list[str]) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        if codes:
            f.write("\n".join(codes) + "\n")
        else:
            f.write("")


def _extract_nonempty_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for line in str(raw_text or "").splitlines():
        text = line.strip()
        if text:
            lines.append(text)
    return lines


def _dedupe_local_graph_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    seen_emails: set[str] = set()
    for line in lines:
        parsed = _parse_local_graph_account_line(line)
        if parsed is None:
            continue
        email = str(parsed.get("email") or "").strip().lower()
        if not email or email in seen_emails:
            continue
        seen_emails.add(email)
        merged.append(line.strip())
    return merged


def _load_local_graph_lines() -> list[str]:
    file_path = _local_email_file_path()
    if not file_path or not os.path.exists(file_path):
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return _extract_nonempty_lines(f.read())
    except Exception:
        return []


def _save_local_graph_lines(lines: list[str]) -> None:
    file_path = _local_email_file_path()
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        if lines:
            f.write("\n".join(lines) + "\n")
        else:
            f.write("")


def _append_local_graph_accounts_from_text(raw_text: str) -> int:
    incoming = _dedupe_local_graph_lines(_extract_nonempty_lines(raw_text))
    if not incoming:
        return 0
    existing = _load_local_graph_lines()
    before = len(_dedupe_local_graph_lines(existing))
    merged = _dedupe_local_graph_lines(existing + incoming)
    _save_local_graph_lines(merged)
    return max(0, len(merged) - before)


def _replace_local_graph_accounts_from_text(raw_text: str) -> int:
    incoming = _dedupe_local_graph_lines(_extract_nonempty_lines(raw_text))
    _save_local_graph_lines(incoming)
    CONFIG["tm_local_email_cursor"] = 0
    save_config()
    return len(incoming)


def _append_cdkeys_from_text(raw_text: str) -> int:
    incoming = _extract_code_lines(raw_text)
    if not incoming:
        return 0
    existing_items = load_code_array(quiet=True)
    existing_codes = {
        str(item.get("code") or "").strip()
        for item in existing_items
        if isinstance(item, dict) and str(item.get("code") or "").strip()
    }
    merged = list(existing_items)
    added = 0
    for code in incoming:
        if code in existing_codes:
            continue
        existing_codes.add(code)
        merged.append({"code": code, "use": 0})
        added += 1
    if added > 0:
        save_code_array(merged)
    return added


def _append_redeem_codes_from_text(raw_text: str) -> int:
    """已停用：redeem_codes 机制已取消。"""
    return 0


def sync_code_file_from_cdkeys() -> int:
    """已停用：CDKEY 现已直接作为唯一卡码源。"""
    return 0


def get_cdkey_count() -> int:
    """读取 CDKEY 文件中的唯一数量。"""
    return len(load_code_array(quiet=True))


def print_card_inventory_summary() -> None:
    """打印运行前卡片库存摘要。"""
    virtual_card_count = len(load_code_array(quiet=True))
    _render_kv_table(
        "运行前卡片信息",
        [
            ("CDKEY 数量", str(virtual_card_count)),
        ],
    )


def get_available_card_use_count() -> int:
    """按 use 计数计算当前虚拟卡还可用多少次。"""
    code_array = load_code_array(quiet=True)
    max_use_count = get_card_max_use_count()
    available_uses = 0
    for item in code_array:
        if not isinstance(item, dict):
            continue
        use_count = _normalize_use_count(item.get("use"))
        available_uses += max(0, max_use_count - use_count)
    return available_uses


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
    """日志目录已停用，保留空实现以兼容旧调用。"""
    return ""


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
            headers=_aisub_headers(),
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


def get_aisub_balance_snapshot(proxies: Any = None) -> Dict[str, Any]:
    """获取 AISub 余额快照，便于在运行前后汇总展示。"""
    balance_result = get_aisub_balance(proxies)
    balance_data = balance_result.get("response") or {}
    balance = 0
    if isinstance(balance_data, dict):
        try:
            balance = int(float(balance_data.get("balance") or 0))
        except (TypeError, ValueError):
            balance = 0
    return {
        "status_code": int(balance_result.get("status_code") or 0),
        "balance": balance,
        "remaining_times": balance // 30,
        "raw": balance_data,
    }


def print_aisub_balance_summary(title: str, snapshot: Dict[str, Any]) -> None:
    """打印 AISub 余额汇总。"""
    status_code = int(snapshot.get("status_code") or 0)
    if status_code != 200:
        log_section(title)
        raw = snapshot.get("raw") or {}
        message = ""
        if isinstance(raw, dict):
            message = str(raw.get("error") or raw.get("message") or "").strip()
        log_warn(f"AISub 余额查询失败，status={status_code or 'N/A'} {message}".strip())
        return
    remaining_times = int(snapshot.get("remaining_times") or 0)
    available_card_uses = get_available_card_use_count()
    estimated_accounts = min(remaining_times, available_card_uses)
    estimated_positions = estimated_accounts * 5
    _render_kv_table(
        title,
        [
            ("AISub 可用次数", str(remaining_times)),
            ("预计可生成账号", str(estimated_accounts)),
            ("预计可生成位置", str(estimated_positions)),
        ],
    )


def _display_width(text: str) -> int:
    width = 0
    for ch in text:
        width += 2 if unicodedata.east_asian_width(ch) in {"W", "F"} else 1
    return width


def _pad_to_width(text: str, width: int) -> str:
    pad = max(0, width - _display_width(text))
    return text + (" " * pad)


def _shorten_path_display(path_value: str, max_len: int = 42) -> str:
    text = str(path_value or "").strip()
    if not text:
        return "未设置"
    if len(text) <= max_len:
        return text
    return f"...{text[-(max_len - 3):]}"


def _mask_secret(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "未设置"
    if len(raw) <= 8:
        return "*" * len(raw)
    return f"{raw[:4]}...{raw[-4:]}"


def _print_menu_hint(text: str) -> None:
    if RICH_AVAILABLE and CONSOLE:
        CONSOLE.print(f"[dim]{text}[/dim]")
        return
    print(f"\n{ANSI_DIM}{text}{ANSI_RESET}")


def _render_brand_header(title: str, subtitle: str = "") -> None:
    if RICH_AVAILABLE and CONSOLE and Panel:
        CONSOLE.print(
            Panel.fit(
                STARTUP_BANNER.strip("\n"),
                title=f"[bold cyan]{title}[/bold cyan]",
                border_style="bright_blue",
                padding=(1, 2),
            )
        )
        if subtitle:
            CONSOLE.print(f"[dim]{subtitle}[/dim]")
        return
    log_section(title)
    print(STARTUP_BANNER)
    if subtitle:
        log_info(subtitle)


def _render_kv_table(title: str, rows: list[tuple[str, str]]) -> None:
    if RICH_AVAILABLE and CONSOLE and Table:
        CONSOLE.print(f"[bold cyan]{title}[/bold cyan]")
        table = Table(show_header=False, expand=True, box=None, pad_edge=False, padding=(0, 0))
        table.add_column("key", style="bold white", ratio=1)
        table.add_column("value", style="cyan", ratio=1)
        for left, right in rows:
            table.add_row(left, right)
        CONSOLE.print(table)
        return
    log_section(title)
    _print_dashboard_rows(rows)


def _print_dashboard_rows(rows: list[tuple[str, str]], gap: int = 6) -> None:
    left_width = max((_display_width(left) for left, _ in rows), default=0)
    for left, right in rows:
        print(f"{_pad_to_width(left, left_width)}{' ' * gap}{right}")


def _get_startup_dashboard_data(proxies: Any = None) -> Dict[str, Any]:
    register_type = _register_type_key()
    available_card_uses = get_available_card_use_count()
    aisub_snapshot = get_aisub_balance_snapshot(proxies)
    aisub_times = int(aisub_snapshot.get("remaining_times") or 0) if int(aisub_snapshot.get("status_code") or 0) == 200 else 0
    estimated_accounts = min(aisub_times, available_card_uses)
    estimated_positions = estimated_accounts * 5
    return {
        "register_type": register_type,
        "available_card_uses": available_card_uses,
        "aisub_snapshot": aisub_snapshot,
        "aisub_times": aisub_times,
        "estimated_accounts": estimated_accounts,
        "estimated_positions": estimated_positions,
    }


def print_startup_dashboard(proxies: Any = None) -> Dict[str, Any]:
    data = _get_startup_dashboard_data(proxies)
    rows = [("注册类型", _register_type_label(data.get("register_type")))]
    if data.get("register_type") == "team":
        rows.extend(
            [
                ("AISub 可用次数", str(data["aisub_times"])),
                ("虚拟卡可用次数", str(data["available_card_uses"])),
                ("预计可生成账号", str(data["estimated_accounts"])),
                ("预计可生成位置", str(data["estimated_positions"])),
            ]
        )
    else:
        rows.append(("运行模式", "仅注册普号，不绑定 Team"))
    _render_kv_table(
        "运行前卡片信息",
        rows,
    )
    print("=" * 56)
    print("> 1. 开始注册")
    print("  2. 生成账户数")
    print("  3. 其他配置")
    return data["aisub_snapshot"]


def _clear_screen() -> None:
    print("\033[2J\033[H", end="", flush=True)


def _hide_cursor() -> None:
    print("\033[?25l", end="", flush=True)


def _show_cursor() -> None:
    print("\033[?25h", end="", flush=True)


def _select_from_menu(title: str, options: list[str], selected_index: int = 0) -> int:
    try:
        while True:
            _hide_cursor()
            _clear_screen()
            if RICH_AVAILABLE and CONSOLE and Panel:
                lines = []
                for index, option in enumerate(options):
                    prefix = f"{index + 1:>2}. "
                    if index == selected_index:
                        lines.append(f"[bold bright_cyan]▶ {prefix}{option}[/bold bright_cyan]")
                    else:
                        lines.append(f"[dim]  {prefix}{option}[/dim]")
                CONSOLE.print(Panel("\n".join(lines), title=f"[bold]{title}[/bold]", border_style="blue"))
                _print_menu_hint("方向键 / J K 选择，Enter 确认，Esc 返回")
            else:
                print(f"{ANSI_BOLD}{title}{ANSI_RESET}\n")
                for index, option in enumerate(options):
                    prefix = f"{index + 1:>2}. "
                    if index == selected_index:
                        print(f"{ANSI_BOLD}{ANSI_MENU}▶ {prefix}{option}{ANSI_RESET}")
                    else:
                        print(f"{ANSI_DIM}{ANSI_MENU}  {prefix}{option}{ANSI_RESET}")
                _print_menu_hint("方向键 / J K 选择，Enter 确认，Esc 返回")
            key = _read_menu_key()
            if key == "up":
                selected_index = (selected_index - 1) % len(options)
                continue
            if key == "down":
                selected_index = (selected_index + 1) % len(options)
                continue
            if key == "escape":
                return -1
            if key == "enter":
                return selected_index
    finally:
        _show_cursor()


def _read_menu_key() -> str:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)
        if first in {"\r", "\n"}:
            return "enter"
        if first == "\x1b":
            second = sys.stdin.read(1)
            if second in {"[", "O"}:
                third = sys.stdin.read(1)
                if third == "A":
                    return "up"
                if third == "B":
                    return "down"
            return "escape"
        if first in {"k", "K"}:
            return "up"
        if first in {"j", "J"}:
            return "down"
        if first in {"1", "2", "3", "4", "5", "6", "7", "8", "9"}:
            return first
        return ""
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _prompt_input(prompt: str, default: str = "") -> Optional[str]:
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    buffer = list(default)
    try:
        _show_cursor()
        print(f"{prompt}{default}", end="", flush=True)
        tty.setraw(fd)
        while True:
            ch = sys.stdin.read(1)
            if ch in {"\r", "\n"}:
                print()
                return "".join(buffer).strip()
            if ch == "\x1b":
                print()
                return None
            if ch in {"\x7f", "\b"}:
                if buffer:
                    buffer.pop()
                    print("\b \b", end="", flush=True)
                continue
            if ch.isprintable():
                buffer.append(ch)
                print(ch, end="", flush=True)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _prompt_multiline_input(title: str, finish_hint: str = "连续输入，空行结束，ESC 取消") -> Optional[str]:
    _show_cursor()
    print(f"{title}")
    print(f"{finish_hint}")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            return None
        if line == "\x1b":
            return None
        if not line.strip():
            break
        lines.append(line.rstrip("\n"))
    return "\n".join(lines).strip()


def _parse_config_value(raw: str) -> Any:
    text = str(raw or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        return ast.literal_eval(text)
    except Exception:
        return text


def _update_config_value(key: str, prompt: str, *, default: Any = "", parser: Any = None, success_text: str = "配置已更新") -> None:
    value = _prompt_input(prompt, "" if default is None else str(default))
    if value is None:
        return
    parsed = parser(value) if parser else value.strip()
    CONFIG[key] = parsed
    save_config()
    log_ok(success_text)


def _parse_positive_int(raw: str) -> int:
    return max(1, int(raw))


def prompt_file_settings() -> None:
    selected_index = 0
    while True:
        options = [
            f"本地邮箱文件: {_shorten_path_display(str(CONFIG.get('tm_local_email_file') or DEFAULT_CONFIG['tm_local_email_file']))}",
            f"CDKEY 文件: {_shorten_path_display(str(CONFIG.get('cdkey_file') or DEFAULT_CONFIG['cdkey_file']))}",
            f"成功账号文件: {_shorten_path_display(str(CONFIG.get('teams_file') or DEFAULT_CONFIG['teams_file']))}",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / 文件路径", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        if selected_index == 0:
            _update_config_value(
                "tm_local_email_file",
                "请输入本地邮箱文件路径，支持相对路径: ",
                default=CONFIG.get("tm_local_email_file") or DEFAULT_CONFIG["tm_local_email_file"],
                success_text="本地邮箱文件已更新",
            )
        elif selected_index == 1:
            _update_config_value(
                "cdkey_file",
                "请输入 CDKEY 文件路径，支持相对路径: ",
                default=CONFIG.get("cdkey_file") or DEFAULT_CONFIG["cdkey_file"],
                success_text="CDKEY 文件路径已更新",
            )
        elif selected_index == 2:
            _update_config_value(
                "teams_file",
                "请输入成功账号文件路径，支持相对路径: ",
                default=CONFIG.get("teams_file") or DEFAULT_CONFIG["teams_file"],
                success_text="成功账号文件路径已更新",
            )


def prompt_import_settings() -> None:
    selected_index = 0
    while True:
        options = [
            "粘贴追加 CDKEY",
            "粘贴追加本地邮箱",
            "粘贴覆盖本地邮箱",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / 导入数据", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        if selected_index == 0:
            raw_text = _prompt_multiline_input("请粘贴 CDKEY，可多行/空格/逗号分隔")
            if raw_text is None:
                continue
            added = _append_cdkeys_from_text(raw_text)
            log_ok(f"CDKEY 导入完成: {added} 条")
        elif selected_index == 1:
            raw_text = _prompt_multiline_input(
                "请粘贴本地邮箱账号，每行一个，格式：邮箱----邮箱密码----Client ID----Refresh Token"
            )
            if raw_text is None:
                continue
            added = _append_local_graph_accounts_from_text(raw_text)
            log_ok(f"本地邮箱导入完成: {added} 条")
        elif selected_index == 2:
            raw_text = _prompt_multiline_input(
                "请粘贴本地邮箱账号，每行一个，格式：邮箱----邮箱密码----Client ID----Refresh Token"
            )
            if raw_text is None:
                continue
            count = _replace_local_graph_accounts_from_text(raw_text)
            log_ok(f"本地邮箱覆盖完成: {count} 条")


def prompt_email_settings() -> None:
    selected_index = 0
    while True:
        current_provider = str(CONFIG.get("tm_email_provider") or "npcmail").strip().lower()
        options = [
            f"邮箱提供商: {_email_provider_label(current_provider)}",
            f"注册邮箱前缀: {str(CONFIG.get('tm_reg_prefix') or '').strip() or '未设置'}",
            f"注册邮箱域名: {str(CONFIG.get('tm_reg_domain') or '').strip() or '未设置'}",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / 邮箱注册", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        if selected_index == 0:
            provider_options = [
                ("npcmail", "NPCMail"),
                ("gptmail", "GPTMail"),
                ("junmail", "JunMail"),
                ("xiaomajiang", "临时邮箱(仅可做测试使用,封号严重)"),
                ("local_graph", "本地Outlook邮箱"),
            ]
            provider_labels = [label for _, label in provider_options]
            provider_index = next(
                (index for index, (provider_key, _) in enumerate(provider_options) if provider_key == current_provider),
                0,
            )
            provider_choice = _select_from_menu("邮箱提供商", provider_labels, provider_index)
            if provider_choice == -1:
                continue
            provider_key, provider_label = provider_options[provider_choice]
            CONFIG["tm_email_provider"] = provider_key
            save_config()
            log_ok(f"邮箱提供商已更新为 {provider_label}")
        elif selected_index == 1:
            _update_config_value(
                "tm_reg_prefix",
                "请输入注册邮箱前缀，留空则清除: ",
                default=CONFIG.get("tm_reg_prefix") or "",
                success_text="注册邮箱前缀已更新",
            )
        elif selected_index == 2:
            _update_config_value(
                "tm_reg_domain",
                "请输入注册邮箱域名，留空则清除: ",
                default=CONFIG.get("tm_reg_domain") or "",
                success_text="注册邮箱域名已更新",
            )


def prompt_service_settings() -> None:
    selected_index = 0
    while True:
        options = [
            f"NPCMail API Key: {_mask_secret(str(CONFIG.get('tm_npcmail_apikey') or ''))}",
            f"GPTMail API Key: {_mask_secret(str(CONFIG.get('gptmail_api_key') or ''))}",
            f"JunMail API Key: {_mask_secret(str(CONFIG.get('junmail_api_key') or ''))}",
            f"JunMail Base URL: {_shorten_path_display(str(CONFIG.get('junmail_base') or DEFAULT_CONFIG['junmail_base']), 50)}",
            f"AISub API Key: {_mask_secret(str(CONFIG.get('aisub_api_key') or ''))}",
            f"Redeem Base URL: {_shorten_path_display(str(CONFIG.get('redeem_base_url') or DEFAULT_CONFIG['redeem_base_url']), 50)}",
            f"AISub Base URL: {_shorten_path_display(str(CONFIG.get('aisub_base_url') or DEFAULT_CONFIG['aisub_base_url']), 50)}",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / 接口与密钥", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        if selected_index == 0:
            _update_config_value(
                "tm_npcmail_apikey",
                "请输入 NPCMail API Key，留空则清除: ",
                default=CONFIG.get("tm_npcmail_apikey") or "",
                success_text="NPCMail API Key 已更新",
            )
        elif selected_index == 1:
            _update_config_value(
                "gptmail_api_key",
                "请输入 GPTMail API Key，留空则清除: ",
                default=CONFIG.get("gptmail_api_key") or "",
                success_text="GPTMail API Key 已更新",
            )
        elif selected_index == 2:
            _update_config_value(
                "junmail_api_key",
                "请输入 JunMail API Key，留空则清除: ",
                default=CONFIG.get("junmail_api_key") or "",
                success_text="JunMail API Key 已更新",
            )
        elif selected_index == 3:
            _update_config_value(
                "junmail_base",
                "请输入 JunMail Base URL: ",
                default=CONFIG.get("junmail_base") or DEFAULT_CONFIG["junmail_base"],
                success_text="JunMail Base URL 已更新",
            )
        elif selected_index == 4:
            _update_config_value(
                "aisub_api_key",
                "请输入 AISub API Key，留空则清除: ",
                default=CONFIG.get("aisub_api_key") or "",
                success_text="AISub API Key 已更新",
            )
        elif selected_index == 5:
            _update_config_value(
                "redeem_base_url",
                "请输入 Redeem Base URL: ",
                default=CONFIG.get("redeem_base_url") or DEFAULT_CONFIG["redeem_base_url"],
                success_text="Redeem Base URL 已更新",
            )
        elif selected_index == 6:
            _update_config_value(
                "aisub_base_url",
                "请输入 AISub Base URL: ",
                default=CONFIG.get("aisub_base_url") or DEFAULT_CONFIG["aisub_base_url"],
                success_text="AISub Base URL 已更新",
            )


def prompt_runtime_settings() -> None:
    selected_index = 0
    while True:
        options = [
            f"注册类型: {_register_type_label()}",
            f"默认代理: {str(CONFIG.get('default_proxy') or '').strip() or '未设置'}",
            f"单卡最大绑定次数: {get_card_max_use_count()}",
            f"subscribe 失败重开号: {'开' if bool(CONFIG.get('subscribe_retry_new_account_enabled', True)) else '关'}",
            f"subscribe 失败次数上限: {int(CONFIG.get('subscribe_retry_new_account_limit', 50) or 50)}",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / 运行策略", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        if selected_index == 0:
            prompt_register_type_setting()
        elif selected_index == 1:
            _update_config_value(
                "default_proxy",
                "请输入默认代理，留空则清除: ",
                default=CONFIG.get("default_proxy") or "",
                success_text="默认代理已更新",
            )
        elif selected_index == 2:
            raw = _prompt_input("请输入单卡最大绑定次数: ", str(get_card_max_use_count()))
            if raw is None:
                continue
            try:
                CONFIG["card_max_use_count"] = _parse_positive_int(raw)
            except ValueError:
                log_warn("输入无效")
                continue
            save_config()
            log_ok(f"单卡最大绑定次数已更新为 {CONFIG['card_max_use_count']}")
        elif selected_index == 3:
            enabled = bool(CONFIG.get("subscribe_retry_new_account_enabled", True))
            toggle_choice = _select_from_menu("subscribe 失败重开号", ["开", "关"], 0 if enabled else 1)
            if toggle_choice == -1:
                continue
            CONFIG["subscribe_retry_new_account_enabled"] = toggle_choice == 0
            save_config()
            log_ok("subscribe 失败重开号配置已更新")
        elif selected_index == 4:
            raw = _prompt_input(
                "请输入 subscribe 失败次数上限: ",
                str(int(CONFIG.get("subscribe_retry_new_account_limit", 50) or 50)),
            )
            if raw is None:
                continue
            try:
                CONFIG["subscribe_retry_new_account_limit"] = _parse_positive_int(raw)
            except ValueError:
                log_warn("输入无效")
                continue
            save_config()
            log_ok(f"subscribe 失败次数上限已更新为 {CONFIG['subscribe_retry_new_account_limit']}")


def prompt_register_type_setting() -> None:
    register_type_options = [("normal", "普号"), ("team", "Team")]
    current_type = _register_type_key()
    register_type_index = next(
        (index for index, (register_type_key, _) in enumerate(register_type_options) if register_type_key == current_type),
        1,
    )
    choice = _select_from_menu(
        "注册类型",
        [label for _, label in register_type_options],
        register_type_index,
    )
    if choice == -1:
        return
    register_type_key, register_type_label = register_type_options[choice]
    CONFIG["register_type"] = register_type_key
    save_config()
    log_ok(f"注册类型已更新为 {register_type_label}")


def prompt_advanced_settings() -> None:
    selected_index = 0
    while True:
        options = [
            "编辑任意配置项",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / 高级", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        key = _prompt_input("请输入配置项 key，例如 code_results_file: ")
        if key is None:
            continue
        key = key.strip()
        if not key:
            log_warn("key 不能为空")
            continue
        current_value = CONFIG.get(key, DEFAULT_CONFIG.get(key, ""))
        raw_value = _prompt_input(
            f"请输入 {key} 的值，支持字符串/数字/true/false/null/list/dict，当前为 {current_value!r}: "
        )
        if raw_value is None:
            continue
        CONFIG[key] = _parse_config_value(raw_value)
        save_config()
        log_ok(f"配置项 {key} 已更新")


def _render_startup_menu(selected_index: int, dashboard: Dict[str, Any], started_at: datetime, cdkey_added_count: int) -> None:
    _hide_cursor()
    _clear_screen()
    _render_brand_header(
        "Team 注册机",
        f"欢迎使用 Team 注册机，现在是 {_fmt_local_dt(started_at)}",
    )
    _render_kv_table(
        "运行前概览",
        [("注册类型", _register_type_label(dashboard.get("register_type")))]
        + (
            [
                ("虚拟卡可用次数", str(dashboard["available_card_uses"])),
                ("AISub 可用次数", str(dashboard["aisub_times"])),
                ("预计可生成账号", str(dashboard["estimated_accounts"])),
                ("预计可生成位置", str(dashboard["estimated_positions"])),
            ]
            if dashboard.get("register_type") == "team"
            else [("运行模式", "仅注册普号，不绑定 Team")]
        ),
    )
    if RICH_AVAILABLE and CONSOLE and Panel:
        lines = []
        for index, label in enumerate(MENU_OPTIONS):
            prefix = f"{index + 1}. "
            if index == selected_index:
                lines.append(f"[bold bright_cyan]▶ {prefix}{label}[/bold bright_cyan]")
            else:
                lines.append(f"[dim]  {prefix}{label}[/dim]")
        CONSOLE.print(Panel("\n".join(lines), title="[bold]主菜单[/bold]", border_style="cyan"))
        _print_menu_hint("方向键 / J K 选择，数字键快速进入，Enter 确认")
        return
    print("=" * 56)
    for index, label in enumerate(MENU_OPTIONS):
        prefix = f"{index + 1}. "
        if index == selected_index:
            print(f"{ANSI_BOLD}{ANSI_MENU}▶ {prefix}{label}{ANSI_RESET}")
        else:
            print(f"{ANSI_DIM}{ANSI_MENU}  {prefix}{label}{ANSI_RESET}")
    _print_menu_hint("方向键 / J K 选择，数字键快速进入，Enter 确认")


def prompt_execution_count() -> None:
    current_target_type = str(CONFIG.get("target_type") or DEFAULT_CONFIG["target_type"]).strip()
    current_target_value = int(CONFIG.get("target_value") or DEFAULT_CONFIG["target_value"] or 0)
    current_display = current_target_value if current_target_type == "register_count" else 0
    dashboard = _get_startup_dashboard_data()
    register_type = str(dashboard.get("register_type") or "team")
    estimated_accounts = int(dashboard.get("estimated_accounts") or 0)
    estimated_positions = int(dashboard.get("estimated_positions") or 0)
    max_allowed = max(0, estimated_accounts) if register_type == "team" else 0
    prompt = f"请输入生成账户数，0 表示不限，当前为 {current_display}"
    if register_type == "team":
        prompt += f"，最大不超过 {max_allowed}（对应约 {estimated_positions} 个位置）"
    else:
        prompt += "，普号模式下不受 AISub / 卡池限制"
    raw = _prompt_input(f"{prompt}: ")
    if raw is None or not raw:
        return
    try:
        target_value = max(0, int(raw))
    except ValueError:
        log_warn("输入无效，保持原配置")
        return
    if max_allowed > 0 and target_value > max_allowed:
        log_warn(f"生成账户数不能超过预计可生成账号数 {max_allowed}")
        return
    CONFIG["target_type"] = "register_count"
    CONFIG["target_value"] = target_value
    save_config()
    log_ok(f"生成账户数已更新为 {target_value}")


def prompt_other_config() -> None:
    selected_index = 0
    while True:
        options = [
            "文件路径",
            "导入数据",
            "邮箱注册",
            "接口与密钥",
            "运行策略",
            "高级设置",
            "返回",
        ]
        selected_index = _select_from_menu("其他配置", options, selected_index)
        if selected_index == -1:
            return
        if selected_index == len(options) - 1:
            return
        if selected_index == 0:
            prompt_file_settings()
            continue
        if selected_index == 1:
            prompt_import_settings()
            continue
        if selected_index == 2:
            prompt_email_settings()
            continue
        if selected_index == 3:
            prompt_service_settings()
            continue
        if selected_index == 4:
            prompt_runtime_settings()
            continue
        if selected_index == 5:
            prompt_advanced_settings()


def prompt_startup_menu(proxies: Any = None, *, started_at: datetime, cdkey_added_count: int) -> Optional[Dict[str, Any]]:
    selected_index = 0
    options = ("start", "type", "count", "config", "exit")
    menu_proxies = proxies
    dashboard = _get_startup_dashboard_data(menu_proxies)
    try:
        while True:
            _render_startup_menu(selected_index, dashboard, started_at, cdkey_added_count)
            key = _read_menu_key()
            if key == "up":
                selected_index = (selected_index - 1) % len(options)
                continue
            if key == "down":
                selected_index = (selected_index + 1) % len(options)
                continue
            if key.isdigit() and 1 <= int(key) <= len(options):
                selected_index = int(key) - 1
                key = "enter"
            if key == "escape":
                selected_index = len(options) - 1
                key = "enter"
            if key != "enter":
                continue
            selected = options[selected_index]
            if selected == "start":
                _clear_screen()
                return dashboard["aisub_snapshot"]
            if selected == "type":
                _show_cursor()
                _clear_screen()
                prompt_register_type_setting()
                dashboard = _get_startup_dashboard_data(menu_proxies)
                continue
            if selected == "count":
                _show_cursor()
                _clear_screen()
                prompt_execution_count()
                dashboard = _get_startup_dashboard_data(menu_proxies)
                continue
            if selected == "config":
                _show_cursor()
                _clear_screen()
                prompt_other_config()
                proxy_value = str(CONFIG.get("default_proxy") or "").strip() or None
                menu_proxies = {"http": proxy_value, "https": proxy_value} if proxy_value else None
                dashboard = _get_startup_dashboard_data(menu_proxies)
                continue
            if selected == "exit":
                _clear_screen()
                return None
    finally:
        _show_cursor()


def _normalize_use_count(value: Any) -> int:
    """将历史 use 字段统一转换为非负整数计数。"""
    if isinstance(value, bool):
        return 2 if value else 0
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, count)


def get_card_max_use_count() -> int:
    """获取单张卡允许绑定的最大次数。"""
    try:
        count = int(CONFIG.get("card_max_use_count") or DEFAULT_CONFIG["card_max_use_count"])
    except (TypeError, ValueError):
        count = int(DEFAULT_CONFIG["card_max_use_count"])
    return max(1, count)


def get_next_unused_code() -> Optional[tuple[str, list[dict[str, Any]], int]]:
    """获取第一个未达到最大使用次数的 CDKEY。"""
    code_array = load_code_array()
    max_use_count = get_card_max_use_count()
    for index, item in enumerate(code_array):
        code = str(item.get("code") or "").strip()
        use_count = _normalize_use_count(item.get("use"))
        item["use"] = use_count
        if code and use_count < max_use_count:
            return code, code_array, index
    log_warn("CDKEY 文件中没有可用的码")
    return None


def wait_for_next_unused_code() -> tuple[str, list[dict[str, Any]], int]:
    """获取可用 CDKEY；全部用完时停止脚本。"""
    next_code_info = get_next_unused_code()
    if next_code_info:
        return next_code_info
    raise StopScript("CDKEY 已全部用完，脚本停止")


def _drop_code_entry(code_array: list[dict[str, Any]], code_index: int, *, reason: str = "") -> None:
    if code_index < 0 or code_index >= len(code_array):
        return
    code_value = str((code_array[code_index] or {}).get("code") or "").strip()
    del code_array[code_index]
    save_code_array(code_array)
    if code_value:
        detail = f"，原因: {reason}" if reason else ""
        log_info(f"CDKEY {code_value} 已从源文件移除{detail}")


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
    except SkipCurrentCode:
        raise
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
    last_progress = ""
    while True:
        task_data = request_redeem_task_status(task_id, proxies)
        if has_cards(task_data):
            return task_data

        payload = task_data.get("data") if isinstance(task_data, dict) else {}
        status = (payload or {}).get("status") if isinstance(payload, dict) else None
        progress = str((payload or {}).get("progress") or "").strip()
        if status == 2:
            return task_data
        if progress and progress != last_progress:
            last_progress = progress
            log_info(f"开卡进行中: {progress}")
            if progress == "发卡失败已回滚":
                raise SkipCurrentCode("开卡进度出现“发卡失败已回滚” 1 次，跳过当前兑换码")
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
    if has_cards(response_data):
        # 已经拿到卡数据时，即使服务端同时回了“该兑换码已使用完”，
        # 这张卡仍然应该进入后续注册流程，不能在这里提前丢弃。
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


def _normalize_address_component(value: Any) -> str:
    text = str(value or "").replace("，", ",").replace("：", ":").strip()
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*,\s*", ", ", text)
    text = re.sub(r"(,\s*){2,}", ", ", text)
    return text.strip(" ,")


def _extract_template_field(line: str, labels: tuple[str, ...]) -> str:
    raw = str(line or "").strip()
    if not raw:
        return ""
    for label in labels:
        match = re.match(
            rf"^{re.escape(label)}(?:\s*[:：]?\s*)(.+?)\s*$",
            raw,
            flags=re.IGNORECASE,
        )
        if not match:
            continue
        value = _normalize_address_component(match.group(1))
        if value:
            return value
    return ""


def _looks_like_street_address(line: str) -> bool:
    text = _normalize_address_component(line)
    if not text:
        return False
    lower = text.lower()
    if "{$" in text or "mmyy" in lower or "cvc" in lower:
        return False
    if re.fullmatch(r"[A-Z]{2}", text):
        return False
    if re.fullmatch(r"\d{5}(?:-\d{4})?", text):
        return False
    if lower in {"united states", "usa", "us"}:
        return False
    ignored_prefixes = (
        "卡号",
        "地区",
        "姓名",
        "持卡人",
        "国家",
        "城市",
        "州",
        "省",
        "邮编",
        "邮政编码",
        "name",
        "holder",
        "cardholder",
        "country",
        "city",
        "state",
        "province",
        "zip",
        "postal",
        "postcode",
        "region",
    )
    if lower.startswith(ignored_prefixes):
        return False
    if re.search(
        r"\b(street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd|court|ct|"
        r"way|circle|cir|terrace|ter|highway|hwy|parkway|pkwy|trail|trl|place|pl|"
        r"suite|ste|unit|apt|apartment|box)\b",
        lower,
    ):
        return True
    return bool(re.search(r"\d", text) and re.search(r"[a-zA-Z\u4e00-\u9fff]", text))


def _extract_address_from_template(template: str) -> str:
    fields = {
        "address": "",
        "city": "",
        "state": "",
        "zipcode": "",
        "country": "",
    }
    field_labels = {
        "address": (
            "Street Address",
            "Address Line 1",
            "Address1",
            "Street",
            "Address",
            "地址",
            "街道",
        ),
        "city": ("City", "城市"),
        "state": ("Province", "State", "Region", "州", "省"),
        "zipcode": ("Postal Code", "ZIP Code", "Postcode", "Zip", "ZIP", "邮政编码", "邮编"),
        "country": ("Country", "国家"),
    }
    fallback_address_lines: list[str] = []
    lines = [line.strip() for line in str(template or "").splitlines() if line.strip()]
    for line in lines:
        matched = False
        for field_name, labels in field_labels.items():
            value = _extract_template_field(line, labels)
            if not value:
                continue
            fields[field_name] = value
            matched = True
            break
        if not matched and _looks_like_street_address(line):
            fallback_address_lines.append(line)

    if not fields["address"] and fallback_address_lines:
        fields["address"] = _normalize_address_component(fallback_address_lines[0])

    address_parts = [
        _normalize_address_component(fields["address"]),
        _normalize_address_component(fields["city"]),
        _normalize_address_component(fields["state"]),
        _normalize_address_component(fields["zipcode"]),
        _normalize_address_component(fields["country"]),
    ]
    address_parts = [part for part in address_parts if part]
    return ", ".join(address_parts)


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
    address_text = _extract_address_from_template(template) if template else ""

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
    """每次直接从 CDKEY 现场 validate / redeem，直到拿到可用卡片。"""
    while True:
        code_value, code_array, code_index = wait_for_next_unused_code()
        item = code_array[code_index]
        use_count = _normalize_use_count(item.get("use"))
        if use_count > 0:
            log_info(f"第 {use_count + 1} 次使用当前 CDKEY，现场校验并开卡")
        try:
            validate_result = wait_for_validate_result(code_value, proxies)
        except SkipCurrentCode as e:
            _drop_code_entry(code_array, code_index, reason=str(e))
            log_warn(f"当前兑换码 {code_value} 跳过: {e}")
            continue

        if is_exhausted_validate_response(validate_result.get("response")):
            _drop_code_entry(code_array, code_index, reason="达到服务端使用上限")
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
    """在 subscribe 成功后递增当前 CDKEY 的 use 计数，达到上限后移除。"""
    next_use_count = min(use_count + 1, get_card_max_use_count())
    if code_index < 0 or code_index >= len(code_array):
        return
    if next_use_count >= get_card_max_use_count():
        _drop_code_entry(code_array, code_index, reason="达到配置的最大使用次数")
        return
    code_array[code_index]["use"] = next_use_count
    save_code_array(code_array)


def print_run_summary(
    *,
    register_type: str,
    registered_accounts: int,
    aisub_uses: int,
    cards_used: int,
    mother_accounts: int,
    started_at: Optional[datetime] = None,
    ended_at: Optional[datetime] = None,
    aisub_balance_before: Optional[Dict[str, Any]] = None,
    aisub_balance_after: Optional[Dict[str, Any]] = None,
) -> None:
    """打印本次运行汇总。"""
    child_accounts = mother_accounts * 5
    register_type_key = _register_type_key(register_type)
    log_section("本次运行汇总")
    log_ok(f"注册类型: {_register_type_label(register_type_key)}")
    if register_type_key == "team":
        log_ok(f"注册了 {registered_accounts} 个号")
        log_ok(f"使用了 AISub {aisub_uses} 次")
        log_ok(f"使用了 {cards_used} 张卡")
        log_ok(f"绑定 {mother_accounts} 个Team")
        log_ok(f"生成了 {child_accounts} 个位置")
    else:
        log_ok(f"生成了 {registered_accounts} 个普号")
        log_ok(f"生成了 {registered_accounts} 个位置")
    if started_at and ended_at:
        total_seconds = (ended_at - started_at).total_seconds()
        log_ok(f"开始时间: {_fmt_local_dt(started_at)}")
        log_ok(f"结束时间: {_fmt_local_dt(ended_at)}")
        log_ok(f"总耗时: {_fmt_duration(total_seconds)}")
        if registered_accounts > 0:
            log_ok(f"平均每个号耗时: {_fmt_duration(total_seconds / registered_accounts)}")
    if register_type_key == "team" and aisub_balance_before and aisub_balance_after:
        before_status = int(aisub_balance_before.get("status_code") or 0)
        after_status = int(aisub_balance_after.get("status_code") or 0)
        if before_status == 200 and after_status == 200:
            before_times = int(aisub_balance_before.get("remaining_times") or 0)
            after_times = int(aisub_balance_after.get("remaining_times") or 0)
            log_ok(f"AISub 运行前预计可用次数: {before_times}，运行后预计可用次数: {after_times}，变化: {after_times - before_times}")


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

    if _register_type_key() != "team":
        if registered_accounts >= target_value:
            log_info(f"已达到目标生成账户数 {target_value}，脚本停止")
            return True
        return False

    current_value = 0
    target_label = ""
    if target_type == "register_count":
        current_value = registered_accounts
        target_label = "生成账户数"
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

    headers = dict(_aisub_headers())
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
        return result
    except Exception as e:
        result = {
            "status_code": 0,
            "response": {"success": False, "error": str(e)},
        }
        return result


def _extract_subscribe_failure_info(response_data: Any) -> tuple[str, str]:
    full_text = ""
    concise_reason = ""
    if not isinstance(response_data, dict):
        return full_text, concise_reason

    error_text = str(response_data.get("error") or "").strip()
    steps = response_data.get("steps")
    step_texts: list[str] = []
    if isinstance(steps, list):
        step_texts = [str(step).strip() for step in steps if str(step).strip()]

    parts = [part for part in [error_text, *step_texts] if part]
    full_text = " | ".join(parts)

    diagnostic_step = ""
    for step in reversed(step_texts):
        lowered = step.lower()
        if (
            "hcaptcha" in lowered
            or "3ds" in lowered
            or "confirm error:" in lowered
            or "declined" in lowered
            or "postal" in lowered
            or "zip" in lowered
            or "验证码" in step
            or "邮编" in step
            or "地址" in step
            or "error" in lowered
        ):
            diagnostic_step = step
            break

    generic_errors = {
        "",
        "操作失败",
        "操作失败，请重试",
        "请重试",
    }
    is_generic_error = error_text in generic_errors

    if any("需要 hCaptcha challenge" in step for step in step_texts):
        concise_reason = "需要 hCaptcha challenge"
    elif any("3DS" in step or "额外验证" in step for step in step_texts):
        concise_reason = "该账号需要额外验证（3DS）"
    elif error_text and not is_generic_error:
        concise_reason = error_text
    elif error_text and diagnostic_step:
        concise_reason = f"{error_text} | {diagnostic_step}"
    elif error_text:
        concise_reason = error_text
    elif diagnostic_step:
        concise_reason = diagnostic_step
    elif step_texts:
        concise_reason = step_texts[-1]

    return full_text, concise_reason


def wait_for_subscribe_success(
    access_token: str,
    validate_result: Dict[str, Any],
    proxies: Any = None,
) -> Dict[str, Any]:
    """阻塞等待 subscribe 成功。"""
    retry_with_new_account_enabled = bool(
        CONFIG.get("subscribe_retry_new_account_enabled", DEFAULT_CONFIG["subscribe_retry_new_account_enabled"])
    )
    try:
        retry_with_new_account_limit = int(
            CONFIG.get("subscribe_retry_new_account_limit", DEFAULT_CONFIG["subscribe_retry_new_account_limit"])
        )
    except (TypeError, ValueError):
        retry_with_new_account_limit = int(DEFAULT_CONFIG["subscribe_retry_new_account_limit"])
    retry_with_new_account_limit = max(1, retry_with_new_account_limit)
    failed_attempts = 0

    while True:
        subscribe_result = subscribe_aisub(access_token, validate_result, proxies)
        response_data = subscribe_result.get("response") or {}
        failure_text, failure_reason = _extract_subscribe_failure_info(response_data)
        if subscribe_result.get("status_code") == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
            return subscribe_result
        if "该账号需要额外验证（3DS）" in failure_text:
            detail = f"，原因: {failure_reason}" if failure_reason else ""
            raise RetryWithNewAccount(f"该账号需要额外验证（3DS），切换下一个账号继续复用当前卡{detail}")
        if "需要 hCaptcha challenge" in failure_text:
            detail = f"，原因: {failure_reason}" if failure_reason else ""
            raise RetryWithNewAccount(f"该账号触发 hCaptcha challenge，切换下一个账号继续复用当前卡{detail}")
        failed_attempts += 1
        if retry_with_new_account_enabled and failed_attempts >= retry_with_new_account_limit:
            raise RetryWithNewAccount(
                f"subscribe 连续失败 {failed_attempts} 次，放弃当前账号并重新注册，继续复用当前卡"
            )
        detail = f"，原因: {failure_reason}" if failure_reason else ""
        log_warn(f"subscribe 第 {failed_attempts} 次失败，立即重试{detail}")


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


def _ensure_openai_device_id(session: Any, initial_response: Any = None) -> str:
    def _response_cookie_value(response: Any) -> str:
        if response is None:
            return ""
        cookie_value = str(response.cookies.get("oai-did") or "").strip()
        if cookie_value:
            return cookie_value
        raw_set_cookie = str(response.headers.get("set-cookie") or response.headers.get("Set-Cookie") or "")
        match = re.search(r"oai-did=([^;,\s]+)", raw_set_cookie)
        return str(match.group(1) if match else "").strip()

    did = str(session.cookies.get("oai-did") or "").strip()
    if not did and initial_response is not None:
        did = _response_cookie_value(initial_response)
    if did:
        return did

    for fallback_url in (
        "https://auth.openai.com/create-account",
        "https://auth.openai.com/u/login/identifier",
    ):
        try:
            resp = session.get(fallback_url, timeout=15)
        except Exception:
            continue
        did = str(session.cookies.get("oai-did") or _response_cookie_value(resp) or "").strip()
        if did:
            return did

    return ""


def run(proxy: Optional[str]) -> Optional[str]:
    proxies: Any = None
    if proxy:
        proxies = {"http": proxy, "https": proxy}

    s = requests.Session(proxies=proxies, impersonate="chrome")
    mailbox: Optional[Dict[str, Any]] = None

    try:
        trace = s.get("https://cloudflare.com/cdn-cgi/trace", timeout=10)
        trace = trace.text
        loc_re = re.search(r"^loc=(.+)$", trace, re.MULTILINE)
        loc = loc_re.group(1) if loc_re else None
        if loc == "CN" or loc == "HK":
            raise RuntimeError("检查代理哦w - 所在地不支持")
    except Exception as e:
        log_error(f"网络连接检查失败: {e}")
        return None

    try:
        mailbox = create_registration_email_context(proxies)
    except Exception as e:
        log_error(f"创建注册邮箱失败: {e}")
        return None
    email = str(mailbox.get("email") or "").strip()
    if not email:
        log_error("邮箱创建结果为空")
        return None
    provider_name = "TempMail" if mailbox.get("custom_domain") else _email_provider_label(mailbox.get("email_provider"))
    log_ok(f"邮箱就绪 [{provider_name}]: {email}")

    oauth = generate_oauth_url()
    url = oauth.auth_url

    try:
        resp = s.get(url, timeout=15)
        did = _ensure_openai_device_id(s, resp)
        if not did:
            log_error("未获取到 OpenAI 下发的 Device ID（oai-did Cookie），当前代理/网络无法通过 auth.openai.com 前置校验")
            return None

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
        if signup_resp.status_code >= 400:
            log_error(f"注册入口失败: {signup_resp.status_code}")
            return None

        password = str(mailbox.get("password") or "").strip()
        if not password:
            log_error("注册上下文缺少密码")
            return None

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
        if pwd_resp.status_code >= 400:
            log_error(f"提交注册信息失败: {pwd_resp.status_code}")
            return None

        # 发送邮箱验证码
        otp_resp = s.get(
            "https://auth.openai.com/api/accounts/email-otp/send",
            headers={
                "referer": "https://auth.openai.com/create-account/password",
                "accept": "application/json",
            },
        )
        if otp_resp.status_code >= 400:
            log_error(f"发送验证码失败: {otp_resp.status_code}")
            return None

        code = get_oai_code(mailbox, proxies)
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
        if code_resp.status_code >= 400:
            log_error(f"验证码校验失败: {code_resp.status_code}")
            return None

        full_name = f"{mailbox.get('first_name', '')} {mailbox.get('last_name', '')}".strip()
        birthdate = str(mailbox.get("birthdate") or "2000-02-20").strip()
        create_account_body = json.dumps({"name": full_name or "Neo", "birthdate": birthdate})
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

        if create_account_status != 200:
            log_error(f"账户创建失败: {create_account_status}")
            return None
        log_ok("OpenAI 账号创建完成")

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
                token_json = submit_callback_url(
                    callback_url=next_url,
                    code_verifier=oauth.code_verifier,
                    redirect_uri=oauth.redirect_uri,
                    expected_state=oauth.state,
                )
                try:
                    token_data = json.loads(token_json)
                except Exception:
                    return token_json
                token_data["password"] = password
                token_data["first_name"] = str(mailbox.get("first_name") or "")
                token_data["last_name"] = str(mailbox.get("last_name") or "")
                token_data["birthdate"] = birthdate
                token_data["email_provider"] = str(mailbox.get("email_provider") or "")
                token_data["custom_domain"] = bool(mailbox.get("custom_domain"))
                if mailbox.get("junmail_mailbox_id"):
                    token_data["junmail_mailbox_id"] = str(mailbox.get("junmail_mailbox_id") or "")
                return json.dumps(token_data, ensure_ascii=False, separators=(",", ":"))
            current_url = next_url

        log_error("未能在重定向链中捕获到最终 Callback URL")
        return None

    except Exception as e:
        log_error(f"运行时发生错误: {e}")
        return None


def main() -> None:
    global CURRENT_OUTPUT_DIR
    parser = argparse.ArgumentParser(description="OpenAI 自动注册脚本 (demo 邮箱逻辑版)")
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
    CURRENT_OUTPUT_DIR = create_run_output_dir()
    teams_file = _teams_file_path()
    register_type = _register_type_key()
    registered_accounts = 0
    aisub_uses = 0
    cards_used = 0
    mother_accounts = 0
    ui_started_at = datetime.now()
    started_at = ui_started_at
    ended_at = started_at
    aisub_balance_before: Dict[str, Any] = {}
    aisub_balance_after: Dict[str, Any] = {}
    cdkey_added_count = 0

    count = 0
    cdkey_added_count = sync_code_file_from_cdkeys()
    if sys.stdin.isatty():
        menu_result = prompt_startup_menu(
            proxies,
            started_at=ui_started_at,
            cdkey_added_count=cdkey_added_count,
        )
        if menu_result is None:
            log_info("已退出 Team 注册机")
            return
        aisub_balance_before = menu_result
        proxy_value = args.proxy or str(CONFIG.get("default_proxy") or "").strip() or None
        proxies = {"http": proxy_value, "https": proxy_value} if proxy_value else None
        register_type = _register_type_key()
    try:
        if not sys.stdin.isatty():
            _render_brand_header(
                "Team 注册机",
                f"欢迎使用 Team 注册机，现在是 {_fmt_local_dt(ui_started_at)}",
            )
            _render_kv_table("运行前概览", [("注册类型", _register_type_label(register_type))])
            if register_type == "team":
                print_card_inventory_summary()
                aisub_balance_before = get_aisub_balance_snapshot(proxies)
                print_aisub_balance_summary("运行前 AISub 余额", aisub_balance_before)
        if register_type == "team":
            ensure_aisub_balance(proxies)

        started_at = datetime.now()
        while True:
            count += 1
            if count == 1:
                reset_teams_file(teams_file)
            log_section(f"开始第 {count} 次注册流程")

            try:
                validate_context: Optional[Dict[str, Any]] = None
                validate_result: Dict[str, Any] = {}
                if register_type == "team":
                    ensure_aisub_balance(proxies)
                    validate_context = get_validate_context(proxies)
                    validate_result = validate_context["validate_result"]

                token_json = run(proxy_value)

                if token_json:
                    registered_accounts += 1
                    try:
                        t_data = json.loads(token_json)
                    except Exception:
                        t_data = {}

                    t_data["register_type"] = register_type
                    if register_type == "team":
                        access_token = str(t_data.get("access_token") or "").strip()
                        if not access_token:
                            raise RuntimeError("token_json 中缺少 access_token")
                        if not validate_context:
                            raise RuntimeError("缺少 Team 绑定上下文")

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
                        mother_accounts += 1
                    append_team_entry(teams_file, t_data)
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
        ended_at = datetime.now()
        if register_type == "team":
            aisub_balance_after = get_aisub_balance_snapshot(proxies)
            print_aisub_balance_summary("运行后 AISub 余额", aisub_balance_after)
        print_run_summary(
            register_type=register_type,
            registered_accounts=registered_accounts,
            aisub_uses=aisub_uses,
            cards_used=cards_used,
            mother_accounts=mother_accounts,
            started_at=started_at,
            ended_at=ended_at,
            aisub_balance_before=aisub_balance_before,
            aisub_balance_after=aisub_balance_after,
        )


if __name__ == "__main__":
    main()
