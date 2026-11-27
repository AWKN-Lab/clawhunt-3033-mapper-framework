"""AC5：README 用不超过 10 步说明如何新增映射器，DemoMapper 测试通过。"""

import re
import sqlite3
from pathlib import Path

from src.demo_mapper import DemoMapper
from src.registry import get_mapper

README = Path(__file__).resolve().parent.parent / "README.md"


def _readme_add_mapper_steps() -> list[str]:
    text = README.read_text(encoding="utf-8")
    section = text.split("## 新增一个映射器", 1)[1].split("\n## ", 1)[0]
    return [line for line in section.splitlines() if re.match(r"^\d+[.、]", line.strip())]


def test_readme_add_mapper_steps_at_most_ten():
    steps = _readme_add_mapper_steps()
    assert 1 <= len(steps) <= 10, f"新增映射器步骤数为 {len(steps)}，须在 1-10 步内"


def test_demo_mapper_end_to_end():
    mapper_cls = get_mapper("demo_member_roster")
    mapper = mapper_cls()
    assert mapper.version == "1.0.0"
    raw = {
        "会员编号": "M-001",
        "姓名": "张三",
        "联系电话（手机）": "138 0000 0001",
        "邮箱": "zhangsan@example.com",
        "会员类型": "个人",
    }
    mapped = mapper.map_row(raw)
    assert mapped["phone"] == "138 0000 0001"
    cleaned, clean_issues = mapper.clean(mapped)
    assert clean_issues == []
    assert cleaned["phone"] == "13800000001"
    assert mapper.validate(cleaned) == []
    assert mapper.natural_key(cleaned) == "M-001"
    conn = sqlite3.connect(":memory:")
    first = mapper.upsert(conn, cleaned)
    assert first["action"] == "create"
    second = mapper.upsert(conn, cleaned)
    assert second["action"] == "unchanged"
    batch = {"rows": [cleaned], "missing_required": []}
    checks = mapper.reconcile(batch)
    assert all(check["passed"] for check in checks), checks
