#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""根据 demo.yml 自动生成 macOS 备忘录（Notes.app）日报。

demo.yml 的结构约定为：

    日期:
      Notes 标题:
        项目:
          测试项:
            测试子项: 测试圈数

例如：

    "Sep 7":
      "J123 25G83":
        "J123a":
          "MTBF":
            "Reboot": 123

每次运行会读取 demo.yml 中的所有日期，按日期从新到旧生成日报块。
日报块之间用一行 "=====================" 分隔。默认只预览，不写入 Notes；
确认无误后加 --apply 才会写入对应标题的备忘录。
"""

from __future__ import annotations

import argparse
import copy
import html
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - 没有 PyYAML 时使用内置的简易解析器
    yaml = None


SEPARATOR_TEXT = "=" * 21
SEPARATOR_HTML = f"<div>{SEPARATOR_TEXT}</div>"
BLUE = "#0000FF"

DATE_RE = re.compile(
    r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s+\d{4})?$",
    re.IGNORECASE,
)


@dataclass
class DateBlock:
    date: str
    lines: list[str] = field(default_factory=list)


@dataclass
class NoteState:
    preamble: list[str] = field(default_factory=list)
    blocks: list[DateBlock] = field(default_factory=list)


def strip_html(value: str) -> str:
    """把 Notes body 的单行 HTML 粗略还原成纯文本，用于日期识别。"""
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def parse_date(value: str) -> datetime | None:
    """解析常见日期文本；只有月/日时补当前年份，仅用于排序。"""
    text = strip_html(value)
    if not text:
        return None

    current_year = datetime.now().year
    candidates = [
        ("%b %d, %Y", True),
        ("%B %d, %Y", True),
        ("%Y-%m-%d", True),
        ("%Y/%m/%d", True),
        ("%b %d", False),
        ("%B %d", False),
        ("%m月%d日", False),
        ("%m月%d号", False),
        ("%m/%d", False),
        ("%m-%d", False),
    ]

    for fmt, has_year in candidates:
        try:
            parse_text = text if has_year else f"{text} {current_year}"
            parse_fmt = fmt if has_year else f"{fmt} %Y"
            parsed = datetime.strptime(parse_text, parse_fmt)
            return parsed
        except ValueError:
            continue

    return None


def date_sort_key(block: DateBlock):
    parsed = parse_date(block.date)
    return parsed if parsed is not None else datetime.min


def sort_dates(dates: list[str]) -> list[str]:
    known = [date for date in dates if parse_date(date) is not None]
    unknown = [date for date in dates if parse_date(date) is None]
    known.sort(key=lambda date: parse_date(date), reverse=True)
    return known + unknown


def normalize_date_key(value: str) -> str:
    return strip_html(value).casefold()


def local_today() -> str:
    now = datetime.now()
    return f"{now.strftime('%b')} {now.day}"


def is_separator_line(line: str) -> bool:
    return "====" in strip_html(line)


def make_preamble(title: str) -> list[str]:
    return [
        f"<div><b>{html.escape(title)}</b></div>",
        "<div><br></div>",
    ]


def ensure_preamble(state: NoteState, title: str) -> None:
    """保留已有备忘录开头内容，并确保首行标题正确。"""
    if not state.preamble:
        state.preamble = make_preamble(title)
        return

    for index, line in enumerate(state.preamble[:5]):
        if "<b>" in line and "</b>" in line:
            state.preamble[index] = f"<div><b>{html.escape(title)}</b></div>"
            return

    state.preamble = make_preamble(title) + state.preamble


def parse_block(block_lines: list[str]) -> DateBlock:
    """从已有日期块中识别日期。"""
    date = ""
    checked = 0
    for line in block_lines[1:]:
        text = strip_html(line)
        if not text:
            continue
        checked += 1
        if parse_date(text) is not None or DATE_RE.match(text):
            date = text
            break
        if checked >= 5:
            break
    return DateBlock(date=date, lines=block_lines)


def _is_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _looks_like_manual_line(text: str) -> bool:
    """识别 Notes 中手工添加的标题/链接，例如 Bug List: 和 radar://..."""
    return text.endswith(":") or "://" in text


def _prune_empty(data: dict[str, Any]) -> dict[str, Any]:
    pruned: dict[str, Any] = {}
    for project, project_data in data.items():
        if not isinstance(project_data, dict):
            continue
        test_items: dict[str, Any] = {}
        for test_item, subitems in project_data.items():
            if isinstance(subitems, dict) and subitems:
                test_items[test_item] = subitems
        if test_items:
            pruned[project] = test_items
    return pruned


def parse_block_parts(block: DateBlock) -> tuple[dict[str, Any], list[str]]:
    """解析已有日报块，同时返回未识别的 HTML 行以便保留。"""
    data: dict[str, Any] = {}
    unparsed_lines: list[str] = []
    current_project: str | None = None
    current_test_item: str | None = None

    for raw_line in block.lines:
        text = re.sub(r"<[^>]+>", "", raw_line)
        text = html.unescape(text).replace("\xa0", " ")
        raw_indent = len(text) - len(text.lstrip(" "))
        text = text.strip()
        if not text:
            continue
        if text == SEPARATOR_TEXT or parse_date(text) is not None or DATE_RE.match(text):
            continue

        indent = raw_indent // 4

        if indent == 0:
            if _looks_like_manual_line(text):
                unparsed_lines.append(raw_line)
                continue
            current_project = text
            current_test_item = None
            data.setdefault(current_project, {})
        elif indent == 1:
            if current_project is None:
                unparsed_lines.append(raw_line)
                continue
            current_test_item = text
            data[current_project].setdefault(current_test_item, {})
        elif indent >= 2 and current_project is not None and current_test_item is not None:
            if ":" in text:
                subitem, value = text.split(":", 1)
                if _is_numeric(value.strip()):
                    data[current_project][current_test_item][subitem.strip()] = value.strip()
                else:
                    unparsed_lines.append(raw_line)
            else:
                unparsed_lines.append(raw_line)
        else:
            unparsed_lines.append(raw_line)

    return _prune_empty(data), unparsed_lines


def parse_block_data(block: DateBlock) -> dict[str, Any]:
    """从已有日报块中解析出 项目 -> 测试项 -> 子项 -> 圈数。"""
    data, _ = parse_block_parts(block)
    return data


def merge_nested_dicts(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    """深度合并两个嵌套 dict，extra 中的新项目/测试项/子项会被加入。"""
    merged = copy.deepcopy(base)

    for key, value in extra.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = merge_nested_dicts(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)

    return merged


def parse_body(raw_body: str) -> NoteState:
    state = NoteState()
    if not raw_body:
        return state

    lines = raw_body.splitlines()
    index = 0

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

        state.blocks.append(parse_block(lines[start:end]))
        index = end

    return state


def render_block(
    date: str,
    note_data: dict[str, Any],
    previous_data: dict[str, Any] | None = None,
) -> DateBlock:
    """把某个日期、某个 Note 的嵌套数据渲染成 HTML 日报块。"""

    def escape(value: Any) -> str:
        return html.escape(str(value))

    lines: list[str] = [SEPARATOR_HTML]

    def add(text: str, indent: int = 0) -> None:
        prefix = "&nbsp;" * (indent * 4)
        lines.append(f"<div>{prefix}{text}</div>")

    add(f"<b>{escape(date)}</b>")
    add("<br>")

    projects = note_data.items()
    project_list = list(projects)

    for project_index, (project, project_data) in enumerate(project_list):
        add(escape(project))

        if not isinstance(project_data, dict):
            add(f"{escape(project_data)}", indent=1)
            if project_index < len(project_list) - 1:
                add("<br>", indent=0)
            continue

        test_items = list(project_data.items())
        for test_item_index, (test_item, subitems) in enumerate(test_items):
            add(escape(test_item), indent=1)

            if not isinstance(subitems, dict):
                add(str(escape(subitems)), indent=2)
                if test_item_index < len(test_items) - 1:
                    add("<br>", indent=0)
                continue

            for subitem, cycles in subitems.items():
                current_value = str(cycles)
                previous_value = None
                if isinstance(previous_data, dict):
                    previous_project = previous_data.get(project)
                    if isinstance(previous_project, dict):
                        previous_test_item = previous_project.get(test_item)
                        if isinstance(previous_test_item, dict):
                            previous_value = previous_test_item.get(subitem)

                if previous_value is None or str(previous_value) != current_value:
                    add(
                        f'<font color="{BLUE}">{escape(subitem)}: {escape(cycles)}</font>',
                        indent=2,
                    )
                else:
                    add(f"{escape(subitem)}: {escape(cycles)}", indent=2)

            if test_item_index < len(test_items) - 1:
                add("<br>", indent=0)

        if project_index < len(project_list) - 1:
            add("<br>", indent=0)

    return DateBlock(date=date, lines=lines)


def render_note(state: NoteState) -> str:
    output = list(state.preamble)

    known = [block for block in state.blocks if parse_date(block.date) is not None]
    unknown = [block for block in state.blocks if parse_date(block.date) is None]
    known.sort(key=date_sort_key, reverse=True)

    for block in known + unknown:
        output.extend(block.lines)

    return "\n".join(output)


def build_note_body(title: str, existing_body: str, records: list[tuple[str, dict[str, Any]]]) -> str:
    state = parse_body(existing_body)
    ensure_preamble(state, title)

    existing_by_date: dict[str, DateBlock] = {}
    existing_data_by_date: dict[str, dict[str, Any]] = {}
    unparsed_by_date: dict[str, list[str]] = {}

    for block in state.blocks:
        if not block.date:
            continue
        key = normalize_date_key(block.date)
        existing_by_date.setdefault(key, block)
        block_data, unparsed_lines = parse_block_parts(block)
        existing_data_by_date.setdefault(key, block_data)
        unparsed_by_date.setdefault(key, unparsed_lines)

    records = sorted(
        records,
        key=lambda item: (parse_date(item[0]) or datetime.min),
        reverse=True,
    )

    # 合并所有已知日期数据，方便计算“最近一个更早日期”。
    all_data_by_date = copy.deepcopy(existing_data_by_date)
    for date, note_data in records:
        key = normalize_date_key(date)
        base_data = all_data_by_date.get(key, {})
        all_data_by_date[key] = merge_nested_dicts(base_data, note_data)

    all_dates = sort_dates(list(all_data_by_date.keys()))
    previous_data_by_date: dict[str, dict[str, Any]] = {}
    for index, date in enumerate(all_dates):
        if index + 1 < len(all_dates):
            previous_data_by_date[date] = all_data_by_date[all_dates[index + 1]]

    new_blocks: list[DateBlock] = []

    for date, note_data in records:
        key = normalize_date_key(date)
        existing_block = existing_by_date.get(key)
        merged_data = all_data_by_date[key]
        previous_data = previous_data_by_date.get(key)
        replacement = render_block(date, merged_data, previous_data)
        replacement.lines.extend(unparsed_by_date.get(key, []))

        if existing_block is not None:
            for index, block in enumerate(state.blocks):
                if block is existing_block:
                    state.blocks[index] = replacement
                    break
        else:
            new_blocks.append(replacement)

    state.blocks = new_blocks + state.blocks
    return render_note(state)


def save_preview(preview_dir: str, results: dict[str, str]) -> list[Path]:
    path = Path(preview_dir)
    path.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    for note_name, body in results.items():
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", note_name).strip("_") or "note"
        file_path = path / f"{safe_name}.html"
        document = (
            "<!doctype html>\n"
            "<html><head><meta charset=\"utf-8\"></head>\n"
            f"<body>\n{body}\n</body></html>\n"
        )
        file_path.write_text(document, encoding="utf-8")
        saved.append(file_path)

    return saved


class AppleScriptNotes:
    """通过 osascript 读写 macOS Notes.app。"""

    NOT_FOUND = "__NOTE_NOT_FOUND__"

    READ_SCRIPT = r'''
on run argv
    set noteName to item 1 of argv
    tell application "Notes"
        activate
        delay 0.5
        set matchingNotes to every note whose name is noteName
        if (count of matchingNotes) is 0 then
            return "__NOTE_NOT_FOUND__"
        end if
        return body of item 1 of matchingNotes
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
        set matchingNotes to every note whose name is noteName
        if (count of matchingNotes) is 0 then
            set targetNote to make new note with properties {name:noteName, body:newBody}
        else
            set targetNote to item 1 of matchingNotes
            set body of targetNote to newBody
        end if
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
            message = completed.stderr.strip() or completed.stdout.strip()
            raise RuntimeError(message or "osascript 执行失败")
        return completed.stdout.strip()

    def read(self, note_name: str) -> str:
        output = self._run(self.READ_SCRIPT, note_name)
        if output == self.NOT_FOUND:
            return ""
        return output

    def write(self, note_name: str, body: str) -> str:
        return self._run(self.WRITE_SCRIPT, note_name, body)


def collect_records(
    data: dict[str, Any],
    only_dates: list[str] | None = None,
    note_filter: list[str] | None = None,
) -> tuple[dict[str, list[tuple[str, dict[str, Any]]]], list[str]]:
    """把 YAML 数据按 Note 标题聚合，并返回实际处理的日期。"""
    date_items = list(data.items())

    if only_dates:
        wanted = {normalize_date_key(date) for date in only_dates}
        wanted_parsed = [parse_date(date) for date in only_dates]
        wanted_parsed = [date for date in wanted_parsed if date is not None]

        def matches(date: str) -> bool:
            if normalize_date_key(date) in wanted:
                return True
            parsed = parse_date(date)
            return parsed is not None and parsed in wanted_parsed

        date_items = [
            (date, payload)
            for date, payload in date_items
            if matches(str(date))
        ]

    date_items.sort(
        key=lambda item: (parse_date(item[0]) or datetime.min),
        reverse=True,
    )

    note_records: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    seen_dates: list[str] = []

    for date, payload in date_items:
        if not isinstance(payload, dict):
            print(f"警告：日期 {date} 下的数据不是 object，已跳过", file=sys.stderr)
            continue

        seen_dates.append(date)
        for note_name, note_data in payload.items():
            if note_filter and note_name not in note_filter:
                continue
            if not isinstance(note_data, dict):
                print(f"警告：Note {note_name} 的数据不是 object，已跳过", file=sys.stderr)
                continue
            note_records.setdefault(str(note_name), []).append((date, note_data))

    return note_records, seen_dates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="根据 demo.yml 自动生成 macOS Notes 日报"
    )
    parser.add_argument(
        "--yml",
        default="demo.yml",
        help="demo.yml 路径，默认当前目录下的 demo.yml",
    )
    parser.add_argument(
        "--date",
        action="append",
        help="只处理指定日期，可重复传入，例如 --date \"Sep 7\"",
    )
    parser.add_argument(
        "--today",
        action="store_true",
        help="只处理今天的日期（按本机日期生成 Sep 14 这类 key）",
    )
    parser.add_argument(
        "--note",
        action="append",
        help="只更新指定标题的 Note，可重复传入",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="写入 macOS Notes；不传则只预览",
    )
    parser.add_argument(
        "--preview-dir",
        help="把每个 Note 的预览 HTML 保存到指定目录",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    yml_path = Path(args.yml)

    if not yml_path.exists():
        print(f"找不到 demo.yml: {yml_path}", file=sys.stderr)
        return 2

    raw = yml_path.read_text(encoding="utf-8")
    try:
        data = load_yaml(raw)
    except Exception as exc:
        print(f"解析 YAML 失败: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("demo.yml 顶层必须是 object（日期到数据的映射）", file=sys.stderr)
        return 2

    only_dates = list(args.date or [])
    if args.today:
        only_dates.append(local_today())

    note_records, seen_dates = collect_records(data, only_dates or None, args.note)
    if not note_records:
        print("没有可处理的数据。请检查 --date/--today/--note 过滤条件。", file=sys.stderr)
        return 3

    store = AppleScriptNotes() if args.apply else None
    results: dict[str, str] = {}

    for note_name, records in note_records.items():
        records.sort(
            key=lambda item: (parse_date(item[0]) or datetime.min),
            reverse=True,
        )
        existing_body = store.read(note_name) if store else ""
        body = build_note_body(note_name, existing_body, records)

        if store:
            written_name = store.write(note_name, body)
            print(f"已写入 Note: {written_name}")
        else:
            print(f"预览 Note: {note_name}")
            if len(note_records) == 1:
                print(f"\n{body}")

        results[note_name] = body

    if args.preview_dir:
        saved = save_preview(args.preview_dir, results)
        print("预览文件:")
        for path in saved:
            print(path)

    if not args.apply and not args.preview_dir and len(note_records) > 1:
        print("\n提示：有多个 Note，使用 --preview-dir 可分别保存预览。")

    return 0


# ---------------------------------------------------------------------------
# 简易 YAML 解析器：仅在未安装 PyYAML 时作为兜底，支持本项目所需的嵌套 object。
# ---------------------------------------------------------------------------


def load_yaml(text: str) -> dict[str, Any]:
    if yaml is not None:
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise ValueError("YAML 顶层必须是 object")
        return loaded
    return SimpleYamlLoader(text).parse()


class SimpleYamlLoader:
    """解析 demo.yml 这类纯嵌套 mapping，不支持 list/多行字符串/锚点。"""

    def __init__(self, text: str):
        self.text = text

    def parse(self) -> dict[str, Any]:
        root: dict[str, Any] = {}
        stack: list[tuple[int, dict[str, Any]]] = []

        for raw_line in self.text.splitlines():
            line = self._strip_comment(raw_line).rstrip()
            if not line.strip():
                continue

            indent = len(line) - len(line.lstrip(" "))
            stripped = line.lstrip(" ")
            colon = self._find_colon(stripped)
            if colon is None:
                raise ValueError(f"不是合法的 mapping 行: {raw_line!r}")

            key = self._parse_scalar(stripped[:colon])
            value_text = stripped[colon + 1 :].strip()
            key = str(key)

            while stack and indent <= stack[-1][0]:
                stack.pop()

            current = stack[-1][1] if stack else root

            if not value_text:
                nested: dict[str, Any] = {}
                current[key] = nested
                stack.append((indent, nested))
            else:
                current[key] = self._parse_scalar(value_text)

        return root

    @staticmethod
    def _find_colon(text: str) -> int | None:
        in_single = False
        in_double = False
        index = 0

        while index < len(text):
            char = text[index]
            if char == "\\" and in_double:
                index += 2
                continue
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            elif char == ":" and not in_single and not in_double:
                return index
            index += 1

        return None

    @staticmethod
    def _strip_comment(line: str) -> str:
        in_single = False
        in_double = False
        index = 0

        while index < len(line):
            char = line[index]
            if char == "\\" and in_double:
                index += 2
                continue
            if char == "'" and not in_double:
                in_single = not in_single
            elif char == '"' and not in_single:
                in_double = not in_double
            elif char == "#" and not in_single and not in_double:
                if index == 0 or line[index - 1].isspace():
                    return line[:index]
            index += 1

        return line

    @staticmethod
    def _parse_scalar(text: str) -> Any:
        text = text.strip()
        if not text:
            return None

        if text.startswith('"') and text.endswith('"') and len(text) >= 2:
            import json

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text[1:-1]

        if text.startswith("'") and text.endswith("'") and len(text) >= 2:
            return text[1:-1].replace("''", "'")

        lowered = text.lower()
        if lowered in {"null", "~"}:
            return None
        if lowered in {"true", "yes", "on"}:
            return True
        if lowered in {"false", "no", "off"}:
            return False

        try:
            return int(text)
        except ValueError:
            pass

        try:
            return float(text)
        except ValueError:
            return text


if __name__ == "__main__":
    raise SystemExit(main())
