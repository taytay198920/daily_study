import html
import subprocess
from datetime import date
from pathlib import Path

import yaml


REPORT_PATH = Path(__file__).with_name("report.yml")
MONTH_ABBR = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
MONTH_TO_NUMBER = {name: index for index, name in enumerate(MONTH_ABBR, start=1)}


def _today_key(today: date) -> str:
    return f"{MONTH_ABBR[today.month - 1]} {today.day:02d}"


def _parse_date_key(key: str, today: date) -> date | None:
    try:
        month_name, day_text = key.strip().split()
        month = MONTH_TO_NUMBER[month_name]
        day = int(day_text)
    except (ValueError, KeyError, AttributeError):
        return None

    candidate = date(today.year, month, day)
    if candidate > today:
        candidate = candidate.replace(year=today.year - 1)
    return candidate


def _select_report_keys(report_data: dict, today: date) -> tuple[str, str | None]:
    today_key = _today_key(today)
    if today_key in report_data:
        current_key = today_key
    elif len(report_data) == 1:
        current_key = next(iter(report_data))
    else:
        raise ValueError(f"today's data ({today_key}) not found in report.yml")

    if len(report_data) == 1:
        return current_key, None

    current_date = _parse_date_key(current_key, today)
    previous_keys = []
    for key in report_data:
        if key == current_key:
            continue
        key_date = _parse_date_key(key, today)
        if key_date is None or current_date is None:
            continue
        if key_date < current_date:
            previous_keys.append((key_date, key))

    if not previous_keys:
        return current_key, None

    previous_keys.sort(reverse=True)
    return current_key, previous_keys[0][1]


def _render_sub_item(sub_item: str, value, previous_items: dict | None) -> str:
    escaped_name = html.escape(str(sub_item))
    escaped_value = html.escape(str(value))
    is_unchanged = (
        previous_items is not None
        and sub_item in previous_items
        and value == previous_items[sub_item]
    )
    if is_unchanged:
        return f"<div>{escaped_name} {escaped_value}</div>"
    return f"<div>{escaped_name} <font color='blue'>{escaped_value}</font></div>"


def _render_test_type(test_type: str, projects: dict, previous_projects: dict | None) -> str:
    parts = [f"<div><font color='red'>{html.escape(str(test_type))}</font></div>"]
    projects = projects or {}
    previous_projects = previous_projects or {}

    for project, sub_items in projects.items():
        parts.append(
            f"<div><font color='orange'>{html.escape(str(project))}</font></div>"
            "<div>Accumulative:</div>"
        )
        sub_items = sub_items or {}
        previous_sub_items = previous_projects.get(project)
        for sub_item, value in sub_items.items():
            parts.append(_render_sub_item(sub_item, value, previous_sub_items))
        parts.append("<div>Bug List:</div><br/>")

    return "".join(parts)


def _render_report(date_key: str, current_data: dict, previous_data: dict | None) -> str:
    parts = [
        f"<div>{'=' * 50}</div>",
        f"<div>Update:</div><div><b>{html.escape(str(date_key))}</b></div><br/>",
    ]
    current_data = current_data or {}

    for test_type, projects in current_data.items():
        previous_projects = (previous_data or {}).get(test_type)
        parts.append(_render_test_type(test_type, projects, previous_projects))
        if previous_data is not None:
            parts.append("<br/>")

    return "".join(parts)


def _escape_applescript_string(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def _build_applescript(note_name: str, report_content: str) -> str:
    note_name = _escape_applescript_string(str(note_name))
    report_content = _escape_applescript_string(report_content)
    return (
        'tell application "Notes"\n'
        f'set targetNote to first note of folder "Notes" whose name is "{note_name}"\n'
        f'set body of targetNote to "{report_content}"\n'
        "end tell\n"
    )


def generate_html_report(rt: str) -> None:
    try:
        report_data = yaml.safe_load(REPORT_PATH.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        print(f"report file not found: {REPORT_PATH}")
        return

    if not isinstance(report_data, dict):
        print("report.yml should be a mapping of dates")
        return

    today = date.today()
    try:
        current_key, previous_key = _select_report_keys(report_data, today)
    except ValueError as exc:
        print(exc)
        return

    current_data = report_data[current_key].get(rt)
    if current_data is None:
        print(f"report title '{rt}' not found for {current_key}")
        return

    previous_data = None
    if previous_key is not None:
        previous_data = report_data[previous_key].get(rt)

    report_content = _render_report(current_key, current_data, previous_data)
    applescript = _build_applescript(rt, report_content)

    try:
        result = subprocess.run(
            ["osascript"],
            input=applescript,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        print("osascript not found; are you running on macOS?")
        return

    if result.returncode != 0:
        print("generate failed")
        print((result.stderr or result.stdout or "").strip())
    else:
        print("generate success")


generate_html_report("P11 25G83")