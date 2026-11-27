"""normalize_column 规范化规则：全角转半角、去括号、去空白标点、转小写。"""

from src.mapper_base import normalize_column


def test_fullwidth_to_halfwidth():
    assert normalize_column("ＴＥＬ") == "tel"
    assert normalize_column("联系电话　（手机）") == "联系电话"


def test_parentheses_and_content_removed():
    assert normalize_column("联系电话(手机)") == "联系电话"
    assert normalize_column("姓名（必填）") == "姓名"


def test_whitespace_and_punctuation_removed():
    assert normalize_column(" 联系 电话 ") == "联系电话"
    assert normalize_column("联系-电话！") == "联系电话"


def test_casefolded():
    assert normalize_column("Email") == "email"
    assert normalize_column("  MEMBER_CODE ") == "member_code"
