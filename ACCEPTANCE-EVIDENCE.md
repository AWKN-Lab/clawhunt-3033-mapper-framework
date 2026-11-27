# #3033 验收证据（逐条，真实输出）

订单：#3033 会员空间平台 · 导入框架：映射器插件基类、注册表与列名别名匹配。
任务编码 S2-IMP-003。预算 $100.00，报价 $90.00（90%），身份 1642（my-agent_246）。
验证环境：Python 3.12.3，pytest 9.2.0；只用标准库，不连接任何真实数据库；
只用虚构测试数据。

## 总结果

```text
$ python -m pytest -q
........................ [100%]
24 passed in 0.08s
```

原始输出：`evidence/pytest-20261127.log`。

## AC1：列名「联系电话（手机）」与「 联系 电话 」匹配到同一目标字段（测试断言）

文件：`tests/test_ac1_alias_match.py`（3 个测试，全过）。

- `联系电话（手机）` 匹配到目标字段 `phone`，`missing_required == []`。
- ` 联系 电话 ` 匹配到目标字段 `phone`，`missing_required == []`。
- 两次匹配的 `mapping` 值均为 `phone`，即同一目标字段。

## AC2：缺少必填列时 missing_required 列表包含该字段名（测试断言）

文件：`tests/test_ac2_missing_required.py`（3 个测试，全过）。

- 缺 `phone` 一列时 `missing_required == ["phone"]`。
- 缺 `member_code` 与 `phone` 两列时 `missing_required == ["member_code", "phone"]`；
  未知列 `备注` 进 `unmatched`。
- 三列必填齐全时 `missing_required == []`。

## AC3：同一 source_type 重复登记映射器抛出异常（测试断言）

文件：`tests/test_ac3_duplicate_registration.py`（3 个测试，全过）。

- 同一个类登记两次抛 `DuplicateMapperError`。
- 另一个类用同一 `source_type`（`demo_member_roster`）登记也抛 `DuplicateMapperError`。
- `get_mapper("demo_member_roster")` 返回 `DemoMapper`；未登记的 `source_type` 抛 `KeyError`。

## AC4：mapping_override 指定的映射优先于别名匹配（测试断言）

文件：`tests/test_ac4_override_priority.py`（3 个测试，全过）。

- `mapping_override={"手机": "email"}` 时 `mapping["手机"] == "email"`，
  `matched["email"] == "手机"`，`phone` 不在 `matched` 内（`手机` 本是 `phone` 的别名）。
- 覆盖键带空格（`" 手机 "`）时规范化后同样生效。
- `record_mapping_override` 把覆盖写回批次记录：`batch["mapping_override"] == {"手机": "email"}`，
  且 `batch["mapping"]["手机"] == "email"`。

## AC5：README 用不超过 10 步说明如何新增映射器，DemoMapper 测试通过

文件：`tests/test_ac5_readme_demo.py`（2 个测试，全过）。

- README `## 新增一个映射器` 一节共 7 步（测试数出步骤数，1-10 步内通过）。
- DemoMapper 端到端：原始行 `联系电话（手机）` 列值为 `138 0000 0001`，
  `map_row` 映射到 `phone`，`clean` 后为 `13800000001`，`validate` 无问题，
  `natural_key` 为 `M-001`，`upsert` 首次 `create`、再次 `unchanged`，
  `reconcile` 四项检查全部通过。

## 其余测试

- `tests/test_mapper_base.py`（6 项）：`map_row` 丢弃未匹配列；`clean` 去首尾空格、
  电话去连字符；必填为空报 error；电话格式错报 error、邮箱缺 @ 与会员类型
  不在枚举内报 warning；`upsert` 改电话后 `action == "update"` 且
  `changed_fields == ["phone"]`；`reconcile` 对重复自然键报
  `no_duplicate_natural_key` 不通过。
- `tests/test_normalize.py`（4 项）：全角转半角（`ＴＥＬ` → `tel`，全角空格亦然）；
  括号及括号内说明去掉；空白与标点去掉；大小写折叠。

## 变异自证

`scripts/mutation_check.py`：MUTATION CHECK: PASS（原始输出 `evidence/mutation-check-20261127.log`）。

- A 相：原代码全量 pytest，exit 0，24 passed。
- B 相：复制仓删掉别名索引后跑 `tests/test_ac1_alias_match.py`，exit 1，
  3 failed（`KeyError: 'phone'`），证明 AC1 测试确实覆盖别名匹配路径。
- C 相：原代码重跑全量 pytest，exit 0，24 passed。
- 变异前后 `src/mapper_base.py` 的 SHA256 一致，原文件未被改动。

## 一键复跑

`bash setup.sh` 的一次完整运行记录在 `evidence/selftest-setup-sh-20261127.log`：
第 1 步 pytest 通过，第 2 步变异自证通过；第 3 步（核对 MANIFEST）报失败，
原因是本次把 `setup.sh` 的输出重定向进了 `evidence/` 下、MANIFEST 已收录
的日志文件本身，核对时该文件正在被写入、哈希对不上，不是交付内容问题。
冻结后用 `sha256sum -c MANIFEST` 逐项核对全部通过，且
`bash scripts/run_all.sh`（pytest + 变异自证 + MANIFEST 核验，只读，
不写仓内文件）全程通过：RUN_ALL: PASS。
