"""BaseMapper 默认行为：map_row / clean / validate / upsert / reconcile。"""

import sqlite3

from src.demo_mapper import DemoMapper

MAPPER = DemoMapper()


def test_map_row_drops_unmatched_columns():
    mapped = MAPPER.map_row({"会员编号": "M-002", "姓名": "李四", "联系电话": "13900000002", "备注": "丢弃"})
    assert mapped == {"member_code": "M-002", "name": "李四", "phone": "13900000002"}


def test_clean_strips_whitespace():
    cleaned, issues = MAPPER.clean({"member_code": " M-003 ", "name": " 王五 ", "phone": " 138-0000-0003 "})
    assert cleaned["member_code"] == "M-003"
    assert cleaned["name"] == "王五"
    assert cleaned["phone"] == "13800000003"
    assert issues == []


def test_validate_missing_required_reports_error():
    issues = MAPPER.validate({"member_code": "M-004", "name": "赵六", "phone": ""})
    assert [i for i in issues if i.level == "error" and i.field == "phone"]


def test_validate_bad_phone_reports_error_and_bad_email_warns():
    issues = MAPPER.validate(
        {"member_code": "M-005", "name": "钱七", "phone": "abc", "email": "not-an-email", "membership_type": "未知"}
    )
    assert any(i.level == "error" and i.field == "phone" for i in issues)
    assert any(i.level == "warning" and i.field == "email" for i in issues)
    assert any(i.level == "warning" and i.field == "membership_type" for i in issues)


def test_upsert_update_reports_changed_fields():
    conn = sqlite3.connect(":memory:")
    first_row = {"member_code": "M-006", "name": "孙八", "phone": "13800000006", "email": "", "membership_type": "个人"}
    assert MAPPER.upsert(conn, first_row)["action"] == "create"
    changed_row = dict(first_row, phone="13900000006")
    result = MAPPER.upsert(conn, changed_row)
    assert result["action"] == "update"
    assert result["changed_fields"] == ["phone"]


def test_reconcile_flags_duplicate_natural_keys():
    rows = [
        {"member_code": "M-007", "name": "周九", "phone": "13800000007"},
        {"member_code": "M-007", "name": "吴十", "phone": "13800000010"},
    ]
    checks = {c["name"]: c["passed"] for c in MAPPER.reconcile({"rows": rows, "missing_required": []})}
    assert checks["no_duplicate_natural_key"] is False
    assert checks["rows_present"] is True
    assert checks["natural_key_present"] is True
