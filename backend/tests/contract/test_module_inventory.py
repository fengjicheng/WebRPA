# -*- coding: utf-8 -*-
"""模块清单与数量口径审计（契约层）。

本文件守护「module_type 作为唯一主键」在各张元信息表之间的一致性。新增模块时只要漏改
其中一张表，就会产生用户可见但原有测试发现不了的缺陷，因此这里的断言一律采用
**双向差集 + 显式豁免登记**，不允许通过放宽判定条件来消除差异。

当前覆盖：
  · 前端 moduleTypeLabels 与后端已注册执行器的双向差集（Property 5）
  · 对外披露的模块数量口径（Property 15）

口径说明（三个数字都真实存在，含义不同，文档里必须统一用 569）：
  571 = moduleTypeLabels 键总数，含 custom_module、subflow_header 两个伪类型
  569 = 对外披露口径，= 571 - custom_module - subflow_header，含 group、note 两个画布工具
  567 = 纯功能模块，= 569 - group - note

后续新增用例（如 AI schema 双向一致）请追加到文件末尾的对应小节，公共解析函数放在
「源码解析」小节，避免各用例各自实现一份解析逻辑。
"""
import os
import re

import pytest

import app.executors  # noqa: F401  导入触发执行器注册 / 启用懒加载清单
from app.executors.base import registry

# ---------------------------------------------------------------- 路径与读取

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_FE = os.path.join(_ROOT, "frontend", "src")
_BE = os.path.join(_ROOT, "backend", "app")
_DOCS = os.path.join(_FE, "components", "workflow", "documentation")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------- 口径常量

#: 伪类型：出现在 moduleTypeLabels 中但不是可拖拽的功能模块
PSEUDO_TYPES: set[str] = {"custom_module", "subflow_header", "group", "note"}

#: 不计入对外披露数量的伪类型（group / note 是画布工具，用户可见可拖，计入口径）
COUNT_EXCLUDED_TYPES: set[str] = {"custom_module", "subflow_header"}

#: 对外披露的模块数量。README、教学文档、AI 提示词中的数字必须与此一致。
#:
#: 口径构成：moduleTypeLabels 全部键数 减去 COUNT_EXCLUDED_TYPES 两个伪类型。
#: 573 = 571（立项时）+ infinite_loop + sap_select_tab —— 这两个模块后端一直有执行器、
#: AI schema 也有条目，只是前端漏了登记，用户在界面上用不到；任务 15 补齐前端登记后
#: 它们进入披露口径（见 tasks.md 任务 15）。
DISCLOSED_MODULE_COUNT = 571

#: 前后端差集的显式豁免登记表：module_type -> 豁免理由（禁止空字符串）
#: 新增豁免项必须写明「为什么这个 module_type 合法地只存在于一侧」，
#: 禁止为了让测试变绿而把真实差集项塞进这里。
EXEMPT_TYPES: dict[str, str] = {
    "group": "画布分组框，纯前端视觉容器；后端仅有空实现占位，不承载业务语义",
    "note": "画布便签，纯前端批注；后端仅有空实现占位，不承载业务语义",
    "custom_module": "自定义模块占位类型，运行时展开为用户定义的子流程",
    "subflow_header": "子流程头节点，由 workflow_executor 内部处理，非独立执行器",
}


# ---------------------------------------------------------------- 源码解析

def _parse_module_type_labels() -> dict[str, str]:
    """解析 workflowStore.ts 的 moduleTypeLabels，返回 module_type -> 中文名。

    解析失败（找不到声明、条目数异常少）时抛异常，绝不返回空字典——静默返回空会让
    所有依赖它的断言退化成「什么都没测」的假绿。
    """
    src = _read(os.path.join(_FE, "store", "workflowStore.ts"))
    anchor = "export const moduleTypeLabels: Record<ModuleType, string> = {"
    start = src.find(anchor)
    if start < 0:
        raise AssertionError(
            "在 frontend/src/store/workflowStore.ts 中找不到 moduleTypeLabels 声明，"
            "解析规则需更新（不要让本测试静默通过）"
        )
    body_start = start + len(anchor)
    end = src.find("\n}", body_start)
    if end < 0:
        raise AssertionError("moduleTypeLabels 声明未正常闭合，解析规则需更新")
    body = src[body_start:end]

    labels: dict[str, str] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        m = re.match(r"^['\"]?([A-Za-z0-9_]+)['\"]?\s*:\s*['\"](.*?)['\"]\s*,?\s*(?://.*)?$", line)
        if m:
            labels[m.group(1)] = m.group(2)

    if len(labels) < 400:
        raise AssertionError(
            f"moduleTypeLabels 只解析出 {len(labels)} 条，明显少于实际规模，解析规则需更新"
        )
    return labels


def _backend_registered_types() -> set[str]:
    """后端已注册（含懒加载占位）的 module_type 全集"""
    types = set(registry.get_all_types())
    if len(types) < 300:
        raise AssertionError(
            f"后端注册表只有 {len(types)} 个 module_type，注册/懒加载流程可能已损坏"
        )
    return types


def _doc_files_with_module_count() -> list[str]:
    """参与「模块数量数字」扫描的文件：README（中英）+ 全部教学文档正文"""
    files = [os.path.join(_ROOT, "README.md"), os.path.join(_ROOT, "README.EN.md")]
    for name in sorted(os.listdir(_DOCS)):
        if name.startswith("content-") and name.endswith(".ts"):
            files.append(os.path.join(_DOCS, name))
    return files


#: 模块数量数字的识别规则。仅认「对外披露口径」的表述，且只取三位及以上的数字——
#: 两位数以内基本都是局部举例（如「以下 5 个模块」），不属于披露口径。
_COUNT_PATTERNS = (
    r"模块数量-(\d{3,})个",          # README 中文徽章
    r"modules-(\d{3,})-",            # README 英文徽章
    r"(\d{3,})\s*个模块",
    r"(\d{3,})\s*个功能模块",
    r"(\d{3,})\s*个内置模块",
    r"(\d{3,})\s*个自动化模块",
    r"(\d{3,})\s+modules",
)


def _scan_documented_module_counts() -> list[tuple[str, int, int]]:
    """扫描文档中的模块数量数字，返回 [(相对路径, 行号, 数字)]"""
    hits: list[tuple[str, int, int]] = []
    for path in _doc_files_with_module_count():
        if not os.path.exists(path):
            continue
        rel = os.path.relpath(path, _ROOT).replace("\\", "/")
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            for pattern in _COUNT_PATTERNS:
                for m in re.finditer(pattern, line):
                    hits.append((rel, lineno, int(m.group(1))))
    return hits


# ---------------------------------------------------------------- 差集计算（纯函数）

def diff_module_sets(frontend: set, backend: set, exempt: set) -> dict:
    """计算前后端模块清单的双向差集（抽成纯函数以便属性化测试）。

    返回 {"frontend_only": [...], "backend_only": [...]}，均已排序、已剔除豁免项。
    刻意不在这里做「结果为空就通过」之外的任何兜底：输入什么就如实算什么，
    边界情况（空集合、含伪类型、含未知 type）的行为由属性化测试锁定。
    """
    return {
        "frontend_only": sorted(frontend - backend - exempt),
        "backend_only": sorted(backend - frontend - exempt),
    }


def count_disclosed_modules(labels_keys, excluded: set) -> int:
    """按对外披露口径统计模块数量（抽成纯函数以便属性化测试）"""
    return len(set(labels_keys) - excluded)


# ---------------------------------------------------------------- fixture

@pytest.fixture(scope="module")
def labels() -> dict[str, str]:
    return _parse_module_type_labels()


@pytest.fixture(scope="module")
def backend_types() -> set[str]:
    return _backend_registered_types()


# ---------------------------------------------------------------- 豁免表自检

@pytest.mark.contract
def test_exempt_types_have_nonempty_reason():
    """每个豁免项必须带非空理由字符串——豁免是要被人工评审的，不能只写个键"""
    bad = sorted(k for k, v in EXEMPT_TYPES.items() if not isinstance(v, str) or not v.strip())
    assert not bad, (
        "以下豁免项缺少理由说明，请在 EXEMPT_TYPES 中写明为什么它合法地只存在于一侧：\n  "
        + "\n  ".join(bad)
    )


@pytest.mark.contract
def test_exempt_types_are_real_entries(labels, backend_types):
    """豁免表里不允许出现两侧都不存在的条目（防止豁免表变成历史垃圾堆）"""
    stale = sorted(t for t in EXEMPT_TYPES if t not in labels and t not in backend_types)
    assert not stale, (
        "以下豁免项在前端 moduleTypeLabels 与后端注册表中都不存在，应从 EXEMPT_TYPES 删除：\n  "
        + "\n  ".join(stale)
    )


# ------------------------------------------------- Property 5：前后端双向差集

@pytest.mark.contract
def test_no_frontend_module_without_backend_executor(labels, backend_types):
    """前端有登记、后端无执行器的模块：拖到画布上运行时会报「未知模块类型」"""
    missing = sorted(set(labels) - backend_types - set(EXEMPT_TYPES))
    detail = "\n  ".join(f"{t}（{labels[t]}）" for t in missing)
    assert not missing, (
        f"以下 {len(missing)} 个模块在前端 moduleTypeLabels 中有登记，但后端没有对应执行器，\n"
        "用户拖到画布上运行会报「未知模块类型」。请补后端执行器，\n"
        "或在 EXEMPT_TYPES 中登记并注明理由（禁止放宽本断言）：\n  " + detail
    )


@pytest.mark.contract
def test_no_backend_executor_without_frontend_label(labels, backend_types):
    """后端有执行器、前端无登记的模块：该能力用户在界面上根本用不到"""
    missing = sorted(backend_types - set(labels) - set(EXEMPT_TYPES))
    assert not missing, (
        f"以下 {len(missing)} 个 module_type 在后端已注册执行器，但前端 moduleTypeLabels\n"
        "没有登记，用户无法在界面上使用该能力。请补前端登记（moduleTypeLabels + 分类），\n"
        "或在 EXEMPT_TYPES 中登记并注明理由（禁止放宽本断言）：\n  " + "\n  ".join(missing)
    )


# ------------------------------------------- Property 15：数量口径与文档同步

@pytest.mark.contract
def test_disclosed_module_count_matches_reality(labels):
    """DISCLOSED_MODULE_COUNT 必须等于按口径统计的实际数量"""
    actual = len(set(labels) - COUNT_EXCLUDED_TYPES)
    assert actual == DISCLOSED_MODULE_COUNT, (
        f"对外披露口径的模块数量实际为 {actual}，但常量 DISCLOSED_MODULE_COUNT 是 "
        f"{DISCLOSED_MODULE_COUNT}。\n"
        f"口径 = moduleTypeLabels（{len(labels)} 条）减去伪类型 "
        f"{sorted(COUNT_EXCLUDED_TYPES)}。\n"
        "若确实新增/删除了模块，请同步更新本常量与 README、教学文档中的所有数字。"
    )


@pytest.mark.contract
def test_documented_module_counts_match_disclosed_count():
    """README 与教学文档里出现的模块数量数字必须全部等于披露口径"""
    hits = _scan_documented_module_counts()
    assert hits, (
        "未在 README 与教学文档中扫描到任何模块数量数字，"
        "说明识别规则 _COUNT_PATTERNS 已与文档写法脱节，请更新规则"
    )
    wrong = [(rel, lineno, num) for rel, lineno, num in hits if num != DISCLOSED_MODULE_COUNT]
    detail = "\n  ".join(f"{rel}:{lineno} 写的是 {num}" for rel, lineno, num in wrong)
    assert not wrong, (
        f"以下 {len(wrong)} 处文档的模块数量与披露口径 {DISCLOSED_MODULE_COUNT} 不一致：\n  "
        + detail
    )


# ------------------------------------------- Property 8：AI schema 双向一致
#
# AI 小助手依据 ai_assistant_module_schemas.py 生成模块配置。两类缺口都会让它产出
# 跑不起来的工作流：
#   · 缺失条目 -> AI 不知道该模块的必填项，生成的节点缺字段，执行时报错；
#   · 僵尸条目 -> schema 里有、moduleTypeLabels 里没有的 module_type，AI 会生成一个
#     前端根本渲染不出来的节点。
# 因此必须双向比对，且判定基准是 moduleTypeLabels（模块集合的唯一主键来源）。

from app.services.ai_assistant_module_schemas import get_all_module_schemas  # noqa: E402

#: schema 条目必须具备的键。缺键会让 AI 拿不到必填项或取值说明。
_REQUIRED_SCHEMA_KEYS = ("required", "optional", "defaults", "desc", "example")

#: 前端配置面板源码目录（校验 required 字段在界面上有处可填）
_PANEL_DIRS = (
    os.path.join(_FE, "components", "workflow"),
    os.path.join(_FE, "components"),
)


@pytest.fixture(scope="module")
def ai_schemas() -> dict:
    schemas = get_all_module_schemas()
    if len(schemas) < 400:
        raise AssertionError(
            f"AI schema 只解析出 {len(schemas)} 条，明显少于实际规模，导入或组装流程可能已损坏"
        )
    return schemas


@pytest.mark.contract
def test_ai_schema_covers_every_module(labels, ai_schemas):
    """每个真实模块都必须有 schema 条目，否则 AI 不知道它的必填项"""
    missing = sorted(set(labels) - PSEUDO_TYPES - set(ai_schemas))
    detail = "\n  ".join(f"{t}（{labels[t]}）" for t in missing)
    assert not missing, (
        f"以下 {len(missing)} 个真实模块在 ai_assistant_module_schemas.py 中没有 schema 条目，\n"
        "AI 小助手不知道它们的必填项与取值含义，生成的配置很可能跑不起来：\n  " + detail
    )


@pytest.mark.contract
def test_ai_schema_has_no_zombie_entries(labels, ai_schemas):
    """schema 中不得出现 moduleTypeLabels 里不存在的 module_type（僵尸条目）"""
    zombies = sorted(set(ai_schemas) - set(labels))
    assert not zombies, (
        f"以下 {len(zombies)} 个 module_type 在 AI schema 中有条目，但前端 moduleTypeLabels\n"
        "里不存在，AI 会据此生成前端渲染不出来的节点，必须从 schema 中删除：\n  "
        + "\n  ".join(zombies)
    )


@pytest.mark.contract
def test_ai_schema_entries_are_structurally_complete(ai_schemas):
    """每个 schema 条目都必须含 required / optional / defaults / desc / example 五个键"""
    broken = []
    for mtype in sorted(ai_schemas):
        schema = ai_schemas[mtype]
        if not isinstance(schema, dict):
            broken.append(f"  {mtype}: 条目不是 dict，实际为 {type(schema).__name__}")
            continue
        absent = [k for k in _REQUIRED_SCHEMA_KEYS if k not in schema]
        if absent:
            broken.append(f"  {mtype}: 缺少键 {', '.join(absent)}")
    assert not broken, (
        f"以下 {len(broken)} 个 schema 条目结构不完整（AI 会拿不到必填项或取值说明）：\n"
        + "\n".join(broken)
    )


#: 参与「required 字段可填性」扫描的前端配置面板源码目录。
#: ConfigPanel.tsx 只是容器，各模块的字段实际分散在 config-panels/ 下的 40+ 个文件里，
#: 只扫容器会把几乎所有字段误报为「界面上无处可填」。
_PANEL_ROOTS = (
    os.path.join(_FE, "components", "workflow", "ConfigPanel.tsx"),
    os.path.join(_FE, "components", "workflow", "config-panels"),
)

#: required 字段的可填性豁免：字段名 -> 理由。
#: 仅用于「确实不需要在配置面板出现」的字段（由系统注入或由其它交互产生），
#: 每条必须写明理由，禁止用它消化真实缺口。
REQUIRED_FIELD_EXEMPTIONS: dict[str, str] = {}


def _panel_corpus() -> str:
    parts = []
    for root in _PANEL_ROOTS:
        if not os.path.exists(root):
            raise AssertionError(f"配置面板源码不存在：{root}，扫描规则需更新")
        if os.path.isfile(root):
            parts.append(_read(root))
            continue
        for name in sorted(os.listdir(root)):
            if name.endswith(".tsx") or name.endswith(".ts"):
                parts.append(_read(os.path.join(root, name)))
    corpus = "\n".join(parts)
    if len(corpus) < 200000:
        raise AssertionError(
            f"配置面板源码语料只有 {len(corpus)} 字符，明显偏小，扫描规则可能已失效"
        )
    return corpus


@pytest.mark.contract
def test_ai_schema_required_fields_exist_in_config_panel(labels, ai_schemas):
    """schema 里 required 声明的字段，必须能在前端配置面板中找到同名字段。

    防的是「AI 按 schema 生成了某个必填字段，但用户在界面上根本找不到这个输入框」——
    这种情况下用户既无法核对也无法修改 AI 的配置。

    判定口径：字段名以标识符形式出现在 ConfigPanel.tsx 源码中（`field:`、`'field'`、
    `.field`、`"field"` 任一形式）。这是宽口径，只保证「界面上存在这个字段」，不校验
    它是否恰好挂在该模块的面板分支下——精确到分支需要解析 JSX 条件渲染，代价过高且
    容易误报。宽口径已足够抓出整块缺失的字段。
    """
    corpus = _panel_corpus()
    missing: list[str] = []
    for mtype in sorted(ai_schemas):
        if mtype not in labels or mtype in PSEUDO_TYPES:
            continue  # 僵尸条目由 test_ai_schema_has_no_zombie_entries 负责
        schema = ai_schemas[mtype]
        if not isinstance(schema, dict):
            continue
        for field in schema.get("required") or []:
            if not isinstance(field, str) or field in REQUIRED_FIELD_EXEMPTIONS:
                continue
            patterns = (f"'{field}'", f'"{field}"', f".{field}", f"{field}:")
            if not any(p in corpus for p in patterns):
                missing.append(f"  {mtype}.{field}")

    assert not missing, (
        f"以下 {len(missing)} 个 schema 必填字段在前端配置面板中找不到同名字段，\n"
        "AI 按 schema 生成的配置在界面上无处可填、无法核对：\n" + "\n".join(missing)
    )


@pytest.mark.contract
def test_required_field_exemptions_have_nonempty_reason():
    """required 字段豁免必须写明理由"""
    bad = sorted(k for k, v in REQUIRED_FIELD_EXEMPTIONS.items() if not isinstance(v, str) or not v.strip())
    assert not bad, "以下 required 字段豁免缺少理由说明：\n  " + "\n  ".join(bad)
