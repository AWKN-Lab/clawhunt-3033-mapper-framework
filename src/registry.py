"""映射器注册表：register_mapper 装饰器登记、get_mapper 取用。

同一 source_type 重复登记抛出 DuplicateMapperError。
"""

from __future__ import annotations

from src.mapper_base import BaseMapper

__all__ = ["DuplicateMapperError", "register_mapper", "get_mapper", "list_mappers", "reset_registry"]

_REGISTRY: dict[str, type[BaseMapper]] = {}


class DuplicateMapperError(ValueError):
    """同一 source_type 被登记了两次。"""


def register_mapper(cls: type[BaseMapper]) -> type[BaseMapper]:
    """装饰器：把一个 BaseMapper 子类登记到注册表。"""
    if not (isinstance(cls, type) and issubclass(cls, BaseMapper)):
        raise TypeError("register_mapper 只能登记 BaseMapper 的子类")
    source_type = cls.source_type
    if not source_type:
        raise ValueError("映射器必须声明非空 source_type")
    if source_type in _REGISTRY:
        raise DuplicateMapperError(f"source_type {source_type!r} 已登记映射器，重复登记")
    _REGISTRY[source_type] = cls
    return cls


def get_mapper(source_type: str) -> type[BaseMapper]:
    """取用指定 source_type 的映射器类；未登记时抛 KeyError。"""
    try:
        return _REGISTRY[source_type]
    except KeyError:
        raise KeyError(f"未登记的 source_type: {source_type!r}") from None


def list_mappers() -> list[str]:
    """返回已登记的 source_type 列表（排序后）。"""
    return sorted(_REGISTRY)


def reset_registry() -> None:
    """清空注册表。只供测试使用，生产代码不调用。"""
    _REGISTRY.clear()
