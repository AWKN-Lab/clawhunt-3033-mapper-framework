"""pytest 共用夹具：每个测试前清空注册表并重新登记 DemoMapper。

直接 import src.demo_mapper 只会在进程内执行一次登记，清空后不会自动
重登，所以夹具里显式调一次 register_mapper(DemoMapper)。
"""

import pytest

from src.demo_mapper import DemoMapper
from src.registry import register_mapper, reset_registry


@pytest.fixture(autouse=True)
def _fresh_registry():
    reset_registry()
    register_mapper(DemoMapper)
    yield
    reset_registry()
