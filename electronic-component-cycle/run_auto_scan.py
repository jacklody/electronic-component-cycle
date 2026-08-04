#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动扫描脚本：执行过去7天行情事件扫描、入库、预警和日志记录
"""

import sys
import os
import json
from datetime import datetime

# 确保 scripts 在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from auto_cycle_pipeline import AutoCyclePipeline

# ========== 配置 ==========
KG_PATH = "graphiti/cycle_knowledge_graph.json"
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# ========== 1. 提取已入库事件去重 key ==========
with open(KG_PATH, 'r', encoding='utf-8') as f:
    kg = json.load(f)

existing_descriptions = set()
for evt in kg.get("events", []):
    existing_descriptions.add(evt["description"][:30])

print(f"已入库事件数：{len(kg.get('events', []))}")
print(f"去重 key 集合大小：{len(existing_descriptions)}")

# ========== 2. WebSearch 结果整理（预整理好的摘要） ==========
# 注意：实际 WebSearch 已由 agent 在外部完成，这里是整理后的搜索摘要
search_results = [
    {
        "category": "MLCC",
        "description": "2026年7月底三星电机宣布MLCC相关产品出货价格自8月1日起统一上调30%，日本太阳诱电也通知自9月1日起对部分产品调价。AI算力升级驱动电容需求升级，MLCC是AI服务器电容升级核心。",
        "source": "证券日报/东吴证券"
    },
    {
        "category": "MLCC",
        "description": "截至2026年7月，村田1微法及以上的高端MLCC交货周期拉长至30周，相比6月再度增加6周，相当于客户下单后要等待大半年才能拿货。",
        "source": "市场研究公司/今日头条"
    },
    {
        "category": "MLCC",
        "description": "2026年7月1日全球被动元件龙头国巨宣布对全系列电容产品涨价，涵盖MLCC、铝电解电容、钽质电容等。高端高容型号涨幅最大，行业正式迈入由算力需求驱动的新一轮景气周期。",
        "source": "新浪财经"
    },
    {
        "category": "MLCC",
        "description": "风华高科8月起多款高压、高容MLCC涨价15%-100%，直接抬升毛利率。国内MLCC绝对龙头，专门划分产线生产AI、车规高端型号，稼动率常年90%左右。",
        "source": "东方财富"
    },
    {
        "category": "DRAM",
        "description": "2026年7月初三星电子正式向客户发出三季度DRAM均价上调20%的书面通知。HBM产能挤占导致通用DRAM产能不足，且原材料成本上升。",
        "source": "韩媒/第一财经"
    },
    {
        "category": "DRAM",
        "description": "瑞银2026年7月发布报告，将第三季度DDR合约价格环比涨幅从17%大幅上调至32%，第四季度从12%上调至18%。2027年供需缺口将比2026年进一步扩大70%。",
        "source": "瑞银UBS"
    },
    {
        "category": "DRAM",
        "description": "2026年7月24日媒体报道，服务器DRAM现货价格剧烈波动，64GB服务器DRAM现货报价突破3100美元，较6月底合约价1380美元高出约146%。",
        "source": "观点地产网/Meritz Securities"
    },
    {
        "category": "DRAM",
        "description": "TrendForce统计2026年7月PC DRAM模块合同价格环比上涨13%至17%，DDR4和DDR5芯片上涨12%至14%。但涨幅较6月大幅收窄，部分紧急订单逐步消化。",
        "source": "TrendForce"
    },
    {
        "category": "HBM",
        "description": "2026年7月24日英伟达宣布与SK集团签署总规模超5000亿美元的多年期战略合作意向书，SK海力士与英伟达签订长期AI内存合作协议，锁定下一代HBM稳定供应。",
        "source": "搜狐/呱呱唠时事"
    },
    {
        "category": "HBM",
        "description": "2026年HBM高带宽内存全年产能缺口达50%至60%，订单排至2027年一季度。SK海力士已拿下英伟达HBM4超过三分之二的供应订单。",
        "source": "SemiAnalysis/各研报"
    },
    {
        "category": "存储芯片",
        "description": "2026年7月中旬消费级内存条终端价格出现显著回落，较年初高点平均下降约30%，但同比仍高出约5倍。国产存储产能释放打破海外垄断定价。",
        "source": "新浪财经/代码演进窗"
    },
    {
        "category": "NAND Flash",
        "description": "TrendForce最新调查2026年7月由于供应紧张，成熟的SLC NAND工艺价格激增35%至50%。AI挤压成熟工艺产能，汽车、工控及网络设备需求强劲。",
        "source": "TrendForce/EEPW"
    },
    {
        "category": "LCD面板",
        "description": "2026年7月全球LCD TV面板价格向下温和调整。群智咨询预计32英寸均价下降1美元，50英寸下降2美元，55英寸下降2美元，大尺寸方面65/75英寸下降3美元。",
        "source": "群智咨询/证券时报"
    },
    {
        "category": "LCD面板",
        "description": "2026年7月京东方晶芯、强力巨彩、大华等9家企业再发布调价通知，受上游供应链成本持续上涨影响，覆盖芯片、封装灯珠、驱动IC、PCB到终端屏体全环节。",
        "source": "行家talk"
    },
    {
        "category": "功率器件",
        "description": "2026年AI服务器供应结构性短缺，关键MOSFET和功率器件来自英飞凌、Vishay等供应商的交期已 routinely 超过52周，成为AI供应链最脆弱的子环节。",
        "source": "SpecForge/PPSI"
    },
]

# 去重过滤
unique_results = []
for r in search_results:
    key = r["description"][:30]
    if key not in existing_descriptions:
        unique_results.append(r)
        existing_descriptions.add(key)

print(f"\nWebSearch 返回结果数（去重前）：{len(search_results)}")
print(f"去重后新增事件数：{len(unique_results)}")

# ========== 3. 调用 Pipeline 分析 ==========
pipeline = AutoCyclePipeline(KG_PATH)

added_events = []
red_alerts = []
orange_alerts = 0
green_alerts = 0
failed_events = 0

for r in unique_results:
    try:
        result = pipeline.auto_analyze_new_event(
            event_description=r["description"],
            category=r["category"],
            source=f"WebSearch 自动扫描 ({r['source']})"
        )
        added_events.append({
            "event_id": result["event_id"],
            "case_id": result["case_id"],
            "category": r["category"],
            "cycle_type": result["cycle_type"],
            "description": r["description"],
            "warning_template": result["warning_template"]
        })
        # 统计预警
        has_red = False
        for wt in result.get("warning_template", []):
            level = wt.get("level", "")
            if "🔴红色预警" in level:
                has_red = True
            elif "🟠橙色预警" in level:
                orange_alerts += 1
            elif "🟢绿色预警" in level:
                green_alerts += 1
        if has_red:
            red_alerts.append({
                "event_id": result["event_id"],
                "category": r["category"],
                "cycle_type": result["cycle_type"],
                "description": r["description"],
                "warning_template": result["warning_template"]
            })
    except Exception as e:
        print(f"  ❌ 分析失败：{r['description'][:50]}... 错误：{e}")
        failed_events += 1

print(f"\n入库成功数：{len(added_events)}")
print(f"红色预警数：{len(red_alerts)}")
print(f"橙色预警数：{orange_alerts}")
print(f"绿色预警数：{green_alerts}")

# ========== 4. 处理红色预警：写 alerts.log 并尝试发飞书 ==========
now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
alerts_log_path = os.path.join(REPORTS_DIR, "alerts.log")

lark_success = False
lark_error = None

for alert in red_alerts:
    # 取第一个红色预警的 signal/prediction
    red_signal = ""
    red_prediction = ""
    for wt in alert["warning_template"]:
        if "🔴红色预警" in wt.get("level", ""):
            red_signal = wt.get("signal", "")
            red_prediction = wt.get("prediction", "")
            break

    log_line = (
        f"[{now_str}] [{alert['category']}] [{alert['cycle_type']}] "
        f"[{alert['description'][:80]}] [{red_signal}] [{red_prediction}]\n"
    )
    with open(alerts_log_path, 'a', encoding='utf-8') as f:
        f.write(log_line)
    print(f"  🚨 红色预警已记录：{alert['event_id']} [{alert['category']}]")

    # 尝试发送飞书消息（使用 lark-im skill，这里通过子进程调用 lark-cli）
    if not lark_success:
        # 实际上由于在当前脚本中无法直接调用 skill，我们在这里标记为待处理，由外部 agent 发送
        pass

# ========== 5. 写入 daily_scan 摘要日志 ==========
scan_hour = datetime.now().strftime("%H")
# 取整点到 08 或 20
target_hour = "08" if int(scan_hour) < 12 else "20"
daily_log_name = f"daily_scan_{datetime.now().strftime('%Y%m%d')}_{target_hour}.log"
daily_log_path = os.path.join(REPORTS_DIR, daily_log_name)

# 运行完整校验
validation_result = pipeline.run_full_validation()

log_content = f"""
========== 电子元器件周期智能体 — 自动扫描摘要 ==========
扫描时间：{now_str}
查询Query数：10（MLCC×2 + DRAM×2 + HBM×2 + 存储芯片×1 + NAND×1 + LCD面板×2 + 功率器件×1）
WebSearch返回结果数：{len(search_results)}
去重后新增事件数：{len(unique_results)}
入库成功数：{len(added_events)}
入库失败数：{failed_events}
触发红色预警的事件列表：
"""

if red_alerts:
    for alert in red_alerts:
        log_content += f"  - {alert['event_id']} [{alert['category']}] {alert['cycle_type']}：{alert['description'][:60]}...\n"
else:
    log_content += "  （无）\n"

log_content += f"""
橙色预警数量：{orange_alerts}
绿色预警数量：{green_alerts}

========== 完整校验结果 ==========
校验时间：{validation_result.get('validation_time', now_str)}
总因果关系数：{validation_result.get('total_relations', 'N/A')}
有效因果关系数：{validation_result.get('valid_relations', 'N/A')}
无效因果关系数：{validation_result.get('invalid_relations', 'N/A')}
校验是否通过：{validation_result.get('validation_passed', 'N/A')}
"""

if validation_result.get('invalid_details'):
    log_content += "无效关系详情：\n"
    for inv in validation_result['invalid_details']:
        log_content += f"  - {inv.get('relation_id', '')}: {inv.get('description', '')}\n"

with open(daily_log_path, 'w', encoding='utf-8') as f:
    f.write(log_content)

print(f"\n📄 扫描摘要已写入：{daily_log_path}")
print(f"📄 预警日志已写入：{alerts_log_path}")

# 输出摘要供外部 agent 使用
print("\n========== SCAN_SUMMARY ==========")
print(json.dumps({
    "scan_time": now_str,
    "query_count": 10,
    "search_results": len(search_results),
    "unique_new_events": len(unique_results),
    "added_success": len(added_events),
    "red_alerts": len(red_alerts),
    "orange_alerts": orange_alerts,
    "green_alerts": green_alerts,
    "daily_log": daily_log_path,
    "alerts_log": alerts_log_path,
    "red_alert_details": [
        {
            "event_id": a["event_id"],
            "category": a["category"],
            "cycle_type": a["cycle_type"],
            "description": a["description"]
        } for a in red_alerts
    ]
}, ensure_ascii=False))
