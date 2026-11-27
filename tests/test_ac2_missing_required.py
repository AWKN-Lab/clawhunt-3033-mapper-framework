"""AC2：缺少必填列时 missing_required 列表包含该字段名。"""

from src.demo_mapper import DemoMapper

MAPPER = DemoMapper()


def test_missing_phone_listed():
    result = MAPPER.match_columns(["会员编号", "姓名", "邮箱"])
    assert result.missing_required == ["phone"]
    assert "phone" not in result.matched


def test_missing_two_required_fields_listed():
    result = MAPPER.match_columns(["姓名", "邮箱", "备注"])
    assert result.missing_required == ["member_code", "phone"]
    assert result.unmatched == ["备注"]


def test_nothing_missing_when_all_required_present():
    result = MAPPER.match_columns(["会员编号", "姓名", "联系电话"])
    assert result.missing_required == []
