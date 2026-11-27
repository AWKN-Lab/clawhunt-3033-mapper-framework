"""AC1：列名「联系电话（手机）」与「 联系 电话 」匹配到同一目标字段。"""

from src.demo_mapper import DemoMapper

MAPPER = DemoMapper()


def test_parenthesised_header_matches_phone():
    result = MAPPER.match_columns(["会员编号", "姓名", "联系电话（手机）"])
    assert result.matched["phone"] == "联系电话（手机）"
    assert result.missing_required == []


def test_spaced_header_matches_phone():
    result = MAPPER.match_columns(["会员编号", "姓名", " 联系 电话 "])
    assert result.matched["phone"] == " 联系 电话 "
    assert result.missing_required == []


def test_both_headers_map_to_same_target_field():
    first = MAPPER.match_columns(["会员编号", "姓名", "联系电话（手机）"])
    second = MAPPER.match_columns(["会员编号", "姓名", " 联系 电话 "])
    assert first.mapping["联系电话（手机）"] == "phone"
    assert second.mapping[" 联系 电话 "] == "phone"
    assert first.matched["phone"] and second.matched["phone"]
