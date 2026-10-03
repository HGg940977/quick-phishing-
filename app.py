#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════
#  EIIN RECON TOOLKIT — Professional Edition
#  Developer : Ahmed Shariar
#  Style     : Kali Recon Ops
#  Platform  : Windows / Linux / Termux / macOS
#  Python    : 3.7+
# ═══════════════════════════════════════════════════════════════

import sys
import os
import re
import io
import csv
import json
import time
import html
import argparse
import platform
import threading
import subprocess
from datetime import datetime
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
#  UTF-8 ENFORCEMENT
# ═══════════════════════════════════════════════════════════════
def _force_utf8():
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        else:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8",
                errors="replace", line_buffering=True
            )
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding="utf-8",
                errors="replace", line_buffering=True
            )
    except Exception:
        pass
    if platform.system() == "Windows":
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")
        try:
            os.system("chcp 65001 > nul 2>&1")
        except Exception:
            pass


_force_utf8()


# ═══════════════════════════════════════════════════════════════
#  COLOR SYSTEM
# ═══════════════════════════════════════════════════════════════
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"

    # Hacker palette (256-color)
    HGREEN = "\033[38;5;46m"
    HAMBER = "\033[38;5;214m"
    HRED = "\033[38;5;196m"
    HCYAN = "\033[38;5;51m"
    HMAG = "\033[38;5;201m"
    HWHITE = "\033[38;5;255m"
    HDIM = "\033[38;5;240m"


def _enable_windows_ansi():
    if platform.system() != "Windows":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        for attr in dir(C):
            if attr.isupper():
                setattr(C, attr, "")


_enable_windows_ansi()

if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
    for attr in dir(C):
        if attr.isupper():
            setattr(C, attr, "")


def safe_out(s):
    if s is None:
        return ""
    return str(s)


# ═══════════════════════════════════════════════════════════════
#  SESSION INFO
# ═══════════════════════════════════════════════════════════════
def _get_user():
    return os.environ.get("USER") or os.environ.get("USERNAME") or "root"


def _get_host():
    try:
        h = platform.node() or "kali"
        h = re.sub(r"[^\w\-]", "", h)[:16]
        return h or "kali"
    except Exception:
        return "kali"


USER_NAME = _get_user()
HOST_NAME = _get_host()


def kali_prompt():
    return (
        f"{C.HGREEN}{C.BOLD}{USER_NAME}@{HOST_NAME}{C.RESET}"
        f"{C.HDIM}:{C.RESET}"
        f"{C.HCYAN}{C.BOLD}~{C.RESET}"
        f"{C.HGREEN}{C.BOLD}#{C.RESET} "
    )


# ═══════════════════════════════════════════════════════════════
#  HTTP
# ═══════════════════════════════════════════════════════════════
def http_get(url, timeout=30):
    import ssl
    import urllib.request

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) "
                "Gecko/20100101 Firefox/120.0"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        code = resp.getcode()
        data = resp.read().decode("utf-8", errors="replace")
        return code, data


# ═══════════════════════════════════════════════════════════════
#  TERMINAL HELPERS
# ═══════════════════════════════════════════════════════════════
def term_width():
    try:
        return min(os.get_terminal_size().columns, 110)
    except Exception:
        return 90


def clear_screen():
    os.system("cls" if platform.system() == "Windows" else "clear")


def writeln(s=""):
    sys.stdout.write(s + "\n")
    sys.stdout.flush()


def kv(label, value, color=None, indent=2, width=22):
    color = color if color is not None else C.WHITE
    pad = " " * indent
    lab = safe_out(str(label))
    val = safe_out(str(value))
    writeln(f"{pad}{C.HDIM}{lab:<{width}}{C.RESET}{color}{val}{C.RESET}")


def section(title, color=None):
    color = color if color is not None else C.HCYAN
    w = term_width()
    t = safe_out(title)
    writeln()
    writeln(f"{color}{C.BOLD}▌ {t}{C.RESET}")
    writeln(f"{color}{'─' * w}{C.RESET}")


# ═══════════════════════════════════════════════════════════════
#  BANNER + BOOT
# ═══════════════════════════════════════════════════════════════
BANNER_LINES = [
    "  ███████ ██ ██ ███    ██     ██████  ███████  ██████  ██████  ███    ██",
    "  ██      ██ ██ ████   ██     ██   ██ ██      ██      ██    ██ ████   ██",
    "  █████   ██ ██ ██ ██  ██     ██████  █████   ██      ██    ██ ██ ██  ██",
    "  ██      ██ ██ ██  ██ ██     ██   ██ ██      ██      ██    ██ ██  ██ ██",
    "  ███████ ██ ██ ██   ████     ██   ██ ███████  ██████  ██████  ██   ████",
]

BOOT_LINES = [
    ("Initializing recon toolkit",          "ok"),
    ("Loading modules: net, parse, render", "ok"),
    ("Bypassing TLS verification",          "warn"),
    ("Spoofing user agent",                 "warn"),
    ("Opening encrypted channel",           "ok"),
    ("Channel established. Awaiting target.","ok"),
]


def boot_sequence(skip=False):
    clear_screen()
    w = term_width()
    line_w = w - 2

    writeln(f"{C.HGREEN}┌{'─' * line_w}┐{C.RESET}")

    for line in BANNER_LINES:
        pad = max(0, (line_w - len(line)) // 2)
        trail = max(0, line_w - pad - len(line))
        writeln(
            f"{C.HGREEN}│{C.RESET}"
            f"{' ' * pad}{C.HGREEN}{C.BOLD}{line}{C.RESET}{' ' * trail}"
            f"{C.HGREEN}│{C.RESET}"
        )

    writeln(f"{C.HGREEN}│{' ' * line_w}│{C.RESET}")

    tag = "Bangladesh Education Board · Teacher Database Recon"
    pad = max(0, (line_w - len(tag)) // 2)
    trail = max(0, line_w - pad - len(tag))
    writeln(
        f"{C.HGREEN}│{C.RESET}"
        f"{' ' * pad}{C.HCYAN}{tag}{C.RESET}{' ' * trail}"
        f"{C.HGREEN}│{C.RESET}"
    )

    dev = "Developer: Ahmed Shariar   ·   v3.0 Recon Edition"
    pad = max(0, (line_w - len(dev)) // 2)
    trail = max(0, line_w - pad - len(dev))
    writeln(
        f"{C.HGREEN}│{C.RESET}"
        f"{' ' * pad}{C.HMAG}{dev}{C.RESET}{' ' * trail}"
        f"{C.HGREEN}│{C.RESET}"
    )

    writeln(f"{C.HGREEN}└{'─' * line_w}┘{C.RESET}")
    writeln()

    if skip:
        return

    for label, kind in BOOT_LINES:
        tag = "[*]" if kind == "warn" else "[+]"
        tag_c = C.HAMBER if kind == "warn" else C.HGREEN
        sys.stdout.write(f"{C.HDIM}{tag}{C.RESET} {label} ...")
        sys.stdout.flush()
        time.sleep(0.22)
        sys.stdout.write(f" {C.HGREEN}[OK]{C.RESET}\n")
        sys.stdout.flush()

    writeln()


def scan_animation(eiin):
    w = term_width()
    writeln()
    writeln(
        f"{C.HGREEN}{C.BOLD}[→] TARGET ACQUIRED:{C.RESET} "
        f"{C.HAMBER}{C.BOLD}EIIN {eiin}{C.RESET}"
    )
    writeln(
        f"{C.HDIM}[*] Endpoint:{C.RESET} "
        f"{C.HCYAN}cxofb.nid-bd.my.id/eiin1.php{C.RESET}"
    )
    writeln()

    steps = [
        "Resolving DNS",
        "Establishing TLS tunnel",
        "Crafting request payload",
        "Awaiting response packets",
    ]
    bar_len = max(24, min(46, w - 40))

    for label in steps:
        for pct in range(0, 101, 10):
            filled = int(bar_len * pct / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            sys.stdout.write(
                f"\r{C.HDIM}[*]{C.RESET} {label:<28} "
                f"{C.HGREEN}[{bar}]{C.RESET} "
                f"{C.HAMBER}{pct:>3}%{C.RESET}"
            )
            sys.stdout.flush()
            time.sleep(0.045)
        sys.stdout.write(f" {C.HGREEN}[OK]{C.RESET}\n")
        sys.stdout.flush()

    writeln()


# ═══════════════════════════════════════════════════════════════
#  API
# ═══════════════════════════════════════════════════════════════
API_BASE = "https://cxofb.nid-bd.my.id/eiin1.php"


def fetch_eiin(eiin):
    url = f"{API_BASE}?eiin={eiin}"
    t0 = time.time()
    meta = {"_url": url}

    try:
        code, body = http_get(url, timeout=30)
    except Exception as e:
        meta.update({
            "_error": True,
            "_message": f"Connection failed: {e}",
            "_elapsed": time.time() - t0,
        })
        return None, meta

    meta["_elapsed"] = time.time() - t0

    if code != 200:
        meta.update({
            "_error": True,
            "_message": f"HTTP {code}",
            "_raw": body[:500],
        })
        return None, meta

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as e:
        meta.update({
            "_error": True,
            "_message": f"Invalid JSON: {e}",
            "_raw": body[:500],
        })
        return None, meta

    return parsed, meta


# ═══════════════════════════════════════════════════════════════
#  TEACHER DETECTION
# ═══════════════════════════════════════════════════════════════
TEACHERISH_KEYS = {
    "name", "teacher_name", "tname", "name_bn", "name_en",
    "designation", "subject", "index", "mobile", "phone",
    "teacher", "teachers", "full_name", "fullname",
    "teacher_id", "tid", "id_no", "nid",
}


def extract_teachers(payload):
    candidates = []

    def walk(node, path=""):
        if isinstance(node, list) and node and all(isinstance(x, dict) for x in node):
            keys_union = set()
            for x in node[:5]:
                keys_union.update(k for k in x.keys() if isinstance(k, str))
            if keys_union & TEACHERISH_KEYS:
                candidates.append((path or "root", node))

        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")

    walk(payload)
    if not candidates:
        return None, None

    best = max(candidates, key=lambda p: len(p[1]))
    return best[0], best[1]


# ═══════════════════════════════════════════════════════════════
#  FIELD LABELS
# ═══════════════════════════════════════════════════════════════
FIELD_LABELS = {
    "name": "Name",
    "teacher_name": "Teacher Name",
    "tname": "Teacher Name",
    "name_bn": "Name (বাংলা)",
    "name_en": "Name (English)",
    "full_name": "Full Name",
    "fullname": "Full Name",
    "designation": "Designation",
    "subject": "Subject",
    "index": "Index",
    "mobile": "Mobile",
    "phone": "Phone",
    "email": "Email",
    "nid": "NID",
    "teacher_id": "Teacher ID",
    "tid": "Teacher ID",
    "id_no": "ID No",
    "gender": "Gender",
    "dob": "Date of Birth",
    "joining_date": "Joining Date",
    "index_no": "Index No",
    "mp_index": "MP Index",
    "bank_account": "Bank Account",
    "bank_name": "Bank Name",
    "branch": "Branch",
    "routing": "Routing",
    "present_address": "Present Address",
    "permanent_address": "Permanent Address",
    "father_name": "Father's Name",
    "mother_name": "Mother's Name",
    "spouse_name": "Spouse's Name",
    "religion": "Religion",
    "blood_group": "Blood Group",
    "marital_status": "Marital Status",
    "nationality": "Nationality",
    "position": "Position",
    "post": "Post",
    "salary": "Salary",
    "grade": "Grade",
    "teacher_index": "Teacher Index",
    "teacher_type": "Teacher Type",
    "school_name": "School Name",
    "institute": "Institute",
    "institute_name": "Institute Name",
    "district": "District",
    "thana": "Thana",
    "upazila": "Upazila",
    "address": "Address",
    "eiin": "EIIN",
}


def label_for(key):
    k = str(key).strip()
    low = k.lower()
    if low in FIELD_LABELS:
        return FIELD_LABELS[low]
    return k.replace("_", " ").replace("-", " ").title()


PRIORITY = [
    "name", "name_bn", "name_en", "teacher_name", "tname",
    "full_name", "fullname",
    "designation", "position", "post", "subject", "teacher_type",
    "index", "index_no", "teacher_index", "mp_index", "id_no",
    "teacher_id", "tid", "nid",
    "mobile", "phone", "email",
    "gender", "dob", "blood_group", "religion", "nationality",
    "marital_status", "father_name", "mother_name", "spouse_name",
    "joining_date", "salary", "grade",
    "bank_account", "bank_name", "branch", "routing",
    "present_address", "permanent_address", "address",
    "institute", "institute_name", "school_name",
    "district", "thana", "upazila", "eiin",
]


def normalize_record(t):
    if not isinstance(t, dict):
        return [("Value", t)]

    seen = set()
    out = []
    for k in PRIORITY:
        for real_k in t.keys():
            if str(real_k).lower() == k and real_k not in seen:
                v = t[real_k]
                seen.add(real_k)
                if v is None or (isinstance(v, str) and not v.strip()):
                    continue
                out.append((label_for(real_k), v))
    for k, v in t.items():
        if k in seen:
            continue
        if isinstance(k, str) and k.startswith("_"):
            continue
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        out.append((label_for(k), v))
    return out


# ═══════════════════════════════════════════════════════════════
#  RENDER
# ═══════════════════════════════════════════════════════════════
def render_status(msg, kind="ok"):
    colors = {"ok": C.HGREEN, "warn": C.HAMBER, "err": C.HRED, "info": C.HCYAN}
    tags = {"ok": "[+]", "warn": "[!]", "err": "[-]", "info": "[*]"}
    writeln(f"{colors[kind]}{C.BOLD}{tags[kind]}{C.RESET} {msg}")


def render_teacher(idx, teacher, total):
    w = term_width()
    head = f" ▌ RECORD {idx:02d}/{total:02d} "
    trail = "─" * max(0, w - len(head))
    writeln()
    writeln(f"{C.HGREEN}{C.BOLD}{head}{trail}{C.RESET}")
    writeln()

    rows = normalize_record(teacher)
    if not rows:
        writeln(f"    {C.HDIM}(no fields){C.RESET}")
        return

    max_lab = min(max(len(str(lab)) for lab, _ in rows), 22)

    for lab, val in rows:
        lab_s = safe_out(str(lab))[:max_lab]
        if isinstance(val, (dict, list)):
            writeln(f"    {C.HCYAN}{lab_s:<{max_lab}}{C.RESET} {C.HDIM}▸{C.RESET}")
            pretty = json.dumps(val, ensure_ascii=False, indent=2)
            for line in pretty.splitlines():
                writeln(f"      {C.HWHITE}{line}{C.RESET}")
            continue

        val_s = safe_out(val)
        low = lab_s.lower()
        color = C.HWHITE
        if low in ("name", "name (বাংলা)", "teacher name", "full name"):
            color = C.HAMBER + C.BOLD
        elif low in ("designation", "position", "post", "subject"):
            color = C.HCYAN
        elif low in ("mobile", "phone", "email"):
            color = C.HGREEN
        elif low in ("nid", "index", "index no", "id no"):
            color = C.HMAG

        writeln(
            f"    {C.HDIM}{lab_s:<{max_lab}}{C.RESET} "
            f"{C.HDIM}»{C.RESET} {color}{val_s}{C.RESET}"
        )


def render_institute(core):
    inst_keys = (
        "institute", "institute_name", "school_name", "school",
        "college", "institution", "eiin", "address", "district",
        "thana", "upazila", "phone", "mobile", "email", "type",
        "affiliation",
    )
    pairs = []
    for k in inst_keys:
        if k in core and not isinstance(core[k], (dict, list)):
            v = core[k]
            if v is None:
                continue
            if isinstance(v, str) and not v.strip():
                continue
            pairs.append((k, v))

    if not pairs:
        return

    section("INSTITUTE PROFILE", C.HMAG)
    max_lab = min(max(len(label_for(k)) for k, _ in pairs), 22)
    for k, v in pairs:
        lab = label_for(k)
        color = C.HAMBER + C.BOLD if str(k).lower() == "eiin" else C.HWHITE
        writeln(
            f"  {C.HDIM}{lab:<{max_lab}}{C.RESET} "
            f"{C.HDIM}»{C.RESET} {color}{safe_out(v)}{C.RESET}"
        )


def render_result(eiin, payload, meta=None, raw_mode=False):
    meta = meta or {}

    if raw_mode:
        writeln(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if meta.get("_error") or payload is None:
        writeln()
        writeln(
            f"{C.BG_RED}{C.WHITE}{C.BOLD}  FAILED  {C.RESET} "
            f"{C.HRED}{safe_out(meta.get('_message', 'unknown'))}{C.RESET}"
        )
        if meta.get("_url"):
            writeln(f"  {C.HDIM}endpoint: {meta['_url']}{C.RESET}")
        if meta.get("_raw"):
            writeln()
            writeln(f"{C.HDIM}{safe_out(meta['_raw'][:500])}{C.RESET}")
        writeln()
        return

    section("RECON SUMMARY", C.HCYAN)
    kv("Target", f"EIIN {eiin}", C.HAMBER)
    kv("Endpoint", meta.get("_url", "-"), C.HCYAN)
    kv("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), C.HWHITE)
    kv("Latency", f"{meta.get('_elapsed', 0):.2f}s", C.HGREEN)
    try:
        blen = len(json.dumps(payload, ensure_ascii=False))
    except Exception:
        blen = 0
    kv("Payload", f"{blen:,} bytes", C.HWHITE)

    # List payload
    if isinstance(payload, list):
        src, teachers = extract_teachers(payload)
        if teachers:
            render_status(f"{len(teachers)} teacher record(s) extracted", "ok")
            for i, t in enumerate(teachers, 1):
                render_teacher(i, t, len(teachers))
            writeln()
            render_status("Extraction complete.", "ok")
            writeln()
            return

        section(f"RAW ARRAY · {len(payload)} item(s)", C.HCYAN)
        writeln(json.dumps(payload, ensure_ascii=False, indent=2))
        writeln()
        return

    # Dict payload
    if isinstance(payload, dict):
        core = {
            k: v for k, v in payload.items()
            if not (isinstance(k, str) and k.startswith("_"))
        }

        success = core.get("success", core.get("status"))
        if success is not None:
            ok = success in (True, "true", "success", 1, "1")
            render_status(f"Server flag: {success}", "ok" if ok else "err")

        src, teachers = extract_teachers(core)
        if teachers:
            render_status(f"{len(teachers)} teacher record(s) extracted", "ok")
            render_institute(core)
            for i, t in enumerate(teachers, 1):
                render_teacher(i, t, len(teachers))

            used = set((
                "institute", "institute_name", "school_name", "school",
                "college", "institution", "eiin", "address", "district",
                "thana", "upazila", "phone", "mobile", "email", "type",
                "affiliation", "success", "status", "message", "msg",
                "error", "data", "result", "records", "teachers", "list",
            ))
            extras = {k: v for k, v in core.items() if k not in used}
            extras = {k: v for k, v in extras.items() if v is not teachers}

            if extras:
                section("OTHER FIELDS", C.HCYAN)
                for k, v in extras.items():
                    if isinstance(v, (dict, list)):
                        writeln(f"  {C.HCYAN}{label_for(k)}{C.RESET}")
                        writeln(json.dumps(v, ensure_ascii=False, indent=2))
                    else:
                        kv(label_for(k), safe_out(v))

            writeln()
            render_status("Extraction complete.", "ok")
            writeln()
            return

        section("RAW RESPONSE", C.HCYAN)
        writeln(json.dumps(core, ensure_ascii=False, indent=2))
        writeln()
        return

    section("RESPONSE", C.HCYAN)
    writeln(f"  {safe_out(payload)}")
    writeln()


# ═══════════════════════════════════════════════════════════════
#  EXPORTERS
# ═══════════════════════════════════════════════════════════════
def ensure_dir(p):
    try:
        Path(p).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def default_out_dir():
    base = Path.home() / "eiin_output"
    ensure_dir(base)
    return base


def export_json(payload, meta, eiin, out_dir):
    ensure_dir(out_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = Path(out_dir) / f"eiin_{eiin}_{ts}.json"
    wrapped = {
        "meta": {
            "eiin": eiin,
            "url": meta.get("_url"),
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "response_time_sec": round(meta.get("_elapsed", 0), 3),
            "success": not bool(meta.get("_error")),
            "error_message": meta.get("_message"),
            "tool": "EIIN Recon Toolkit",
            "developer": "Ahmed Shariar",
            "version": "3.0",
        },
        "data": payload,
    }
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(wrapped, f, ensure_ascii=False, indent=2)
    return fname


def export_csv(payload, meta, eiin, out_dir):
    ensure_dir(out_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = Path(out_dir) / f"eiin_{eiin}_{ts}.csv"

    _, teachers = (extract_teachers(payload)
                   if payload is not None else (None, None))

    with open(fname, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if teachers:
            keys = []
            seen = set()
            for t in teachers:
                for k in t.keys():
                    if isinstance(k, str) and k not in seen:
                        seen.add(k)
                        keys.append(k)
            w.writerow(["#"] + [label_for(k) for k in keys])
            for i, t in enumerate(teachers, 1):
                row = [i]
                for k in keys:
                    v = t.get(k, "")
                    if isinstance(v, (dict, list)):
                        v = json.dumps(v, ensure_ascii=False)
                    row.append(v)
                w.writerow(row)
        else:
            w.writerow(["Field", "Value"])
            if isinstance(payload, dict):
                for k, v in payload.items():
                    if isinstance(v, (dict, list)):
                        v = json.dumps(v, ensure_ascii=False)
                    w.writerow([label_for(k), v])
    return fname


def export_html(payload, meta, eiin, out_dir):
    ensure_dir(out_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = Path(out_dir) / f"eiin_{eiin}_{ts}.html"

    _, teachers = (extract_teachers(payload)
                   if payload is not None else (None, None))

    def esc(x):
        return html.escape(str(x if x is not None else ""))

    def render_json_html(node):
        if node is None:
            return "<span class='muted'>null</span>"
        if isinstance(node, bool):
            cls = "bool-true" if node else "bool-false"
            return f"<span class='{cls}'>{str(node).lower()}</span>"
        if isinstance(node, (int, float)):
            return f"<span class='num'>{node}</span>"
        if isinstance(node, str):
            return f"<span class='str'>{esc(node)}</span>"
        if isinstance(node, list):
            if not node:
                return "<span class='muted'>[ ]</span>"
            parts = []
            for i, it in enumerate(node):
                parts.append(f"<span class='muted'>[{i}]</span> {render_json_html(it)}")
            return "<br>".join(parts)
        if isinstance(node, dict):
            if not node:
                return "<span class='muted'>{ }</span>"
            parts = []
            for k, v in node.items():
                if isinstance(k, str) and k.startswith("_"):
                    continue
                parts.append(
                    f"<span class='key'>{esc(label_for(k))}</span> "
                    f"<span class='muted'>:</span> {render_json_html(v)}"
                )
            return "<br>".join(parts)
        return esc(node)

    teacher_cards = []
    if teachers:
        for i, t in enumerate(teachers, 1):
            rows = normalize_record(t)
            cells = []
            for lab, v in rows:
                if isinstance(v, (dict, list)):
                    v = json.dumps(v, ensure_ascii=False)
                cells.append(
                    f"<tr><td class='k'>{esc(lab)}</td>"
                    f"<td class='v'>{esc(v)}</td></tr>"
                )
            teacher_cards.append(
                "<div class='card'>"
                f"<div class='card-head'>RECORD {i:02d}</div>"
                f"<table>{''.join(cells)}</table>"
                "</div>"
            )

    cards_block = "".join(teacher_cards) or (
        "<div class='empty'>No teacher records detected in the response.</div>"
    )
    raw_block = render_json_html(payload)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    doc = f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EIIN {esc(eiin)} · Recon Report</title>
<style>
  :root {{
    --bg:#050a05; --card:#0a140a; --border:#1a2f1a;
    --txt:#c8ffc8; --dim:#5a8a5a; --green:#39ff14;
    --amber:#ffb000; --red:#ff3b3b; --cyan:#00e5ff; --mag:#ff2bd6;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    font-family:'JetBrains Mono','Consolas','Noto Sans Bengali',monospace;
    background:var(--bg); color:var(--txt); margin:0; padding:22px;
    line-height:1.55; font-size:13px;
  }}
  .wrap {{ max-width:960px; margin:0 auto; }}
  .banner {{
    border:1px solid var(--border); border-radius:8px;
    padding:14px 18px; margin-bottom:20px;
    background:linear-gradient(180deg,#0a140a,#050a05);
  }}
  .banner h1 {{
    font-size:16px; color:var(--green); margin:0;
    letter-spacing:3px; text-transform:uppercase;
  }}
  .banner .sub {{ color:var(--dim); font-size:11px; margin-top:6px; }}
  .meta {{
    background:var(--card); border:1px solid var(--border);
    border-radius:8px; padding:14px 18px; margin-bottom:20px;
  }}
  .meta-row {{ display:flex; gap:12px; padding:4px 0; font-size:12px; }}
  .meta-row .k {{
    color:var(--dim); min-width:150px;
    text-transform:uppercase; letter-spacing:1px; font-size:11px;
  }}
  .meta-row .v {{ color:var(--txt); }}
  h2 {{
    font-size:12px; letter-spacing:3px; text-transform:uppercase;
    color:var(--cyan); margin:24px 0 12px;
    border-bottom:1px solid var(--border); padding-bottom:6px;
  }}
  .card {{
    background:var(--card); border:1px solid var(--border);
    border-radius:8px; padding:14px 18px; margin-bottom:12px;
  }}
  .card-head {{
    color:var(--green); font-weight:700; margin-bottom:10px;
    font-size:12px; letter-spacing:2px;
  }}
  table {{ width:100%; border-collapse:collapse; }}
  td {{ padding:5px 0; vertical-align:top; font-size:12.5px; }}
  td.k {{ color:var(--dim); width:200px; }}
  td.v {{ color:var(--txt); word-break:break-word; }}
  .raw {{
    background:#020602; border:1px solid var(--border);
    border-radius:8px; padding:14px;
    font-family:inherit; font-size:12px; line-height:1.7;
    white-space:pre-wrap; word-break:break-word;
    overflow-x:auto;
  }}
  .key {{ color:var(--cyan); }}
  .str {{ color:var(--txt); }}
  .num {{ color:var(--amber); }}
  .muted {{ color:var(--dim); }}
  .bool-true {{ color:var(--green); }}
  .bool-false {{ color:var(--red); }}
  .empty {{ color:var(--dim); font-style:italic; padding:10px 0; }}
  .footer {{
    margin-top:32px; padding-top:14px;
    border-top:1px solid var(--border);
    color:var(--dim); font-size:11px; text-align:center;
    letter-spacing:1px;
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="banner">
    <h1>▌ EIIN RECON REPORT ▐</h1>
    <div class="sub">EIIN {esc(eiin)} · Generated {esc(now)}</div>
  </div>

  <div class="meta">
    <div class="meta-row"><span class="k">Target EIIN</span><span class="v">{esc(eiin)}</span></div>
    <div class="meta-row"><span class="k">Endpoint</span><span class="v">{esc(meta.get('_url',''))}</span></div>
    <div class="meta-row"><span class="k">Latency</span><span class="v">{round(meta.get('_elapsed',0),3)}s</span></div>
    <div class="meta-row"><span class="k">Toolkit</span><span class="v">EIIN Recon · Ahmed Shariar · v3.0</span></div>
  </div>

  <h2>Teacher Records</h2>
  {cards_block}

  <h2>Raw Response</h2>
  <div class="raw">{raw_block}</div>

  <div class="footer">
    GENERATED BY EIIN RECON TOOLKIT · AHMED SHARIAR · v3.0<br>
    {esc(now)}
  </div>
</div>
</body>
</html>"""

    with open(fname, "w", encoding="utf-8") as f:
        f.write(doc)
    return fname


# ═══════════════════════════════════════════════════════════════
#  CLIPBOARD
# ═══════════════════════════════════════════════════════════════
def copy_to_clipboard(text):
    try:
        if platform.system() == "Windows":
            subprocess.run("clip", input=text.encode("utf-16le"), check=False)
            return True
        if platform.system() == "Darwin":
            subprocess.run("pbcopy", input=text.encode("utf-8"), check=False)
            return True
        for cmd in (
            ["xclip", "-selection", "clipboard"],
            ["wl-copy"],
            ["termux-clipboard-set"],
        ):
            try:
                subprocess.run(cmd, input=text.encode("utf-8"),
                               check=False, timeout=2)
                return True
            except FileNotFoundError:
                continue
    except Exception:
        pass
    return False


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════
def validate_eiin(s):
    return bool(re.match(r"^\d{4,8}$", s))


def main():
    ap = argparse.ArgumentParser(
        prog="eiin",
        description="EIIN Recon Toolkit — Developer: Ahmed Shariar",
        epilog="Example: python app.py 127985 --all",
        add_help=False,
    )
    ap.add_argument("eiin", nargs="?", help="EIIN number (4-8 digits)")
    ap.add_argument("-h", "--help", action="help")
    ap.add_argument("-v", "--version", action="store_true")
    ap.add_argument("-r", "--raw", action="store_true", help="raw JSON only")
    ap.add_argument("-j", "--json", action="store_true", help="clean JSON only")
    ap.add_argument("-o", "--out", metavar="DIR", help="output directory")
    ap.add_argument("--save-json", action="store_true")
    ap.add_argument("--save-csv", action="store_true")
    ap.add_argument("--save-html", action="store_true")
    ap.add_argument("--all", action="store_true", help="save JSON + CSV + HTML")
    ap.add_argument("-q", "--quiet", action="store_true", help="skip boot sequence")
    ap.add_argument("-i", "--interactive", action="store_true")
    ap.add_argument("--copy", action="store_true")
    ap.add_argument("--fast", action="store_true", help="skip scan animation")

    args = ap.parse_args()

    if args.version:
        writeln(
            f"{C.HGREEN}EIIN Recon Toolkit v3.0{C.RESET} "
            f"· Developer: {C.HMAG}Ahmed Shariar{C.RESET}"
        )
        return 0

    out_dir = args.out if args.out else default_out_dir()

    if args.interactive or (not args.eiin and sys.stdin.isatty()):
        return interactive_shell(args, out_dir)

    if not args.eiin:
        boot_sequence(skip=args.quiet)
        ap.print_help()
        return 1

    eiin = args.eiin.strip()
    if not validate_eiin(eiin):
        writeln(f"{C.HRED}[-] Invalid EIIN. Expected 4-8 digits.{C.RESET}")
        return 2

    boot_sequence(skip=args.quiet or args.json)

    if not args.json:
        if not args.fast:
            scan_animation(eiin)
        payload, meta = fetch_eiin(eiin)
    else:
        payload, meta = fetch_eiin(eiin)

    if args.all or args.save_json or args.save_csv or args.save_html:
        saved = []
        if args.all or args.save_json:
            try:
                saved.append(("JSON", export_json(payload, meta, eiin, out_dir)))
            except Exception as e:
                writeln(f"{C.HRED}JSON export failed: {e}{C.RESET}")
        if args.all or args.save_csv:
            try:
                saved.append(("CSV", export_csv(payload, meta, eiin, out_dir)))
            except Exception as e:
                writeln(f"{C.HRED}CSV export failed: {e}{C.RESET}")
        if args.all or args.save_html:
            try:
                saved.append(("HTML", export_html(payload, meta, eiin, out_dir)))
            except Exception as e:
                writeln(f"{C.HRED}HTML export failed: {e}{C.RESET}")
        if saved:
            section("ARTIFACTS WRITTEN", C.HGREEN)
            for kind, path in saved:
                kv(kind, str(path), C.HWHITE)

    if args.copy:
        txt = json.dumps(payload, ensure_ascii=False, indent=2)
        if copy_to_clipboard(txt):
            render_status("JSON copied to clipboard", "ok")
        else:
            render_status("Clipboard tool not found", "warn")

    if args.json:
        writeln(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        render_result(eiin, payload, meta, raw_mode=args.raw)

    return 0


# ═══════════════════════════════════════════════════════════════
#  INTERACTIVE SHELL — Kali style
# ═══════════════════════════════════════════════════════════════
def interactive_shell(args, out_dir):
    boot_sequence(skip=args.quiet)

    writeln(f"{C.HGREEN}{C.BOLD}▌ RECON SHELL READY{C.RESET}")
    writeln(f"{C.HDIM}    type a 4-8 digit EIIN to scan · 'help' for commands{C.RESET}")
    writeln()

    auto_save = args.all
    history = []

    while True:
        try:
            sys.stdout.write(kali_prompt())
            sys.stdout.flush()
            line = input().strip()
        except (EOFError, KeyboardInterrupt):
            writeln()
            break

        if not line:
            continue

        low = line.lower()

        if low in ("q", "quit", "exit"):
            break
        if low in ("h", "help", "?"):
            print_interactive_help()
            continue
        if low in ("cls", "clear"):
            boot_sequence(skip=True)
            continue
        if low == "save":
            auto_save = not auto_save
            render_status(f"Auto-save: {'ON' if auto_save else 'OFF'}", "ok")
            writeln()
            continue
        if low == "history":
            if history:
                render_status("Recent targets: " + ", ".join(history[-12:]), "info")
            else:
                render_status("No history yet.", "info")
            writeln()
            continue
        if low.startswith("scan "):
            line = line[5:].strip()
            low = line.lower()
            if not line:
                continue

        if not validate_eiin(line):
            render_status("Invalid EIIN (4-8 digits expected).", "err")
            writeln()
            continue

        try:
            scan_animation(line)
            payload, meta = fetch_eiin(line)
        except Exception as e:
            render_status(f"Fetch error: {e}", "err")
            writeln()
            continue

        history.append(line)

        if auto_save:
            saved = []
            for kind, fn in (("JSON", export_json),
                             ("CSV", export_csv),
                             ("HTML", export_html)):
                try:
                    saved.append((kind, fn(payload, meta, line, out_dir)))
                except Exception as e:
                    render_status(f"{kind} export failed: {e}", "err")
            if saved:
                section("ARTIFACTS WRITTEN", C.HGREEN)
                for kind, path in saved:
                    kv(kind, str(path), C.HWHITE)

        try:
            render_result(line, payload, meta, raw_mode=args.raw)
        except Exception as e:
            render_status(f"Render error: {e}", "err")
            writeln()

        writeln(f"{C.HDIM}{'─' * term_width()}{C.RESET}")
        writeln()

    writeln()
    render_status("Session closed. Channels dropped.", "info")
    writeln(f"{C.HDIM}· EIIN Recon Toolkit · Ahmed Shariar · v3.0{C.RESET}")
    return 0


def print_interactive_help():
    writeln()
    writeln(f"{C.HGREEN}{C.BOLD}▌ RECON SHELL COMMANDS{C.RESET}")
    writeln(f"{C.HDIM}{'─' * 50}{C.RESET}")
    writeln(f"  {C.HGREEN}<digits>{C.RESET}       scan an EIIN (4-8 digits)")
    writeln(f"  {C.HGREEN}scan <digits>{C.RESET}  scan with explicit keyword")
    writeln(f"  {C.HGREEN}save{C.RESET}           toggle auto-save (JSON+CSV+HTML)")
    writeln(f"  {C.HGREEN}history{C.RESET}        show recent targets")
    writeln(f"  {C.HGREEN}help{C.RESET}           this menu")
    writeln(f"  {C.HGREEN}clear{C.RESET}          reset terminal")
    writeln(f"  {C.HGREEN}quit{C.RESET}           terminate session")
    writeln()


# ═══════════════════════════════════════════════════════════════
#  BOOTSTRAP
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        writeln(f"\n{C.HDIM}Interrupted.{C.RESET}")
        sys.exit(130)
