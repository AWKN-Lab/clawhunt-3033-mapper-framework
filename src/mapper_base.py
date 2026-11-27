"""映射器插件基类 BaseMapper 与列名别名匹配。

任务编码 S2-IMP-003。只用 Python 标准库。

列名匹配规则（与平台任务描述逐字一致）：
对表头做去首尾空格、全角转半角、去掉括号及括号内说明、去空白与标点、
转小写后与别名比对，输出 matched / unmatched / missing_required 三类结果；
支持批次级映射覆盖 mapping_override（原始列名 -> 目标字段），覆盖优先于
别名匹配，并写回 import_batch。
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

__all__ = [
    "FieldSpec",
    "Issue",
    "MatchResult",
    "normalize_column",
    "match_columns",
    "record_mapping_override",
    "BaseMapper",
]


@dataclass(frozen=True)
class FieldSpec:
    """目标字段定义：字段名、类型、是否必填、中文说明。"""

    name: str
    type: str = "str"
    required: bool = False
    description: str = ""


@dataclass(frozen=True)
class Issue:
    """清洗或校验发现的问题。level 为 error 或 warning。"""

    level: str
    field: str
    message: str


@dataclass
class MatchResult:
    """列名匹配结果：三类输出 + 原始列名到目标字段的最终映射。"""

    matched: dict[str, str] = field(default_factory=dict)  # 目标字段 -> 原始列名
    unmatched: list[str] = field(default_factory=list)  # 未匹配上的原始列名
    missing_required: list[str] = field(default_factory=list)  # 缺失的必填目标字段
    mapping: dict[str, str] = field(default_factory=dict)  # 原始列名 -> 目标字段


_PAREN_RE = re.compile(r"[\(（][^\)）]*[\)）]")
_NON_WORD_RE = re.compile(r"[^\w]", re.UNICODE)


def normalize_column(header: str) -> str:
    """规范化一个原始列名，供别名比对使用。

    步骤：去首尾空格 -> 全角转半角（NFKC，含全角空格）-> 去掉括号及括号内
    说明 -> 去空白与标点 -> 转小写。
    例：normalize_column("联系电话（手机）") == "联系电话"；
        normalize_column(" 联系 电话 ") == "联系电话"。
    """
    text = str(header).strip()
    text = unicodedata.normalize("NFKC", text)
    text = _PAREN_RE.sub("", text)
    text = _NON_WORD_RE.sub("", text)
    return text.casefold()


def match_columns(
    headers: list[str],
    target_fields: list[FieldSpec],
    column_aliases: dict[str, list[str]],
    mapping_override: dict[str, str] | None = None,
) -> MatchResult:
    """把原始表头匹配到目标字段。

    mapping_override 的键按原始列名精确匹配，也接受规范化后的列名；
    覆盖优先于别名匹配。同一目标字段被两个原始列名命中时，先出现的
    列名获胜，后出现的列名进 unmatched。
    """
    override = dict(mapping_override or {})
    override_norm = {normalize_column(k): v for k, v in override.items()}
    field_names = {f.name for f in target_fields}
    required = [f.name for f in target_fields if f.required]

    # 别名索引：规范化后的别名 -> 目标字段；目标字段名本身也算一个别名。
    alias_index: dict[str, str] = {}
    for spec in target_fields:
        alias_index.setdefault(normalize_column(spec.name), spec.name)
    for target, aliases in column_aliases.items():
        if target not in field_names:
            continue
        for alias in aliases:
            alias_index.setdefault(normalize_column(alias), target)

    result = MatchResult()
    for header in headers:
        target = override.get(header) or override_norm.get(normalize_column(header))
        if target is not None and target in field_names:
            if target in result.matched:
                result.unmatched.append(header)
                continue
            result.matched[target] = header
            result.mapping[header] = target
            continue
        target = alias_index.get(normalize_column(header))
        if target is None:
            result.unmatched.append(header)
            continue
        if target in result.matched:
            result.unmatched.append(header)
            continue
        result.matched[target] = header
        result.mapping[header] = target
    result.missing_required = [name for name in required if name not in result.matched]
    return result


def record_mapping_override(batch: dict, mapping_override: dict[str, str]) -> dict:
    """把批次级映射覆盖写回 import_batch（字典形态的批次记录）。

    覆盖内容同时写进 batch["mapping_override"] 与 batch["mapping"]，
    调用方落库时把同一内容写入 import_batch 表的对应字段。
    """
    batch["mapping_override"] = dict(mapping_override)
    batch.setdefault("mapping", {}).update(dict(mapping_override))
    return batch


class BaseMapper(ABC):
    """各来源映射器共用的抽象基类。

    子类必须声明 source_type、version、target_fields、column_aliases，
    并实现 map_row / clean / validate / natural_key / upsert / reconcile
    中与本来源有关的逻辑；不相关的步骤可直接沿用基类默认实现。
    """

    source_type: str = ""
    version: str = "1.0.0"
    target_fields: list[FieldSpec] = []
    column_aliases: dict[str, list[str]] = {}
    table_name: str = "target_record"
    natural_key_fields: list[str] = []

    def match_columns(
        self, headers: list[str], mapping_override: dict[str, str] | None = None
    ) -> MatchResult:
        """用本映射器的字段与别名做列名匹配（覆盖优先于别名）。"""
        return match_columns(headers, self.target_fields, self.column_aliases, mapping_override)

    def map_row(self, raw: dict[str, object]) -> dict[str, object]:
        """把原始行转成目标字段字典：未匹配的原始列丢弃。"""
        matched = self.match_columns(list(raw.keys()))
        return {target: raw[header] for target, header in matched.matched.items()}

    def clean(self, mapped: dict[str, object]) -> tuple[dict[str, object], list[Issue]]:
        """清洗：字符串去首尾空格；返回清洗后的值与问题列表。"""
        cleaned: dict[str, object] = {}
        issues: list[Issue] = []
        for spec in self.target_fields:
            value = mapped.get(spec.name)
            if isinstance(value, str):
                value = value.strip()
            cleaned[spec.name] = value
        return cleaned, issues

    def validate(self, cleaned: dict[str, object]) -> list[Issue]:
        """校验：必填字段缺失或为空字符串报 error。"""
        issues: list[Issue] = []
        for spec in self.target_fields:
            if not spec.required:
                continue
            value = cleaned.get(spec.name)
            if value is None or (isinstance(value, str) and value == ""):
                issues.append(Issue("error", spec.name, f"必填字段 {spec.name} 缺失"))
        return issues

    def natural_key(self, cleaned: dict[str, object]) -> str:
        """返回幂等用的自然键：默认取 natural_key_fields 的值以 | 连接。"""
        fields = self.natural_key_fields or [
            f.name for f in self.target_fields if f.required
        ][:1]
        return "|".join(str(cleaned.get(name, "")) for name in fields)

    def upsert(self, session: sqlite3.Connection, cleaned: dict[str, object]) -> dict:
        """写入业务表并返回变更记录。

        session 为 sqlite3 连接（样品用内存库；生产接入时换成 SQLAlchemy
        会话并由各映射器重写本方法）。表不存在时按 target_fields 建表，
        自然键字段为主键；同键已存在且值相同返回 unchanged，否则 update。
        """
        key_fields = self.natural_key_fields or [
            f.name for f in self.target_fields if f.required
        ][:1]
        columns = [f.name for f in self.target_fields]
        pk = ", ".join(f'"{name}"' for name in key_fields)
        column_defs = ", ".join(
            f'"{name}" TEXT' + (" PRIMARY KEY" if name in key_fields and len(key_fields) == 1 else "")
            for name in columns
        )
        if len(key_fields) > 1:
            column_defs += f", PRIMARY KEY ({pk})"
        session.execute(f'CREATE TABLE IF NOT EXISTS "{self.table_name}" ({column_defs})')
        key = self.natural_key(cleaned)
        placeholders = ", ".join("?" for _ in columns)
        column_list = ", ".join(f'"{name}"' for name in columns)
        values = [cleaned.get(name) for name in columns]
        row = session.execute(
            f'SELECT {column_list} FROM "{self.table_name}" WHERE '
            + " AND ".join(f'"{name}" = ?' for name in key_fields),
            [cleaned.get(name) for name in key_fields],
        ).fetchone()
        if row is None:
            session.execute(
                f'INSERT INTO "{self.table_name}" ({column_list}) VALUES ({placeholders})',
                values,
            )
            session.commit()
            return {"action": "create", "natural_key": key, "changed_fields": columns}
        existing = dict(zip(columns, row))
        changed = [name for name in columns if existing.get(name) != cleaned.get(name)]
        if not changed:
            return {"action": "unchanged", "natural_key": key, "changed_fields": []}
        session.execute(
            f'UPDATE "{self.table_name}" SET '
            + ", ".join(f'"{name}" = ?' for name in columns)
            + " WHERE " + " AND ".join(f'"{name}" = ?' for name in key_fields),
            values + [cleaned.get(name) for name in key_fields],
        )
        session.commit()
        return {"action": "update", "natural_key": key, "changed_fields": changed}

    def reconcile(self, batch: dict) -> list[dict]:
        """返回该来源专属的对账检查项：每项含 name / passed / detail。"""
        rows: list[dict] = batch.get("rows", [])
        checks: list[dict] = []
        checks.append(
            {
                "name": "rows_present",
                "passed": len(rows) > 0,
                "detail": f"rows={len(rows)}",
            }
        )
        keys = [self.natural_key(row) for row in rows]
        checks.append(
            {
                "name": "natural_key_present",
                "passed": all(key not in ("", "|") for key in keys),
                "detail": f"keys={len(keys)}",
            }
        )
        checks.append(
            {
                "name": "no_duplicate_natural_key",
                "passed": len(set(keys)) == len(keys),
                "detail": f"unique={len(set(keys))}/{len(keys)}",
            }
        )
        missing = batch.get("missing_required", [])
        checks.append(
            {
                "name": "no_missing_required",
                "passed": len(missing) == 0,
                "detail": f"missing_required={missing}",
            }
        )
        return checks
