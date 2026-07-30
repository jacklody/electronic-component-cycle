#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电子元器件周期智能体 - 自动定时扫描脚本
- 读取已入库事件描述前30字做去重
- 喂入 WebSearch 抓到的新事件到 AutoCyclePipeline
- 红色预警写入 alerts.log，并通过 lark-im 飞书通知
- 扫描摘要写入 daily_scan_YYYYMMDD_HH.log
"""
import sys
import os
import json
import importlib.util
import types
from datetime import datetime

# 工作目录
os.chdir('/workspace/electronic-component-cycle')

# ============================================================
# 步骤 1: 运行时 patch cycle_analyzer.py 语法错误
# （源文件 line 253 含未转义双引号，不修改源文件）
# ============================================================
def _patched_cycle_analyzer():
    src_path = 'scripts/cycle_analyzer.py'
    with open(src_path, 'r', encoding='utf-8') as f:
        src = f.read()
    fixed = src.replace(
        '"不要相信"游资炒作"传言，核心是供给收缩"',
        '"不要相信\\"游资炒作\\"传言，核心是供给收缩"',
    )
    mod = types.ModuleType('cycle_analyzer')
    code = compile(fixed, src_path, 'exec')
    exec(code, mod.__dict__)
    sys.modules['cycle_analyzer'] = mod
    return mod

_patched_cycle_analyzer()
spec = importlib.util.spec_from_file_location(
    'auto_cycle_pipeline', 'scripts/auto_cycle_pipeline.py'
)
acp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acp)
AutoCyclePipeline = acp.AutoCyclePipeline
AutoKnowledgeGraphUpdater = acp.AutoKnowledgeGraphUpdater

# 运行时 patch: 修复 ComponentCycleAnalyzer.load_knowledge_graph 中
# evt.get('object', '') 当 object=None 时返回 None，传入 _parse_category 报错
def _safe_parse_category(self, obj):
    obj = obj or ''
    category_map = {
        'E021': 'LCD面板',
        'E022': 'DRAM存储',
        'E023': 'NAND存储',
        'E024': 'HBM存储',
        'E025': '通用MCU',
        'E026': '车规MCU',
        'E027': '功率器件',
        'E028': 'MLCC',
        'E029': '钽电容',
        'E030': '片阻',
    }
    for k, v in category_map.items():
        if k in obj:
            return v
    return '全品类'

ComponentCycleAnalyzer = acp.ComponentCycleAnalyzer
ComponentCycleAnalyzer._orig_parse_category = ComponentCycleAnalyzer._parse_category
ComponentCycleAnalyzer._parse_category = _safe_parse_category
# 同时 patch 内层 _estimate_price_impact 与 _estimate_duration 防止类似 None 报错
# （这些方法可能会对 object=None 字符串化处理失败，做防御）
# 已通过上游 load_knowledge_graph 测试能跑通，暂不动

# 运行时 patch: 修复 _get_next_id 重复参数 bug (不修改源文件)
# 源代码在第 273 行调用 self._get_next_id("CASE", prefix="CASE")，
# 第一个参数是 prefix 位置实参，第二个又用 prefix 关键字，导致参数重复。
# 这里把 _get_next_id 替换成接受 *args, **kwargs 的版本，吞掉重复参数。
def _patched_get_next_id(self, *args, **kwargs):
    # 解析 prefix
    if args:
        prefix = args[0]
    else:
        prefix = kwargs.pop('prefix', None)
    case_prefix = kwargs.pop('case_prefix', False)
    _orig = AutoKnowledgeGraphUpdater._orig_get_next_id
    return _orig(self, prefix=prefix, case_prefix=case_prefix)
AutoKnowledgeGraphUpdater._orig_get_next_id = AutoKnowledgeGraphUpdater._get_next_id
AutoKnowledgeGraphUpdater._get_next_id = _patched_get_next_id
acp.AutoKnowledgeGraphUpdater._get_next_id = _patched_get_next_id

# ============================================================
# 步骤 2: 加载已入库事件做去重
# ============================================================
KG_PATH = 'graphiti/cycle_knowledge_graph.json'
with open(KG_PATH, 'r', encoding='utf-8') as f:
    existing_kg = json.load(f)

existing_keys = set()
for e in existing_kg.get('events', []):
    existing_keys.add(e['description'][:30])
print(f"已入库事件: {len(existing_kg.get('events', []))} 个，去重 key: {len(existing_keys)} 个")

# ============================================================
# 步骤 3: WebSearch 抓取到的事件（手工提炼，去重后逐条入库）
# ============================================================
candidate_events = [
    {
        "category": "DRAM",
        "description": "2026年7月瑞银上调2026Q3 DRAM合约价预测至环比涨32%，三星通知客户三季度DRAM均价上调20%，AI算力需求拉动HBM挤占通用DRAM产能，2027年供需缺口扩大70%",
        "source": "WebSearch 自动扫描 - 瑞银/新浪财经 2026-07-28",
    },
    {
        "category": "HBM",
        "description": "2026年7月30日三星电子预计2026下半年服务器DRAM、企业级SSD、HBM需求加速，HBM4E计划2027年量产，HBM5将采用2纳米GAA工艺",
        "source": "WebSearch 自动扫描 - 财联社 2026-07-30",
    },
    {
        "category": "MLCC",
        "description": "2026年7月1日国巨全系列MLCC涨价约50%，村田对AI服务器及高端车规MLCC涨价10%-40%，AI算力驱动本轮涨价潮从渠道端传导至原厂直供体系",
        "source": "WebSearch 自动扫描 - 新浪财经 2026-07-30",
    },
    {
        "category": "MLCC",
        "description": "2026年7月29日三星电机与太阳诱电宣布MLCC涨价30%，三星电机8月1日执行，太阳诱电9月1日执行，AI服务器需求爆发导致高端MLCC供不应求、交期4-6个月以上",
        "source": "WebSearch 自动扫描 - 新浪财经 2026-07-30",
    },
    {
        "category": "DRAM",
        "description": "2026年7月27日长鑫科技科创板上市，首日市值突破3.65万亿元超越工行成为A股市值第一，2026Q1全球DRAM份额8%，2026上半年净利润预计500-570亿元同比增长22倍",
        "source": "WebSearch 自动扫描 - 中国企业家 2026-07-29",
    },
    {
        "category": "存储芯片",
        "description": "2026年7月28-29日美韩芯片股48小时内暴跌，SK海力士两日累跌超20%、美光跌近9%、闪迪跌超14%，市场担忧存储超级周期提前终结进入产能过剩阶段",
        "source": "WebSearch 自动扫描 - 央广网 2026-07-29",
    },
    {
        "category": "DRAM",
        "description": "2026年7月28日英伟达通知下游GPU套装涨价30%，RTX5070/5080零售价较去年涨30%以上，根因是AI服务器对HBM需求增长导致消费级显存供应被挤压",
        "source": "WebSearch 自动扫描 - 界面新闻 2026-07-30",
    },
    {
        "category": "通用MCU",
        "description": "2026年7月23日ST发布Q2财报，通用MCU业务同比增35.5%为各分部最高，book-to-bill接近2，分销渠道库存低于标准目标，CECP领域显著高于2",
        "source": "WebSearch 自动扫描 - 芯世相 2026-07-29",
    },
    {
        "category": "功率器件",
        "description": "2026年7月1日全球近20家模拟及功率半导体企业集体启动年内第二轮涨价，英飞凌10%-20%、TI 15%-85%、ST 12%-18%、ADI 30%、华润微15%以上、扬杰科技10%-15%",
        "source": "WebSearch 自动扫描 - 电子产品世界/icviews 2026-07-28",
    },
    {
        "category": "电源管理IC",
        "description": "2026年7月1日TI第四次调价，AI服务器及数据中心专用PMIC、高压信号链模拟芯片涨幅15%-25%，工业自动化及储能隔离芯片涨幅10%-15%，MPS和立锜同步跟涨",
        "source": "WebSearch 自动扫描 - 中国经营报 2026-07-25",
    },
    {
        "category": "晶圆代工",
        "description": "2026年7月21日台积电计划2027年起上调晶圆代工价格，7纳米及以下先进制程涨幅5%-10%，成熟制程最高涨10%，高性能计算芯片新订单在基础涨价上加收10%-15%溢价",
        "source": "WebSearch 自动扫描 - 财联社 2026-07-21",
    },
    {
        "category": "封测",
        "description": "2026年7月1日日月光年内第三次上调先进封装报价最高涨幅超20%，覆盖CoWoS/FoCoS/HBM堆叠/2.5D/3D，国内长电科技、通富微电、华天科技同步涨价15%-30%",
        "source": "WebSearch 自动扫描 - 上海证券报 2026-07-02",
    },
    {
        "category": "NAND Flash",
        "description": "2026年下半年SLC NAND结构性紧缺价格预计上涨120-170%，高层数3D NAND排挤成熟制程产能，MLC NAND供给极度短缺迫使工控/车用/网通客户改用SLC",
        "source": "WebSearch 自动扫描 - TrendForce 2026-07-13",
    },
    {
        "category": "LCD面板",
        "description": "2026年7月全球液晶电视面板价格全线下跌，32/43/55/65/75寸预计8月再跌1-8美元，主力面板厂稼动率维持90%以上，以价换量",
        "source": "WebSearch 自动扫描 - 洛图科技 2026-07-29",
    },
    {
        "category": "NAND Flash",
        "description": "2026年7月TrendForce报告显示消费级NAND Flash需求疲弱买方抵制，3Q26合约价涨幅收敛进入高原期，2H27供给紧张情形有望改善",
        "source": "WebSearch 自动扫描 - TrendForce 2026-07-21",
    },
    {
        "category": "晶圆代工",
        "description": "2026年7月19日台积电宣布在美国亚利桑那州追加1000亿美元投资，使当地总投资规模达2650亿美元，将兴建2nm及以下制程晶圆厂与先进封装厂",
        "source": "WebSearch 自动扫描 - SEMI/财联社 2026-07-20",
    },
]

# 去重：跳过已入库事件
new_events = []
for ev in candidate_events:
    key = ev['description'][:30]
    if key in existing_keys:
        print(f"  跳过(已入库): {ev['description'][:40]}...")
        continue
    existing_keys.add(key)
    new_events.append(ev)

print(f"\n去重后待入库事件: {len(new_events)} 个")

# ============================================================
# 步骤 4: 逐条入库
# ============================================================
pipeline = AutoCyclePipeline(KG_PATH)

added = []
red_alerts = []
orange_count = 0
green_count = 0
failed = []

for ev in new_events:
    try:
        result = pipeline.auto_analyze_new_event(
            event_description=ev['description'],
            category=ev['category'],
            source=ev['source'],
        )
        added.append({
            'event_id': result['event_id'],
            'case_id': result['case_id'],
            'category': ev['category'],
            'cycle_type': result['cycle_type'],
            'warning_template': result['warning_template'],
            'description': ev['description'],
        })
        # 统计预警等级
        has_red = False
        for w in result['warning_template']:
            level = w.get('level', '')
            if '🔴' in level:
                has_red = True
            elif '🟠' in level:
                orange_count += 1
            elif '🟢' in level:
                green_count += 1
        if has_red:
            red_alerts.append(added[-1])
        print(f"  ✅ {result['event_id']} {ev['category']} -> {result['cycle_type']}, red={has_red}")
    except Exception as e:
        print(f"  ❌ 入库失败: {ev['description'][:40]}... 错误: {e}")
        failed.append({'event': ev, 'error': str(e)})

# ============================================================
# 步骤 5: 红色预警处理
# ============================================================
alerts_log_path = 'reports/alerts.log'
os.makedirs('reports', exist_ok=True)

def is_red_warning(w):
    return '🔴' in w.get('level', '')

lark_payloads = []
for ra in red_alerts:
    first_red = next((w for w in ra['warning_template'] if is_red_warning(w)), None)
    if not first_red:
        continue
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = (
        f"[{ts}] [{ra['category']}] [{ra['cycle_type']}] "
        f"[{ra['description'][:80]}] "
        f"[{first_red.get('signal', '')}] [{first_red.get('prediction', '')}]\n"
    )
    with open(alerts_log_path, 'a', encoding='utf-8') as f:
        f.write(log_line)
    print(f"  🚨 红色预警已记录到 alerts.log: {ra['event_id']}")
    lark_payloads.append({
        'event_id': ra['event_id'],
        'category': ra['category'],
        'cycle_type': ra['cycle_type'],
        'signal': first_red.get('signal', ''),
        'prediction': first_red.get('prediction', ''),
        'description': ra['description'],
    })

# 保存处理结果到 /workspace，供下一步使用
out = {
    'candidates_total': len(candidate_events),
    'new_events': len(new_events),
    'added': added,
    'red_alerts': red_alerts,
    'orange_count': orange_count,
    'green_count': green_count,
    'failed': failed,
    'lark_payloads': lark_payloads,
}
out_path = '/workspace/scan_results.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"\n中间结果已保存到 {out_path}")
print(f"新增入库: {len(added)} | 红色预警: {len(red_alerts)} | 橙色预警条目: {orange_count} | 绿色预警条目: {green_count} | 失败: {len(failed)}")
