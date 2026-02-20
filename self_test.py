import argparse
import importlib
import json
import os
import sys
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

REQUIRED_FILES = [
    "main.py",
    "requirements.txt",
    ".github/workflows/daily_news.yml",
]
REQUIRED_MODULES = [
    "tenacity",
    "google.genai",
    "linebot",
]
REQUIRED_ENVS = [
    "GEMINI_API_KEY",
    "LINE_CHANNEL_ACCESS_TOKEN",
    "LINE_USER_ID",
]
CONNECTIVITY_URLS = [
    ("Gemini API", "https://generativelanguage.googleapis.com"),
    ("LINE API", "https://api.line.me"),
    ("Google", "https://www.google.com"),
]

def check_files():
    ok = True
    for f in REQUIRED_FILES:
        if Path(f).exists():
            print(f"[PASS] file: {f}")
        else:
            print(f"[FAIL] file: {f}")
            ok = False
    return ok

def check_modules():
    ok = True
    for m in REQUIRED_MODULES:
        try:
            importlib.import_module(m)
            print(f"[PASS] module: {m}")
        except ImportError as e:
            print(f"[FAIL] module: {m} ({e})")
            ok = False
    return ok

def check_envs():
    for e in REQUIRED_ENVS:
        val = os.getenv(e)
        if val:
            masked = val[:6] + "..." if len(val) > 6 else "***"
            print(f"[PASS] env: {e} = {masked}")
        else:
            print(f"[WARN] env not set: {e}")

def check_connectivity():
    ok = True
    for name, url in CONNECTIVITY_URLS:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = getattr(resp, "status", 200)
                print(f"[PASS] connectivity: {name} (HTTP {code})")
        except Exception as e:
            print(f"[FAIL] connectivity: {name} ({e})")
            ok = False
    return ok

def check_dry_run():
    python_exe = sys.executable
    try:
        result = subprocess.run(
            [python_exe, "main.py", "--dry-run"],
            capture_output=True, text=True, timeout=30,
            cwd=str(Path(__file__).parent),
        )
        if result.returncode == 0:
            print("[PASS] dry-run: main.py --dry-run ok")
            lines = result.stdout.strip().split("\n")
            for line in lines[:3]:
                print(f"       | {line}")
            if len(lines) > 3:
                print(f"       | ... ({len(lines)} lines total)")
            return True
        else:
            print(f"[FAIL] dry-run: exit code {result.returncode}")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[:5]:
                    print(f"       | {line}")
            return False
    except subprocess.TimeoutExpired:
        print("[FAIL] dry-run: timeout (30s)")
        return False
    except Exception as e:
        print(f"[FAIL] dry-run: {e}")
        return False

def send_line_test_message(message):
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    user_id = os.getenv("LINE_USER_ID", "")
    if not token or not user_id:
        print("[FAIL] send-test: missing LINE credentials")
        return False
    body = {"to": user_id, "messages": [{"type": "text", "text": message}]}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://api.line.me/v2/bot/message/push",
        data=data, method="POST",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = getattr(resp, "status", 200)
            if 200 <= code < 300:
                print(f"[PASS] send-test: LINE message sent (HTTP {code})")
                return True
            print(f"[FAIL] send-test: HTTP {code}")
            return False
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="ignore")
        print(f"[FAIL] send-test: HTTP {e.code} {detail}")
        return False
    except Exception as e:
        print(f"[FAIL] send-test: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="ai-news-bot self test")
    parser.add_argument("--send-test", action="store_true", help="發送測試 LINE 訊息")
    parser.add_argument("--message", default="ai-news-bot self test OK")
    parser.add_argument("--skip-network", action="store_true", help="略過網路連線測試")
    parser.add_argument("--skip-dry-run", action="store_true", help="略過 dry-run 測試")
    args = parser.parse_args()

    print("=" * 40)
    print("  ai-news-bot self test")
    print("=" * 40)
    ok = True

    print("\n[1/5] files...")
    ok &= check_files()

    print("\n[2/5] modules...")
    ok &= check_modules()

    print("\n[3/5] env...")
    check_envs()

    if not args.skip_network:
        print("\n[4/5] connectivity...")
        ok &= check_connectivity()
    else:
        print("\n[4/5] skip connectivity")

    if not args.skip_dry_run:
        print("\n[5/5] dry-run...")
        ok &= check_dry_run()
    else:
        print("\n[5/5] skip dry-run")

    if args.send_test:
        print("\n[EXTRA] LINE send-test...")
        ok &= send_line_test_message(args.message)

    print("\n" + "=" * 40)
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")
    print("=" * 40)
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
