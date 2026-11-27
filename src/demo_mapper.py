"""DemoMapper：会员名册来源的示例映射器，作为后续映射器的写法样例。

只用虚构测试数据，不出现客户名称；手机号只做格式校验，不做真实性核验。
"""

from __future__ import annotations

import re

from src.mapper_base import BaseMapper, FieldSpec, Issue
from src.registry import register_mapper

__all__ = ["DemoMapper"]

_PHONE_RE = re.compile(r"^\+?\d{7,15}$")
_MEMBERSHIP_TYPES = {"个人", "企业", "家庭"}


@register_mapper
class DemoMapper(BaseMapper):
    """示例映射器：虚构会员名册（demo_member_roster）。"""

    source_type = "demo_member_roster"
    version = "1.0.0"
    table_name = "member_record"
    natural_key_fields = ["member_code"]
    target_fields = [
        FieldSpec("member_code", "str", True, "会员编号"),
        FieldSpec("name", "str", True, "姓名"),
        FieldSpec("phone", "str", True, "联系电话"),
        FieldSpec("email", "str", False, "邮箱"),
        FieldSpec("membership_type", "str", False, "会员类型"),
    ]
    column_aliases = {
        "member_code": ["会员编号", "会员号", "编号"],
        "name": ["姓名", "名字", "会员姓名"],
        "phone": ["联系电话", "联系电话（手机）", "手机", "电话", "手机号", "联系电话（座机）"],
        "email": ["邮箱", "电子邮箱", "Email"],
        "membership_type": ["会员类型", "类型", "会员类别"],
    }

    def clean(self, mapped: dict[str, object]) -> tuple[dict[str, object], list[Issue]]:
        """清洗：去首尾空格；电话去空格与连字符；返回清洗后的值与问题列表。"""
        cleaned, issues = super().clean(mapped)
        phone = cleaned.get("phone")
        if isinstance(phone, str) and phone != "":
            cleaned["phone"] = re.sub(r"[\s\-]", "", phone)
        return cleaned, issues

    def validate(self, cleaned: dict[str, object]) -> list[Issue]:
        """校验：必填缺失报 error；电话格式不对报 error；邮箱缺 @、会员类型不在
        枚举内报 warning。"""
        issues = super().validate(cleaned)
        phone = cleaned.get("phone")
        if isinstance(phone, str) and phone != "" and not _PHONE_RE.match(phone):
            issues.append(Issue("error", "phone", "联系电话格式不正确，应为 7-15 位数字，可带 + 前缀"))
        email = cleaned.get("email")
        if isinstance(email, str) and email != "" and "@" not in email:
            issues.append(Issue("warning", "email", "邮箱缺少 @"))
        membership_type = cleaned.get("membership_type")
        if (
            isinstance(membership_type, str)
            and membership_type != ""
            and membership_type not in _MEMBERSHIP_TYPES
        ):
            issues.append(
                Issue("warning", "membership_type", "会员类型不在 个人/企业/家庭 枚举内")
            )
        return issues

    def natural_key(self, cleaned: dict[str, object]) -> str:
        """返回幂等用的自然键：会员编号。"""
        return str(cleaned.get("member_code", ""))
