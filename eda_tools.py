import json
import os
import shlex
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "eda_tools.json"


def _tools():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["tools"]


def _resolve(cmd):
    cmd = os.path.expandvars(os.path.expanduser(str(cmd).strip()))
    if os.path.isabs(cmd) or "/" not in cmd and "\\" not in cmd:
        return cmd
    return str((ROOT / cmd).resolve())


def tool_path(name):
    return _resolve(_tools()[name])


def tool_command(name):
    value = _tools()[name]
    parts = [str(part) for part in value] if isinstance(value, list) else shlex.split(str(value))
    parts[0] = _resolve(parts[0])
    return parts


def openroad_command(script="openroad_sta.tcl"):
    return tool_command("openroad") + [script]


def run_checked(args, cwd=None, **kwargs):
    try:
        return subprocess.run(args, cwd=cwd, check=True, **kwargs)
    except FileNotFoundError as exc:
        tool = exc.filename or args[0]
        raise FileNotFoundError(f"Cannot start '{tool}'. Check {CONFIG_PATH}.") from exc


def run_logged(args, cwd, log_name, mode="w"):
    log_path = Path(log_name)
    if not log_path.is_absolute():
        log_path = Path(cwd) / log_path
    with open(log_path, mode) as log:
        return run_checked(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT)
