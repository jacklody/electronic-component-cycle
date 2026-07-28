# 电子元器件周期智能体 - Code Wiki

> 基于2016-2026三轮大周期深度复盘的AI行情分析专家，自动分析因果、自动积累经验、自动预警行情。

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构设计](#2-系统架构设计)
3. [项目目录结构](#3-项目目录结构)
4. [核心模块详解](#4-核心模块详解)
   - 4.1 [cycle_analyzer.py - 周期分析引擎](#41-cycle_analyzerpy---周期分析引擎)
   - 4.2 [auto_cycle_pipeline.py - 自动工作流](#42-auto_cycle_pipelinepy---自动工作流)
   - 4.3 [start_config_server.py - 配置管理服务](#43-start_config_serverpy---配置管理服务)
5. [数据结构与知识图谱](#5-数据结构与知识图谱)
6. [配置管理](#6-配置管理)
7. [运行方式与使用示例](#7-运行方式与使用示例)
8. [依赖关系](#8-依赖关系)
9. [扩展指南](#9-扩展指南)
10. [版本历史](#10-版本历史)

---

## 1. 项目概述

### 1.1 项目定位

本项目是一个**电子元器件周期智能分析系统**，旨在通过对2016-2026年电子行业三轮大周期的深度复盘，构建一个能够自动分析行情因果、积累历史经验、预警未来行情的AI智能体。

### 1.2 核心价值

| 能力维度 | 具体价值 |
|---------|---------|
| 自动根因分析 | 区分根因/催化剂/放大器，排除市场噪音 |
| 时序因果校验 | 强制"原因早于结果"，杜绝因果倒置 |
| 信息可信度分级 | A/B/C三级自动打标，不把传言当事实 |
| 三级预警机制 | 红/橙/绿预警，明确备货/去库存/观望时机 |
| 自学习经验库 | 每分析一个事件，经验库自动增长 |
| 可视化配置 | 自带Web配置工具，无需改代码即可扩展 |

### 1.3 覆盖范围

- **28大类电子元器件**：被动元件、存储芯片、逻辑芯片、显示面板、制造服务等
- **9种周期类型**：供给收缩型、供需错配型、成本推动型、需求革命型、政策驱动型、产能过剩型、需求疲软型、价格战型、需求冲击型
- **18条预警规则**：红色预警8条、橙色预警4条、绿色预警6条

---

## 2. 系统架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                      电子元器件周期智能体                         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: 事件发现层 (EventDiscovery)                           │
│  - 按年+品类自动生成搜索Query                                     │
│  - 自动去重已入库事件                                            │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: 信息收集层 (InformationGrader)                        │
│  - 多源数据交叉验证                                              │
│  - 自动A/B/C可信度分级                                           │
│  - 自动提取时间、价格数据                                         │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: 智能分析层 (RCAAnalyzer)                              │
│  - 自动RCA根因分析                                               │
│  - 周期类型自动分类 (涨/跌双向)                                   │
│  - 自动生成预警模板                                              │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: 自动校验层 (ComponentCycleAnalyzer)                    │
│  - 时序因果校验 (原因必须早于结果)                                 │
│  - 字段完整性校验                                                 │
│  - 噪音自动排除                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Layer 5: 经验库层 (AutoKnowledgeGraphUpdater)                   │
│  - Graphiti时序知识图谱                                          │
│  - 自动追加事件/案例/因果关系                                     │
│  - 自动更新版本号与统计数据                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 数据流

```
输入事件描述
    ↓
信息提取（时间、价格、来源）
    ↓
可信度分级（A/B/C）
    ↓
RCA根因分析（根因/催化剂/放大器/噪音）
    ↓
周期类型判断（上涨/下跌，9种类型）
    ↓
生成预警规则（红/橙/绿）
    ↓
时序因果校验
    ↓
写入知识图谱（事件/案例/因果关系）
    ↓
输出分析结果
```

---

## 3. 项目目录结构

```
electronic-component-cycle/
├── 📂 graphiti/                      # 时序知识图谱（经验库）
│   └── cycle_knowledge_graph.json    # 实体、事件、案例、因果关系
├── 📂 scripts/                       # 核心代码模块
│   ├── cycle_analyzer.py             # 周期分析引擎（MCP接口）
│   └── auto_cycle_pipeline.py        # 全自动工作流pipeline
├── 📂 skills/                        # 可复用预测技能
│   └── electronic-component-cycle-prediction.md
├── 📂 reports/                       # 历史复盘报告
│   └── 2016-2026电子元器件周期复盘报告.md
├── config-manager.html               # 可视化配置工具
├── config.json                       # 系统配置文件
├── start_config_server.py            # 配置管理HTTP服务
├── LICENSE                           # MIT许可证
├── README.md                         # 项目说明文档
├── 扩展操作指南.md                    # 详细扩展文档
├── 自动工作流使用说明.md              # Pipeline使用说明
└── 项目经理验收报告.md                # 验收报告
```

### 文件职责对照表

| 文件 | 职责 | 核心功能 |
|-----|------|---------|
| `config.json` | 全局配置 | 品类、关键词、预警规则、噪音词 |
| `cycle_analyzer.py` | 分析引擎 | 周期检测、案例匹配、因果校验、MCP接口 |
| `auto_cycle_pipeline.py` | 自动工作流 | 事件发现、信息分级、RCA分析、知识图谱更新 |
| `start_config_server.py` | 配置服务 | 提供配置读写HTTP接口 |
| `cycle_knowledge_graph.json` | 知识存储 | 实体、事件、案例、因果关系 |
| `config-manager.html` | 配置UI | 可视化配置管理界面 |

---

## 4. 核心模块详解

### 4.1 cycle_analyzer.py - 周期分析引擎

#### 4.1.1 模块定位

[cycle_analyzer.py](file:///workspace/electronic-component-cycle/scripts/cycle_analyzer.py) 是系统的核心分析引擎，提供周期检测、相似案例匹配、历史拐点查询和时序因果校验功能，遵循MCP函数调用规范，可被DataAnalyst-Agent调用。

#### 4.1.2 核心类与方法

##### 枚举类 `Confidence`

```python
class Confidence(Enum):
    A = "A - 事后证实事实"
    B = "B - 同期市场传闻"
    C = "C - 无法确认信息"
```

| 等级 | 含义 | 适用场景 |
|-----|------|---------|
| A | 事后证实事实 | 官方公告、权威数据、事后复盘 |
| B | 同期市场传闻 | 媒体报道、产业访谈 |
| C | 无法确认信息 | 自媒体、股吧、传言 |

##### 数据类 `CycleEvent`

```python
@dataclass
class CycleEvent:
    event_id: str              # 事件ID
    time: str                  # 时间（YYYYQn格式）
    category: str              # 品类
    event_type: str            # 事件类型（价格上涨/缺货涨价/产能调整等）
    subject: str               # 主体（厂商/品类）
    description: str           # 描述
    confidence: str            # 可信度（A/B/C）
    price_impact: float        # 价格影响幅度（正数上涨，负数下跌）
    duration_impact: int       # 影响持续月数
```

##### 核心类 `ComponentCycleAnalyzer`

| 方法 | 功能 | 参数 | 返回值 |
|-----|------|------|-------|
| `__init__` | 初始化分析器 | `knowledge_graph_path`: 知识图谱路径 | - |
| `load_knowledge_graph` | 加载知识图谱 | `path`: JSON文件路径 | - |
| `detect_cycle_phase` | 检测周期阶段 | `current_signals`: 当前市场信号字典 | 周期阶段判断结果 |
| `find_similar_cases` | 相似案例匹配 | `current_features`: 特征字典, `top_k`: 返回数量 | 相似案例列表 |
| `get_price_inflection_points` | 获取历史拐点 | `category`: 指定品类（可选） | 拐点列表 |
| `validate_time_causality` | 时序因果校验 | - | 校验结果 |
| `run_mcp_analysis` | MCP统一调用入口 | `query_type`: 查询类型, `params`: 参数 | 分析结果 |

##### 关键方法详解

**`detect_cycle_phase(current_signals)`**

检测当前周期处于哪个阶段（上行/震荡/下行），核心逻辑：
1. 遍历所有预警规则，计算每条规则的匹配度
2. 匹配度≥60%的规则被视为触发
3. 根据总匹配分数判断周期阶段

```python
# 输入示例
current_signals = {
    "features": ["头部厂商发布涨价函", "AI需求爆发", "产能收缩"],
    "capex_growth": "连续2年低增长",
    "bb_ratio": 1.3,
    "channel_inventory": "1.5个月",
    "capacity_utilization": "90%+"
}

# 输出示例
{
    "analysis_time": "2026-07-24T10:00:00",
    "current_phase": "上行周期 - 涨价阶段",
    "confidence_score": "5/8",
    "triggered_rules": [...],
    "recommendation": "建议：适当增加安全库存..."
}
```

**`validate_time_causality()`**

时序因果校验的核心方法，确保所有因果关系满足"原因发生时间早于结果"：
1. 解析每个事件的时间为季度序号
2. 对于每条因果关系，取原因的最晚时间和结果的最早时间比较
3. 如果原因时间 > 结果时间，则标记为无效

**`run_mcp_analysis(query_type, params)`**

MCP统一调用入口，支持四种查询类型：

| query_type | 功能 | 对应方法 |
|------------|------|---------|
| `cycle_phase` | 周期阶段检测 | `detect_cycle_phase` |
| `similar_cases` | 相似案例匹配 | `find_similar_cases` |
| `inflection_points` | 历史拐点查询 | `get_price_inflection_points` |
| `validate_causality` | 时序因果校验 | `validate_time_causality` |

#### 4.1.3 内置预警规则

系统内置4条核心预警规则（`cycle_rules`）：

| 规则ID | 规则名称 | 触发条件数量 | 概率 |
|--------|---------|-------------|------|
| R001 | 供给收缩型涨价预警 | 4 | 85% |
| R002 | 周期见顶预警 | 4 | 90% |
| R003 | 周期底部预警 | 4 | 80% |
| R004 | 黑天鹅冲击预警 | 3 | 70% |

---

### 4.2 auto_cycle_pipeline.py - 自动工作流

#### 4.2.1 模块定位

[auto_cycle_pipeline.py](file:///workspace/electronic-component-cycle/scripts/auto_cycle_pipeline.py) 是系统的全自动工作流引擎，实现从事件发现→信息收集→智能分析→自动校验→经验库更新的完整流程。

#### 4.2.2 核心组件

##### `EventDiscovery` - 事件发现模块

负责自动搜索历史涨价/缺货/降价事件：

| 方法 | 功能 |
|-----|------|
| `generate_search_queries` | 按年(2016-2026)×品类×事件关键词生成所有搜索Query |
| `filter_new_events` | 过滤已入库事件，避免重复 |

事件关键词覆盖双向周期：
- 上涨信号：`涨价`、`提价`、`缺货`、`交期延长`、`供应紧张`、`产能不足`
- 下跌信号：`降价`、`价格战`、`产能过剩`、`库存高企`、`去库存`、`周期反转`

##### `InformationGrader` - 信息分级模块

负责根据来源自动打A/B/C可信度标签：

| 方法 | 功能 |
|-----|------|
| `grade_source` | 根据来源字符串自动分级 |
| `extract_price_data` | 从文本中自动提取价格数据（涨幅、交期、产能影响） |
| `extract_time` | 从文本中自动提取时间，转换为YYYYQn格式 |

**来源分级规则**：

| 等级 | 来源类型 | 示例 |
|-----|---------|------|
| A | 权威第三方/官方公告 | TrendForce、Omdia、原厂公告、反垄断调查 |
| B | 媒体报道/产业访谈 | 财新、第一财经、供应链人士 |
| C | 自媒体/股吧/传言 | 微博、微信、网传、据传 |

##### `RCAAnalyzer` - 根因分析模块

负责自动RCA根因分析，覆盖涨跌双向周期：

| 方法 | 功能 |
|-----|------|
| `classify_cause` | 自动分类原因类型（根因/催化剂/放大器/噪音） |
| `determine_cycle_type` | 根据根因判断周期类型 |
| `generate_warning_template` | 根据周期类型生成预警模板 |

**根因分类体系**：

| 周期方向 | 根因类型 | 关键词示例 |
|---------|---------|-----------|
| 上涨 | 产能收缩 | 关厂、减产、产能调整、转产 |
| 上涨 | 需求错配 | 砍单、需求预测错误、V型复苏 |
| 上涨 | 成本推动 | 原材料涨价、能源涨价、物流成本 |
| 上涨 | 需求革命 | AI、新能源汽车、HBM、新需求 |
| 上涨 | 政策/贸易 | 关税、制裁、国产替代、环保限产 |
| 下跌 | 产能过剩 | 扩产、新产能投产、供过于求 |
| 下跌 | 需求下滑 | 需求不及预期、消费电子疲软、去库存 |
| 下跌 | 价格战 | 降价促销、抢份额、恶性竞争 |
| 下跌 | 黑天鹅需求冲击 | 疫情封控、经济危机、地缘冲突 |

##### `AutoKnowledgeGraphUpdater` - 知识图谱更新器

负责自动更新Graphiti时序知识图谱：

| 方法 | 功能 |
|-----|------|
| `add_event` | 添加新事件 |
| `add_case_study` | 添加标杆案例 |
| `add_causal_relation` | 添加因果关系（含时间校验） |
| `save` | 保存并更新元数据和验证结果 |

##### `AutoCyclePipeline` - 主Pipeline类

整合所有模块的主类：

| 方法 | 功能 |
|-----|------|
| `__init__` | 初始化所有子模块 |
| `auto_analyze_new_event` | 一键分析单个新事件（核心入口） |
| `manual_add_event_from_search_result` | 批量导入搜索结果 |
| `run_full_validation` | 运行完整知识图谱校验 |

#### 4.2.3 核心流程：`auto_analyze_new_event`

```
输入：事件描述、品类、来源
    ↓
1. 信息提取（时间、价格数据、可信度分级）
    ↓
2. RCA根因分析（根因/催化剂/放大器/噪音）
    ↓
3. 周期类型判断
    ↓
4. 生成预警模板
    ↓
5. 添加事件到知识图谱
    ↓
6. （可选）添加为标杆案例
    ↓
7. 保存并运行时序校验
    ↓
输出：分析结果（事件ID、周期类型、预警规则、校验结果）
```

---

### 4.3 start_config_server.py - 配置管理服务

#### 4.3.1 模块定位

[start_config_server.py](file:///workspace/electronic-component-cycle/start_config_server.py) 提供本地HTTP服务，用于配置文件的读写，配合 `config-manager.html` 实现可视化配置管理。

#### 4.3.2 API接口

| 接口 | 方法 | 功能 |
|-----|------|------|
| `/api/config` | GET | 获取当前配置 |
| `/api/save` | POST | 保存新配置（含自动备份） |

**使用方式**：
```bash
python start_config_server.py
# 服务启动在 http://localhost:8765
# 然后打开 config-manager.html 即可可视化管理配置
```

---

## 5. 数据结构与知识图谱

### 5.1 知识图谱整体结构

[cycle_knowledge_graph.json](file:///workspace/electronic-component-cycle/graphiti/cycle_knowledge_graph.json) 采用Graphiti格式，包含5个核心部分：

```json
{
    "metadata": {...},           // 元数据（版本、时间范围、描述）
    "entities": [...],           // 实体（厂商、品类、要素）
    "events": [...],             // 事件（涨价、缺货、产能调整等）
    "case_studies": [...],       // 标杆案例（完整周期复盘）
    "causal_relations": [...],   // 因果关系（事件间的因果链）
    "validation_result": {...}   // 验证结果统计
}
```

### 5.2 实体结构

| 字段 | 类型 | 说明 |
|-----|------|------|
| `id` | string | 实体唯一标识（E001-E045） |
| `name` | string | 实体名称 |
| `type` | string | 类型：厂商/品类/要素 |
| `aliases` | list | 别名列表 |

**实体类型分类**：

| 类型 | 数量 | 示例 |
|-----|------|------|
| 厂商 | 20 | LGD、京东方、三星、村田、TI、瑞萨 |
| 品类 | 10 | LCD面板、DRAM、MLCC、MCU、功率器件 |
| 要素 | 15 | 资本开支、产线关停、下游需求、疫情、AI服务器 |

### 5.3 事件结构

| 字段 | 类型 | 说明 |
|-----|------|------|
| `id` | string | 事件ID（EVT001-EVT041） |
| `time` | string | 时间（YYYYQn格式） |
| `subject` | string | 主体实体ID |
| `predicate` | string | 事件类型（价格上涨/关停产线/产能调整等） |
| `object` | string | 对象实体ID（可选） |
| `description` | string | 事件描述 |
| `confidence` | string | 可信度（A/B/C） |
| `source` | string | 信息来源 |
| `price_data` | object | 价格数据（可选） |

**事件类型枚举**：

| 类型 | 说明 | 示例 |
|-----|------|------|
| 价格上涨 | 价格开始上涨 | EVT004 |
| 价格见顶 | 价格达到峰值 | EVT006 |
| 价格下跌 | 价格开始下跌 | EVT008 |
| 关停产线 | 厂商关闭产线 | EVT002 |
| 产能调整 | 产能结构调整 | EVT005 |
| 新产能投产 | 新产线投产 | EVT007 |
| 缺货涨价 | 缺货导致涨价 | EVT016 |
| 发布涨价函 | 原厂发布涨价通知 | EVT022 |
| 生产事故 | 工厂事故 | EVT015 |
| 需求爆发 | 需求突然增长 | EVT032 |

### 5.4 案例结构

| 字段 | 类型 | 说明 |
|-----|------|------|
| `case_id` | string | 案例ID（CASE001-CASE003） |
| `case_name` | string | 案例名称 |
| `category` | string | 涉及品类 |
| `cycle_type` | string | 周期类型 |
| `start_time` | string | 开始时间 |
| `peak_time` | string | 峰值时间 |
| `end_time` | string | 结束时间 |
| `rise_duration_months` | int | 上涨持续月数 |
| `max_price_increase_pct` | int | 最大涨幅(%) |
| `root_cause` | string | 根因 |
| `catalyst` | string | 催化剂 |
| `amplifier` | string | 放大器 |
| `false_narratives` | list | 错误传言 |
| `warning_template` | list | 预警规则模板 |

### 5.5 因果关系结构

| 字段 | 类型 | 说明 |
|-----|------|------|
| `id` | string | 关系ID（CAUS001-CAUS010） |
| `from_event` | string | 原因事件ID（逗号分隔） |
| `to_event` | string | 结果事件ID（逗号分隔） |
| `relation_type` | string | 关系类型：直接因果/触发/加速/放大/市场情绪 |
| `strength` | string | 强度：强/中/弱 |
| `time_order_valid` | bool | 时序是否有效 |
| `description` | string | 关系描述 |

---

## 6. 配置管理

### 6.1 config.json 配置项

[config.json](file:///workspace/electronic-component-cycle/config.json) 是系统的核心配置文件，包含以下配置项：

#### 6.1.1 品类配置

```json
"categories": [
    "MLCC", "片式电阻", "钽电容", "铝电解电容", ...
]
```

#### 6.1.2 根因关键词配置

```json
"root_cause_keywords": {
    "产能收缩": ["关厂", "关线", "停产", "减产", ...],
    "需求错配": ["砍单", "需求预测错误", "居家办公", ...],
    "成本推动": ["原材料涨价", "铜价", "铝箔", ...],
    "需求革命": ["AI", "人工智能", "新能源汽车", ...],
    "政策/贸易": ["反垄断", "关税", "贸易战", ...],
    "产能出清": ["全行业亏损", "破产", "并购", ...]
}
```

#### 6.1.3 下跌原因关键词配置

```json
"downturn_cause_keywords": {
    "产能过剩": ["扩产", "新产能投产", "产能释放", ...],
    "需求下滑": ["需求不及预期", "消费电子疲软", ...],
    "价格战": ["价格战", "降价促销", "抢份额", ...],
    "黑天鹅需求冲击": ["疫情封控", "经济危机", ...]
}
```

#### 6.1.4 催化剂与放大器配置

```json
"catalyst_keywords": ["火灾", "地震", "暴雪", "停电", ...]
"amplifier_keywords": ["牛鞭效应", "超量下单", "囤货", ...]
```

#### 6.1.5 噪音词配置

```json
"false_narratives": ["游资炒作", "永远涨价", "卡脖子", ...]
```

#### 6.1.6 预警规则模板配置

```json
"warning_templates": {
    "供给收缩型上涨": [
        {"signal": "...", "level": "🔴红色预警", "prediction": "..."},
        {"signal": "...", "level": "🟢绿色预警", "prediction": "..."}
    ],
    ...
}
```

### 6.2 可视化配置工具

打开 `config-manager.html` 即可在浏览器中可视化管理配置，支持：
- 添加/删除监控品类
- 添加/删除原因类型
- 添加/删除预警规则
- 添加/删除噪音词
- 自动生成需要修改的代码

---

## 7. 运行方式与使用示例

### 7.1 环境要求

- Python 3.8+
- 无需额外依赖（仅使用标准库）

### 7.2 运行分析引擎

```bash
cd /workspace/electronic-component-cycle/scripts
python cycle_analyzer.py
```

### 7.3 运行自动Pipeline

```bash
cd /workspace/electronic-component-cycle/scripts
python auto_cycle_pipeline.py
```

### 7.4 使用示例

#### 示例1：一键分析新事件

```python
from auto_cycle_pipeline import AutoCyclePipeline

pipeline = AutoCyclePipeline("../graphiti/cycle_knowledge_graph.json")

result = pipeline.auto_analyze_new_event(
    event_description="""
    2026Q3 TI宣布全系列模拟芯片涨价15%，
    原因是8寸成熟产能紧张，原材料涨价，
    市场传言又是游资炒作。
    """,
    category="模拟芯片",
    source="TI官方公告"
)

print(result["cycle_type"])           # 周期类型
print(result["cause_analysis"])       # 根因分析结果
print(result["warning_template"])     # 生成的预警规则
```

#### 示例2：检测周期阶段

```python
from cycle_analyzer import ComponentCycleAnalyzer

analyzer = ComponentCycleAnalyzer("../graphiti/cycle_knowledge_graph.json")

current_signals = {
    "features": ["头部厂商发布涨价函", "AI需求爆发", "产能收缩"],
    "capex_growth": "连续2年低增长",
    "bb_ratio": 1.3,
    "channel_inventory": "1.5个月"
}

result = analyzer.detect_cycle_phase(current_signals)
print(f"当前周期阶段: {result['current_phase']}")
print(f"操作建议: {result['recommendation']}")
```

#### 示例3：查找相似案例

```python
similar = analyzer.find_similar_cases(current_signals, top_k=3)
for case in similar:
    print(f"{case['case_name']} (相似度: {case['similarity']*100:.0f}%)")
```

#### 示例4：运行完整校验

```python
validation = pipeline.run_full_validation()
print(f"因果关系校验: {validation['valid_relations']}/{validation['total_relations']}条有效")
```

### 7.5 MCP接口调用

```python
from cycle_analyzer import ComponentCycleAnalyzer

analyzer = ComponentCycleAnalyzer("graphiti/cycle_knowledge_graph.json")

# 1. 判断周期阶段
result = analyzer.run_mcp_analysis("cycle_phase", current_signals)

# 2. 查找相似案例
similar = analyzer.run_mcp_analysis("similar_cases", {"features": ["产能收缩", "需求爆发"]})

# 3. 查询历史拐点
points = analyzer.run_mcp_analysis("inflection_points", {"category": "MLCC"})

# 4. 自动校验因果时序
validation = analyzer.run_mcp_analysis("validate_causality", {})
```

---

## 8. 依赖关系

### 8.1 模块依赖关系

```
auto_cycle_pipeline.py
    └── cycle_analyzer.py
            └── config.json

start_config_server.py
    └── config.json

config-manager.html
    └── start_config_server.py (HTTP API)
```

### 8.2 文件依赖关系

```
cycle_knowledge_graph.json
    ├── 被 cycle_analyzer.py 读取
    ├── 被 auto_cycle_pipeline.py 读取和写入
    └── 包含验证结果统计

config.json
    ├── 被 auto_cycle_pipeline.py 读取
    ├── 被 start_config_server.py 读取和写入
    └── 包含品类、关键词、预警规则配置
```

### 8.3 外部依赖

本项目仅使用Python标准库，无需安装任何第三方包：

| 模块 | 用途 |
|-----|------|
| `json` | JSON文件读写 |
| `re` | 正则表达式（时间/价格提取） |
| `datetime` | 时间处理 |
| `typing` | 类型注解 |
| `dataclasses` | 数据类定义 |
| `enum` | 枚举类定义 |
| `os` | 文件路径处理 |
| `http.server` | HTTP配置服务 |
| `urllib.parse` | URL解析 |

---

## 9. 扩展指南

### 9.1 添加新品类

**方式1：可视化配置（推荐）**
1. 打开 `config-manager.html`
2. 在「品类管理」标签页输入品类名
3. 点击添加，复制生成的代码

**方式2：手动修改**
1. 打开 `config.json`
2. 在 `categories` 数组中添加新品类名称

### 9.2 添加新原因类型

1. 打开 `config.json`
2. 在 `root_cause_keywords`（上涨）或 `downturn_cause_keywords`（下跌）中添加新的原因类型和关键词
3. 预警规则会自动匹配

### 9.3 添加新预警规则

1. 打开 `config.json`
2. 在 `warning_templates` 中对应周期类型的数组里添加新规则

### 9.4 添加新噪音词

1. 打开 `config.json`
2. 在 `false_narratives` 数组中添加新的噪音词

### 9.5 对接新数据源

在搜索循环中添加新的API调用，返回格式需为：
```python
{"title": "...", "content": "...", "source": "..."}
```

### 9.6 添加消息推送

在pipeline处理完事件后添加推送逻辑：
```python
result = pipeline.auto_analyze_new_event(...)
if "🔴红色预警" in result.get("warning_level", ""):
    # 调用webhook发送通知
    requests.post("your_webhook_url", json=result)
```

---

## 10. 版本历史

| 版本 | 日期 | 主要更新 |
|-----|------|---------|
| v1.3 | 2026-07-24 | 新增自动工作流pipeline，增加涨跌双向周期支持，完善时序因果校验 |
| v1.2 | 2026-07-24 | 新增3个标杆事件深度复盘（LCD面板、MCU存储、被动元件） |
| v1.1 | 2026-07-24 | 增加时序因果自动校验功能，完善MCP接口 |
| v1.0 | 2026-07-24 | 初始版本，基于2016-2026三轮大周期复盘完成 |

---

## 附录：关键设计理念

### A. 时序因果铁则

**核心原则**：原因必须发生在结果之前。

系统在写入任何因果关系时都会自动校验时间顺序，如果发现原因时间晚于结果时间，会标记为无效并拒绝入库。

### B. 信息分级机制

**核心原则**：不把传言当事实。

- A级信息：可作为判断依据（官方公告、权威数据、事后复盘）
- B级信息：仅作参考，需交叉验证（媒体报道、产业访谈）
- C级信息：直接排除（自媒体、股吧、传言）

### C. 噪音自动排除

**核心原则**：每轮周期都会出现但从未被证实的说法，直接排除。

常见噪音词：游资炒作、永远涨价、卡脖子、缺货3-5年、超级周期、外国控产、国家收储、销售话术

### D. 自学习经验库

**核心原则**：每分析一个事件，经验库自动增长，判断越来越准。

新事件分析完成后自动追加到知识图谱，包含：
- 事件本身（时间、描述、可信度）
- 根因分析结果
- 生成的预警规则
- 因果关系（自动校验后入库）

---

**⚠️ 免责声明**：本工具仅用于行业研究和学习，不构成任何投资或采购建议，市场有风险，决策需谨慎。

---

*文档生成时间：2026-07-28*
*项目版本：v1.3*
