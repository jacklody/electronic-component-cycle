#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动扫描过去7天行情事件，迭代事件库，触发红色预警通知"""
import os
import sys
import json
import re
from datetime import datetime

BASE = "/workspace/electronic-component-cycle"
SCRIPTS = os.path.join(BASE, "scripts")
sys.path.insert(0, SCRIPTS)

# 1. 修复 cycle_analyzer.py 的嵌套双引号语法错误（内存补丁，不修改磁盘）
ca_path = os.path.join(SCRIPTS, "cycle_analyzer.py")
with open(ca_path, "r", encoding="utf-8") as f:
    src = f.read()
bad = '"key_lesson": "不要相信"游资炒作"传言，核心是供给收缩"'
good = '"key_lesson": \'不要相信"游资炒作"传言，核心是供给收缩\''
src_fixed = src.replace(bad, good)
# 修复 _parse_category 对 None 的处理
src_fixed = src_fixed.replace(
    "        for k, v in category_map.items():\n            if k in obj:\n                return v",
    "        if obj is None:\n            return '全品类'\n        for k, v in category_map.items():\n            if k in obj:\n                return v",
)

# 用 fixed 源码加载该模块
import importlib.util
spec = importlib.util.spec_from_loader("cycle_analyzer", loader=None)
ca_mod = importlib.util.module_from_spec(spec)
ca_mod.__file__ = ca_path
exec(compile(src_fixed, ca_path, "exec"), ca_mod.__dict__)
sys.modules["cycle_analyzer"] = ca_mod

# 2. 修复 auto_cycle_pipeline.py 的 _get_next_id 调用 bug（内存补丁）
acp_path = os.path.join(SCRIPTS, "auto_cycle_pipeline.py")
with open(acp_path, "r", encoding="utf-8") as f:
    acp_src = f.read()
acp_src = acp_src.replace(
    'self.next_case_id = self._get_next_id("CASE", prefix="CASE")',
    'self.next_case_id = self._get_next_id("CASE", case_prefix=True)',
)
acp_spec = importlib.util.spec_from_loader("auto_cycle_pipeline", loader=None)
acp_mod = importlib.util.module_from_spec(acp_spec)
acp_mod.__file__ = acp_path
# cycle_analyzer 已注入 sys.modules，可直接 exec
exec(compile(acp_src, acp_path, "exec"), acp_mod.__dict__)
sys.modules["auto_cycle_pipeline"] = acp_mod
from auto_cycle_pipeline import AutoCyclePipeline

KG_PATH = os.path.join(BASE, "graphiti", "cycle_knowledge_graph.json")
REPORTS = os.path.join(BASE, "reports")
os.makedirs(REPORTS, exist_ok=True)

# 3. 初始化 pipeline 并提取已入库事件去重 key
pipeline = AutoCyclePipeline(KG_PATH)
existing_keys = set()
for evt in pipeline.updater.kg.get("events", []):
    existing_keys.add(evt.get("description", "")[:30])
print(f"\n📦 已入库事件 {len(pipeline.updater.kg.get('events', []))} 个，去重 key {len(existing_keys)} 个")

# 4. WebSearch 过去7天获取的新事件（2026-07 末）
candidates = [
    {
        "category": "DRAM",
        "source": "新浪财经、TrendForce集邦咨询",
        "description": (
            "2026Q3 三星电子计划将三季度通用DRAM平均售价环比提高20%，连续第三个季度大幅提价，"
            "一季度涨90%、二季度涨50%-60%。AI基础设施建设催生结构性存储短缺，"
            "DDR5 16GB合约价从2025年5月4.8美元涨至2026年5月37.5美元，一年涨681%。"
            "渠道库存仅4周，远低于8-12周健康水平。三星、SK海力士、美光三大巨头将70%-80%先进产能转向HBM，"
            "消费级DRAM产能被压缩。TrendForce预计Q3 DRAM合约价涨幅13%-18%。"
        ),
    },
    {
        "category": "HBM",
        "source": "证券时报、DigiTimes、Omdia",
        "description": (
            "2026Q3 三星率先实现HBM4规模化量产，良率接近70%；SK海力士占全球HBM4市场54%份额，"
            "承接英伟达60%-70%供应。HBM3e 12Hi单颗价格从2025年初80美元涨至2026Q2的700美元以上，涨近8倍。"
            "2026年全球HBM产量同比增长103%仍供不应求，HBM4价格从下半年约2美元/千比特涨至4-5美元。"
            "SK海力士CEO郭鲁正预警：2027年将成为存储芯片行业史上供应最紧张的一年，缺口持续至2030年后。"
            "三大厂商与AI客户签订3-5年长期协议锁定供应。"
        ),
    },
    {
        "category": "MLCC",
        "source": "第一财经、东方财富、雪球、中国电子元件行业协会",
        "description": (
            "2026Q3 MLCC涨价进入第三轮：村田7月1日第三轮提价10%-40%（仅限AI服务器、车规高容型号），"
            "国巨7月1日今年第二次正式涨价50%-80%，部分品类达120%。三星电机连续两月签署AI服务器MLCC长协，"
            "年内长协总额7500亿韩元（5.1亿美元），覆盖2027全年。高容MLCC现货年初至今涨5-8倍，"
            "部分料号预计涨至10-15倍。原厂交期拉长至4-6个月，订单出货率仅10%-20%。"
            "AI服务器MLCC用量是传统服务器8-13倍，单机价值量提升182%。"
        ),
    },
    {
        "category": "MOSFET",
        "source": "新浪财经、环球网财经、网通社",
        "description": (
            "2026Q3 功率半导体年内第二轮集中涨价：英飞凌7月1日年内二次提价，AI服务器电源芯片、"
            "车规IGBT、高压MOSFET涨10%-20%；德州仪器PMIC/MOSFET涨15%-25%；"
            "士兰微7月1日全线涨价15%起；斯达半导IGBT/SiC MOSFET涨15%起；扬杰科技全系列涨10%-15%；"
            "芯联集成Q3涨15%-25%。单台AI服务器功率半导体用量是传统服务器3-5倍，"
            "8英寸成熟制程产能被AI挤占，低压MOSFET交期拉长至40周以上，部分超52周。"
            "英飞凌AI电源营收指引从FY2025的7亿欧元增至FY2027的25亿欧元。"
        ),
    },
    {
        "category": "晶圆代工",
        "source": "财联社、ICNET、经济日报",
        "description": (
            "2026Q3 台积电计划2027年上调先进及成熟制程代工价5%-10%，HPC新增订单再加收10%-15%溢价，"
            "部分先进制程总涨幅超10%。7nm及更先进制程贡献约77%营收，成熟制程（12/16/28nm）占23%。"
            "三星4nm/5nm先进节点报价上调15%。联电、力积电7月起8英寸成熟代工涨价10%-15%，"
            "12英寸通用晶圆上调5%-10%。全球8英寸晶圆代工平均利用率攀升至85%-90%，"
            "先进制程产能被AI大厂长协锁单排产至2027年。台积电资本支出上调至640亿美元。"
        ),
    },
    {
        "category": "NAND Flash",
        "source": "TrendForce集邦、高盛、野村证券",
        "description": (
            "2026Q3 NAND Flash紧缺延续至2027上半年：TrendForce数据显示2026年NAND供需位元差距达-4%至-5%。"
            "铠侠2026年4-6月季度位元价格环比+70%（上调自+65%），7-9月预计+25%（上调自+20%）。"
            "高盛大幅上调铠侠目标价24.7%至11.6万日元，预计2026年ASP同比增长4.5倍，2027年再增38%。"
            "ADATA 4-6月SSD销售环比增87%。新NAND晶圆厂供应增量要到2028年才明显释放。"
            "三星启动第十代V-NAND量产供应英伟达，英伟达CMX平台2026年NAND需求达3500万TB。"
        ),
    },
]

# 5. 去重 + 入库 + 红色预警检测
scan_results = []
red_alerts = []
new_event_count = 0

print("\n" + "=" * 70)
print("开始去重与入库分析")
print("=" * 70)

for idx, cand in enumerate(candidates, 1):
    desc = cand["description"]
    key = desc[:30]
    print(f"\n[{idx}/{len(candidates)}] 品类={cand['category']}  去重key前30字={key}")
    if key in existing_keys:
        print(f"  ⏭️  跳过：已入库（前30字符命中）")
        scan_results.append({
            "category": cand["category"], "status": "skipped_duplicate",
            "desc_head": key,
        })
        continue

    # 调用 pipeline.auto_analyze_new_event 入库
    result = pipeline.auto_analyze_new_event(
        event_description=desc,
        category=cand["category"],
        source=cand["source"],
    )
    new_event_count += 1
    existing_keys.add(key)  # 防止本批次重复

    # 判断红色预警
    wt = result.get("warning_template", []) or []
    red_items = [w for w in wt if "🔴红色预警" in str(w.get("level", ""))]
    is_red = len(red_items) > 0

    scan_results.append({
        "category": cand["category"],
        "status": "added",
        "event_id": result.get("event_id"),
        "case_id": result.get("case_id"),
        "cycle_type": result.get("cycle_type"),
        "root_cause": result.get("cause_analysis", {}).get("root_cause", []),
        "downturn_cause": result.get("cause_analysis", {}).get("downturn_cause", []),
        "catalysts": result.get("cause_analysis", {}).get("catalysts", []),
        "amplifiers": result.get("cause_analysis", {}).get("amplifiers", []),
        "false_narratives": result.get("cause_analysis", {}).get("false_narratives", []),
        "warning_template": wt,
        "is_red_alert": is_red,
        "red_items": red_items,
        "desc_head": key,
    })

    if is_red:
        red_alerts.append({
            "category": cand["category"],
            "event_id": result.get("event_id"),
            "cycle_type": result.get("cycle_type"),
            "red_items": red_items,
            "desc_head": key,
            "full_desc": desc,
        })
        print(f"  🚨 触发红色预警！{len(red_items)}条红色预警规则")
        for r in red_items:
            print(f"     - {r.get('signal')}")
            print(f"       预测：{r.get('prediction')}")
    else:
        print(f"  ✅ 已入库 {result.get('event_id')}，未触发红色预警")

# 6. 调用 run_full_validation
print("\n" + "=" * 70)
print("运行完整知识图谱校验")
print("=" * 70)
validation = pipeline.run_full_validation()

# 7. 写 alerts.log（追加红色预警）
alerts_log = os.path.join(REPORTS, "alerts.log")
scan_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
if red_alerts:
    with open(alerts_log, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*70}\n")
        f.write(f"扫描时间：{scan_ts}\n")
        f.write(f"红色预警事件数：{len(red_alerts)}\n")
        f.write(f"{'='*70}\n")
        for ra in red_alerts:
            f.write(f"\n[事件ID] {ra['event_id']}  品类={ra['category']}  周期类型={ra['cycle_type']}\n")
            f.write(f"[事件描述] {ra['full_desc']}\n")
            for r in ra["red_items"]:
                f.write(f"[红色预警信号] {r.get('signal')}\n")
                f.write(f"[预警预测] {r.get('prediction')}\n")
            f.write("-" * 70 + "\n")
    print(f"\n📝 已追加写入 alerts.log：{len(red_alerts)} 条红色预警")

# 8. 写 daily_scan 日志
scan_date = datetime.now().strftime("%Y%m%d_%H%M")
daily_log = os.path.join(REPORTS, f"daily_scan_{scan_date}.log")
with open(daily_log, "w", encoding="utf-8") as f:
    f.write("电子元器件周期智能体 - 自动扫描摘要日志\n")
    f.write(f"扫描时间：{scan_ts}\n")
    f.write(f"扫描范围：过去7天行情事件\n")
    f.write(f"覆盖品类：DRAM / HBM / MLCC / MOSFET / 晶圆代工 / NAND Flash\n")
    f.write("=" * 70 + "\n\n")
    f.write(f"【扫描统计】\n")
    f.write(f"  候选事件数：{len(candidates)}\n")
    f.write(f"  新增入库事件数：{new_event_count}\n")
    f.write(f"  跳过(去重)事件数：{len(candidates) - new_event_count}\n")
    f.write(f"  触发红色预警事件数：{len(red_alerts)}\n\n")
    f.write("【新增事件明细】\n")
    for sr in scan_results:
        if sr["status"] == "added":
            f.write(f"\n  事件ID：{sr['event_id']}  品类：{sr['category']}  周期类型：{sr['cycle_type']}\n")
            f.write(f"  描述前30字：{sr['desc_head']}\n")
            f.write(f"  根因：{sr['root_cause']}  下跌根因：{sr['downturn_cause']}\n")
            f.write(f"  催化剂：{sr['catalysts']}  放大器：{sr['amplifiers']}\n")
            f.write(f"  排除传言：{sr['false_narratives']}\n")
            f.write(f"  红色预警：{'是' if sr['is_red_alert'] else '否'}\n")
            if sr["is_red_alert"]:
                for r in sr["red_items"]:
                    f.write(f"    - 信号：{r.get('signal')}\n")
                    f.write(f"      预测：{r.get('prediction')}\n")
    f.write("\n" + "=" * 70 + "\n")
    f.write("【知识图谱校验结果】\n")
    f.write(f"  总事件数：{validation.get('total_relations', 'N/A')}\n")
    f.write(f"  有效因果关系：{validation.get('valid_relations', 'N/A')}/{validation.get('total_relations', 'N/A')}\n")
    f.write(f"  无效因果关系：{validation.get('invalid_relations', 'N/A')}\n")
    f.write(f"  校验通过：{validation.get('validation_passed', 'N/A')}\n")
    f.write("=" * 70 + "\n")
    f.write("【飞书通知】\n")
    f.write(f"  红色预警飞书消息：{'待发送' if red_alerts else '无红色预警，无需发送'}\n")

print(f"\n📋 已写入 daily_scan 日志：{daily_log}")

# 9. 输出结构化结果供后续 Lark 通知使用
summary = {
    "scan_time": scan_ts,
    "candidates": len(candidates),
    "new_events": new_event_count,
    "skipped_duplicates": len(candidates) - new_event_count,
    "red_alerts": len(red_alerts),
    "red_alert_details": red_alerts,
    "validation": {
        "total_relations": validation.get("total_relations"),
        "valid_relations": validation.get("valid_relations"),
        "invalid_relations": validation.get("invalid_relations"),
        "validation_passed": validation.get("validation_passed"),
    },
    "alerts_log": alerts_log if red_alerts else None,
    "daily_log": daily_log,
}

print("\n" + "=" * 70)
print("扫描完成 - 汇总")
print("=" * 70)
print(json.dumps(summary, ensure_ascii=False, indent=2))
