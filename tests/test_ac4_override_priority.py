"""AC4：mapping_override 指定的映射优先于别名匹配。"""

from src.demo_mapper import DemoMapper
from src.mapper_base import record_mapping_override

MAPPER = DemoMapper()


def test_override_beats_alias():
    # “手机”本身是 phone 的别名；覆盖把它指到 email，email 获胜，phone 落空。
    result = MAPPER.match_columns(
        ["会员编号", "姓名", "手机"], mapping_override={"手机": "email"}
    )
    assert result.mapping["手机"] == "email"
    assert result.matched["email"] == "手机"
    assert "phone" not in result.matched
    assert result.missing_required == ["phone"]


def test_override_key_matches_after_normalization():
    result = MAPPER.match_columns(
        ["会员编号", "姓名", "手机"], mapping_override={" 手机 ": "email"}
    )
    assert result.mapping["手机"] == "email"


def test_override_written_back_to_import_batch():
    batch: dict = {"id": "batch-demo-001", "source_type": "demo_member_roster"}
    record_mapping_override(batch, {"手机": "email"})
    assert batch["mapping_override"] == {"手机": "email"}
    assert batch["mapping"]["手机"] == "email"
