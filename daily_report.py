#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daily Report Notes 生成器（demo.html 效果）

结构按 demo.html 实现：
- 同一个 Note 中保存多个日期块，日期块倒序排列
- 日期块之间用 ========================================== 分隔
- 每个日期块包含 Sta2.0 / MTBF 两个分组
- 每个分组下包含 J123 / J456 两个项目
- 新日期与上一个日期对比，变化项蓝色，未变化项按 demo.html 的配色保留
"""

import argparse
import html
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime


SEPARATOR_TEXT = "=" * 42
SEPARATOR_HTML = f"<div>{SEPARATOR_TEXT}</div>"

DATE_RE = re.compile(
    r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$",
    re.IGNORECASE,
)

GROUPS = ["Sta2.0", "MTBF"]
PROJECTS = ["J123", "J456"]
METRIC_NAMES = {
    "Sta2.0": ["Continous_Sleep", "Reboot", "Shutdown", "Sleep"],
    "MTBF": ["Reboot", "Shutdown", "Sleep"],
}

BLUE_STA = "#0000F4"
BLUE_MTBF = "#0000FF"
UNCHANGED_MTBF = "#454545"


# 作为演示的旧日期块，尽量保留 demo.html 的原始样式。
# 这样运行 --demo 时，新的 Sep 7 会与下面的 Sep 6 对比。
DEMO_LEGACY_BLOCK = '''
<div>==========================================</div>
<div>Update:</div>
<div><i><br></i></div>
<div><b>Sep 6</b></div>
<div><br></div>
<div>Sta2.0</div>
<div>J123</div>
<div>Accumulated:</div>
<div><font color="#0000F4">Continous_Sleep 456</font><br></div>
<div><font color="#0000F4">Reboot 12</font></div>
<div><font color="#0000F4">Shutdown 456</font></div>
<div><font color="#0000F4">Sleep 789</font><br></div>
<div><br></div>
<div>J456</div>
<div>Accumulated:</div>
<div><font color="#0000F4">Continous_Sleep 456</font><br></div>
<div><font color="#0000F4">Reboot 123</font><br></div>
<div><font color="#0000F4">Shutdown 46</font></div>
<div><font color="#0000F4">Sleep 78</font><br></div>
<div><br></div>
<div>MTBF</div>
<div>J123</div>
<div>Accumulated：<br></div>
<div><font color="#0000FF">Reboot 126</font><br></div>
<div><font color="#0000FF">Shutdown 888</font><br></div>
<div><font color="#0000F4">Sleep 999</font><br></div>
<div>Data upload： </div>
<div>Radar List：<br></div>
<div><br></div>
<div><br></div>
<div>J456</div>
<div>Accumulated：<br></div>
<div><font color="#0000FF">Reboot 123</font><br></div>
<div><font color="#0000FF">Shutdown 456</font><br></div>
<div><font color="#0000FF">Sleep 999</font><br></div>
<div>Data upload： </div>
<div>Radar List：<br></div>
'''.strip()


DEMO_SEP7 = {
    "Sta2.0": {
        "J123": {"Continous_Sleep": "456", "Reboot": "123", "Shutdown": "777", "Sleep": "789"},
        "J456": {"Continous_Sleep": "456", "Reboot": "123", "Shutdown": "456", "Sleep": "80"},
    },
    "MTBF": {
        "J123": {"Reboot": "129", "Shutdown": "989", "Sleep": "999"},
        "J456": {"Reboot": "123", "Shutdown": "456", "Sleep": "11525"},
    },
}

DEMO_SEP7_RECORD = {"date": "Sep 7", "data": DEMO_SEP7}

DEMO_SEP8 = {
    "Sta2.0": {
        "J123": {"Continous_Sleep": "456", "Reboot": "124", "Shutdown": "777", "Sleep": "790"},
        "J456": {"Continous_Sleep": "456", "Reboot": "123", "Shutdown": "460", "Sleep": "80"},
    },
    "MTBF": {
        "J123": {"Reboot": "130", "Shutdown": "989", "Sleep": "1000"},
        "J456": {"Reboot": "123", "Shutdown": "456", "Sleep": "11530"},
    },
}

DEMO_NEW_RECORDS = [{"date": "Sep 8", "data": DEMO_SEP8}]


@dataclass
class DateBlock:
    date: str
    lines: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)


@dataclass
class NoteState:
    preamble: list[str] = field(default_factory=list)
    blocks: list[DateBlock] = field(default_factory=list)


def strip_html(value: str) -> str:
    """把 Notes body 中的单行 HTML 转成纯文本，用于结构判断和对比。"""
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def parse_date(value: str) -> datetime | None:
    """解析 Sep 6 / September 6 这类日期，只用于排序。"""
    text = strip_html(value)
    for fmt in ("%b %d %Y", "%B %d %Y"):
        try:
            return datetime.strptime(f"{text} 2026", fmt)
        except ValueError:
            continue
    return None


def is_separator_line(line: str) -> bool:
    return "====" in strip_html(line)


def empty_data() -> dict:
    return {group: {project: {} for project in PROJECTS} for group in GROUPS}


def make_preamble(title: str) -> list[str]:
    return [
        f"<div><b>{html.escape(title)}</b><br></div>",
        "<div><br></div>",
        "<div>MacOS: 26.6.2 (25G83)</div>",
        "<div><br></div>",
    ]


def ensure_preamble(state: NoteState, title: str) -> None:
    """保留 MacOS 等原有 preamble，同时把标题行更新为用户输入标题。"""
    if not state.preamble:
        state.preamble = make_preamble(title)
        return

    for index, line in enumerate(state.preamble):
        if "<b>" in line and "</b>" in line:
            state.preamble[index] = f"<div><b>{html.escape(title)}</b><br></div>"
            return

    state.preamble = make_preamble(title) + state.preamble


def local_today() -> str:
    """返回和 demo 一致的日期格式，例如 Sep 8。"""
    now = datetime.now()
    return f"{now.strftime('%b')} {now.day}"


def normalize_server_data(payload: dict) -> dict:
    """把服务器返回的 JSON 转成 ReportData，并把数值统一成字符串。"""
    data = empty_data()

    for group in GROUPS:
        group_payload = payload.get(group, {}) or {}
        for project in PROJECTS:
            project_payload = group_payload.get(project, {}) or {}
            for metric in METRIC_NAMES[group]:
                value = project_payload.get(metric, "")
                data[group][project][metric] = str(value)

    return data


class ServerDataFetcher:
    """从服务器拉取当天测试数据。"""

    def __init__(self, url: str, token: str | None = None, timeout: int = 10):
        self.url = url
        self.token = token
        self.timeout = timeout

    def fetch(self) -> dict:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = urllib.request.Request(self.url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"服务器返回 HTTP {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"无法连接服务器: {exc.reason}") from exc

        if not isinstance(payload, dict):
            raise RuntimeError("服务器返回格式错误，应为 JSON object")

        return normalize_server_data(payload)


def parse_date_block(block_lines: list[str]) -> DateBlock:
    date = ""
    data = empty_data()
    current_group: str | None = None
    current_project: str | None = None

    for line in block_lines:
        text = strip_html(line)

        if not date and DATE_RE.match(text):
            date = text
            continue

        if text in GROUPS:
            current_group = text
            current_project = None
            continue

        if text in PROJECTS:
            current_project = text
            continue

        if current_group is None or current_project is None:
            continue

        for metric in METRIC_NAMES[current_group]:
            match = re.match(rf"^{re.escape(metric)}\s+(.+)$", text)
            if match:
                data[current_group][current_project][metric] = match.group(1).strip()
                break

    return DateBlock(date=date or "Unknown", lines=block_lines, data=data)


def parse_body(raw_body: str) -> NoteState:
    state = NoteState()
    if not raw_body:
        return state

    lines = raw_body.splitlines()
    index = 0

    # 第一条分隔线之前的内容作为 Note 的 preamble，原样保留。
    while index < len(lines) and not is_separator_line(lines[index]):
        state.preamble.append(lines[index])
        index += 1

    while index < len(lines):
        if not is_separator_line(lines[index]):
            index += 1
            continue

        start = index
        end = index + 1
        while end < len(lines) and not is_separator_line(lines[end]):
            end += 1

        state.blocks.append(parse_date_block(lines[start:end]))
        index = end

    return state


def render_metric_lines(
    group: str,
    project: str,
    metrics: dict[str, str],
    previous_metrics: dict[str, str] | None,
) -> list[str]:
    """渲染一个项目下的测试项。有对比数据时，变化项蓝色，未变化项按 demo 配色。"""
    lines: list[str] = []

    for metric in METRIC_NAMES[group]:
        value = metrics.get(metric, "")
        old_value = previous_metrics.get(metric) if previous_metrics is not None else None

        if previous_metrics is not None and old_value is not None and old_value != value:
            if group == "MTBF":
                lines.append(
                    f"<div><font color=\"{BLUE_MTBF}\">{html.escape(metric)} {html.escape(value)}</font><br></div>"
                )
            else:
                lines.append(
                    f"<div>{html.escape(metric)} <font color=\"{BLUE_STA}\">{html.escape(value)}</font><br></div>"
                )
        elif previous_metrics is not None and group == "MTBF":
            lines.append(
                f"<div><font color=\"{UNCHANGED_MTBF}\">{html.escape(metric)} {html.escape(value)}</font><br></div>"
            )
        else:
            lines.append(f"<div>{html.escape(metric)} {html.escape(value)}</div>")

    return lines


def render_date_block(
    date: str,
    data: dict,
    previous_data: dict | None = None,
) -> DateBlock:
    """生成一个日期块，结构对齐 demo.html。"""
    lines = [
        SEPARATOR_HTML,
        "<div>Update:</div>",
        "<div><i><br></i></div>",
        f"<div><b>{html.escape(date)}</b></div>",
        "<div><br></div>",
    ]

    for group_index, group in enumerate(GROUPS):
        lines.append(f"<div>{html.escape(group)}</div>")
        group_data = data.get(group, {})
        previous_group = (previous_data or {}).get(group, {})

        for project_index, project in enumerate(PROJECTS):
            lines.append(f"<div>{html.escape(project)}</div>")
            accumulated_label = "Accumulated：" if group == "MTBF" else "Accumulated:"
            lines.append(f"<div>{accumulated_label}</div>")

            metrics = group_data.get(project, {})
            previous_metrics = previous_group.get(project) if previous_data is not None else None
            lines.extend(render_metric_lines(group, project, metrics, previous_metrics))

            if group == "MTBF":
                lines.append("<div>Data upload： </div>")
                lines.append("<div>Radar List：<br></div>")

            if project_index < len(PROJECTS) - 1:
                lines.append("<div><br></div>")
                if group == "MTBF":
                    lines.append("<div><br></div>")
            elif group_index < len(GROUPS) - 1:
                lines.append("<div><br></div>")

    return DateBlock(date=date, lines=lines, data=data)


def sort_key(block: DateBlock):
    parsed = parse_date(block.date)
    return (parsed or datetime.min, block.date)


def update_note_state(state: NoteState, records: list[dict]) -> NoteState:
    """把新日期插入已有日期块中，旧日期块原样保留。"""
    ordered_records = sorted(records, key=lambda record: parse_date(record["date"]) or datetime.min)

    for record in ordered_records:
        date = record["date"]
        data = record["data"]
        state.blocks = [block for block in state.blocks if block.date != date]

        previous_block = max(
            (block for block in state.blocks if parse_date(block.date) < parse_date(date)),
            key=sort_key,
            default=None,
        )
        state.blocks.append(render_date_block(date, data, previous_block.data if previous_block else None))

    return state


def render_note(state: NoteState) -> str:
    output = list(state.preamble)
    ordered_blocks = sorted(state.blocks, key=sort_key, reverse=True)
    for block in ordered_blocks:
        output.extend(block.lines)
    return "\n".join(output)


class AppleScriptNotes:
    """通过 osascript 读写 macOS Notes。"""

    READ_SCRIPT = r'''
on run argv
    set noteName to item 1 of argv
    tell application "Notes"
        activate
        delay 0.5
        try
            set targetNote to first note of folder "Notes" whose name is noteName
            return body of targetNote
        on error
            return ""
        end try
    end tell
end run
'''

    WRITE_SCRIPT = r'''
on run argv
    set noteName to item 1 of argv
    set newBody to item 2 of argv
    tell application "Notes"
        activate
        delay 0.5
        try
            set targetNote to first note of folder "Notes" whose name is noteName
            set body of targetNote to newBody
        on error
            set targetNote to make new note at folder "Notes" with properties {name:noteName, body:newBody}
        end try
        return name of targetNote
    end tell
end run
'''

    def _run(self, script: str, *args: str) -> str:
        completed = subprocess.run(
            ["osascript", "-e", script, *args],
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
        return completed.stdout.strip()

    def read(self, note_name: str) -> str:
        return self._run(self.READ_SCRIPT, note_name)

    def write(self, note_name: str, body: str) -> str:
        return self._run(self.WRITE_SCRIPT, note_name, body)


def save_preview(preview_dir: str, results: dict[str, str]) -> list[str]:
    os.makedirs(preview_dir, exist_ok=True)
    saved: list[str] = []

    for note_name, body in results.items():
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", note_name).strip("_")
        path = os.path.join(preview_dir, f"{safe_name}.html")
        document = (
            "<!doctype html>\n"
            "<html><head><meta charset=\"utf-8\"></head>\n"
            f"<body>\n{body}\n</body></html>\n"
        )
        with open(path, "w", encoding="utf-8") as file:
            file.write(document)
        saved.append(path)

    return saved


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 Daily Report Note（demo.html 效果）")
    parser.add_argument("--title", "-t", help="Note 标题；不传则交互输入")
    parser.add_argument("--source", choices=["demo", "server"], default="demo", help="数据源")
    parser.add_argument("--url", default="http://192.168.1.7:9000/get_data", help="服务器数据接口")
    parser.add_argument("--token", help="服务器鉴权 token，可选")
    parser.add_argument("--date", help="覆盖当天日期，格式如 Sep 8")
    parser.add_argument("--demo-history", action="store_true", help="只写入 demo 中的旧日期块")
    parser.add_argument("--demo-update", action="store_true", help="只写入 demo 中的新日期块")
    parser.add_argument("--apply", action="store_true", help="写入 macOS Notes；不加时只预览")
    parser.add_argument("--preview-dir", help="把预览 HTML 保存到指定目录")
    args = parser.parse_args()

    title = (args.title or "").strip()
    if not title and sys.stdin.isatty():
        title = input("请输入 Note 标题: ").strip()
    if not title:
        title = "Daily Report"

    demo_source = args.source == "demo"

    if args.source == "server":
        try:
            server_data = ServerDataFetcher(args.url, args.token).fetch()
        except RuntimeError as exc:
            print(f"获取服务器数据失败: {exc}", file=sys.stderr)
            return 2

        date = args.date or local_today()
        records = [{"date": date, "data": server_data}]
    else:
        if args.demo_history:
            records: list[dict] = []
        else:
            records = DEMO_NEW_RECORDS

    store = AppleScriptNotes() if args.apply else None
    existing_body = store.read(title) if store else ""
    if not existing_body and demo_source:
        existing_body = DEMO_LEGACY_BLOCK
        if not args.demo_history:
            # 空 Note 时补齐 demo 历史，再插入最新 Sep 8。
            records = [DEMO_SEP7_RECORD, *records]

    state = parse_body(existing_body)
    ensure_preamble(state, title)
    update_note_state(state, records)
    body = render_note(state)

    if store:
        written_name = store.write(title, body)
        print(f"已写入 Note: {written_name}")
    else:
        print(f"预览 Note: {title}")

    results = {title: body}
    if args.preview_dir:
        for path in save_preview(args.preview_dir, results):
            print(f"预览文件: {path}")
    else:
        print(f"\n{body}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
