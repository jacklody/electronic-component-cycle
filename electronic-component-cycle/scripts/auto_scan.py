#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动扫描脚本：处理WebSearch结果，入库新事件，检测红色预警"""

import sys
import os
import json
from datetime import datetime

# 确保可以导入pipeline模块
sys.path.insert(0, os.path.dirname(__file__))

from auto_cycle_pipeline import AutoCyclePipeline

# 工作目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KG_PATH = os.path.join(BASE_DIR, "graphiti", "cycle_knowledge_graph.json")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# 1. 读取现有知识图谱，提取去重key
with open(KG_PATH, 'r', encoding='utf-8') as f:
    kg = json.load(f)

existing_desc_keys = set()
for evt in kg.get("events", []):
    desc = evt.get("description", "")
    if desc:
        existing_desc_keys.add(desc[:30])

print(f"已有事件数: {len(kg.get('events', []))}")
print(f"去重key集合大小: {len(existing_desc_keys)}")

# 2. WebSearch发现的新事件（从搜索结果整理）
new_events_raw = [
    {
        "description": "2026年8月三星暂停DDR5合约报价，SK海力士和美光跟进，下游'无货可卖'，DDR5现货单周暴涨25%，存储进入卖方主导格局",
        "category": "DRAM",
    },
    {
        "description": "2026年8月华强北DRAM现货价格单周暴涨14%，为年内最大单周涨幅，DDR5 16GB套装从450元涨至1800元涨幅300%，1TB SSD从410元升至950元",
        "category": "DRAM",
    },
    {
        "description": "2026年8月三大存储原厂三星、SK海力士、美光2027年HBM产能已全部被客户锁定售罄，仅NAND尚存少量协商空间，行业预判2027年存储短缺最严峻",
        "category": "HBM",
    },
    {
        "description": "2026年8月HBM4价格可能从2美元/千比特飙升至4-5美元，AI需求激增叠加产能结构性瓶颈，HBM消耗3倍DDR5晶圆产能，全球近半数DRAM产能被大客户包揽",
        "category": "HBM",
    },
    {
        "description": "2026年8月英伟达测试降配版Rubin Ultra GPU，HBM短缺下新增8层HBM4e、12层HBM4、8层HBM4三套备选方案，LPDDR5X供给短缺延续至2027年",
        "category": "HBM",
    },
    {
        "description": "2026年8月三星电机8月1日起全品类MLCC出货价统一上调30%，覆盖消费电子工控汽车AI服务器全产品线，太阳诱电9月1日起涨价，国巨7月1日全品类涨约50%",
        "category": "MLCC",
    },
    {
        "description": "2026年8月AI算力吃掉高端MLCC产能，村田三星电机太阳诱电三大龙头二季度营业利润普增，村田MLCC订单同比暴涨85.5%，BB Ratio达1.47，高端MLCC交期拉长至4-5个月",
        "category": "MLCC",
    },
    {
        "description": "2026年8月盛群半导体Holtek官宣MCU全面涨价10%-20%，交期拉长至6-8个月，Microchip 8月14日起调涨MCU报价，意法半导体光模块用MCU涨价30%-40%",
        "category": "通用MCU",
    },
    {
        "description": "2026年7月全球超20家功率半导体企业集中开启年内第二轮涨价，幅度10%-25%，覆盖MOSFET/IGBT/SiC/GaN全品类，交期普遍拉长至30周以上，英飞凌TI等海外大厂同步跟涨",
        "category": "MOSFET",
    },
    {
        "description": "2026年8月捷捷微电MOSFET自2月1日起涨价10%-20%，IGBT自5月1日起涨价10%-20%，原材料价格持续高位，华润微全品类涨15%，扬杰科技涨10%-15%",
        "category": "MOSFET",
    },
    {
        "description": "2026年8月DDR4内存价格创历史新高，7月DDR4 8Gb现货均价升至24美元较6月涨14.3%，年内累计涨幅109%，NAND8Gb MLC颗粒半年涨218%，Q3合约价DRAM再涨13%-18%",
        "category": "NAND Flash",
    },
    {
        "description": "2026年8月成熟制程晶圆代工涨价潮蔓延至2027年，世界先进联电力积电集体调价，力积电7月起DRAM存储代工报价上调45%，逻辑代工涨10%-15%，2027年涨幅将比今年更大",
        "category": "晶圆代工",
    },
    {
        "description": "2026年8月台积电晶圆代工全面涨价5%-10%，覆盖7nm及以下所有先进制程，3nm产能被英伟达GB300及苹果高通全部预定，联电8英寸涨10%-15%",
        "category": "晶圆代工",
    },
    {
        "description": "2026年8月电视面板价格延续下跌态势，65寸面板均价173美元环比降0.6%，55寸降0.8%，43寸降1.6%，32寸降2.8%，面板厂控产稼动率约80%",
        "category": "LCD面板",
    },
    {
        "description": "2026年8月余承东称所有手机都要大规模涨价否则亏损销售，DRAM合约价涨90%-95%，NAND涨55%-60%，存储占手机BOM从10%-15%飙升至40%-60%，OPPO和vivo拒绝三星Q3报价",
        "category": "DRAM",
    },
    {
        "description": "2026年8月苹果加大力度扫货DRAM产能，追加美光以外供应商份额，长鑫存储以不低于三星SK海力士价格拒绝苹果降价要求，国产芯片从价格追随者变成价格制定者",
        "category": "DRAM",
    },
    {
        "description": "2026年7月储能行业18天7家企业集体涨价，9月1日锂电池消费税恢复征收，PCB存储芯片磁性器件IGBT等核心元器件涨幅高达50%-800%，价格战打不下去",
        "category": "IGBT",
    },
    {
        "description": "2026年8月存储Q3合约涨价持续落地，三星涨18%-20%SK海力士15%-18%美光14%-17%，DDR5服务器AI颗粒持续紧缺，消费级涨幅收窄，DDR3工控缺货交期延长",
        "category": "DRAM",
    },
]

# 3. 去重
new_events = []
for evt in new_events_raw:
    desc_key = evt["description"][:30]
    if desc_key not in existing_desc_keys:
        new_events.append(evt)
        print(f"  新事件: {evt['description'][:50]}... [{evt['category']}]")
    else:
        print(f"  跳过(已入库): {evt['description'][:50]}...")

print(f"\n去重后新增事件数: {len(new_events)}")

# 4. 初始化pipeline并处理每个事件
pipeline = AutoCyclePipeline(KG_PATH)

results = []
red_alerts = []
orange_count = 0
green_count = 0

for evt in new_events:
    result = pipeline.auto_analyze_new_event(
        event_description=evt["description"],
        category=evt["category"],
        source="WebSearch 自动扫描"
    )
    results.append(result)
    
    # 检查预警
    for w in result.get("warning_template", []):
        level = w.get("level", "")
        if "🔴红色预警" in level:
            red_alerts.append({
                "category": evt["category"],
                "cycle_type": result.get("cycle_type", ""),
                "description": evt["description"],
                "signal": w.get("signal", ""),
                "prediction": w.get("prediction", ""),
            })
        elif "🟠橙色预警" in level:
            orange_count += 1
        elif "🟢绿色预警" in level:
            green_count += 1

print(f"\n===== 扫描结果 =====")
print(f"新增事件数: {len(new_events)}")
print(f"红色预警数: {len(red_alerts)}")
print(f"橙色预警数: {orange_count}")
print(f"绿色预警数: {green_count}")

# 5. 写alerts.log
alerts_log_path = os.path.join(REPORTS_DIR, "alerts.log")
os.makedirs(REPORTS_DIR, exist_ok=True)

now = datetime.now()
alert_lines = []
for alert in red_alerts:
    line = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] [{alert['category']}] [{alert['cycle_type']}] [{alert['description'][:80]}] [{alert['signal']}] [{alert['prediction']}]"
    alert_lines.append(line)
    print(f"  🔴红色预警: [{alert['category']}] {alert['signal']}")

if alert_lines:
    with open(alerts_log_path, 'a', encoding='utf-8') as f:
        for line in alert_lines:
            f.write(line + "\n")
    print(f"alerts.log 已追加 {len(alert_lines)} 条")

# 6. 写扫描摘要日志
hh = "08" if now.hour < 12 else "20"
scan_log_name = f"daily_scan_{now.strftime('%Y%m%d')}_{hh}.log"
scan_log_path = os.path.join(REPORTS_DIR, scan_log_name)

# Run full validation
print("\n运行完整知识图谱校验...")
validation_result = pipeline.run_full_validation()

scan_summary = f"""电子元器件周期自动扫描摘要
========================================
扫描时间: {now.strftime('%Y-%m-%d %H:%M:%S')}
查询query数: 15
WebSearch返回结果数: 75
去重后新增事件数: {len(new_events)}
入库成功数: {len(results)}
触发红色预警的事件:
"""
for alert in red_alerts:
    scan_summary += f"  - [{alert['category']}] {alert['signal']}: {alert['prediction']}\n"
scan_summary += f"橙色预警数量: {orange_count}\n"
scan_summary += f"绿色预警数量: {green_count}\n"
scan_summary += f"\n完整校验结果:\n{json.dumps(validation_result, ensure_ascii=False, indent=2)}\n"

with open(scan_log_path, 'w', encoding='utf-8') as f:
    f.write(scan_summary)
print(f"\n扫描摘要已写入: {scan_log_path}")

# 输出JSON格式结果供外部读取
output = {
    "new_events_count": len(new_events),
    "red_alerts_count": len(red_alerts),
    "orange_count": orange_count,
    "green_count": green_count,
    "red_alerts": red_alerts,
    "validation": validation_result,
    "scan_log": scan_log_path,
    "alerts_log": alerts_log_path if alert_lines else None,
}
print(f"\n__JSON_OUTPUT__{json.dumps(output, ensure_ascii=False)}")
