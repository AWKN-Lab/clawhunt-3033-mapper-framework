"""AC3：同一 source_type 重复登记映射器抛出异常。"""

import pytest

from src.demo_mapper import DemoMapper
from src.mapper_base import BaseMapper, FieldSpec
from src.registry import (
    DuplicateMapperError,
    get_mapper,
    list_mappers,
    register_mapper,
)


def test_registering_same_class_twice_raises():
    with pytest.raises(DuplicateMapperError):
        register_mapper(DemoMapper)


def test_registering_other_class_with_same_source_type_raises():
    class AnotherMemberMapper(BaseMapper):
        source_type = "demo_member_roster"
        version = "2.0.0"
        target_fields = [FieldSpec("member_code", "str", True, "会员编号")]
        column_aliases = {}

    with pytest.raises(DuplicateMapperError):
        register_mapper(AnotherMemberMapper)


def test_get_mapper_returns_registered_class():
    assert get_mapper("demo_member_roster") is DemoMapper
    assert "demo_member_roster" in list_mappers()
    with pytest.raises(KeyError):
        get_mapper("no_such_source")
