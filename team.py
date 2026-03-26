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
from types import MethodType
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
    "duckmail_api_base": "https://api.duckmail.sbs",
    "duckmail_bearer": "",
    "npcmail_base": "https://dash.xphdfs.me",
    "gptmail_base": "https://mail.chatgpt.org.uk/api",
    "junmail_base": "https://mail.zhujunpeng.cc.cd",
    "lamail_api_base": "https://maliapi.215.im/v1",
    "lamail_api_key": "",
    "lamail_domain": "",
    "cfmail_config_path": "cpa_20260323/zhuce5_cfmail_accounts.json",
    "cfmail_profile": "auto",
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
    "card_provider": "ncet",
    "redeem_base_url": "https://yyl.ncet.top",
    "efuncard_base_url": "https://card.efuncard.com",
    "efuncard_csrf_token": "",
    "efuncard_address_cities_url": "https://usaddressgen.com/data/cities/us-cities.70518e158991aef99b470662cb3b5a408c6e0b189f77fb7c64da1ab6a95ff737.json",
    "efuncard_card_max_use_count": 1,
    "aisub_base_url": "https://stripe.xmdbd.com",
    "aisub_api_key": "sk-49d7e4023898fb4acdb7d0ca0c1d7744b12e13bcda843d7f",
    "aisub_proxy_region": "auto",
    "aisub_payment_mode": "async",
    "aisub_async_timeout": 300,
    "aisub_async_poll_interval": 3,
    "subscribe_plan": "team",
    "team_card_open_timing": "after_register",
    "card_max_use_count": 2,
    "verbose_info_logs_enabled": False,
    "subscribe_retry_new_account_enabled": True,
    "subscribe_switch_account_on_3ds_enabled": True,
    "subscribe_retry_new_account_limit": 50,
    "oauth_client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
    "oauth_originator": "codex_vscode",
    "oauth_redirect_uri": "http://localhost:1455/auth/callback",
    "oauth_scope": "openid email profile offline_access",
    "openai_pow_value": "",
    "token_json_dir": "codex_tokens",
    "ak_file": "ak.txt",
    "rk_file": "rk.txt",
    "upload_api_url": "",
    "upload_api_token": "",
    "upload_api_proxy": "",
    "cpa_cleanup_enabled": True,
    "cpa_upload_every_n": 3,
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


def _get_openai_pow_value() -> str:
    return str(CONFIG.get("openai_pow_value") or DEFAULT_CONFIG["openai_pow_value"]).strip()


def _get_openai_client_id() -> str:
    return str(CONFIG.get("oauth_client_id") or DEFAULT_CONFIG["oauth_client_id"]).strip()


def _get_openai_originator() -> str:
    return str(CONFIG.get("oauth_originator") or DEFAULT_CONFIG["oauth_originator"]).strip()


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
EFUNCARD_CITY_DATA_CACHE: Optional[Dict[str, Any]] = None
LAST_RUN_FAILURE_REASON = ""
FILE_WRITE_LOCK = threading.Lock()
_CPA_REFERENCE_MODULE: Any = None
_CPA_IMPERSONATE_SUPPORT_CACHE: Dict[str, bool] = {}
_CPA_REFERENCE_PROFILES_NORMALIZED = False

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
    "duckmail": "DuckMail",
    "npcmail": "NPCMail",
    "gptmail": "GPTMail",
    "junmail": "JunMail",
    "lamail": "LaMail",
    "cfmail": "CFMail",
    "tempmail_lol": "TempMail.lol",
    "xiaomajiang": "TempMail.lol(兼容旧配置)",
    "local_graph": "本地Outlook邮箱",
    "tempmail": "TempMail",
}

CARD_PROVIDER_LABELS: Dict[str, str] = {
    "ncet": "NCET",
    "efuncard": "EFunCard",
    "hosted": "托管支付",
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


def _info_logs_enabled() -> bool:
    return bool(CONFIG.get("verbose_info_logs_enabled", DEFAULT_CONFIG["verbose_info_logs_enabled"]))


def log_info(message: str) -> None:
    if _info_logs_enabled():
        log_line("INFO", message)


def log_verbose(message: str) -> None:
    log_info(message)


def log_ok(message: str) -> None:
    log_line(" OK ", message)


def log_warn(message: str) -> None:
    log_line("WARN", message)


def log_error(message: str) -> None:
    log_line("ERR ", message)


def _record_last_run_failure(reason: str) -> None:
    global LAST_RUN_FAILURE_REASON
    LAST_RUN_FAILURE_REASON = str(reason or "").strip()


def _peek_last_run_failure() -> str:
    return LAST_RUN_FAILURE_REASON


def _take_last_run_failure() -> str:
    global LAST_RUN_FAILURE_REASON
    reason = LAST_RUN_FAILURE_REASON
    LAST_RUN_FAILURE_REASON = ""
    return reason


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


def _team_card_open_timing_key(value: Any = None) -> str:
    key = str(CONFIG.get("team_card_open_timing") if value is None else value or "").strip().lower()
    if key not in {"before_register", "after_register"}:
        return "after_register"
    return key


def _team_card_open_timing_label(value: Any = None) -> str:
    key = _team_card_open_timing_key(value)
    return "先开卡再注册" if key == "before_register" else "先注册再开卡"


def _aisub_payment_mode_key(value: Any = None) -> str:
    key = str(CONFIG.get("aisub_payment_mode") if value is None else value or "").strip().lower()
    if key not in {"sync", "async"}:
        return "async"
    return key


def _aisub_payment_mode_label(value: Any = None) -> str:
    key = _aisub_payment_mode_key(value)
    return "异步(推荐)" if key == "async" else "同步"


def _card_provider_key(value: Any = None) -> str:
    key = str(CONFIG.get("card_provider") if value is None else value or "").strip().lower()
    if key == "default":
        return "ncet"
    if key not in CARD_PROVIDER_LABELS:
        return "ncet"
    return key


def _card_provider_label(value: Any = None) -> str:
    key = _card_provider_key(value)
    return CARD_PROVIDER_LABELS.get(key, "NCET")


def _uses_hosted_payment(value: Any = None) -> bool:
    return _card_provider_key(value) == "hosted"


def _extract_verification_code(content: str) -> str:
    text = str(content or "")
    patterns = [
        r"Verification code:?\s*(\d{6})",
        r"code is\s*(\d{6})",
        r"代码为[:：]?\s*(\d{6})",
        r"验证码[:：]?\s*(\d{6})",
        r"Your ChatGPT code is\s*(\d{6})",
        r"temporary verification code to continue:\s*(\d{6})",
        r">\s*(\d{6})\s*<",
        r"(?<![#&])\b(\d{6})\b",
        r"\b(\d{4,8})\b",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for code in matches:
            if code == "177010":
                continue
            return str(code)
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


def _cfmail_config_path() -> str:
    return _resolve_config_path(str(CONFIG.get("cfmail_config_path") or DEFAULT_CONFIG["cfmail_config_path"]))


@dataclass(frozen=True)
class CfmailAccount:
    name: str
    worker_domain: str
    email_domain: str
    admin_password: str


_cfmail_account_lock = threading.Lock()
_cfmail_reload_lock = threading.Lock()
_cfmail_account_index = 0
_CFMAIL_ACCOUNTS_CACHE: list[CfmailAccount] = []
_CFMAIL_CONFIG_MTIME: Optional[float] = None


def _normalize_host(value: str) -> str:
    host = str(value or "").strip()
    if host.startswith("https://"):
        host = host[len("https://"):]
    elif host.startswith("http://"):
        host = host[len("http://"):]
    return host.strip().strip("/")


def _normalize_cfmail_account(raw: Dict[str, Any]) -> Optional[CfmailAccount]:
    if not isinstance(raw, dict):
        return None
    if not raw.get("enabled", True):
        return None
    name = str(raw.get("name") or "").strip()
    worker_domain = _normalize_host(raw.get("worker_domain") or raw.get("WORKER_DOMAIN") or "")
    email_domain = _normalize_host(raw.get("email_domain") or raw.get("EMAIL_DOMAIN") or "")
    admin_password = str(raw.get("admin_password") or raw.get("ADMIN_PASSWORD") or "").strip()
    if not name or not worker_domain or not email_domain or not admin_password:
        return None
    return CfmailAccount(
        name=name,
        worker_domain=worker_domain,
        email_domain=email_domain,
        admin_password=admin_password,
    )


def _load_cfmail_accounts_from_file(config_path: str, *, silent: bool = False) -> list[Dict[str, Any]]:
    path = str(config_path or "").strip()
    if not path or not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        if not silent:
            log_warn(f"读取 CFMail 配置失败: {exc}")
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        accounts = data.get("accounts")
        if isinstance(accounts, list):
            return [item for item in accounts if isinstance(item, dict)]
    if not silent:
        log_warn(f"CFMail 配置格式无效: {path}")
    return []


def _build_cfmail_accounts(raw_accounts: list[Dict[str, Any]]) -> list[CfmailAccount]:
    accounts: list[CfmailAccount] = []
    seen_names: set[str] = set()
    for item in raw_accounts:
        account = _normalize_cfmail_account(item)
        if not account:
            continue
        key = account.name.lower()
        if key in seen_names:
            continue
        seen_names.add(key)
        accounts.append(account)

    env_worker_domain = _normalize_host(os.getenv("CFMAIL_WORKER_DOMAIN", ""))
    env_email_domain = _normalize_host(os.getenv("CFMAIL_EMAIL_DOMAIN", ""))
    env_admin_password = str(os.getenv("CFMAIL_ADMIN_PASSWORD", "")).strip()
    env_profile_name = str(os.getenv("CFMAIL_PROFILE_NAME", "default")).strip() or "default"
    if env_worker_domain and env_email_domain and env_admin_password:
        env_account = CfmailAccount(
            name=env_profile_name,
            worker_domain=env_worker_domain,
            email_domain=env_email_domain,
            admin_password=env_admin_password,
        )
        accounts = [item for item in accounts if item.name.lower() != env_account.name.lower()]
        accounts.insert(0, env_account)

    return accounts


def _reload_cfmail_accounts_if_needed(force: bool = False) -> bool:
    global _CFMAIL_CONFIG_MTIME, _CFMAIL_ACCOUNTS_CACHE, _cfmail_account_index
    config_path = _cfmail_config_path()
    if not config_path:
        return False
    try:
        mtime = os.path.getmtime(config_path)
    except OSError:
        if force:
            _CFMAIL_ACCOUNTS_CACHE = []
            _CFMAIL_CONFIG_MTIME = None
        return False
    with _cfmail_reload_lock:
        if not force and _CFMAIL_CONFIG_MTIME == mtime and _CFMAIL_ACCOUNTS_CACHE:
            return False
        raw_accounts = _load_cfmail_accounts_from_file(config_path, silent=True)
        _CFMAIL_ACCOUNTS_CACHE = _build_cfmail_accounts(raw_accounts)
        _CFMAIL_CONFIG_MTIME = mtime
        _cfmail_account_index = 0
        return True


def _select_cfmail_account(profile_name: str = "auto") -> Optional[CfmailAccount]:
    global _cfmail_account_index
    if not _CFMAIL_ACCOUNTS_CACHE:
        _reload_cfmail_accounts_if_needed(force=True)
    accounts = _CFMAIL_ACCOUNTS_CACHE
    if not accounts:
        return None

    selected_name = str(profile_name or "auto").strip()
    if selected_name and selected_name.lower() != "auto":
        for account in accounts:
            if account.name.lower() == selected_name.lower():
                return account
        return None

    with _cfmail_account_lock:
        index = _cfmail_account_index % len(accounts)
        account = accounts[index]
        _cfmail_account_index = (index + 1) % len(accounts)
        return account


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


def _create_duckmail_session(proxies: Any = None) -> Any:
    session = requests.Session(proxies=proxies, impersonate="chrome131")
    session.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
    )
    return session


def _create_duckmail_mailbox(proxies: Any = None) -> Dict[str, str]:
    bearer = str(CONFIG.get("duckmail_bearer") or DEFAULT_CONFIG["duckmail_bearer"]).strip()
    if not bearer:
        raise RuntimeError("请先配置 DuckMail Bearer")
    api_base = str(CONFIG.get("duckmail_api_base") or DEFAULT_CONFIG["duckmail_api_base"]).strip().rstrip("/")
    chars = string.ascii_lowercase + string.digits
    local_part = "".join(random.choice(chars) for _ in range(random.randint(8, 13)))
    email = f"{local_part}@duckmail.sbs"
    email_password = _generate_password()
    session = _create_duckmail_session(proxies)

    try:
        create_resp = session.post(
            f"{api_base}/accounts",
            json={"address": email, "password": email_password},
            headers={"Authorization": f"Bearer {bearer}"},
            timeout=15,
        )
        if create_resp.status_code not in (200, 201):
            raise RuntimeError(f"DuckMail 创建邮箱失败: HTTP {create_resp.status_code}")
        time.sleep(0.5)
        token_resp = session.post(
            f"{api_base}/token",
            json={"address": email, "password": email_password},
            timeout=15,
        )
        if token_resp.status_code != 200:
            raise RuntimeError(f"DuckMail 获取 Token 失败: HTTP {token_resp.status_code}")
        payload = token_resp.json() if token_resp.content else {}
    finally:
        try:
            session.close()
        except Exception:
            pass

    token = str(payload.get("token") or "").strip() if isinstance(payload, dict) else ""
    if not token:
        raise RuntimeError("DuckMail 返回 token 为空")
    return {"email": email, "email_password": email_password, "token": token}


def _fetch_duckmail_messages(mail_token: str, proxies: Any = None) -> list[Dict[str, Any]]:
    if not mail_token:
        return []
    api_base = str(CONFIG.get("duckmail_api_base") or DEFAULT_CONFIG["duckmail_api_base"]).strip().rstrip("/")
    session = _create_duckmail_session(proxies)
    try:
        resp = session.get(
            f"{api_base}/messages",
            headers={"Authorization": f"Bearer {mail_token}"},
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        payload = resp.json() if resp.content else {}
    except Exception:
        return []
    finally:
        try:
            session.close()
        except Exception:
            pass
    if not isinstance(payload, dict):
        return []
    messages = payload.get("hydra:member") or payload.get("member") or payload.get("data") or []
    return messages if isinstance(messages, list) else []


def _fetch_duckmail_message_detail(mail_token: str, msg_id: str, proxies: Any = None) -> Optional[Dict[str, Any]]:
    if not mail_token or not msg_id:
        return None
    api_base = str(CONFIG.get("duckmail_api_base") or DEFAULT_CONFIG["duckmail_api_base"]).strip().rstrip("/")
    normalized_id = str(msg_id).split("/")[-1]
    session = _create_duckmail_session(proxies)
    try:
        resp = session.get(
            f"{api_base}/messages/{normalized_id}",
            headers={"Authorization": f"Bearer {mail_token}"},
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        payload = resp.json() if resp.content else {}
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None
    finally:
        try:
            session.close()
        except Exception:
            pass


def _fetch_duckmail_code(mail_token: str, proxies: Any = None) -> str:
    messages = _fetch_duckmail_messages(mail_token, proxies)
    for message in messages:
        if not isinstance(message, dict):
            continue
        msg_id = str(message.get("id") or message.get("@id") or "").strip()
        content = _stringify_message_payload(message)
        if not _looks_like_openai_message(content) and msg_id:
            detail = _fetch_duckmail_message_detail(mail_token, msg_id, proxies)
            content = _stringify_message_payload(detail)
        if not _looks_like_openai_message(content):
            continue
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


def _lamail_headers(*, bearer: str = "", use_json: bool = False, api_key: str = "") -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if use_json:
        headers["Content-Type"] = "application/json"
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    if api_key:
        headers["X-API-Key"] = api_key
    return headers


def _lamail_unwrap_json(resp: Any, *, action: str = "请求") -> Any:
    try:
        payload = resp.json() if resp.content else {}
    except Exception as exc:
        raise RuntimeError(f"LaMail {action}返回非 JSON: HTTP {resp.status_code}") from exc
    if isinstance(payload, dict) and "success" in payload:
        if payload.get("success") is not True:
            raise RuntimeError(str(payload.get("error") or f"LaMail {action}失败"))
        return payload.get("data")
    return payload


def _create_lamail_mailbox(proxies: Any = None) -> Dict[str, str]:
    api_base = str(CONFIG.get("lamail_api_base") or DEFAULT_CONFIG["lamail_api_base"]).strip().rstrip("/")
    api_key = str(CONFIG.get("lamail_api_key") or DEFAULT_CONFIG["lamail_api_key"]).strip()
    domain = str(CONFIG.get("lamail_domain") or DEFAULT_CONFIG["lamail_domain"]).strip()
    payload: Dict[str, Any] = {}
    if domain:
        payload["domain"] = domain
    resp = requests.post(
        f"{api_base}/accounts",
        json=payload,
        headers=_lamail_headers(use_json=True, api_key=api_key),
        proxies=proxies,
        impersonate="chrome",
        timeout=15,
    )
    if resp.status_code not in (200, 201):
        raise RuntimeError(f"LaMail 创建邮箱失败: HTTP {resp.status_code}")
    data = _lamail_unwrap_json(resp, action="创建邮箱")
    if not isinstance(data, dict):
        raise RuntimeError("LaMail 创建邮箱返回格式异常")
    email = str(data.get("address") or data.get("email") or "").strip()
    token = str(data.get("token") or "").strip()
    if not email or not token:
        raise RuntimeError("LaMail 返回邮箱或 token 为空")
    return {"email": email, "token": token}


def _fetch_lamail_messages(mail_token: str, email: str, proxies: Any = None) -> list[Dict[str, Any]]:
    if not mail_token or not email:
        return []
    api_base = str(CONFIG.get("lamail_api_base") or DEFAULT_CONFIG["lamail_api_base"]).strip().rstrip("/")
    try:
        resp = requests.get(
            f"{api_base}/messages",
            params={"address": email},
            headers=_lamail_headers(bearer=mail_token),
            proxies=proxies,
            impersonate="chrome",
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        data = _lamail_unwrap_json(resp, action="拉取邮件列表")
    except Exception:
        return []
    if not isinstance(data, dict):
        return []
    messages = data.get("messages") or []
    return messages if isinstance(messages, list) else []


def _fetch_lamail_message_detail(mail_token: str, msg_id: str, proxies: Any = None) -> Optional[Dict[str, Any]]:
    if not mail_token or not msg_id:
        return None
    api_base = str(CONFIG.get("lamail_api_base") or DEFAULT_CONFIG["lamail_api_base"]).strip().rstrip("/")
    try:
        resp = requests.get(
            f"{api_base}/messages/{quote(msg_id)}",
            headers=_lamail_headers(bearer=mail_token),
            proxies=proxies,
            impersonate="chrome",
            timeout=15,
        )
        if resp.status_code != 200:
            return None
        data = _lamail_unwrap_json(resp, action="拉取邮件详情")
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _fetch_lamail_code(mail_token: str, email: str, proxies: Any = None) -> str:
    messages = _fetch_lamail_messages(mail_token, email, proxies)
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        content = _stringify_message_payload(message)
        if not _looks_like_openai_message(content):
            detail = _fetch_lamail_message_detail(
                mail_token,
                str(message.get("id") or "").strip(),
                proxies,
            )
            content = _stringify_message_payload(detail)
        if not _looks_like_openai_message(content):
            continue
        code = _extract_verification_code(content)
        if code:
            return code
    return ""


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
        if not _looks_like_openai_message(content):
            continue
        code = _extract_verification_code(content)
        if code:
            return code
    return ""


def _create_cfmail_mailbox(proxies: Any = None) -> Dict[str, Any]:
    _reload_cfmail_accounts_if_needed()
    profile_name = str(CONFIG.get("cfmail_profile") or DEFAULT_CONFIG["cfmail_profile"]).strip() or "auto"
    account = _select_cfmail_account(profile_name)
    if not account:
        raise RuntimeError(f"没有可用的 CFMail 配置，请检查: {_cfmail_config_path()}")

    local_part = f"oc{secrets.token_hex(5)}"
    resp = requests.post(
        f"https://{account.worker_domain}/admin/new_address",
        headers={
            "x-admin-auth": account.admin_password,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json={"enablePrefix": True, "name": local_part, "domain": account.email_domain},
        proxies=proxies,
        impersonate="chrome",
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"CFMail 创建邮箱失败: HTTP {resp.status_code}")
    try:
        payload = resp.json() if resp.content else {}
    except Exception as exc:
        raise RuntimeError("CFMail 创建邮箱返回非 JSON") from exc
    email = str(payload.get("address") or "").strip()
    token = str(payload.get("jwt") or "").strip()
    if not email or not token:
        raise RuntimeError("CFMail 返回邮箱或 jwt 为空")
    return {
        "email": email,
        "token": token,
        "cfmail_api_base": f"https://{account.worker_domain}",
        "cfmail_account_name": account.name,
    }


def _fetch_cfmail_messages(mailbox: Dict[str, Any], proxies: Any = None) -> list[Dict[str, Any]]:
    api_base = str(mailbox.get("cfmail_api_base") or "").strip()
    mail_token = str(mailbox.get("tm_token") or "").strip()
    if not api_base or not mail_token:
        return []
    try:
        resp = requests.get(
            f"{api_base}/api/mails",
            params={"limit": 10, "offset": 0},
            headers={"Accept": "application/json", "Authorization": f"Bearer {mail_token}"},
            proxies=proxies,
            impersonate="chrome",
            timeout=15,
        )
        if resp.status_code != 200:
            return []
        payload = resp.json() if resp.content else {}
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []
    messages = payload.get("results") or []
    return messages if isinstance(messages, list) else []


def _fetch_cfmail_code(mailbox: Dict[str, Any], proxies: Any = None) -> str:
    email = str(mailbox.get("email") or "").strip().lower()
    messages = _fetch_cfmail_messages(mailbox, proxies)
    patterns = [
        r"Subject:\s*Your ChatGPT code is\s*(\d{6})",
        r"Your ChatGPT code is\s*(\d{6})",
        r"temporary verification code to continue:\s*(\d{6})",
        r"(?<![#&])\b(\d{6})\b",
    ]
    for message in messages:
        if not isinstance(message, dict):
            continue
        recipient = str(message.get("address") or "").strip().lower()
        if recipient and email and recipient != email:
            continue
        content = _stringify_message_payload(message)
        if not _looks_like_openai_message(content):
            continue
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return str(match.group(1) or "").strip()
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
    if provider == "duckmail":
        mailbox = _create_duckmail_mailbox(proxies)
        context.update(
            {
                "email": mailbox["email"],
                "email_provider": "duckmail",
                "custom_domain": False,
                "tm_token": mailbox["token"],
                "email_password": mailbox["email_password"],
            }
        )
        return context

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

    if provider in {"tempmail_lol", "xiaomajiang"}:
        inbox = _create_tempmail_lol_inbox(proxies)
        context.update(
            {
                "email": inbox["email"],
                "email_provider": "tempmail_lol",
                "custom_domain": False,
                "tm_token": inbox["token"],
            }
        )
        return context

    if provider == "lamail":
        mailbox = _create_lamail_mailbox(proxies)
        context.update(
            {
                "email": mailbox["email"],
                "email_provider": "lamail",
                "custom_domain": False,
                "tm_token": mailbox["token"],
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

    if provider == "cfmail":
        mailbox = _create_cfmail_mailbox(proxies)
        context.update(
            {
                "email": mailbox["email"],
                "email_provider": "cfmail",
                "custom_domain": False,
                "tm_token": mailbox["token"],
                "cfmail_api_base": mailbox["cfmail_api_base"],
                "cfmail_account_name": mailbox["cfmail_account_name"],
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


def get_oai_code(
    mailbox: Dict[str, Any],
    proxies: Any = None,
    *,
    timeout_seconds: int = 180,
    tried_codes: Optional[set[str]] = None,
) -> str:
    email = str(mailbox.get("email") or "").strip()
    provider = str(mailbox.get("email_provider") or "gptmail").strip().lower()
    receiver_addr = str(mailbox.get("tm_addr") or "").strip()
    receiver_epin = str(mailbox.get("tm_epin") or "").strip()
    tempmail_lol_token = str(mailbox.get("tm_token") or "").strip()
    blocked_codes = tried_codes if isinstance(tried_codes, set) else set()
    attempts = max(1, int(math.ceil(max(1, timeout_seconds) / 3)))

    for attempt in range(attempts):
        try:
            if mailbox.get("custom_domain") and receiver_addr:
                code = _fetch_tempmail_plus_code(receiver_addr, receiver_epin, proxies)
            elif provider == "duckmail":
                code = _fetch_duckmail_code(tempmail_lol_token, proxies)
            elif provider == "npcmail":
                code = _fetch_npcmail_code(email, proxies)
            elif provider == "tempmail_lol" or provider == "xiaomajiang":
                code = _fetch_tempmail_lol_code(tempmail_lol_token, proxies)
            elif provider == "lamail":
                code = _fetch_lamail_code(tempmail_lol_token, email, proxies)
            elif provider == "junmail":
                code = _fetch_junmail_code(str(mailbox.get("junmail_mailbox_id") or "").strip(), proxies)
            elif provider == "cfmail":
                code = _fetch_cfmail_code(mailbox, proxies)
            elif provider == "local_graph":
                code = _fetch_graph_mail_code(mailbox, proxies)
            else:
                code = _fetch_gptmail_code(email, proxies)
            if code and code not in blocked_codes:
                log_ok(f"收到验证码: {code}")
                return code
        except Exception:
            pass
        if attempt < attempts - 1:
            time.sleep(3)
    log_warn("验证码超时")
    return ""


# ==========================================
# OAuth 授权与辅助函数
# ==========================================

AUTH_URL = "https://auth.openai.com/oauth/authorize"
TOKEN_URL = "https://auth.openai.com/oauth/token"
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
    aisub_base_url = str(CONFIG.get("aisub_base_url") or DEFAULT_CONFIG["aisub_base_url"]).rstrip("/")
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "*/*",
        "Referer": f"{aisub_base_url}/",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
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


def _ak_file_path() -> str:
    return _resolve_config_path(str(CONFIG.get("ak_file") or DEFAULT_CONFIG["ak_file"]))


def _rk_file_path() -> str:
    return _resolve_config_path(str(CONFIG.get("rk_file") or DEFAULT_CONFIG["rk_file"]))


def _token_json_dir_path() -> str:
    return _resolve_config_path(str(CONFIG.get("token_json_dir") or DEFAULT_CONFIG["token_json_dir"]))


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(str(path or ""))
    if parent:
        os.makedirs(parent, exist_ok=True)


def _append_text_line(file_path: str, line: str) -> None:
    if not file_path or not line:
        return
    _ensure_parent_dir(file_path)
    with FILE_WRITE_LOCK:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"{line}\n")


def _save_codex_token_artifacts(token_data: Dict[str, Any]) -> str:
    if not isinstance(token_data, dict):
        return ""
    email = str(token_data.get("email") or "").strip()
    access_token = str(token_data.get("access_token") or "").strip()
    refresh_token = str(token_data.get("refresh_token") or "").strip()
    if not email or not access_token:
        return ""

    if access_token:
        _append_text_line(_ak_file_path(), access_token)
    if refresh_token:
        _append_text_line(_rk_file_path(), refresh_token)

    token_payload = dict(token_data)
    token_payload["type"] = str(token_payload.get("type") or "codex")
    token_dir = _token_json_dir_path()
    os.makedirs(token_dir, exist_ok=True)
    token_path = os.path.join(token_dir, f"{email}.json")
    with FILE_WRITE_LOCK:
        with open(token_path, "w", encoding="utf-8") as f:
            json.dump(token_payload, f, ensure_ascii=False, indent=2)
    return token_path


def _resolve_cpa_upload_proxy_candidates() -> list[Optional[str]]:
    configured = str(CONFIG.get("upload_api_proxy") or DEFAULT_CONFIG["upload_api_proxy"]).strip()
    default_proxy = str(CONFIG.get("default_proxy") or DEFAULT_CONFIG["default_proxy"]).strip()
    if configured:
        lowered = configured.lower()
        if lowered in {"direct", "none", "off", "false", "0"}:
            return [None]
        if lowered == "default":
            return [default_proxy or None, None]
        return [configured]
    if default_proxy:
        return [default_proxy, None]
    return [None]


def _upload_token_json(filepath: str) -> bool:
    upload_api_url = str(CONFIG.get("upload_api_url") or DEFAULT_CONFIG["upload_api_url"]).strip()
    upload_api_token = str(CONFIG.get("upload_api_token") or DEFAULT_CONFIG["upload_api_token"]).strip()
    if not upload_api_url or not filepath or not os.path.exists(filepath):
        return False

    filename = os.path.basename(filepath)
    proxy_candidates: list[Optional[str]] = []
    for item in _resolve_cpa_upload_proxy_candidates():
        if item not in proxy_candidates:
            proxy_candidates.append(item)

    last_error = ""
    for index, proxy in enumerate(proxy_candidates):
        mime = None
        session = None
        try:
            from curl_cffi import CurlMime

            mime = CurlMime()
            mime.addpart(
                name="file",
                content_type="application/json",
                filename=filename,
                local_path=filepath,
            )
            session = requests.Session()
            if proxy:
                session.proxies = {"http": proxy, "https": proxy}
            headers = {"Authorization": f"Bearer {upload_api_token}"} if upload_api_token else {}
            resp = session.post(
                upload_api_url,
                multipart=mime,
                headers=headers,
                verify=False,
                timeout=30,
            )
            if resp.status_code == 200:
                mode = f"代理 {proxy}" if proxy else "直连"
                log_ok(f"CPA 自动导入成功: {filename} ({mode})")
                return True
            last_error = f"HTTP {resp.status_code}"
            if proxy and index < len(proxy_candidates) - 1:
                log_warn(f"CPA 上传失败，切换直连重试: {filename} ({last_error})")
                continue
            log_warn(f"CPA 上传失败: {filename} ({last_error})")
            return False
        except Exception as exc:
            last_error = str(exc)
            if proxy and index < len(proxy_candidates) - 1:
                log_warn(f"CPA 代理上传异常，切换直连重试: {filename} ({exc})")
                continue
            log_warn(f"CPA 上传异常: {filename} ({exc})")
            return False
        finally:
            if mime:
                try:
                    mime.close()
                except Exception:
                    pass
            if session:
                try:
                    session.close()
                except Exception:
                    pass

    if last_error:
        log_warn(f"CPA 上传失败: {filename} ({last_error})")
    return False


def _upload_all_tokens_to_cpa() -> tuple[int, int]:
    upload_api_url = str(CONFIG.get("upload_api_url") or DEFAULT_CONFIG["upload_api_url"]).strip()
    if not upload_api_url:
        return 0, 0
    token_dir = _token_json_dir_path()
    if not os.path.isdir(token_dir):
        return 0, 0
    json_files = sorted(filename for filename in os.listdir(token_dir) if filename.endswith(".json"))
    if not json_files:
        return 0, 0

    log_info(f"CPA 自动导入开始，共 {len(json_files)} 个 token 文件")
    uploaded = 0
    failed = 0
    for filename in json_files:
        filepath = os.path.join(token_dir, filename)
        if _upload_token_json(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
            uploaded += 1
        else:
            failed += 1

    if failed == 0:
        log_ok(f"CPA 自动导入完成: 成功 {uploaded} 个")
    else:
        log_warn(f"CPA 自动导入完成: 成功 {uploaded} 个，失败 {failed} 个")
    return uploaded, failed


def _load_cpa_reference_module() -> Any:
    global _CPA_REFERENCE_MODULE
    if _CPA_REFERENCE_MODULE is not None:
        return _CPA_REFERENCE_MODULE

    script_path = os.path.join(BASE_DIR, "cpa_20260323", "ncs_register.py")
    if not os.path.exists(script_path):
        raise RuntimeError(f"未找到参考脚本: {script_path}")

    spec = importlib.util.spec_from_file_location("teamkeygen_cpa_reference", script_path)
    if not spec or not spec.loader:
        raise RuntimeError("加载 CPA 参考脚本失败")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _CPA_REFERENCE_MODULE = module
    return module


def _run_cpa_cleanup_before_register() -> None:
    upload_api_url = str(CONFIG.get("upload_api_url") or DEFAULT_CONFIG["upload_api_url"]).strip()
    upload_api_token = str(CONFIG.get("upload_api_token") or DEFAULT_CONFIG["upload_api_token"]).strip()
    if not upload_api_url:
        return
    if not upload_api_token:
        log_warn("已配置 CPA 上传地址，但未配置管理密钥，跳过注册前清理")
        return

    try:
        module = _load_cpa_reference_module()
        log_info("注册前开始清理 CPA 无效号")
        result = module._cpa_execute_cleanup(
            {
                "management_url": upload_api_url,
                "management_token": upload_api_token,
                "active_probe": True,
                "probe_workers": 12,
                "delete_workers": 8,
                "max_active_probes": 120,
            },
            log=lambda message: log_info(f"[CPA清理] {message}"),
        )
        log_ok(
            f"CPA 清理完成: 扫描 {int(result.get('scanned_total') or 0)} 个，"
            f"删除 {int(result.get('deleted_total') or 0)} 个"
        )
    except Exception as exc:
        log_warn(f"CPA 清理失败，继续注册: {exc}")


def _extract_code_from_url(url: str) -> str:
    if not url or "code=" not in url:
        return ""
    try:
        return str(parse_qs(urlparse(url).query).get("code", [""])[0] or "").strip()
    except Exception:
        return ""


def _build_proxy_dict(proxy: Optional[str]) -> Any:
    value = str(proxy or "").strip()
    if not value:
        return None
    return {"http": value, "https": value}


def _sync_cpa_reference_runtime(module: Any) -> None:
    module.OAUTH_ISSUER = "https://auth.openai.com"
    module.OAUTH_CLIENT_ID = _get_openai_client_id()
    module.OAUTH_REDIRECT_URI = str(
        CONFIG.get("oauth_redirect_uri") or DEFAULT_CONFIG["oauth_redirect_uri"]
    ).strip()


def _is_unsupported_impersonate_error(exc: Exception) -> bool:
    text = str(exc or "").strip()
    return exc.__class__.__name__ == "ImpersonateError" or (
        "Impersonating" in text and "not supported" in text
    )


def _cpa_impersonate_supported(module: Any, impersonate: str) -> bool:
    key = str(impersonate or "").strip()
    if not key:
        return False
    cached = _CPA_IMPERSONATE_SUPPORT_CACHE.get(key)
    if cached is not None:
        return cached

    supported = True
    session = None
    try:
        session = module.curl_requests.Session(impersonate=key)
        try:
            session.get("https://example.com", timeout=1, verify=False)
        except Exception as exc:
            supported = not _is_unsupported_impersonate_error(exc)
    except Exception as exc:
        supported = not _is_unsupported_impersonate_error(exc)
    finally:
        try:
            if session is not None:
                session.close()
        except Exception:
            pass

    _CPA_IMPERSONATE_SUPPORT_CACHE[key] = supported
    return supported


def _normalize_cpa_reference_profiles(module: Any) -> None:
    global _CPA_REFERENCE_PROFILES_NORMALIZED
    if _CPA_REFERENCE_PROFILES_NORMALIZED:
        return

    profiles = list(getattr(module, "_CHROME_PROFILES", []) or [])
    if not profiles:
        _CPA_REFERENCE_PROFILES_NORMALIZED = True
        return

    supported_profiles = [
        profile
        for profile in profiles
        if _cpa_impersonate_supported(module, str(profile.get("impersonate") or ""))
    ]
    if supported_profiles:
        unsupported = [
            str(profile.get("impersonate") or "")
            for profile in profiles
            if profile not in supported_profiles
        ]
        module._CHROME_PROFILES = supported_profiles

    _CPA_REFERENCE_PROFILES_NORMALIZED = True


def _cpa_style_wait_for_verification_email(
    self: Any,
    mail_token: str,
    timeout: int = 120,
    email: str = "",
    provider: str = "",
) -> Optional[str]:
    mailbox = dict(getattr(self, "_team_mailbox_context", {}) or {})
    if mail_token and not mailbox.get("tm_token"):
        mailbox["tm_token"] = mail_token
    if email and not mailbox.get("email"):
        mailbox["email"] = email
    proxy_mapping = _build_proxy_dict(getattr(self, "proxy", None))
    code = get_oai_code(mailbox, proxy_mapping, timeout_seconds=max(1, int(timeout or 120)))
    return code or None


def _cpa_reference_verbose_enabled() -> bool:
    return bool(CONFIG.get("verbose_info_logs_enabled", DEFAULT_CONFIG["verbose_info_logs_enabled"]))


def _cpa_style_log(
    self: Any,
    step: Any,
    method: Any,
    url: Any,
    status: Any,
    body: Any = None,
) -> None:
    if not _cpa_reference_verbose_enabled():
        return
    original = getattr(self, "_team_original_log", None)
    if callable(original):
        original(step, method, url, status, body)


def _cpa_style_print(self: Any, *parts: Any, **kwargs: Any) -> None:
    if not _cpa_reference_verbose_enabled():
        return
    original = getattr(self, "_team_original_print", None)
    if callable(original):
        original(*parts, **kwargs)
        return
    print(*parts, **kwargs)


def _build_cpa_style_register(proxy: Optional[str], mailbox: Dict[str, Any]) -> Any:
    module = _load_cpa_reference_module()
    _sync_cpa_reference_runtime(module)
    _normalize_cpa_reference_profiles(module)
    reg = module.ChatGPTRegister(proxy=proxy or None)
    reg._team_mailbox_context = dict(mailbox or {})
    if mailbox.get("cfmail_api_base"):
        reg._cfmail_api_base = str(mailbox.get("cfmail_api_base") or "")
    if mailbox.get("cfmail_account_name"):
        reg._cfmail_account_name = str(mailbox.get("cfmail_account_name") or "")
    reg._team_original_log = getattr(reg, "_log", None)
    reg._team_original_print = getattr(reg, "_print", None)
    reg._log = MethodType(_cpa_style_log, reg)
    reg._print = MethodType(_cpa_style_print, reg)
    reg.wait_for_verification_email = MethodType(_cpa_style_wait_for_verification_email, reg)
    return reg


def _perform_cpa_style_codex_oauth_login_http(
    reg: Any,
    *,
    mailbox: Dict[str, Any],
    email: str,
    password: str,
) -> Optional[str]:
    module = _load_cpa_reference_module()
    _sync_cpa_reference_runtime(module)
    oauth = generate_oauth_url()
    issuer = "https://auth.openai.com"

    reg._print("[OAuth] 开始执行 Codex OAuth 纯协议流程...")
    reg.session.cookies.set("oai-did", reg.device_id, domain=".auth.openai.com")
    reg.session.cookies.set("oai-did", reg.device_id, domain="auth.openai.com")

    authorize_url = oauth.auth_url
    provider = str(mailbox.get("email_provider") or "").strip().lower()
    proxy_mapping = _build_proxy_dict(getattr(reg, "proxy", None))

    def _oauth_json_headers(referer: str) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": issuer,
            "Referer": referer,
            "User-Agent": reg.ua,
            "oai-device-id": reg.device_id,
        }
        headers.update(module._make_trace_headers())
        return headers

    def _bootstrap_oauth_session() -> tuple[bool, str]:
        reg._print("[OAuth] 1/7 GET /oauth/authorize")
        try:
            resp = reg.session.get(
                authorize_url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": f"{reg.BASE}/",
                    "Upgrade-Insecure-Requests": "1",
                    "User-Agent": reg.ua,
                },
                allow_redirects=True,
                timeout=30,
                impersonate=reg.impersonate,
            )
        except Exception as exc:
            reg._print(f"[OAuth] /oauth/authorize 异常: {exc}")
            return False, ""

        final_url = str(resp.url)
        has_login_session = any(
            getattr(cookie, "name", "") == "login_session" for cookie in reg.session.cookies
        )
        if not has_login_session:
            try:
                resp_fallback = reg.session.get(
                    f"{issuer}/api/oauth/oauth2/auth",
                    headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Referer": authorize_url,
                        "Upgrade-Insecure-Requests": "1",
                        "User-Agent": reg.ua,
                    },
                    params=dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(authorize_url).query)),
                    allow_redirects=True,
                    timeout=30,
                    impersonate=reg.impersonate,
                )
                final_url = str(resp_fallback.url)
            except Exception as exc:
                reg._print(f"[OAuth] /api/oauth/oauth2/auth 异常: {exc}")
            has_login_session = any(
                getattr(cookie, "name", "") == "login_session" for cookie in reg.session.cookies
            )
        return has_login_session, final_url

    def _post_authorize_continue(referer_url: str) -> Any:
        sentinel_authorize = module.build_sentinel_token(
            reg.session,
            reg.device_id,
            flow="authorize_continue",
            user_agent=reg.ua,
            sec_ch_ua=reg.sec_ch_ua,
            impersonate=reg.impersonate,
        )
        if not sentinel_authorize:
            reg._print("[OAuth] sentinel authorize token 生成失败")
            return None
        headers_continue = _oauth_json_headers(referer_url)
        headers_continue["openai-sentinel-token"] = sentinel_authorize
        try:
            return reg.session.post(
                f"{issuer}/api/accounts/authorize/continue",
                json={"username": {"kind": "email", "value": email}},
                headers=headers_continue,
                timeout=30,
                allow_redirects=False,
                impersonate=reg.impersonate,
            )
        except Exception as exc:
            reg._print(f"[OAuth] authorize/continue 异常: {exc}")
            return None

    _, authorize_final_url = _bootstrap_oauth_session()
    if not authorize_final_url:
        return None

    continue_referer = (
        authorize_final_url if authorize_final_url.startswith(issuer) else f"{issuer}/log-in"
    )
    reg._print("[OAuth] 2/7 POST /api/accounts/authorize/continue")
    resp_continue = _post_authorize_continue(continue_referer)
    if resp_continue is None:
        reg._print("[OAuth] authorize/continue 请求未发出或失败")
        return None

    reg._print(f"[OAuth] /authorize/continue -> {resp_continue.status_code}")
    if resp_continue.status_code == 400 and "invalid_auth_step" in (resp_continue.text or ""):
        _, authorize_final_url = _bootstrap_oauth_session()
        if not authorize_final_url:
            return None
        continue_referer = (
            authorize_final_url if authorize_final_url.startswith(issuer) else f"{issuer}/log-in"
        )
        resp_continue = _post_authorize_continue(continue_referer)
        if resp_continue is None:
            reg._print("[OAuth] authorize/continue 重试失败")
            return None

    if resp_continue.status_code != 200:
        reg._print(
            f"[OAuth] authorize/continue 非200: {resp_continue.status_code}, body={resp_continue.text[:220]}"
        )
        return None

    try:
        continue_data = resp_continue.json()
    except Exception:
        reg._print(f"[OAuth] authorize/continue JSON 解析失败: {resp_continue.text[:220]}")
        return None

    continue_url = str(continue_data.get("continue_url") or "").strip()
    page_type = str(((continue_data.get("page") or {}).get("type") or "")).strip()

    reg._print("[OAuth] 3/7 POST /api/accounts/password/verify")
    sentinel_pwd = module.build_sentinel_token(
        reg.session,
        reg.device_id,
        flow="password_verify",
        user_agent=reg.ua,
        sec_ch_ua=reg.sec_ch_ua,
        impersonate=reg.impersonate,
    )
    if not sentinel_pwd:
        reg._print("[OAuth] sentinel password token 生成失败")
        return None

    headers_verify = _oauth_json_headers(f"{issuer}/log-in/password")
    headers_verify["openai-sentinel-token"] = sentinel_pwd
    try:
        resp_verify = reg.session.post(
            f"{issuer}/api/accounts/password/verify",
            json={"password": password},
            headers=headers_verify,
            timeout=30,
            allow_redirects=False,
            impersonate=reg.impersonate,
        )
    except Exception as exc:
        reg._print(f"[OAuth] password/verify 异常: {exc}")
        return None

    if resp_verify.status_code != 200:
        reg._print(
            f"[OAuth] password/verify 非200: {resp_verify.status_code}, body={resp_verify.text[:220]}"
        )
        return None

    try:
        verify_data = resp_verify.json()
    except Exception:
        reg._print(f"[OAuth] password/verify JSON 解析失败: {resp_verify.text[:220]}")
        return None

    continue_url = str(verify_data.get("continue_url") or continue_url or "").strip()
    page_type = str(((verify_data.get("page") or {}).get("type") or page_type or "")).strip()

    need_oauth_otp = (
        page_type == "email_otp_verification"
        or "email-verification" in continue_url
        or "email-otp" in continue_url
    )
    if need_oauth_otp:
        reg._print("[OAuth] 4/7 检测到邮箱 OTP 验证")
        tried_codes: set[str] = set()
        otp_code = get_oai_code(
            mailbox,
            proxy_mapping,
            timeout_seconds=120,
            tried_codes=tried_codes,
        )
        if not otp_code:
            reg._print("[OAuth] OAuth 阶段 OTP 验证失败")
            return None
        tried_codes.add(otp_code)

        headers_otp = _oauth_json_headers(f"{issuer}/email-verification")
        try:
            resp_otp = reg.session.post(
                f"{issuer}/api/accounts/email-otp/validate",
                json={"code": otp_code},
                headers=headers_otp,
                timeout=30,
                allow_redirects=False,
                impersonate=reg.impersonate,
            )
        except Exception as exc:
            reg._print(f"[OAuth] email-otp/validate 异常: {exc}")
            return None
        if resp_otp.status_code != 200:
            reg._print(
                f"[OAuth] email-otp/validate 非200: {resp_otp.status_code}, body={resp_otp.text[:220]}"
            )
            return None
        try:
            otp_data = resp_otp.json()
        except Exception:
            reg._print(f"[OAuth] email-otp/validate JSON 解析失败: {resp_otp.text[:220]}")
            return None
        continue_url = str(otp_data.get("continue_url") or continue_url or "").strip()
        page_type = str(((otp_data.get("page") or {}).get("type") or page_type or "")).strip()

    code = ""
    consent_url = continue_url
    if consent_url and consent_url.startswith("/"):
        consent_url = f"{issuer}{consent_url}"
    if consent_url:
        code = _extract_code_from_url(consent_url)

    if not code and consent_url:
        reg._print("[OAuth] 5/7 跟随 continue_url 提取 code")
        code, _ = reg._oauth_follow_for_code(consent_url, referer=f"{issuer}/log-in/password")

    consent_hint = (
        ("consent" in (consent_url or ""))
        or ("sign-in-with-chatgpt" in (consent_url or ""))
        or ("workspace" in (consent_url or ""))
        or ("organization" in (consent_url or ""))
        or ("consent" in page_type)
        or ("organization" in page_type)
    )

    if not code and consent_hint:
        if not consent_url:
            consent_url = f"{issuer}/sign-in-with-chatgpt/codex/consent"
        reg._print("[OAuth] 6/7 执行 workspace/org 选择")
        code = reg._oauth_submit_workspace_and_org(consent_url)

    if not code:
        fallback_consent = f"{issuer}/sign-in-with-chatgpt/codex/consent"
        reg._print("[OAuth] 6/7 回退 consent 路径重试")
        code = reg._oauth_submit_workspace_and_org(fallback_consent)
        if not code:
            code, _ = reg._oauth_follow_for_code(
                fallback_consent,
                referer=f"{issuer}/log-in/password",
            )

    if not code:
        reg._print("[OAuth] 未获取到 authorization code")
        return None

    reg._print("[OAuth] 7/7 POST /oauth/token")
    callback_url = f"{oauth.redirect_uri}?{urllib.parse.urlencode({'code': code, 'state': oauth.state})}"
    try:
        token_json = submit_callback_url(
            callback_url=callback_url,
            expected_state=oauth.state,
            code_verifier=oauth.code_verifier,
            redirect_uri=oauth.redirect_uri,
        )
    except Exception as exc:
        reg._print(f"[OAuth] token 交换失败: {exc}")
        return None

    reg._print("[OAuth] Codex Token 获取成功")
    return _enrich_token_json_with_registration_context(
        token_json,
        password=password,
        birthdate=str(mailbox.get("birthdate") or "").strip(),
        mailbox=mailbox,
    )


def _run_cpa_style_registration_flow(
    *,
    proxy: Optional[str],
    mailbox: Dict[str, Any],
    email: str,
    oauth_log_to_info: bool = False,
) -> Optional[str]:
    password = str(mailbox.get("password") or "").strip()
    if not password:
        _record_last_run_failure("注册上下文缺少密码")
        log_error("注册上下文缺少密码")
        return None

    full_name = f"{mailbox.get('first_name', '')} {mailbox.get('last_name', '')}".strip()
    birthdate = str(mailbox.get("birthdate") or "2000-02-20").strip()
    provider = str(mailbox.get("email_provider") or "").strip().lower()
    mail_token = str(mailbox.get("tm_token") or "").strip()

    reg = _build_cpa_style_register(proxy, mailbox)
    try:
        reg.run_register(
            email,
            password,
            full_name or "Neo",
            birthdate,
            mail_token,
            provider=provider,
        )
    except Exception as exc:
        if _is_unsupported_impersonate_error(exc):
            message = f"当前 curl_cffi 不支持 CPA 选中的浏览器指纹: {exc}"
            _record_last_run_failure(message)
            log_error(message)
            return None
        if "registration_disallowed" in str(exc):
            message = (
                f"OpenAI 返回 registration_disallowed，当前环境被风控拒绝注册"
                f"（常见原因: 代理/IP、邮箱域名或设备指纹）"
            )
            _record_last_run_failure(message)
            log_error(message)
            return None
        raise
    log_ok("OpenAI 账号创建完成")

    if oauth_log_to_info:
        from types import MethodType as _MethodType

        def _force_print(self: Any, *parts: Any, **kwargs: Any) -> None:
            log_info(" ".join(str(part) for part in parts))

        reg._print = _MethodType(_force_print, reg)

    token_json = _perform_cpa_style_codex_oauth_login_http(
        reg,
        mailbox=mailbox,
        email=email,
        password=password,
    )
    if not token_json:
        _record_last_run_failure("按 CPA 流程执行 Codex OAuth 失败")
        log_error("按 CPA 流程执行 Codex OAuth 失败")
        return None
    return token_json


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
                log_verbose(f"成功读取 CDKEY 数组，共 {len(items)} 项")
            return items

    try:
        python_like = raw.replace("false", "False").replace("true", "True").replace("null", "None")
        data = ast.literal_eval(python_like)
        items = _normalize_loaded_code_items(data)
        if items or _looks_like_code_container(data):
            if not quiet:
                log_verbose(f"成功读取 CDKEY 数组，共 {len(items)} 项")
            return items
    except Exception:
        pass

    plain_codes = _extract_code_lines(raw)
    if plain_codes:
        items = [{"code": code, "use": 0} for code in plain_codes]
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


def _replace_cdkeys_from_text(raw_text: str) -> int:
    incoming = _extract_code_lines(raw_text)
    replaced = [{"code": code, "use": 0} for code in incoming]
    save_code_array(replaced)
    return len(replaced)


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
    if _uses_hosted_payment():
        _render_kv_table(
            "运行前卡片信息",
            [
                ("卡商", _card_provider_label()),
                ("本地卡池", "不需要"),
            ],
        )
        return
    virtual_card_count = len(load_code_array(quiet=True))
    _render_kv_table(
        "运行前卡片信息",
        [
            ("CDKEY 数量", str(virtual_card_count)),
        ],
    )


def get_available_card_use_count() -> int:
    """按 use 计数计算当前虚拟卡还可用多少次。"""
    if _uses_hosted_payment():
        return 10**9
    code_array = load_code_array(quiet=True)
    max_use_count = get_card_max_use_count()
    available_uses = 0
    for item in code_array:
        if not isinstance(item, dict):
            continue
        use_count = _normalize_use_count(item.get("use"))
        available_uses += max(0, max_use_count - use_count)
    return available_uses


def ensure_team_card_capacity_available() -> int:
    """仅检查卡池剩余次数，不提前开卡。"""
    if _uses_hosted_payment():
        return 10**9
    available_uses = get_available_card_use_count()
    if available_uses > 0:
        return available_uses
    raise StopScript("虚拟卡可用次数不足，请补充 CDKEY 后再试")


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
            f"{aisub_base_url}/api/balance",
            headers=_aisub_headers(),
            proxies=proxies,
            impersonate="chrome",
            timeout=20,
        )
        if resp.status_code == 404:
            resp = requests.get(
                f"{aisub_base_url}/api/v1/balance",
                headers=_aisub_headers(),
                proxies=proxies,
                impersonate="chrome",
                timeout=20,
            )
        if resp.status_code == 200:
            data: Any = resp.json()
        else:
            data = {"error": resp.text}
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
    status_code = balance_result.get("status_code")
    balance_data = balance_result.get("response") or {}

    if status_code == 401:
        raise StopScript("AISub API Key 无效，请在设置中更新 API Key 后再试")

    balance = 0
    if isinstance(balance_data, dict):
        try:
            balance = int(float(balance_data.get("balance") or 0))
        except (TypeError, ValueError):
            balance = 0

    remaining_times = balance  # 新 API 单价 ¥1/次，余额即可用次数
    if status_code == 200 and remaining_times > 0:
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
        "remaining_times": balance,  # 新 API 单价 ¥1/次，余额即可用次数
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
    estimated_accounts = remaining_times if _uses_hosted_payment() else min(remaining_times, available_card_uses)
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
    team_card_open_timing = _team_card_open_timing_key()
    provider = _card_provider_key()
    hosted_payment = _uses_hosted_payment(provider)
    available_card_uses = get_available_card_use_count()
    aisub_snapshot = get_aisub_balance_snapshot(proxies)
    aisub_times = int(aisub_snapshot.get("remaining_times") or 0) if int(aisub_snapshot.get("status_code") or 0) == 200 else 0
    estimated_accounts = aisub_times if hosted_payment else min(aisub_times, available_card_uses)
    estimated_positions = estimated_accounts * 5
    return {
        "register_type": register_type,
        "card_provider": provider,
        "hosted_payment": hosted_payment,
        "team_card_open_timing": team_card_open_timing,
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
                ("卡商", _card_provider_label(data.get("card_provider"))),
                ("开卡时机", _team_card_open_timing_label(data.get("team_card_open_timing"))),
                ("AISub 可用次数", str(data["aisub_times"])),
                ("虚拟卡可用次数", "托管支付无需本地卡" if data.get("hosted_payment") else str(data["available_card_uses"])),
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
            f"兑换结果文件: {_shorten_path_display(str(CONFIG.get('code_results_file') or DEFAULT_CONFIG['code_results_file']))}",
            f"输出根目录: {_shorten_path_display(str(CONFIG.get('output_root') or DEFAULT_CONFIG['output_root'] or '未设置'))}",
            f"CFMail 配置文件: {_shorten_path_display(str(CONFIG.get('cfmail_config_path') or DEFAULT_CONFIG['cfmail_config_path']))}",
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
        elif selected_index == 3:
            _update_config_value(
                "code_results_file",
                "请输入兑换结果文件路径，支持相对路径: ",
                default=CONFIG.get("code_results_file") or DEFAULT_CONFIG["code_results_file"],
                success_text="兑换结果文件路径已更新",
            )
        elif selected_index == 4:
            _update_config_value(
                "output_root",
                "请输入输出根目录，留空则清除: ",
                default=CONFIG.get("output_root") or "",
                success_text="输出根目录已更新",
            )
        elif selected_index == 5:
            _update_config_value(
                "cfmail_config_path",
                "请输入 CFMail 配置文件路径，支持相对路径: ",
                default=CONFIG.get("cfmail_config_path") or DEFAULT_CONFIG["cfmail_config_path"],
                success_text="CFMail 配置文件路径已更新",
            )
            _reload_cfmail_accounts_if_needed(force=True)


def prompt_import_settings() -> None:
    selected_index = 0
    while True:
        options = [
            "粘贴追加 CDKEY",
            "粘贴覆盖 CDKEY",
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
            raw_text = _prompt_multiline_input("请粘贴 CDKEY，可多行/空格/逗号分隔")
            if raw_text is None:
                continue
            count = _replace_cdkeys_from_text(raw_text)
            log_ok(f"CDKEY 覆盖完成: {count} 条")
        elif selected_index == 2:
            raw_text = _prompt_multiline_input(
                "请粘贴本地邮箱账号，每行一个，格式：邮箱----邮箱密码----Client ID----Refresh Token"
            )
            if raw_text is None:
                continue
            added = _append_local_graph_accounts_from_text(raw_text)
            log_ok(f"本地邮箱导入完成: {added} 条")
        elif selected_index == 3:
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
        custom_domains = _load_custom_domains()
        options = [
            f"邮箱提供商: {_email_provider_label(current_provider)}",
            f"注册邮箱前缀: {str(CONFIG.get('tm_reg_prefix') or '').strip() or '未设置'}",
            f"注册邮箱域名: {str(CONFIG.get('tm_reg_domain') or '').strip() or '未设置'}",
            f"TempMail.plus 地址: {str(CONFIG.get('tm_tm_addr') or '').strip() or '未设置'}",
            f"TempMail.plus EPIN: {_mask_secret(str(CONFIG.get('tm_tm_epin') or ''))}",
            f"自定义域名开关: {'开' if bool(CONFIG.get('tm_use_cd')) else '关'}",
            f"自定义域名列表: {len(custom_domains)} 个",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / 邮箱注册", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        if selected_index == 0:
            provider_options = [
                ("duckmail", "DuckMail"),
                ("npcmail", "NPCMail"),
                ("gptmail", "GPTMail"),
                ("junmail", "JunMail"),
                ("lamail", "LaMail"),
                ("cfmail", "CFMail"),
                ("tempmail_lol", "TempMail.lol"),
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
        elif selected_index == 3:
            _update_config_value(
                "tm_tm_addr",
                "请输入 TempMail.plus 地址，留空则清除: ",
                default=CONFIG.get("tm_tm_addr") or "",
                success_text="TempMail.plus 地址已更新",
            )
        elif selected_index == 4:
            _update_config_value(
                "tm_tm_epin",
                "请输入 TempMail.plus EPIN，留空则清除: ",
                default=CONFIG.get("tm_tm_epin") or "",
                success_text="TempMail.plus EPIN 已更新",
            )
        elif selected_index == 5:
            enabled = bool(CONFIG.get("tm_use_cd"))
            toggle_choice = _select_from_menu("自定义域名开关", ["开", "关"], 0 if enabled else 1)
            if toggle_choice == -1:
                continue
            CONFIG["tm_use_cd"] = toggle_choice == 0
            save_config()
            log_ok("自定义域名开关已更新")
        elif selected_index == 6:
            raw = _prompt_input(
                "请输入自定义域名，多个可用逗号分隔，留空则清除: ",
                ", ".join(custom_domains),
            )
            if raw is None:
                continue
            CONFIG["tm_custom_domains"] = [
                part.strip()
                for part in re.split(r"[\n,;]+", raw)
                if part.strip()
            ]
            save_config()
            log_ok("自定义域名列表已更新")


def prompt_service_settings() -> None:
    global EFUNCARD_CITY_DATA_CACHE
    selected_index = 0
    while True:
        current_card_provider = _card_provider_key()
        options = [
            f"卡商: {_card_provider_label(current_card_provider)}",
            f"TempMail.lol Base URL: {_shorten_path_display(str(CONFIG.get('tempmail_base') or DEFAULT_CONFIG['tempmail_base']), 50)}",
            f"TempMail.plus API: {_shorten_path_display(str(CONFIG.get('tempmail_plus_api') or DEFAULT_CONFIG['tempmail_plus_api']), 50)}",
            f"NPCMail API Key: {_mask_secret(str(CONFIG.get('tm_npcmail_apikey') or ''))}",
            f"NPCMail Base URL: {_shorten_path_display(str(CONFIG.get('npcmail_base') or DEFAULT_CONFIG['npcmail_base']), 50)}",
            f"GPTMail API Key: {_mask_secret(str(CONFIG.get('gptmail_api_key') or ''))}",
            f"GPTMail Base URL: {_shorten_path_display(str(CONFIG.get('gptmail_base') or DEFAULT_CONFIG['gptmail_base']), 50)}",
            f"JunMail API Key: {_mask_secret(str(CONFIG.get('junmail_api_key') or ''))}",
            f"JunMail Base URL: {_shorten_path_display(str(CONFIG.get('junmail_base') or DEFAULT_CONFIG['junmail_base']), 50)}",
            f"DuckMail Bearer: {_mask_secret(str(CONFIG.get('duckmail_bearer') or ''))}",
            f"DuckMail Base URL: {_shorten_path_display(str(CONFIG.get('duckmail_api_base') or DEFAULT_CONFIG['duckmail_api_base']), 50)}",
            f"LaMail API Key: {_mask_secret(str(CONFIG.get('lamail_api_key') or ''))}",
            f"LaMail Base URL: {_shorten_path_display(str(CONFIG.get('lamail_api_base') or DEFAULT_CONFIG['lamail_api_base']), 50)}",
            f"LaMail 域名: {_shorten_path_display(str(CONFIG.get('lamail_domain') or DEFAULT_CONFIG['lamail_domain'] or '未设置'), 50)}",
            f"CFMail Profile: {_shorten_path_display(str(CONFIG.get('cfmail_profile') or DEFAULT_CONFIG['cfmail_profile']), 50)}",
            f"AISub API Key: {_mask_secret(str(CONFIG.get('aisub_api_key') or ''))}",
            f"AISub Base URL: {_shorten_path_display(str(CONFIG.get('aisub_base_url') or DEFAULT_CONFIG['aisub_base_url']), 50)}",
            f"AISub Proxy Region: {str(CONFIG.get('aisub_proxy_region') or DEFAULT_CONFIG['aisub_proxy_region'] or 'auto')}",
            f"NCET Base URL: {_shorten_path_display(str(CONFIG.get('redeem_base_url') or DEFAULT_CONFIG['redeem_base_url']), 50)}",
            f"EFunCard Base URL: {_shorten_path_display(str(CONFIG.get('efuncard_base_url') or DEFAULT_CONFIG['efuncard_base_url']), 50)}",
            f"EFunCard CSRF Token: {_mask_secret(str(CONFIG.get('efuncard_csrf_token') or ''))}",
            f"EFunCard 城市库 URL: {_shorten_path_display(str(CONFIG.get('efuncard_address_cities_url') or DEFAULT_CONFIG['efuncard_address_cities_url']), 50)}",
            f"OpenAI Client ID: {_shorten_path_display(_get_openai_client_id() or '未设置', 50)}",
            f"OpenAI Originator: {_shorten_path_display(_get_openai_originator() or '未设置', 50)}",
            f"OpenAI Redirect URI: {_shorten_path_display(str(CONFIG.get('oauth_redirect_uri') or DEFAULT_CONFIG['oauth_redirect_uri']), 50)}",
            f"OpenAI Scope: {_shorten_path_display(str(CONFIG.get('oauth_scope') or DEFAULT_CONFIG['oauth_scope']), 50)}",
            f"OpenAI POW 参数: {(_get_openai_pow_value() or '未设置')}",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / 接口与密钥", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        if selected_index == 0:
            provider_options = [
                ("ncet", "NCET"),
                ("efuncard", "EFunCard"),
                ("hosted", "托管支付"),
            ]
            provider_labels = [label for _, label in provider_options]
            provider_index = next(
                (index for index, (provider_key, _) in enumerate(provider_options) if provider_key == current_card_provider),
                0,
            )
            provider_choice = _select_from_menu("卡商", provider_labels, provider_index)
            if provider_choice == -1:
                continue
            provider_key, provider_label = provider_options[provider_choice]
            CONFIG["card_provider"] = provider_key
            save_config()
            log_ok(f"卡商已更新为 {provider_label}")
        elif selected_index == 1:
            _update_config_value(
                "tempmail_base",
                "请输入 TempMail.lol Base URL: ",
                default=CONFIG.get("tempmail_base") or DEFAULT_CONFIG["tempmail_base"],
                success_text="TempMail.lol Base URL 已更新",
            )
        elif selected_index == 2:
            _update_config_value(
                "tempmail_plus_api",
                "请输入 TempMail.plus API: ",
                default=CONFIG.get("tempmail_plus_api") or DEFAULT_CONFIG["tempmail_plus_api"],
                success_text="TempMail.plus API 已更新",
            )
        elif selected_index == 3:
            _update_config_value(
                "tm_npcmail_apikey",
                "请输入 NPCMail API Key，留空则清除: ",
                default=CONFIG.get("tm_npcmail_apikey") or "",
                success_text="NPCMail API Key 已更新",
            )
        elif selected_index == 4:
            _update_config_value(
                "npcmail_base",
                "请输入 NPCMail Base URL: ",
                default=CONFIG.get("npcmail_base") or DEFAULT_CONFIG["npcmail_base"],
                success_text="NPCMail Base URL 已更新",
            )
        elif selected_index == 5:
            _update_config_value(
                "gptmail_api_key",
                "请输入 GPTMail API Key，留空则清除: ",
                default=CONFIG.get("gptmail_api_key") or "",
                success_text="GPTMail API Key 已更新",
            )
        elif selected_index == 6:
            _update_config_value(
                "gptmail_base",
                "请输入 GPTMail Base URL: ",
                default=CONFIG.get("gptmail_base") or DEFAULT_CONFIG["gptmail_base"],
                success_text="GPTMail Base URL 已更新",
            )
        elif selected_index == 7:
            _update_config_value(
                "junmail_api_key",
                "请输入 JunMail API Key，留空则清除: ",
                default=CONFIG.get("junmail_api_key") or "",
                success_text="JunMail API Key 已更新",
            )
        elif selected_index == 8:
            _update_config_value(
                "junmail_base",
                "请输入 JunMail Base URL: ",
                default=CONFIG.get("junmail_base") or DEFAULT_CONFIG["junmail_base"],
                success_text="JunMail Base URL 已更新",
            )
        elif selected_index == 9:
            _update_config_value(
                "duckmail_bearer",
                "请输入 DuckMail Bearer，留空则清除: ",
                default=CONFIG.get("duckmail_bearer") or "",
                success_text="DuckMail Bearer 已更新",
            )
        elif selected_index == 10:
            _update_config_value(
                "duckmail_api_base",
                "请输入 DuckMail Base URL: ",
                default=CONFIG.get("duckmail_api_base") or DEFAULT_CONFIG["duckmail_api_base"],
                success_text="DuckMail Base URL 已更新",
            )
        elif selected_index == 11:
            _update_config_value(
                "lamail_api_key",
                "请输入 LaMail API Key，留空则清除: ",
                default=CONFIG.get("lamail_api_key") or "",
                success_text="LaMail API Key 已更新",
            )
        elif selected_index == 12:
            _update_config_value(
                "lamail_api_base",
                "请输入 LaMail Base URL: ",
                default=CONFIG.get("lamail_api_base") or DEFAULT_CONFIG["lamail_api_base"],
                success_text="LaMail Base URL 已更新",
            )
        elif selected_index == 13:
            _update_config_value(
                "lamail_domain",
                "请输入 LaMail 域名，留空则清除: ",
                default=CONFIG.get("lamail_domain") or "",
                success_text="LaMail 域名已更新",
            )
        elif selected_index == 14:
            _update_config_value(
                "cfmail_profile",
                "请输入 CFMail Profile（auto 或具体名称）: ",
                default=CONFIG.get("cfmail_profile") or DEFAULT_CONFIG["cfmail_profile"],
                success_text="CFMail Profile 已更新",
            )
            _reload_cfmail_accounts_if_needed(force=True)
        elif selected_index == 15:
            _update_config_value(
                "aisub_api_key",
                "请输入 AISub API Key，留空则清除: ",
                default=CONFIG.get("aisub_api_key") or "",
                success_text="AISub API Key 已更新",
            )
        elif selected_index == 16:
            _update_config_value(
                "aisub_base_url",
                "请输入 AISub Base URL: ",
                default=CONFIG.get("aisub_base_url") or DEFAULT_CONFIG["aisub_base_url"],
                success_text="AISub Base URL 已更新",
            )
        elif selected_index == 17:
            _update_config_value(
                "aisub_proxy_region",
                "请输入 AISub 代理区域（auto 或具体区域）: ",
                default=CONFIG.get("aisub_proxy_region") or DEFAULT_CONFIG["aisub_proxy_region"],
                success_text="AISub 代理区域已更新",
            )
        elif selected_index == 18:
            _update_config_value(
                "redeem_base_url",
                "请输入 NCET Base URL: ",
                default=CONFIG.get("redeem_base_url") or DEFAULT_CONFIG["redeem_base_url"],
                success_text="NCET Base URL 已更新",
            )
        elif selected_index == 18:
            _update_config_value(
                "efuncard_base_url",
                "请输入 EFunCard Base URL: ",
                default=CONFIG.get("efuncard_base_url") or DEFAULT_CONFIG["efuncard_base_url"],
                success_text="EFunCard Base URL 已更新",
            )
        elif selected_index == 20:
            _update_config_value(
                "efuncard_csrf_token",
                "请输入 EFunCard CSRF Token，留空则清除: ",
                default=CONFIG.get("efuncard_csrf_token") or "",
                success_text="EFunCard CSRF Token 已更新",
            )
        elif selected_index == 21:
            value = _prompt_input(
                "请输入 EFunCard 城市库 URL: ",
                str(CONFIG.get("efuncard_address_cities_url") or DEFAULT_CONFIG["efuncard_address_cities_url"]),
            )
            if value is None:
                continue
            CONFIG["efuncard_address_cities_url"] = value.strip()
            EFUNCARD_CITY_DATA_CACHE = None
            save_config()
            log_ok("EFunCard 城市库 URL 已更新")
        elif selected_index == 22:
            _update_config_value(
                "oauth_client_id",
                "请输入 OpenAI Client ID，留空则恢复默认: ",
                default=_get_openai_client_id(),
                success_text="OpenAI Client ID 已更新",
            )
        elif selected_index == 23:
            _update_config_value(
                "oauth_originator",
                "请输入 OpenAI Originator，留空则清除: ",
                default=_get_openai_originator(),
                success_text="OpenAI Originator 已更新",
            )
        elif selected_index == 24:
            _update_config_value(
                "oauth_redirect_uri",
                "请输入 OpenAI Redirect URI: ",
                default=CONFIG.get("oauth_redirect_uri") or DEFAULT_CONFIG["oauth_redirect_uri"],
                success_text="OpenAI Redirect URI 已更新",
            )
        elif selected_index == 25:
            _update_config_value(
                "oauth_scope",
                "请输入 OpenAI Scope: ",
                default=CONFIG.get("oauth_scope") or DEFAULT_CONFIG["oauth_scope"],
                success_text="OpenAI Scope 已更新",
            )
        elif selected_index == 26:
            _update_config_value(
                "openai_pow_value",
                "请输入 OpenAI POW 参数，留空则清除: ",
                default=_get_openai_pow_value(),
                success_text="OpenAI POW 参数已更新",
            )


def prompt_cpa_settings() -> None:
    selected_index = 0
    while True:
        options = [
            f"Token JSON 目录: {_shorten_path_display(str(CONFIG.get('token_json_dir') or DEFAULT_CONFIG['token_json_dir']))}",
            f"AK 文件: {_shorten_path_display(str(CONFIG.get('ak_file') or DEFAULT_CONFIG['ak_file']))}",
            f"RK 文件: {_shorten_path_display(str(CONFIG.get('rk_file') or DEFAULT_CONFIG['rk_file']))}",
            f"CPA 上传 URL: {_shorten_path_display(str(CONFIG.get('upload_api_url') or DEFAULT_CONFIG['upload_api_url'] or '未设置'), 50)}",
            f"CPA 上传 Token: {_mask_secret(str(CONFIG.get('upload_api_token') or ''))}",
            f"CPA 上传代理: {_shorten_path_display(str(CONFIG.get('upload_api_proxy') or DEFAULT_CONFIG['upload_api_proxy'] or '未设置'), 50)}",
            f"每 N 个自动导入: {int(CONFIG.get('cpa_upload_every_n') or DEFAULT_CONFIG['cpa_upload_every_n'])}",
            f"注册前 CPA 清理: {'开' if bool(CONFIG.get('cpa_cleanup_enabled', DEFAULT_CONFIG['cpa_cleanup_enabled'])) else '关'}",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / CPA 配置", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        if selected_index == 0:
            _update_config_value(
                "token_json_dir",
                "请输入 Token JSON 目录，支持相对路径: ",
                default=CONFIG.get("token_json_dir") or DEFAULT_CONFIG["token_json_dir"],
                success_text="Token JSON 目录已更新",
            )
        elif selected_index == 1:
            _update_config_value(
                "ak_file",
                "请输入 AK 文件路径，支持相对路径: ",
                default=CONFIG.get("ak_file") or DEFAULT_CONFIG["ak_file"],
                success_text="AK 文件路径已更新",
            )
        elif selected_index == 2:
            _update_config_value(
                "rk_file",
                "请输入 RK 文件路径，支持相对路径: ",
                default=CONFIG.get("rk_file") or DEFAULT_CONFIG["rk_file"],
                success_text="RK 文件路径已更新",
            )
        elif selected_index == 3:
            _update_config_value(
                "upload_api_url",
                "请输入 CPA 上传 URL，留空则清除: ",
                default=CONFIG.get("upload_api_url") or "",
                success_text="CPA 上传 URL 已更新",
            )
        elif selected_index == 4:
            _update_config_value(
                "upload_api_token",
                "请输入 CPA 上传 Token，留空则清除: ",
                default=CONFIG.get("upload_api_token") or "",
                success_text="CPA 上传 Token 已更新",
            )
        elif selected_index == 5:
            _update_config_value(
                "upload_api_proxy",
                "请输入 CPA 上传代理（可填 direct/default/代理地址），留空则清除: ",
                default=CONFIG.get("upload_api_proxy") or "",
                success_text="CPA 上传代理已更新",
            )
        elif selected_index == 6:
            _update_config_value(
                "cpa_upload_every_n",
                "请输入每成功多少个账号触发一次 CPA 自动导入: ",
                default=CONFIG.get("cpa_upload_every_n") or DEFAULT_CONFIG["cpa_upload_every_n"],
                parser=_parse_positive_int,
                success_text="CPA 自动导入阈值已更新",
            )
        elif selected_index == 7:
            enabled = bool(CONFIG.get("cpa_cleanup_enabled", DEFAULT_CONFIG["cpa_cleanup_enabled"]))
            toggle_choice = _select_from_menu("注册前 CPA 清理", ["开", "关"], 0 if enabled else 1)
            if toggle_choice == -1:
                continue
            CONFIG["cpa_cleanup_enabled"] = toggle_choice == 0
            save_config()
            log_ok("注册前 CPA 清理配置已更新")


def prompt_runtime_settings() -> None:
    selected_index = 0
    while True:
        current_provider = _card_provider_label()
        max_use_config_key = "efuncard_card_max_use_count" if _card_provider_key() == "efuncard" else "card_max_use_count"
        current_target_type = str(CONFIG.get("target_type") or DEFAULT_CONFIG["target_type"]).strip()
        current_target_value = int(CONFIG.get("target_value") or DEFAULT_CONFIG["target_value"] or 0)
        current_target_display = current_target_value if current_target_type == "register_count" else 0
        options = [
            f"生成账户数: {current_target_display}",
            f"注册类型: {_register_type_label()}",
            f"默认代理: {str(CONFIG.get('default_proxy') or '').strip() or '未设置'}",
            f"休息最短秒数: {int(CONFIG.get('default_sleep_min') or DEFAULT_CONFIG['default_sleep_min'])}",
            f"休息最长秒数: {int(CONFIG.get('default_sleep_max') or DEFAULT_CONFIG['default_sleep_max'])}",
            f"单卡最大绑定次数({current_provider}): {get_card_max_use_count()}",
            f"日志模式: {'详细' if bool(CONFIG.get('verbose_info_logs_enabled', DEFAULT_CONFIG['verbose_info_logs_enabled'])) else '精简'}",
            f"subscribe 失败重开号: {'开' if bool(CONFIG.get('subscribe_retry_new_account_enabled', True)) else '关'}",
            f"3DS 触发换号: {'开' if bool(CONFIG.get('subscribe_switch_account_on_3ds_enabled', True)) else '关'}",
            f"subscribe 失败次数上限: {int(CONFIG.get('subscribe_retry_new_account_limit', 50) or 50)}",
            f"订阅 Plan: {str(CONFIG.get('subscribe_plan') or DEFAULT_CONFIG['subscribe_plan']).strip() or '未设置'}",
            f"AISub 支付模式: {_aisub_payment_mode_label()}",
            f"Team 开卡时机: {_team_card_open_timing_label()}",
            "返回",
        ]
        selected_index = _select_from_menu("配置中心 / 运行策略", options, selected_index)
        if selected_index in {-1, len(options) - 1}:
            return
        if selected_index == 0:
            prompt_execution_count()
        elif selected_index == 1:
            prompt_register_type_setting()
        elif selected_index == 2:
            _update_config_value(
                "default_proxy",
                "请输入默认代理，留空则清除: ",
                default=CONFIG.get("default_proxy") or "",
                success_text="默认代理已更新",
            )
        elif selected_index == 3:
            raw = _prompt_input(
                "请输入休息最短秒数: ",
                str(int(CONFIG.get("default_sleep_min") or DEFAULT_CONFIG["default_sleep_min"])),
            )
            if raw is None:
                continue
            try:
                sleep_min = _parse_positive_int(raw)
            except ValueError:
                log_warn("输入无效")
                continue
            CONFIG["default_sleep_min"] = sleep_min
            if sleep_min > int(CONFIG.get("default_sleep_max") or DEFAULT_CONFIG["default_sleep_max"]):
                CONFIG["default_sleep_max"] = sleep_min
            save_config()
            log_ok(f"休息最短秒数已更新为 {CONFIG['default_sleep_min']}")
        elif selected_index == 4:
            raw = _prompt_input(
                "请输入休息最长秒数: ",
                str(int(CONFIG.get("default_sleep_max") or DEFAULT_CONFIG["default_sleep_max"])),
            )
            if raw is None:
                continue
            try:
                sleep_max = _parse_positive_int(raw)
            except ValueError:
                log_warn("输入无效")
                continue
            CONFIG["default_sleep_max"] = sleep_max
            if sleep_max < int(CONFIG.get("default_sleep_min") or DEFAULT_CONFIG["default_sleep_min"]):
                CONFIG["default_sleep_min"] = sleep_max
            save_config()
            log_ok(f"休息最长秒数已更新为 {CONFIG['default_sleep_max']}")
        elif selected_index == 5:
            raw = _prompt_input(f"请输入单卡最大绑定次数({current_provider}): ", str(get_card_max_use_count()))
            if raw is None:
                continue
            try:
                CONFIG[max_use_config_key] = _parse_positive_int(raw)
            except ValueError:
                log_warn("输入无效")
                continue
            save_config()
            log_ok(f"单卡最大绑定次数({current_provider})已更新为 {CONFIG[max_use_config_key]}")
        elif selected_index == 6:
            enabled = bool(CONFIG.get("verbose_info_logs_enabled", DEFAULT_CONFIG["verbose_info_logs_enabled"]))
            toggle_choice = _select_from_menu("日志模式", ["详细", "精简"], 0 if enabled else 1)
            if toggle_choice == -1:
                continue
            CONFIG["verbose_info_logs_enabled"] = toggle_choice == 0
            save_config()
            log_ok(f"日志模式已更新为 {'详细' if CONFIG['verbose_info_logs_enabled'] else '精简'}")
        elif selected_index == 7:
            enabled = bool(CONFIG.get("subscribe_retry_new_account_enabled", True))
            toggle_choice = _select_from_menu("subscribe 失败重开号", ["开", "关"], 0 if enabled else 1)
            if toggle_choice == -1:
                continue
            CONFIG["subscribe_retry_new_account_enabled"] = toggle_choice == 0
            save_config()
            log_ok("subscribe 失败重开号配置已更新")
        elif selected_index == 8:
            enabled = bool(CONFIG.get("subscribe_switch_account_on_3ds_enabled", True))
            toggle_choice = _select_from_menu("3DS 触发换号", ["开", "关"], 0 if enabled else 1)
            if toggle_choice == -1:
                continue
            CONFIG["subscribe_switch_account_on_3ds_enabled"] = toggle_choice == 0
            save_config()
            log_ok("3DS 触发换号配置已更新")
        elif selected_index == 9:
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
        elif selected_index == 10:
            _update_config_value(
                "subscribe_plan",
                "请输入订阅 Plan: ",
                default=CONFIG.get("subscribe_plan") or DEFAULT_CONFIG["subscribe_plan"],
                success_text="订阅 Plan 已更新",
            )
        elif selected_index == 11:
            payment_mode_options = [
                ("async", "异步(推荐)"),
                ("sync", "同步"),
            ]
            current_mode = _aisub_payment_mode_key()
            payment_mode_index = next(
                (index for index, (mode_key, _) in enumerate(payment_mode_options) if mode_key == current_mode),
                0,
            )
            choice = _select_from_menu(
                "AISub 支付模式",
                [label for _, label in payment_mode_options],
                payment_mode_index,
            )
            if choice == -1:
                continue
            mode_key, mode_label = payment_mode_options[choice]
            CONFIG["aisub_payment_mode"] = mode_key
            save_config()
            log_ok(f"AISub 支付模式已更新为 {mode_label}")
        elif selected_index == 12:
            timing_options = [
                ("after_register", "先注册再开卡"),
                ("before_register", "先开卡再注册"),
            ]
            current_timing = _team_card_open_timing_key()
            timing_index = next(
                (index for index, (timing_key, _) in enumerate(timing_options) if timing_key == current_timing),
                0,
            )
            choice = _select_from_menu("Team 开卡时机", [label for _, label in timing_options], timing_index)
            if choice == -1:
                continue
            timing_key, timing_label = timing_options[choice]
            CONFIG["team_card_open_timing"] = timing_key
            save_config()
            log_ok(f"Team 开卡时机已更新为 {timing_label}")


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
                ("卡商", _card_provider_label(dashboard.get("card_provider"))),
                ("开卡时机", _team_card_open_timing_label(dashboard.get("team_card_open_timing"))),
                ("虚拟卡可用次数", "托管支付无需本地卡" if dashboard.get("hosted_payment") else str(dashboard["available_card_uses"])),
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
    prompt = f"请输入生成账户数，0 表示不限，当前为 {current_display}"
    if register_type == "team":
        prompt += f"，当前预计可生成 {estimated_accounts} 个账号（对应约 {estimated_positions} 个位置，仅供参考）"
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
    CONFIG["target_type"] = "register_count"
    CONFIG["target_value"] = target_value
    save_config()
    log_ok(f"生成账户数已更新为 {target_value}")
    if register_type == "team" and estimated_accounts > 0 and target_value > estimated_accounts:
        log_warn(f"当前目标高于预计可生成账号数 {estimated_accounts}，运行时会在资源耗尽或达到目标时停止")


def prompt_other_config() -> None:
    selected_index = 0
    while True:
        options = [
            "文件路径",
            "导入数据",
            "邮箱注册",
            "接口与密钥",
            "CPA 配置",
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
            prompt_cpa_settings()
            continue
        if selected_index == 5:
            prompt_runtime_settings()
            continue
        if selected_index == 6:
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
    provider = _card_provider_key()
    config_key = "efuncard_card_max_use_count" if provider == "efuncard" else "card_max_use_count"
    default_key = "efuncard_card_max_use_count" if provider == "efuncard" else "card_max_use_count"
    try:
        count = int(CONFIG.get(config_key) or DEFAULT_CONFIG[default_key])
    except (TypeError, ValueError):
        count = int(DEFAULT_CONFIG[default_key])
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
        log_verbose(f"CDKEY {code_value} 已从源文件移除{detail}")


def _build_efuncard_headers(*, json_content: bool = False) -> Dict[str, str]:
    csrf_token = str(CONFIG.get("efuncard_csrf_token") or DEFAULT_CONFIG["efuncard_csrf_token"]).strip()
    if not csrf_token:
        raise RuntimeError("EFunCard CSRF Token 未配置")

    base_url = str(CONFIG.get("efuncard_base_url") or DEFAULT_CONFIG["efuncard_base_url"]).rstrip("/")
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9",
        "connection": "keep-alive",
        "referer": f"{base_url}/",
        "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "x-csrf-token": csrf_token,
    }
    if json_content:
        headers["content-type"] = "application/json"
        headers["origin"] = base_url
    return headers


def _build_efuncard_cookies() -> Dict[str, str]:
    csrf_token = str(CONFIG.get("efuncard_csrf_token") or DEFAULT_CONFIG["efuncard_csrf_token"]).strip()
    if not csrf_token:
        raise RuntimeError("EFunCard CSRF Token 未配置")
    return {"csrf_token": csrf_token}


def _normalize_country_name(value: Any) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    if lowered in {"us", "usa", "united states", "united states of america", "美国"}:
        return "United States"
    return text


def _country_to_alpha2(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return "US"
    upper = text.upper()
    if re.fullmatch(r"[A-Z]{2}", upper):
        return upper

    normalized = re.sub(r"[^a-z\u4e00-\u9fff]+", " ", text.lower()).strip()
    mapping = {
        "us": "US",
        "usa": "US",
        "united states": "US",
        "united states of america": "US",
        "美国": "US",
        "gb": "GB",
        "uk": "GB",
        "great britain": "GB",
        "united kingdom": "GB",
        "英国": "GB",
        "ca": "CA",
        "canada": "CA",
        "加拿大": "CA",
        "au": "AU",
        "australia": "AU",
        "澳大利亚": "AU",
        "eg": "EG",
        "egypt": "EG",
        "埃及": "EG",
    }
    return mapping.get(normalized, "US")


def _parse_efuncard_node_address(node_instructions: str) -> Dict[str, str]:
    fields = {
        "address": "",
        "city": "",
        "state": "",
        "zipcode": "",
        "country": "United States",
    }
    normalized = _normalize_address_component(node_instructions)
    if not normalized:
        return fields

    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    if len(parts) >= 5:
        fields["address"] = _normalize_address_component(", ".join(parts[:-4]))
        fields["city"] = _normalize_address_component(parts[-4])
        fields["state"] = _normalize_address_component(parts[-3]).upper()
        fields["zipcode"] = _normalize_address_component(parts[-2])
        fields["country"] = _normalize_country_name(parts[-1]) or "United States"
        return fields

    if len(parts) == 4:
        fields["address"] = _normalize_address_component(parts[0])
        fields["city"] = _normalize_address_component(parts[1])
        fields["state"] = _normalize_address_component(parts[2]).upper()
        fields["zipcode"] = _normalize_address_component(parts[3])
        return fields

    if len(parts) == 3:
        fields["address"] = _normalize_address_component(parts[0])
        fields["city"] = _normalize_address_component(parts[1])
        state_zip = _normalize_address_component(parts[2])
        match = re.match(r"^([A-Za-z]{2})\s+(\d{5}(?:-\d{4})?)$", state_zip)
        if match:
            fields["state"] = match.group(1).upper()
            fields["zipcode"] = match.group(2)
        else:
            fields["state"] = state_zip.upper()
        return fields

    fields["address"] = normalized
    return fields


def _load_efuncard_city_dataset(proxies: Any = None) -> Dict[str, Any]:
    global EFUNCARD_CITY_DATA_CACHE

    if isinstance(EFUNCARD_CITY_DATA_CACHE, dict):
        return EFUNCARD_CITY_DATA_CACHE

    url = str(CONFIG.get("efuncard_address_cities_url") or DEFAULT_CONFIG["efuncard_address_cities_url"]).strip()
    if not url:
        return {}

    try:
        resp = requests.get(
            url,
            headers={
                "accept": "*/*",
                "accept-language": "zh-CN,zh;q=0.9",
                "referer": "https://usaddressgen.com/tax-free-address/",
                "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
            },
            proxies=proxies,
            impersonate="chrome",
            timeout=20,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")
        payload = resp.json()
        EFUNCARD_CITY_DATA_CACHE = payload if isinstance(payload, dict) else {}
    except Exception as exc:
        log_warn(f"EFunCard 地址城市库加载失败，改用节点地址: {exc}")
        return {}

    return EFUNCARD_CITY_DATA_CACHE or {}


def _generate_efuncard_street_line() -> str:
    street_roots = [
        "Oak", "Maple", "Pine", "Cedar", "Lake", "Hill", "Park", "Washington",
        "Lincoln", "Madison", "Adams", "Jackson", "Sunset", "Willow", "River",
    ]
    street_suffixes = ["Street", "Avenue", "Road", "Drive", "Lane", "Court", "Way", "Boulevard"]
    number = random.randint(100, 9999)
    root = random.choice(street_roots + LAST_NAMES[:10])
    suffix = random.choice(street_suffixes)
    return f"{number} {root} {suffix}"


def _build_efuncard_address(node_instructions: str, proxies: Any = None) -> Dict[str, str]:
    fields = _parse_efuncard_node_address(node_instructions)
    dataset = _load_efuncard_city_dataset(proxies)
    states = dataset.get("states") if isinstance(dataset, dict) else {}

    preferred_state = fields["state"].upper()
    preferred_city = fields["city"].strip().lower()
    selected_state_code = preferred_state
    selected_city_name = fields["city"]

    if isinstance(states, dict) and states:
        state_data = states.get(preferred_state) if preferred_state else None
        if isinstance(state_data, dict):
            cities = state_data.get("cities")
            if isinstance(cities, list) and cities:
                if not selected_city_name:
                    city_entry = random.choice(cities)
                    name_data = city_entry.get("name") if isinstance(city_entry, dict) else {}
                    selected_city_name = str((name_data or {}).get("en") or "").strip()
                elif preferred_city:
                    matched = next(
                        (
                            city_entry
                            for city_entry in cities
                            if isinstance(city_entry, dict)
                            and str(((city_entry.get("name") or {}).get("en") or "")).strip().lower() == preferred_city
                        ),
                        None,
                    )
                    if matched:
                        name_data = matched.get("name") if isinstance(matched, dict) else {}
                        selected_city_name = str((name_data or {}).get("en") or selected_city_name).strip()
        else:
            selectable_states = [
                (state_code, state_payload)
                for state_code, state_payload in states.items()
                if isinstance(state_payload, dict) and isinstance(state_payload.get("cities"), list) and state_payload.get("cities")
            ]
            if selectable_states:
                selected_state_code, state_data = random.choice(selectable_states)
                cities = state_data.get("cities") or []
                city_entry = random.choice(cities)
                name_data = city_entry.get("name") if isinstance(city_entry, dict) else {}
                selected_city_name = str((name_data or {}).get("en") or "").strip()

    address_line = fields["address"] or _generate_efuncard_street_line()
    zipcode = fields["zipcode"]
    if not zipcode or not re.fullmatch(r"\d{5}(?:-\d{4})?", zipcode):
        zipcode = f"{random.randint(10000, 99999)}"

    return {
        "address": _normalize_address_component(address_line),
        "city": _normalize_address_component(selected_city_name or fields["city"]),
        "state": _normalize_address_component(selected_state_code or fields["state"]).upper(),
        "zipcode": zipcode,
        "country": _normalize_country_name(fields["country"]) or "United States",
    }


def _build_efuncard_card_template(address_fields: Dict[str, str]) -> str:
    lines = [
        f"Address: {address_fields.get('address') or ''}",
        f"City: {address_fields.get('city') or ''}",
        f"State: {address_fields.get('state') or ''}",
        f"ZIP Code: {address_fields.get('zipcode') or ''}",
        f"Country: {address_fields.get('country') or 'United States'}",
    ]
    return "\n".join(lines).strip()


def _normalize_efuncard_response(payload: Any, *, allow_unused: bool, proxies: Any = None) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise RuntimeError("EFunCard 返回不是 JSON 对象")

    success = bool(payload.get("success"))
    data = payload.get("data")
    error = str(payload.get("error") or payload.get("message") or "").strip()

    if success and isinstance(data, dict):
        card_number = str(data.get("cardNumber") or "").strip()
        cvv = str(data.get("cvv") or data.get("cardPassword") or "").strip()
        expiry_month = data.get("expiryMonth")
        expiry_year = data.get("expiryYear")

        if not card_number or not cvv:
            raise RuntimeError("EFunCard 已返回成功，但缺少卡号或 CVV")

        try:
            expiry_month_int = int(expiry_month)
            expiry_year_int = int(expiry_year)
            expiry = f"{expiry_month_int:02d}{expiry_year_int % 100:02d}"
        except (TypeError, ValueError):
            expiry = ""

        expire_time = str(data.get("autoCancelAt") or "").strip()
        if not expire_time:
            created_at = _parse_iso_datetime(data.get("createdAt"))
            validity_minutes = data.get("validityMinutes")
            try:
                validity_minutes_int = int(validity_minutes)
            except (TypeError, ValueError):
                validity_minutes_int = 0
            if created_at and validity_minutes_int > 0:
                expire_time = (created_at + timedelta(minutes=validity_minutes_int)).isoformat()

        address_fields = _build_efuncard_address(
            str(data.get("nodeInstructions") or data.get("groupInstructions") or "").strip(),
            proxies,
        )

        return {
            "success": True,
            "vendor": "efuncard",
            "data": {
                "valid": True,
                "message": "",
                "cardTemplate": _build_efuncard_card_template(address_fields),
                "cards": [
                    {
                        "cardNumber": card_number,
                        "cardPassword": cvv,
                        "cardData": {
                            "expiry": expiry,
                            "expireTime": expire_time,
                            "expiryMonth": expiry_month,
                            "expiryYear": expiry_year,
                            "provider": "efuncard",
                            "lastFour": str(data.get("lastFour") or "").strip(),
                            "cardPrefix": str(data.get("cardPrefix") or "").strip(),
                        },
                    }
                ],
                "rawVendorData": data,
            },
        }

    if allow_unused and "未使用" in error:
        return {
            "success": True,
            "vendor": "efuncard",
            "data": {
                "valid": True,
                "message": error,
                "cards": [],
            },
        }

    return {
        "success": False,
        "vendor": "efuncard",
        "data": {
            "valid": False,
            "message": error or "EFunCard 请求失败",
            "cards": [],
        },
    }


def _request_efuncard_query(code: str, proxies: Any = None) -> Dict[str, Any]:
    base_url = str(CONFIG.get("efuncard_base_url") or DEFAULT_CONFIG["efuncard_base_url"]).rstrip("/")
    resp = requests.get(
        f"{base_url}/api/cards/query/{quote(code, safe='')}",
        headers=_build_efuncard_headers(),
        cookies=_build_efuncard_cookies(),
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
    if not isinstance(data, dict):
        raise RuntimeError(f"EFunCard query 返回不是 JSON 对象: HTTP {resp.status_code}")
    return _normalize_efuncard_response(data, allow_unused=True, proxies=proxies)


def _request_efuncard_redeem(code: str, proxies: Any = None) -> Dict[str, Any]:
    base_url = str(CONFIG.get("efuncard_base_url") or DEFAULT_CONFIG["efuncard_base_url"]).rstrip("/")
    resp = requests.post(
        f"{base_url}/api/redeem",
        headers=_build_efuncard_headers(json_content=True),
        cookies=_build_efuncard_cookies(),
        json={"code": code},
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
    if not isinstance(data, dict):
        raise RuntimeError(f"EFunCard redeem 返回不是 JSON 对象: HTTP {resp.status_code}")
    normalized = _normalize_efuncard_response(data, allow_unused=False, proxies=proxies)
    payload = normalized.get("data") if isinstance(normalized, dict) else {}
    message = str((payload or {}).get("message") or "").strip()
    if not has_cards(normalized) and "已使用" in message:
        log_verbose("EFunCard redeem 提示激活码已使用，回退 query 查询卡信息")
        query_data = _request_efuncard_query(code, proxies)
        if has_cards(query_data):
            return query_data
        raise RuntimeError("EFunCard redeem 提示已使用，但 query 未返回卡信息")
    return normalized


def _fetch_efuncard_payload(code: str, proxies: Any = None) -> Dict[str, Any]:
    query_data = _request_efuncard_query(code, proxies)
    if has_cards(query_data):
        expiry_status = _get_card_expiry_status(query_data)
        if not expiry_status["expired"]:
            return query_data
        expired_text = str(expiry_status.get("remaining_text") or "0秒")
        log_warn(f"EFunCard query 返回的卡已过期（已过期 {expired_text}），准备重新激活")

    query_payload = query_data.get("data") if isinstance(query_data, dict) else {}
    if has_cards(query_data) or (isinstance(query_payload, dict) and query_payload.get("valid") is True):
        redeem_data = _request_efuncard_redeem(code, proxies)
        if has_cards(redeem_data):
            expiry_status = _get_card_expiry_status(redeem_data)
            if not expiry_status["expired"]:
                return redeem_data
            expired_text = str(expiry_status.get("remaining_text") or "0秒")
            raise RuntimeError(f"EFunCard 激活后返回的卡已过期（已过期 {expired_text}）")
        raise RuntimeError("EFunCard 激活成功但未返回卡信息")

    return query_data


def _try_fetch_efuncard_payload(code: str, proxies: Any = None) -> Optional[Dict[str, Any]]:
    if _card_provider_key() == "efuncard":
        return None
    csrf_token = str(CONFIG.get("efuncard_csrf_token") or DEFAULT_CONFIG["efuncard_csrf_token"]).strip()
    if not csrf_token:
        return None
    try:
        data = _fetch_efuncard_payload(code, proxies)
    except Exception as exc:
        log_verbose(f"EFunCard 兜底查询失败，继续使用当前卡商结果: {exc}")
        return None
    if has_cards(data):
        log_verbose(f"兑换码 {code} 已切换为 EFunCard 查询/激活流程")
        return data
    return None


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
            log_verbose(f"validate 接口结果: {json.dumps(result, ensure_ascii=False)}")
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
    if _card_provider_key() == "efuncard":
        return _fetch_efuncard_payload(code, proxies)

    validate_data = request_validate(code, proxies)
    if has_cards(validate_data):
        expiry_status = _get_card_expiry_status(validate_data)
        if not expiry_status["expired"]:
            return validate_data
        expired_text = str(expiry_status.get("remaining_text") or "0秒")
        log_warn(f"validate 返回的卡已过期（已过期 {expired_text}），准备重新开卡")

    validate_payload = validate_data.get("data") if isinstance(validate_data, dict) else {}
    if has_cards(validate_data) or (isinstance(validate_payload, dict) and validate_payload.get("valid") is True):
        redeem_data = request_redeem(code, proxies)
        if has_cards(redeem_data):
            expiry_status = _get_card_expiry_status(redeem_data)
            if not expiry_status["expired"]:
                return redeem_data
            expired_text = str(expiry_status.get("remaining_text") or "0秒")
            raise RuntimeError(f"redeem 返回的卡已过期（已过期 {expired_text}）")

        redeem_payload = redeem_data.get("data") if isinstance(redeem_data, dict) else {}
        task_id = str((redeem_payload or {}).get("taskId") or "").strip()
        if not task_id:
            raise RuntimeError("redeem 成功但未返回 taskId")
        task_data = wait_for_redeem_task(task_id, proxies)
        expiry_status = _get_card_expiry_status(task_data)
        if has_cards(task_data) and expiry_status["expired"]:
            expired_text = str(expiry_status.get("remaining_text") or "0秒")
            raise RuntimeError(f"开卡完成但卡已过期（已过期 {expired_text}）")
        return task_data

    fallback_data = _try_fetch_efuncard_payload(code, proxies)
    if fallback_data:
        return fallback_data

    return validate_data


def request_validate(code: str, proxies: Any = None) -> Dict[str, Any]:
    """请求 validate 接口。"""
    if _card_provider_key() == "efuncard":
        return _request_efuncard_query(code, proxies)

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
    if isinstance(payload, dict) and not has_cards(data) and payload.get("valid") is True:
        log_verbose("validate 显示兑换码有效，准备开卡")
    return data


def request_redeem(code: str, proxies: Any = None) -> Dict[str, Any]:
    """请求 redeem 开卡。"""
    if _card_provider_key() == "efuncard":
        return _request_efuncard_redeem(code, proxies)

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
        log_verbose(f"redeem 已提交，orderNo={order_no} taskId={task_id}")
    return data


def request_redeem_task_status(task_id: str, proxies: Any = None) -> Dict[str, Any]:
    """查询 redeem task-status。"""
    if _card_provider_key() == "efuncard":
        raise RuntimeError("EFunCard 不支持 task-status 轮询")

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
            log_verbose(f"开卡进行中: {progress}")
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


def get_validate_unavailable_reason(response_data: Any) -> tuple[str, str]:
    """判断兑换码当前为何不可用。"""
    if not isinstance(response_data, dict) or has_cards(response_data):
        return "", ""

    data = response_data.get("data")
    if not isinstance(data, dict):
        return "", ""

    message = str(data.get("message") or "").strip()
    remaining_quantity = data.get("remainingQuantity")
    is_used = data.get("isUsed")
    valid = data.get("valid")

    if "激活码未使用" in message:
        return "unused", message
    if "兑换码不存在" in message:
        return "not_found", message
    if "该兑换码已使用完" in message:
        return "used", message
    if remaining_quantity == 0 and is_used is True:
        return "used", message
    if valid is False:
        return "invalid", message or "兑换码无效"
    return "", message


def is_exhausted_validate_response(response_data: Any) -> bool:
    """判断兑换码是否已使用完，需要切换下一张卡。"""
    reason, _ = get_validate_unavailable_reason(response_data)
    return reason == "used"


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


def _extract_address_fields_from_template(template: str) -> Dict[str, str]:
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

    for key in fields:
        fields[key] = _normalize_address_component(fields[key])
    return fields


def _extract_address_from_template(template: str) -> str:
    fields = _extract_address_fields_from_template(template)
    address_parts = [fields["address"], fields["city"], fields["state"], fields["zipcode"], fields["country"]]
    address_parts = [part for part in address_parts if part]
    return ", ".join(address_parts)


def _extract_first_card_and_data(response_data: Any) -> tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    if not isinstance(response_data, dict):
        return None, {}

    data = response_data.get("data")
    if not isinstance(data, dict):
        return None, {}

    cards = data.get("cards")
    if not isinstance(cards, list) or not cards:
        return None, {}

    card = cards[0]
    if not isinstance(card, dict):
        return None, {}

    card_data_raw = card.get("cardData")
    card_data: Dict[str, Any] = {}
    if isinstance(card_data_raw, dict):
        card_data = dict(card_data_raw)
    elif isinstance(card_data_raw, str) and card_data_raw.strip():
        try:
            parsed = json.loads(card_data_raw)
            if isinstance(parsed, dict):
                card_data = parsed
        except Exception:
            card_data = {}

    return card, card_data


def _normalize_expiry_year(value: Any) -> str:
    raw = str(value or "").strip()
    if len(raw) == 2 and raw.isdigit():
        raw = f"20{raw}"
    if len(raw) == 4 and raw.isdigit() and not raw.startswith("20"):
        raw = f"20{raw[-2:]}"
    return raw


def _extract_card_details(validate_result: Dict[str, Any]) -> Dict[str, Any]:
    response_data = validate_result.get("response") or {}
    card, card_data = _extract_first_card_and_data(response_data)
    if not card:
        return {}

    card_number = str(card.get("cardNumber") or "").strip()
    if not card_number:
        return {}
    cvv = str(
        card.get("cvv")
        or card.get("cardPassword")
        or card_data.get("cvv")
        or card_data.get("cardPassword")
        or ""
    ).strip()
    expiry_month = str(card_data.get("expiryMonth") or "").strip()
    expiry_year = _normalize_expiry_year(card_data.get("expiryYear"))
    expiry = str(card_data.get("expiry") or "").strip()
    if not expiry_month and len(expiry) >= 2:
        expiry_month = expiry[:2]
    if not expiry_year and len(expiry) >= 4:
        expiry_year = _normalize_expiry_year(expiry[2:])

    template = str((response_data.get("data") or {}).get("cardTemplate") or "").strip()
    return {
        "card_number": card_number,
        "cvv": cvv,
        "expiry_month": expiry_month,
        "expiry_year": expiry_year,
        "billing_template": template,
    }


def _build_billing_from_template(template: str, name: str) -> Dict[str, str]:
    fields = _extract_address_fields_from_template(template)
    billing = {
        "name": name or "AI Sub",
        "line1": fields.get("address") or "Unknown",
        "city": fields.get("city") or "Unknown",
        "state": fields.get("state") or "Unknown",
        "postal_code": fields.get("zipcode") or "00000",
        "country": _country_to_alpha2(fields.get("country")),
    }
    return billing


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None

    normalized = text
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    normalized = re.sub(r"\.(\d{6})\d+(?=(?:[+-]\d{2}:\d{2})?$)", r".\1", normalized)

    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def _get_card_expiry_status(response_data: Any) -> Dict[str, Any]:
    _, card_data = _extract_first_card_and_data(response_data)
    expire_time_raw = str(card_data.get("expireTime") or "").strip()
    if not expire_time_raw:
        return {
            "has_expire_time": False,
            "expired": False,
            "remaining_seconds": None,
            "remaining_text": "",
            "expire_time_raw": "",
        }

    expire_dt = _parse_iso_datetime(expire_time_raw)
    if expire_dt is None:
        return {
            "has_expire_time": False,
            "expired": False,
            "remaining_seconds": None,
            "remaining_text": "",
            "expire_time_raw": expire_time_raw,
        }

    if expire_dt.tzinfo is None:
        remaining_seconds = (expire_dt - datetime.now()).total_seconds()
    else:
        remaining_seconds = (expire_dt - datetime.now(expire_dt.tzinfo)).total_seconds()

    return {
        "has_expire_time": True,
        "expired": remaining_seconds <= 0,
        "remaining_seconds": remaining_seconds,
        "remaining_text": _fmt_duration(abs(remaining_seconds)),
        "expire_time_raw": expire_time_raw,
    }


def format_validate_response(response_data: Any) -> str:
    """将 validate 接口返回格式化为单行卡片信息。"""
    card, card_data = _extract_first_card_and_data(response_data)
    if not card:
        return ""

    card_number = str(card.get("cardNumber") or "").strip()
    card_password = str(card.get("cardPassword") or "").strip()

    data = response_data.get("data")
    if not isinstance(data, dict):
        return ""

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
            log_verbose(f"第 {use_count + 1} 次使用当前 CDKEY，现场校验并开卡")
        try:
            validate_result = wait_for_validate_result(code_value, proxies)
        except SkipCurrentCode as e:
            _drop_code_entry(code_array, code_index, reason=str(e))
            log_warn(f"当前兑换码 {code_value} 跳过: {e}")
            continue

        unavailable_reason, unavailable_message = get_validate_unavailable_reason(validate_result.get("response"))
        if unavailable_reason == "not_found":
            _drop_code_entry(code_array, code_index, reason=unavailable_message or "兑换码不存在")
            log_warn(f"当前兑换码 {code_value} 不存在，切换下一张卡")
            continue
        if unavailable_reason == "invalid":
            _drop_code_entry(code_array, code_index, reason=unavailable_message or "兑换码无效")
            detail = f": {unavailable_message}" if unavailable_message else ""
            log_warn(f"当前兑换码 {code_value} 无效，切换下一张卡{detail}")
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


def ensure_fresh_validate_context(validate_context: Dict[str, Any], proxies: Any = None) -> Dict[str, Any]:
    """绑卡前检查当前卡剩余时间；已过期时重新获取新卡。"""
    while True:
        validate_result = validate_context.get("validate_result") or {}
        response_data = validate_result.get("response")
        expiry_status = _get_card_expiry_status(response_data)
        if not expiry_status["has_expire_time"]:
            return validate_context

        remaining_text = str(expiry_status.get("remaining_text") or "0秒")
        if expiry_status["expired"]:
            log_warn(f"绑卡前检查：当前卡已过期（已过期 {remaining_text}），重新获取卡")
            validate_context = get_validate_context(proxies)
            continue

        log_ok(f"绑卡前检查：当前卡剩余 {remaining_text}")
        return validate_context


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


def _build_aisub_payment_payload(
    access_token: str,
    validate_result: Dict[str, Any],
    cardholder_name: str,
) -> Dict[str, Any]:
    if _uses_hosted_payment():
        return {
            "mode": "scan",
            "scan_mode": "at",
            "access_token": access_token,
            "plan": str(CONFIG.get("subscribe_plan") or DEFAULT_CONFIG["subscribe_plan"]),
            "proxy_region": str(CONFIG.get("aisub_proxy_region") or DEFAULT_CONFIG["aisub_proxy_region"] or "auto"),
        }

    card_info = _extract_card_details(validate_result)
    if not card_info:
        return {}

    billing_name = cardholder_name.strip() or str(validate_result.get("formatted_text") or "").strip()
    return {
        "mode": "at",
        "access_token": access_token,
        "card_number": card_info["card_number"],
        "exp_month": card_info["expiry_month"],
        "exp_year": card_info["expiry_year"],
        "cvv": card_info["cvv"],
        "plan": str(CONFIG.get("subscribe_plan") or DEFAULT_CONFIG["subscribe_plan"]),
        "proxy_region": str(CONFIG.get("aisub_proxy_region") or DEFAULT_CONFIG["aisub_proxy_region"] or "auto"),
        "billing": _build_billing_from_template(card_info["billing_template"], billing_name),
    }


def _parse_aisub_response(resp: Any) -> Any:
    try:
        return resp.json()
    except Exception:
        return {"error": resp.text}


def _extract_aisub_async_result(payload: Any) -> tuple[bool, int, Any, str]:
    if not isinstance(payload, dict):
        return False, 0, payload, ""

    state_text = str(payload.get("status") or "").strip()
    candidates = [payload]
    for key in ("result", "data", "response", "payload"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            candidates.append(nested)

    for candidate in candidates:
        if "success" in candidate:
            effective_status = _to_int(
                candidate.get("status_code")
                or candidate.get("http_status")
                or candidate.get("code")
            )
            if effective_status <= 0:
                effective_status = 200 if candidate.get("success") is True else 0
            return True, effective_status, candidate, state_text

    state_key = state_text.lower()
    if state_key in {"success", "succeeded", "done", "completed"}:
        normalized = dict(payload)
        normalized["success"] = True
        return True, 200, normalized, state_text
    if state_key in {"failed", "error", "cancelled", "canceled"}:
        normalized = dict(payload)
        normalized["success"] = False
        effective_status = _to_int(payload.get("status_code") or payload.get("http_status") or payload.get("code"))
        return True, effective_status, normalized, state_text
    return False, 0, payload, state_text


def _subscribe_aisub_sync(payload: Dict[str, Any], headers: Dict[str, str], proxies: Any = None) -> Dict[str, Any]:
    aisub_base_url = str(CONFIG.get("aisub_base_url") or DEFAULT_CONFIG["aisub_base_url"]).rstrip("/")
    try:
        resp = requests.post(
            f"{aisub_base_url}/api/pay",
            headers=headers,
            json=payload,
            proxies=proxies,
            impersonate="chrome",
            timeout=20,
        )
        return {
            "status_code": resp.status_code,
            "response": _parse_aisub_response(resp),
        }
    except Exception as e:
        return {
            "status_code": 0,
            "response": {"success": False, "error": str(e)},
        }


def _subscribe_aisub_async(payload: Dict[str, Any], headers: Dict[str, str], proxies: Any = None) -> Dict[str, Any]:
    aisub_base_url = str(CONFIG.get("aisub_base_url") or DEFAULT_CONFIG["aisub_base_url"]).rstrip("/")
    try:
        resp = requests.post(
            f"{aisub_base_url}/api/pay/async",
            headers=headers,
            json=payload,
            proxies=proxies,
            impersonate="chrome",
            timeout=20,
        )
    except Exception as e:
        return {
            "status_code": 0,
            "response": {"success": False, "error": str(e)},
        }

    response_data = _parse_aisub_response(resp)
    if resp.status_code not in {200, 201, 202}:
        return {
            "status_code": resp.status_code,
            "response": response_data,
        }

    initial_done, initial_status, initial_payload, _ = _extract_aisub_async_result(response_data)
    if initial_done:
        return {
            "status_code": initial_status or resp.status_code,
            "response": initial_payload,
        }

    task_id = str(
        (response_data.get("task_id") if isinstance(response_data, dict) else "")
        or (response_data.get("taskId") if isinstance(response_data, dict) else "")
        or ""
    ).strip()
    if not task_id:
        return {
            "status_code": 0,
            "response": {"success": False, "error": "AISub 异步支付未返回 task_id"},
        }

    timeout_seconds = max(30, _to_int(CONFIG.get("aisub_async_timeout") or DEFAULT_CONFIG["aisub_async_timeout"]))
    poll_interval = max(1, _to_int(CONFIG.get("aisub_async_poll_interval") or DEFAULT_CONFIG["aisub_async_poll_interval"]))
    last_state = ""
    deadline = time.time() + timeout_seconds
    log_verbose(f"AISub 异步支付任务已创建: {task_id}")

    while time.time() < deadline:
        try:
            status_resp = requests.get(
                f"{aisub_base_url}/api/pay/status/{quote(task_id, safe='')}",
                headers=headers,
                proxies=proxies,
                impersonate="chrome",
                timeout=20,
            )
        except Exception as e:
            return {
                "status_code": 0,
                "response": {"success": False, "error": f"AISub 状态查询失败: {e}", "task_id": task_id},
            }

        status_data = _parse_aisub_response(status_resp)
        if status_resp.status_code != 200:
            return {
                "status_code": status_resp.status_code,
                "response": status_data,
            }

        is_done, effective_status, final_payload, state_text = _extract_aisub_async_result(status_data)
        current_state = state_text or str((status_data.get("message") if isinstance(status_data, dict) else "") or "").strip()
        if current_state and current_state != last_state:
            log_verbose(f"AISub 异步支付状态[{task_id}]: {current_state}")
            last_state = current_state

        if is_done:
            if isinstance(final_payload, dict):
                final_payload = dict(final_payload)
                final_payload.setdefault("task_id", task_id)
            return {
                "status_code": effective_status or status_resp.status_code,
                "response": final_payload,
            }

        time.sleep(poll_interval)

    return {
        "status_code": 0,
        "response": {
            "success": False,
            "error": f"AISub 异步支付超时（{timeout_seconds} 秒）",
            "task_id": task_id,
        },
    }


def subscribe_aisub(access_token: str, validate_result: Dict[str, Any], cardholder_name: str, proxies: Any = None) -> Dict[str, Any]:
    """调用 AISub subscribe 接口。"""
    payload = _build_aisub_payment_payload(access_token, validate_result, cardholder_name)
    if not payload:
        return {
            "status_code": 0,
            "response": {"success": False, "error": "缺少卡信息"},
        }

    headers = dict(_aisub_headers())
    headers["Content-Type"] = "application/json"
    if _aisub_payment_mode_key() == "async":
        return _subscribe_aisub_async(payload, headers, proxies)

    try:
        return _subscribe_aisub_sync(payload, headers, proxies)
    except Exception as e:
        return {
            "status_code": 0,
            "response": {"success": False, "error": str(e)},
        }


def _extract_subscribe_failure_info(response_data: Any) -> tuple[str, str]:
    full_text = ""
    concise_reason = ""
    if not isinstance(response_data, dict):
        return full_text, concise_reason

    message_text = str(response_data.get("message") or response_data.get("detail") or "").strip()
    error_text = str(response_data.get("error") or "").strip()
    error_code = str(response_data.get("code") or response_data.get("error_code") or "").strip()
    task_status = str(response_data.get("status") or "").strip()
    steps = response_data.get("steps")
    step_texts: list[str] = []
    if isinstance(steps, list):
        step_texts = [str(step).strip() for step in steps if str(step).strip()]

    parts = [part for part in [message_text, error_text, error_code, task_status, *step_texts] if part]
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
    is_generic_message = message_text in generic_errors

    if any("需要 hCaptcha challenge" in step for step in step_texts):
        concise_reason = "需要 hCaptcha challenge"
    elif any("3DS" in step or "额外验证" in step for step in step_texts):
        concise_reason = "该账号需要额外验证（3DS）"
    elif message_text and not is_generic_message:
        concise_reason = message_text
    elif message_text and diagnostic_step:
        concise_reason = f"{message_text} | {diagnostic_step}"
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


def _raise_for_aisub_http_error(status_code: int, response_data: Any, failure_reason: str) -> None:
    if status_code not in {401, 402, 403}:
        return
    detail = failure_reason.strip()
    if not detail and isinstance(response_data, dict):
        detail = str(response_data.get("message") or response_data.get("error") or "").strip()
    suffix = f"，详情: {detail}" if detail else ""
    if status_code == 401:
        raise StopScript(f"AISub API Key 无效或缺失{suffix}")
    if status_code == 402:
        raise StopScript(f"AISub 余额不足{suffix}")
    raise StopScript(f"AISub 账户已禁用{suffix}")


def wait_for_subscribe_success(
    access_token: str,
    validate_context: Dict[str, Any],
    proxies: Any = None,
    cardholder_name: str = "",
) -> Dict[str, Any]:
    """阻塞等待 subscribe 成功。"""
    retry_with_new_account_enabled = bool(
        CONFIG.get("subscribe_retry_new_account_enabled", DEFAULT_CONFIG["subscribe_retry_new_account_enabled"])
    )
    switch_account_on_3ds_enabled = bool(
        CONFIG.get(
            "subscribe_switch_account_on_3ds_enabled",
            DEFAULT_CONFIG["subscribe_switch_account_on_3ds_enabled"],
        )
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
        if _uses_hosted_payment():
            validate_result = validate_context.get("validate_result") or {}
        else:
            validate_context = ensure_fresh_validate_context(validate_context, proxies)
            validate_result = validate_context["validate_result"]
        subscribe_result = subscribe_aisub(access_token, validate_result, cardholder_name, proxies)
        response_data = subscribe_result.get("response") or {}
        failure_text, failure_reason = _extract_subscribe_failure_info(response_data)
        status_code = int(subscribe_result.get("status_code") or 0)
        _raise_for_aisub_http_error(status_code, response_data, failure_reason)
        if subscribe_result.get("status_code") == 200 and isinstance(response_data, dict) and response_data.get("success") is True:
            steps = response_data.get("steps")
            last_step = ""
            if isinstance(steps, list):
                last_step = next((str(step).strip() for step in reversed(steps) if str(step).strip()), "")
            detail = f": {last_step}" if last_step else ""
            log_ok(f"AISub 绑卡成功{detail}")
            return {
                "subscribe_result": subscribe_result,
                "validate_context": validate_context,
            }
        if switch_account_on_3ds_enabled and "该账号需要额外验证（3DS）" in failure_text:
            detail = f"，原因: {failure_reason}" if failure_reason else ""
            raise RetryWithNewAccount(f"该账号需要额外验证（3DS），切换下一个账号继续复用当前卡{detail}")
        if "需要 hCaptcha challenge" in failure_text:
            detail = f"，原因: {failure_reason}" if failure_reason else ""
            raise RetryWithNewAccount(f"该账号触发 hCaptcha challenge，切换下一个账号继续复用当前卡{detail}")
        failed_attempts += 1
        if failed_attempts >= retry_with_new_account_limit:
            if retry_with_new_account_enabled:
                raise RetryWithNewAccount(
                    f"subscribe 连续失败 {failed_attempts} 次，放弃当前账号并重新注册，继续复用当前卡"
                )
            raise RuntimeError(f"subscribe 连续失败 {failed_attempts} 次，已达到重试上限")
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
        "client_id": _get_openai_client_id(),
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
    originator = _get_openai_originator()
    if originator:
        params["originator"] = originator
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
            "client_id": _get_openai_client_id(),
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


def _enrich_token_json_with_registration_context(
    token_json: str,
    *,
    password: str,
    birthdate: str,
    mailbox: Dict[str, Any],
) -> str:
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
    if mailbox.get("email_password"):
        token_data["email_password"] = str(mailbox.get("email_password") or "")
    if mailbox.get("junmail_mailbox_id"):
        token_data["junmail_mailbox_id"] = str(mailbox.get("junmail_mailbox_id") or "")
    if mailbox.get("cfmail_account_name"):
        token_data["cfmail_account_name"] = str(mailbox.get("cfmail_account_name") or "")
    return json.dumps(token_data, ensure_ascii=False, separators=(",", ":"))


def run(proxy: Optional[str]) -> Optional[str]:
    proxies = _build_proxy_dict(proxy)

    _record_last_run_failure("")
    mailbox: Optional[Dict[str, Any]] = None

    try:
        s = requests.Session(proxies=proxies, impersonate="chrome")
        trace = s.get("https://cloudflare.com/cdn-cgi/trace", timeout=10)
        trace = trace.text
        loc_re = re.search(r"^loc=(.+)$", trace, re.MULTILINE)
        loc = loc_re.group(1) if loc_re else None
        if loc == "CN" or loc == "HK":
            raise RuntimeError("检查代理哦w - 所在地不支持")
    except Exception as e:
        _record_last_run_failure(f"网络连接检查失败: {e}")
        log_error(f"网络连接检查失败: {e}")
        return None

    try:
        mailbox = create_registration_email_context(proxies)
    except Exception as e:
        _record_last_run_failure(f"创建注册邮箱失败: {e}")
        log_error(f"创建注册邮箱失败: {e}")
        return None
    email = str(mailbox.get("email") or "").strip()
    if not email:
        _record_last_run_failure("邮箱创建结果为空")
        log_error("邮箱创建结果为空")
        return None
    provider_name = "TempMail" if mailbox.get("custom_domain") else _email_provider_label(mailbox.get("email_provider"))
    log_ok(f"邮箱就绪 [{provider_name}]: {email}")

    try:
        return _run_cpa_style_registration_flow(
            proxy=proxy,
            mailbox=mailbox,
            email=email,
            oauth_log_to_info=(_register_type_key() == "team"),
        )
    except Exception as e:
        _record_last_run_failure(f"运行时发生错误: {e}")
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
    pending_cpa_uploads = 0
    cpa_cleanup_executed = False

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
            overview_rows = [("注册类型", _register_type_label(register_type))]
            if register_type == "team":
                overview_rows.extend(
                    [
                        ("卡商", _card_provider_label()),
                        ("开卡时机", _team_card_open_timing_label()),
                    ]
                )
            _render_kv_table("运行前概览", overview_rows)
            if register_type == "team":
                print_card_inventory_summary()
                aisub_balance_before = get_aisub_balance_snapshot(proxies)
                print_aisub_balance_summary("运行前 AISub 余额", aisub_balance_before)
        if register_type == "team":
            ensure_aisub_balance(proxies)
        if (
            register_type != "team"
            and bool(CONFIG.get("cpa_cleanup_enabled", DEFAULT_CONFIG["cpa_cleanup_enabled"]))
            and not cpa_cleanup_executed
        ):
            _run_cpa_cleanup_before_register()
            cpa_cleanup_executed = True

        started_at = datetime.now()
        while True:
            count += 1
            if count == 1:
                reset_teams_file(teams_file)
            log_section(f"开始第 {count} 次注册流程")
            last_cycle_failure_reason = ""

            try:
                validate_context: Optional[Dict[str, Any]] = None
                validate_result: Dict[str, Any] = {}
                if register_type == "team":
                    ensure_aisub_balance(proxies)
                    if not _uses_hosted_payment() and _team_card_open_timing_key() == "before_register":
                        validate_context = get_validate_context(proxies)
                        validate_result = validate_context["validate_result"]
                    elif not _uses_hosted_payment():
                        ensure_team_card_capacity_available()

                token_json = run(proxy_value)

                if token_json:
                    try:
                        t_data = json.loads(token_json)
                    except Exception:
                        t_data = {}

                    t_data["register_type"] = register_type
                    if register_type != "team":
                        token_artifact_path = _save_codex_token_artifacts(t_data)
                        if token_artifact_path:
                            pending_cpa_uploads += 1
                            upload_every_n = max(
                                1,
                                int(CONFIG.get("cpa_upload_every_n") or DEFAULT_CONFIG["cpa_upload_every_n"]),
                            )
                            if (
                                str(CONFIG.get("upload_api_url") or DEFAULT_CONFIG["upload_api_url"]).strip()
                                and pending_cpa_uploads >= upload_every_n
                            ):
                                log_info(
                                    f"达到 CPA 自动导入阈值: {pending_cpa_uploads}/{upload_every_n}，开始上传"
                                )
                                _upload_all_tokens_to_cpa()
                                pending_cpa_uploads = 0

                    if register_type == "team":
                        access_token = str(t_data.get("access_token") or "").strip()
                        if not access_token:
                            raise RuntimeError("token_json 中缺少 access_token")
                        if not validate_context and not _uses_hosted_payment():
                            log_info("账号注册完成，开始获取虚拟卡")
                            validate_context = get_validate_context(proxies)
                            validate_result = validate_context["validate_result"]
                        full_name = f"{t_data.get('first_name', '')} {t_data.get('last_name', '')}".strip()

                        subscribe_context = wait_for_subscribe_success(
                            access_token,
                            validate_context or {},
                            proxies,
                            full_name,
                        )
                        validate_context = subscribe_context["validate_context"]
                        validate_result = validate_context.get("validate_result") or {}
                        subscribe_result = subscribe_context["subscribe_result"]
                        if not _uses_hosted_payment():
                            current_use_count = int(validate_context["use_count"])
                            mark_code_used(
                                validate_context["code_array"],
                                int(validate_context["code_index"]),
                                current_use_count,
                            )
                            if current_use_count == 0:
                                cards_used += 1
                        aisub_uses += 1

                        if validate_result:
                            t_data["validate_result"] = validate_result
                        t_data["subscribe_result"] = subscribe_result
                        mother_accounts += 1
                    append_team_entry(teams_file, t_data)
                    registered_accounts += 1
                    if should_stop_for_target(
                        registered_accounts=registered_accounts,
                        mother_accounts=mother_accounts,
                    ):
                        break
                else:
                    last_cycle_failure_reason = _take_last_run_failure()
                    if bool(CONFIG.get("verbose_info_logs_enabled", DEFAULT_CONFIG["verbose_info_logs_enabled"])) and last_cycle_failure_reason:
                        log_error(f"本次注册失败，原因: {last_cycle_failure_reason}")
                    else:
                        log_error("本次注册失败")

            except RetryWithNewAccount as e:
                last_cycle_failure_reason = str(e)
                log_warn(str(e))
            except StopScript as e:
                last_cycle_failure_reason = str(e)
                log_warn(str(e))
                break
            except Exception as e:
                last_cycle_failure_reason = str(e)
                log_error(f"发生未捕获异常: {e}")

            if args.once:
                break

            wait_time = random.randint(sleep_min, sleep_max)
            if bool(CONFIG.get("verbose_info_logs_enabled", DEFAULT_CONFIG["verbose_info_logs_enabled"])) and last_cycle_failure_reason:
                log_info(f"本轮未成功注册，{wait_time} 秒后重试；原因: {last_cycle_failure_reason}")
            else:
                log_info(f"休息 {wait_time} 秒")
            time.sleep(wait_time)
    finally:
        ended_at = datetime.now()
        if register_type == "team":
            aisub_balance_after = get_aisub_balance_snapshot(proxies)
            print_aisub_balance_summary("运行后 AISub 余额", aisub_balance_after)
        if register_type != "team":
            _upload_all_tokens_to_cpa()
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
