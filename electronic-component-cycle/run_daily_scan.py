#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动扫描脚本 - 20260802
处理新事件、去重、分析、红警检测、校验
"""

import sys
import os
import json
from datetime import datetime

# 1. Add scripts/ to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))

# 2. Import AutoCyclePipeline
from auto_cycle_pipeline import AutoCyclePipeline

# 工作目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KG_PATH = os.path.join(BASE_DIR, "graphiti", "cycle_knowledge_graph.json")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

# 确保 reports 目录存在
os.makedirs(REPORTS_DIR, exist_ok=True)

# 3. 读取现有知识图谱，提取去重key
with open(KG_PATH, 'r', encoding='utf-8') as f:
    existing_kg = json.load(f)

existing_dedup_keys = set()
for evt in existing_kg.get("events", []):
    existing_dedup_keys.add(evt["description"][:30])

print(f"📊 现有知识图谱事件数: {len(existing_kg.get('events', []))}")
print(f"📊 现有去重key数: {len(existing_dedup_keys)}")

# 4. 新事件列表
new_events = [
    {
        "event_description": "2026年7月美银上修DRAM涨价预期，Q3合约价恐涨30-40%，HBM产能挤占消费级DRAM供给，16Gb DDR5现货50美元，DDR4现货80美元，谷歌2027年资本支出或达3000亿美元",
        "category": "DRAM"
    },
    {
        "event_description": "2026年7月AI抢产能挤压消费级供给，显卡内存一天一个价，RTX5070从5000元涨至6500元，固态硬盘从400元涨至800元，三星SK海力士美光产能全售罄，存储超级周期延续",
        "category": "DRAM"
    },
    {
        "event_description": "2026年7月三星Q3 DRAM涨价20%连涨三季度，AI算力抢产能致苹果Mac/iPad涨价20%，瑞银上调DDR合约价涨幅预测至32%，HBM占三星DRAM产能40%以上",
        "category": "DRAM"
    },
    {
        "event_description": "2026年7月HBM产能被抢空，SK海力士业绩暴涨，HBM4售价700美元/颗毛利率60%以上，三大原厂70%新增产能向HBM倾斜，产能缺口仍达50%-60%，长单锁定至2028年",
        "category": "HBM"
    },
    {
        "event_description": "2026年7月三星绑定博通5年2000亿美元MOU，SK牵手英伟达超5000亿美元AI计划，HBM全球供需锁死，长单锁定未来5年产能，HBM从短期采购升级为中长期供应安全",
        "category": "HBM"
    },
    {
        "event_description": "2026年7月MLCC全线涨价，三星电机8月1日起MLCC上调30%，太阳诱电9月1日跟进涨价且无法保障交付，村田AI及车规MLCC涨价10%-40%，国巨全系列电容上调最高50%",
        "category": "MLCC"
    },
    {
        "event_description": "2026年7月MLCC赛道升温，AI算力需求引爆MLCC超级周期，英伟达Rubin机柜单柜MLCC需求65万颗价值54万元，高端高容MLCC交期拉长至16-24周，紧平衡延续至2027年中",
        "category": "MLCC"
    },
    {
        "event_description": "2026年7月功率半导体集体涨价，英飞凌年内二次涨价15%，近20家巨头7月1日调价，车规IGBT涨15%-25%，AI服务器电源PMIC涨15%-25%，交期从8周拉长至30周以上",
        "category": "功率器件"
    },
    {
        "event_description": "2026年7月功率半导体三轮涨价，华润微士兰微扬杰科技跟进涨10%-15%，铜价涨35%锡价涨36%推升成本，8英寸产能利用率90%扩产需2-3年，涨价至少持续到2027年上半年",
        "category": "功率器件"
    },
    {
        "event_description": "2026年7月MCU涨价潮席卷行业，中微半导率先调价，意法半导体年内两次涨价7%-18%，盛群官宣涨价一至两成，车规MCU涨8%-20%，2026年全球MCU市场规模将突破200亿美元",
        "category": "通用MCU"
    },
    {
        "event_description": "2026年7月NAND Flash市场两极分化，云端需求强劲消费端疲软，SLC NAND下半年价格将涨120%-170%，TrendForce预计2027下半年NAND供给趋宽价格面临修正",
        "category": "NAND Flash"
    },
    {
        "event_description": "2026年7月晶圆代工涨价，台积电2027年初全面调价5%-10%，三星4nm/5nm涨约15%，力积电DRAM代工涨45%逻辑代工涨10%-15%，8英寸成熟制程产能紧张",
        "category": "晶圆代工"
    },
    {
        "event_description": "2026年7月PCB价格暴涨，高速PCB涨超300%，AI服务器PCB层数达30-100层价值为普通服务器10倍，建滔6轮涨价FR-4涨15%，电子布价格翻倍，订单锁定至2027年",
        "category": "PCB"
    },
    {
        "event_description": "2026年7月模拟芯片全线涨价交期翻倍，ADI交期拉满6个月，TI年内第四轮调价，国内交期从6周拉长至12周以上，海外交期16周以上，8英寸产能吃紧扩产需18-24个月",
        "category": "模拟芯片"
    },
    {
        "event_description": "2026年7月连接器涨价，安费诺7月1日第二轮涨价5%-15%，TE全线调涨5%-12%，800V高压连接器交期12-30周，224G高速背板订单激增，铜金成本飙升击穿利润底线",
        "category": "连接器"
    },
    {
        "event_description": "2026年7月LCD电视面板价格下跌，65英寸月环比跌1.7%，供需环境趋于宽松，淡季需求偏弱叠加高投产导致供给相对过剩，显示器及笔电面板短期持稳",
        "category": "LCD面板"
    },
    {
        "event_description": "2026年7月电感磁珠涨价，村田7月1日全系列功率电感涨50%，TLVR高端累计涨85%，太阳诱电AI耦合电感再涨35%，TDK分料号滚动调价AI电感累计涨45%-70%，稀土出口管控影响产能",
        "category": "电感"
    },
    {
        "event_description": "2026年7月NOR Flash涨价，聚辰股份全系列上调25%，7月6日生效，受晶圆封测成本持续攀升推动，TrendForce预计下半年NOR Flash结构性缺货价格持续上涨",
        "category": "NOR Flash"
    },
    {
        "event_description": "2026年7月长鑫存储科创板上市首日市值3.28万亿，国产DRAM份额达8%，DDR5全面切换完成LPDDR5X速率10667Mbps，一季度营收508亿同比增长719%",
        "category": "DRAM"
    }
]

# 5. Initialize pipeline
pipeline = AutoCyclePipeline(KG_PATH)

# 6. 去重过滤
deduped_events = []
skipped_events = []
for evt in new_events:
    key = evt["event_description"][:30]
    if key in existing_dedup_keys:
        skipped_events.append(evt)
        print(f"⏭️ 跳过重复事件: {evt['event_description'][:50]}...")
    else:
        deduped_events.append(evt)

print(f"\n📋 新事件总数: {len(new_events)}")
print(f"⏭️ 去重跳过: {len(skipped_events)}")
print(f"🆕 待处理新事件: {len(deduped_events)}")

# 7. 处理每个新事件
results = []
red_alerts = []
orange_count = 0
green_count = 0
success_count = 0

for i, evt in enumerate(deduped_events):
    print(f"\n{'='*60}")
    print(f"处理事件 [{i+1}/{len(deduped_events)}]: {evt['event_description'][:50]}...")
    print(f"{'='*60}")
    
    try:
        result = pipeline.auto_analyze_new_event(
            event_description=evt["event_description"],
            category=evt["category"],
            source="WebSearch 自动扫描"
        )
        results.append(result)
        success_count += 1
        
        # 检查红色预警
        warning_template = result.get("warning_template", [])
        for w in warning_template:
            level = w.get("level", "")
            signal = w.get("signal", "")
            prediction = w.get("prediction", "")
            
            if "🔴红色预警" in level:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                alert_line = f"[{now_str}] [{evt['category']}] [{result['cycle_type']}] [{evt['event_description'][:80]}] [{signal}] [{prediction}]"
                red_alerts.append(alert_line)
                print(f"  🔴 红色预警触发: {signal[:50]}...")
            elif "🟠橙色预警" in level:
                orange_count += 1
            elif "🟢绿色预警" in level:
                green_count += 1
                
    except Exception as e:
        print(f"  ❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print(f"📊 事件处理汇总")
print(f"{'='*60}")
print(f"✅ 成功入库: {success_count}个")
print(f"🔴 红色预警事件: {len(red_alerts)}个")
print(f"🟠 橙色预警次数: {orange_count}")
print(f"🟢 绿色预警次数: {green_count}")

# 8. 写入红色预警到 alerts.log
alerts_log_path = os.path.join(REPORTS_DIR, "alerts.log")
with open(alerts_log_path, 'a', encoding='utf-8') as f:
    f.write(f"\n# ===== 每日扫描 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====\n")
    for alert in red_alerts:
        f.write(alert + "\n")
        print(f"  📝 已写入红警: {alert[:80]}...")

print(f"\n📝 红色预警已写入: {alerts_log_path}")

# 9. 运行完整校验
print(f"\n{'='*60}")
print("🔍 运行完整知识图谱校验...")
print(f"{'='*60}")
validation_result = pipeline.run_full_validation()
print(f"校验结果: {json.dumps(validation_result, ensure_ascii=False, indent=2)}")

# 10. 写入每日扫描日志
scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_content = f"""# 每日扫描日志
# 生成时间: {scan_time}
# 扫描批次: 20260802_08

## 基本信息
- 扫描时间: {scan_time}
- 查询数量(query_count): 20
- WebSearch结果数量: 19
- 去重后新事件数量: {len(deduped_events)}
- 成功入库数量: {success_count}
- 去重跳过数量: {len(skipped_events)}

## 红色预警事件列表
"""

if red_alerts:
    for i, alert in enumerate(red_alerts, 1):
        log_content += f"\n{i}. {alert}\n"
else:
    log_content += "\n无红色预警事件\n"

log_content += f"""
## 预警统计
- 红色预警事件数: {len(red_alerts)}
- 橙色预警次数: {orange_count}
- 绿色预警次数: {green_count}

## 校验结果
- 总因果关系: {validation_result.get('total_relations', 'N/A')}
- 有效因果关系: {validation_result.get('valid_relations', 'N/A')}
- 无效因果关系: {validation_result.get('invalid_relations', 'N/A')}
- 校验是否通过: {'✅ 通过' if validation_result.get('validation_passed', False) else '❌ 未通过'}

## 详细校验结果
{json.dumps(validation_result, ensure_ascii=False, indent=2)}
"""

log_path = os.path.join(REPORTS_DIR, "daily_scan_20260802_08.log")
with open(log_path, 'w', encoding='utf-8') as f:
    f.write(log_content)

print(f"\n📝 每日扫描日志已写入: {log_path}")

# 最终汇总输出
print(f"\n{'='*60}")
print(f"🏁 每日扫描完成 - 最终汇总")
print(f"{'='*60}")
print(f"📅 扫描时间: {scan_time}")
print(f"📊 新事件总数: {len(new_events)}")
print(f"⏭️ 去重跳过: {len(skipped_events)}")
print(f"🆕 待处理新事件: {len(deduped_events)}")
print(f"✅ 成功入库: {success_count}")
print(f"🔴 红色预警: {len(red_alerts)}个事件")
print(f"🟠 橙色预警: {orange_count}次")
print(f"🟢 绿色预警: {green_count}次")
print(f"🔍 校验结果: {validation_result.get('valid_relations', 'N/A')}/{validation_result.get('total_relations', 'N/A')} 因果关系有效, {'✅通过' if validation_result.get('validation_passed') else '❌未通过'}")
