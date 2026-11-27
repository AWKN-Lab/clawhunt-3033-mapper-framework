# ClawHunt #3033 最小可验证样品：导入框架映射器插件基类、注册表与列名别名匹配

任务编码：S2-IMP-003。样品覆盖各来源映射器共用的插件接口与注册表、
列名别名匹配、批次级映射覆盖，以及一个可直接照抄的示例映射器 DemoMapper。

- 只用 Python 标准库 + pytest，不依赖任何第三方包，不连接真实数据库。
- 只用虚构测试数据，不出现客户名称。
- 一键复跑：`bash setup.sh`（建 venv → 装依赖 → 跑 pytest → 变异自证 → 核对 MANIFEST）

## 结构

- `src/mapper_base.py`：`BaseMapper` 抽象基类（`source_type`、`version`、
  `target_fields`、`column_aliases`、`map_row`、`clean`、`validate`、
  `natural_key`、`upsert`、`reconcile`）与列名匹配函数 `normalize_column` /
  `match_columns` / `record_mapping_override`。
- `src/registry.py`：`register_mapper` 装饰器登记、`get_mapper` 取用；
  同一 `source_type` 重复登记抛 `DuplicateMapperError`。
- `src/demo_mapper.py`：示例映射器 `DemoMapper`（虚构会员名册，
  `demo_member_roster`），作为后续映射器的写法样例。
- `tests/`：AC 逐条测试 + 基类默认行为 + 规范化规则测试。
- `scripts/mutation_check.py`：变异自证（删别名索引后 AC1 必须变红）。
- `scripts/run_all.sh`：pytest + 变异自证 + MANIFEST 核验。
- `MANIFEST`：交付文件清单，附 SHA256。

## 验收标准逐条对照

1. 列名「联系电话（手机）」与「 联系 电话 」匹配到同一目标字段（测试断言）——
   `tests/test_ac1_alias_match.py`，3 项通过。
2. 缺少必填列时 missing_required 列表包含该字段名（测试断言）——
   `tests/test_ac2_missing_required.py`，3 项通过。
3. 同一 source_type 重复登记映射器抛出异常（测试断言）——
   `tests/test_ac3_duplicate_registration.py`，3 项通过。
4. mapping_override 指定的映射优先于别名匹配（测试断言）——
   `tests/test_ac4_override_priority.py`，3 项通过。
5. README 用不超过 10 步说明如何新增映射器，DemoMapper 测试通过——
   本节下文为 7 步说明；`tests/test_ac5_readme_demo.py` 数出步骤数并跑通
   DemoMapper 端到端，2 项通过。

## 新增一个映射器

1. 在 `src/` 下新建一个模块，定义一个 `BaseMapper` 子类。
2. 声明 `source_type`（全局唯一，不可与已登记的重复）与 `version`。
3. 列出 `target_fields`：每个目标字段写字段名、类型、是否必填、中文说明。
4. 写 `column_aliases`：每个目标字段列出原始列名别名，含带括号说明的写法。
5. 按需重写 `clean`、`validate`、`natural_key`、`upsert`、`reconcile`；不写就用基类默认实现。
6. 在类上加 `@register_mapper` 装饰器登记。
7. 在 `tests/` 下加测试：别名匹配、必填缺失、覆盖优先、端到端各至少一项，然后跑 `bash setup.sh` 全过。

## 设计说明

- 列名规范化：去首尾空格、全角转半角、去掉括号及括号内说明、去空白与标点、
  转小写，再与别名比对；匹配输出 `matched` / `unmatched` / `missing_required` 三类结果。
- 覆盖优先：`mapping_override`（原始列名 → 目标字段）先于别名匹配生效，
  覆盖内容由 `record_mapping_override` 写回 `import_batch`；同一目标字段被
  两个原始列名命中时，先出现的列名获胜。
- 注册表：`register_mapper` 只接受 `BaseMapper` 子类；`source_type` 为空或
  重复登记都抛异常；`get_mapper` 取不到时抛 `KeyError`。
- `upsert` 的 `session` 在样品里是 `sqlite3` 连接（内存库），生产接入时
  换成 SQLAlchemy 会话并由各映射器重写本方法；表结构按 `target_fields`
  生成，自然键字段为主键。
- `reconcile(batch)` 返回该来源专属的对账检查项：行数、自然键齐全、
  自然键无重复、必填列无缺失。

## 运行与测试

```bash
bash setup.sh
```

实测环境：Python 3.12.3，pytest 9.2.0。测试结果见 `ACCEPTANCE-EVIDENCE.md`
与 `evidence/` 下的原始日志。
