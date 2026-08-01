#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电子元器件周期智能体 - 每日自动扫描脚本
按 README "自动定时运行" 章节执行
"""

import os
import sys
import json
from datetime import datetime

# 设置工作目录并导入脚本
BASE_DIR = "/workspace/electronic-component-cycle"
os.chdir(BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "scripts"))

# ============ 步骤 1：提取已入库事件去重 key ============
print("=" * 60)
print("步骤 1：读取知识图谱，提取已入库事件去重 key")
print("=" * 60)

KG_PATH = os.path.join(BASE_DIR, "graphiti", "cycle_knowledge_graph.json")
with open(KG_PATH, 'r', encoding='utf-8') as f:
    existing_kg = json.load(f)

existing_descriptions = set()
for evt in existing_kg.get("events", []):
    existing_descriptions.add(evt["description"][:30])
print(f"  ✅ 已加载 {len(existing_descriptions)} 个已入库事件的去重 key")

# ============ 步骤 2：构造搜索事件数据（来自 WebSearch 结果） ============
print("\n" + "=" * 60)
print("步骤 2：加载 WebSearch 返回的搜索事件")
print("=" * 60)

# 从 WebSearch 返回的 24 个 query 中整理出的搜索结果
# 每个事件：{description, category, source_title}
raw_search_events = [
    # ===== HBM / DRAM / 存储 =====
    {
        "description": "2026年7月高盛韩国存储专家电话会：2026Q3传统DRAM现货价格两位数环比增长，Q4有望再涨两位数；HBM因DRAM成本抬升，明年存在翻倍空间。超半数服务器DRAM已被LTA长协覆盖，含大额预付款、照付不议条款。",
        "category": "DRAM",
        "source_title": "高盛韩国存储专家电话会纪要 2026-07-29"
    },
    {
        "description": "AI芯片需求激增，HBM内存价格暴涨500%。Yole Group预测2023-2028年HBM供应CAGR 45%，三星和SK海力士占HBM市场90%份额，SK海力士HBM4将于2026年量产。",
        "category": "HBM",
        "source_title": "新浪网 AI芯片需求激增 HBM暴涨500% 2026-07-26"
    },
    {
        "description": "存储涨价逻辑再强化：2026Q3 DRAM现货两位数环比涨幅，Q4再度两位数环比上行；2027年三星HBM售价同比涨幅达87%。三大原厂HBM晶圆消耗比例偏高，有效存储比特增量低于历史均值。",
        "category": "存储芯片",
        "source_title": "网易财经 高盛韩国存储专家会 2026-07-31"
    },
    {
        "description": "2026年7月全球存储芯片销售额达746亿美元创历史最高月度纪录，环比大涨31.7%；DRAM销售额约480亿美元环比增长27.7%。TrendForce预计Server DRAM Q3合约价季度环比增长13%-18%，三星称供应短缺持续到2028年。",
        "category": "DRAM",
        "source_title": "东方财富 存储芯片高景气延续 2026-07-31"
    },
    {
        "description": "HBM改写存储产业价值分配：SK海力士控制全球HBM约56%营收份额，三大原厂2026Q1 HBM产能全部售罄，产能缺口50%-60%。HBM消耗晶圆面积是普通DRAM三倍，三大原厂70%新增产能倾斜HBM，挤压通用DRAM供给。消费级DDR5 PC内存一年内涨幅超5倍。",
        "category": "HBM",
        "source_title": "钛媒体 HBM的战争 2026-07-27"
    },
    {
        "description": "2026年7月下旬显卡全面封仓，现货价格暴涨30%-50%，RTX5080从8000元涨至近12000元。英伟达向显卡厂商发出新一轮涨价通知；三星、海力士、美光优先产能供给HBM，导致GDDR6/GDDR7显存产能被大幅压缩，单张16GB显卡显存成本增加约150美元。",
        "category": "DRAM",
        "source_title": "新浪财经 显卡全面封仓暴涨50% 2026-07-31"
    },
    {
        "description": "AI越热消费电子越贵：存储连续3季度涨价，三星Q2营业利润89.5万亿韩元同比+1814%创历史新高。瑞银2026年7月全球存储销售额746亿美元，Q3 DRAM合约价环比+32% Q4续涨18%，结构性短缺持续至2028Q2。三大原厂70%新增产能倾斜HBM，HBM缺口50-60%，产能锁定至2028年。",
        "category": "存储芯片",
        "source_title": "证券之星 AI越热消费电子越贵 2026-07"
    },
    {
        "description": "野村研报按紧缺排序：第一梯队HBM显存缺口率50%以上，三星SK海力士70%新增产能全倾斜HBM，扩产周期2.5-4年，2026-2027年HBM缺口长期维持50%以上；通用DRAM产能被挤压，Q3继续涨20%-32%。HBM是AI服务器木桶最短板。",
        "category": "HBM",
        "source_title": "东方财富股吧 野村研报紧缺分级 2026-07-10"
    },
    {
        "description": "经济日报：芯片短缺冲击消费电子产业，HBM产能向AI倾斜导致消费级DRAM/NAND严重短缺，2025年现货价格DRAM涨386%、NAND涨207%，推动苹果MacBook iPad全球提价约20%、微软Xbox涨价。2027年预计5800万台PC、1.34亿部手机面临缺口。",
        "category": "NAND Flash",
        "source_title": "经济日报 芯片短缺冲击消费电子 2026-07-07"
    },
    {
        "description": "HBM超级周期爆发：三大原厂2026年HBM产能全部售罄，50-60%缺口，有钱买不到货。SEMI冯莉称2026年HBM市场规模增长58%至546亿美元，占DRAM近四成。SK海力士CEO预测2027年是存储供应最紧张的一年，紧缺或持续到2030年后；HBM4价格预计从下半年2美元/千比特飙到4-5美元翻倍。",
        "category": "HBM",
        "source_title": "东方财富股吧 50%产能缺口HBM超级周期 2026-07-24"
    },
    {
        "description": "HBM产能被洗劫一空：SK海力士Q2单季营收22万亿韩元营业利润9.8万亿韩元同比+300%，HBM3E 12层产品2026全年产能全部被大厂预订清空，2027上半年意向订单超出现有产能两倍。DRAM晶圆流向HBM占比首破20%，PC通用DRAM大幅缩减，结构性缺货；同等容量HBM3E均价是DDR5的5-7倍，毛利率70%+。",
        "category": "DRAM",
        "source_title": "头条号 HBM产能被洗劫一空 2026-07-26"
    },
    {
        "description": "韩系正式封死HBM赛道：SK海力士与英伟达敲定5000亿美元全维度合作（HBM3E/HBM4+定制架构+2GW算力厂），三星携手博通2000亿美元备忘录（定制HBM+2nm晶圆代工+CoWoS封装），合计7000亿美元超长周期协议锁死高端HBM到2030年。全面废除年度短约，强制3-5年LTA，前置定金10-30%。",
        "category": "HBM",
        "source_title": "头条号 7000亿产能锁死至2030 2026-07-27"
    },
    {
        "description": "七巨头失速半导体翻倍：费城半导体半年涨100%。2026年HBM市场涨58%至546亿美元，三大原厂70%新增产能倾斜HBM，缺口仍50-60%，美光称紧张延续至2027后。但Meta出售闲置AI算力，GPU租赁价两个月跌30-70%，单位Token算力成本未来12个月或降40%，算力紧缺转平衡信号显现。",
        "category": "存储芯片",
        "source_title": "亚洲经济报 七巨头失速半导体翻倍 2026-07-05"
    },
    {
        "description": "AI算力周期终局深度研究：HBM毛利率峰值近85%（传统DRAM仅30-45%），属供需错配下阶段性溢价，不具备长期持续性。三大原厂千亿级扩产，HBM投片占比2026年18%→2027年30%；短期2026仍紧平衡、中期2027新增产能集中释放、长期2028或阶段性过剩。",
        "category": "HBM",
        "source_title": "东方财富股吧 AI算力周期终局深度研报 2026-07-02"
    },
    {
        "description": "2026年7月中旬华强北内存条终端价格松动，较年初高点回落约30%：DDR4 16G二手从超700元降至450元；DDR5 16G从约1500元回落至1000出头；32G DDR5套装从3000+跌至1950-2500元。但较去年同期仍贵5-6倍。前期涨幅过高反噬需求、长鑫国产产能释放、存储龙头股回调、谷歌压缩算法等多重因素叠加。",
        "category": "DRAM",
        "source_title": "新浪财经 内存条降价30%商户不敢囤货 2026-07-19"
    },
    {
        "description": "宇瞻科技（台湾DRAM模组大厂）CEO张家騉警告：2027年DRAM原厂对独立模组厂供应量可能削减至2026年的30%，三大原厂新增产能几乎全面投入HBM、服务器DDR5、LPDDR5X等AI产品，一般DDR5/DDR4/工控颗粒持续减少。宇瞻已将库存提升至新台币124亿元环比+48%，策略从怕价高转为怕拿不到货。预测2026Q3 DRAM合约价涨约30%，NAND涨超20%。",
        "category": "DRAM",
        "source_title": "东方财富股吧 宇瞻CEO预警2027模组厂供应砍70% 2026-07-31"
    },
    {
        "description": "中证快报：AI挤占DRAM颗粒供应模组厂预警无货可卖。三大原厂70%以上新增产能投向AI产品（HBM/伺服器DDR5/LPDDR5X），分配给一般DDR5、DDR4及工控市场的颗粒持续减少。依原厂供货规划，未来可分配给模组厂的DRAM供应量仍将持续下降，供需失衡或至少持续至2027年上半年。",
        "category": "DRAM",
        "source_title": "中证快报 AI挤占DRAM供应模组厂预警无货 2026-07-27"
    },
    {
        "description": "南方基金科技板块后市研判（真实产业数据）：被动元件MLCC已开启全面涨价，头部厂商与全球大型科技企业签订AI服务器长协订单，锁定2027年全年产能。存储方面HBM持续挤占通用DRAM产能，2026年DRAM供应低于需求约7%，HBM缺口6%、2027年扩大至9%，供需缺口仍在扩大。PCB及上游材料年内已多次提价。",
        "category": "MLCC",
        "source_title": "新浪财经 南方基金 科技退潮后市怎么看 2026-07-31"
    },
    {
        "description": "抛售美韩芯片股隐忧：激进扩产引发产能过剩担忧。SK海力士和三星计划在韩国各新建两座芯片工厂，800万亿韩元5年内将DRAM产能翻一番。晨星预计DRAM强势暂时，2027下半年-2028年大幅提升产能，2029年起推动价格下降。市场担忧需求高点叠加盲目扩产→几年后价格战和去库存。",
        "category": "DRAM",
        "source_title": "中新经纬 抛售芯片股 激进扩产产能过剩隐忧 2026-07-29"
    },
    {
        "description": "存储现货周报DRAM全线逼空：DDR4 8Gb周涨4.98%、DDR5 16Gb周涨3.04%，原厂先进产能倾斜HBM和高规格DDR5，传统DDR4产线供给侧暴力收缩，涨价缺乏终端真实消费力支撑更像定价权武力宣示。NAND结构性撕裂：MLC/SLC微涨，主流TLC 512Gb周跌0.61%、eMMC周跌0.51%，消费电子萎靡去库存。",
        "category": "DRAM",
        "source_title": "新浪财经 DRAM全线逼空与NAND结构性撕裂 2026-07-17"
    },

    # ===== 功率器件 / 模拟芯片 / MLCC / MCU / PCB =====
    {
        "description": "2026年7月起全球半导体开启年内第二轮涨价，芯联集成、斯达半导、扬杰科技、聚辰股份等向客户发涨价函，上调15-25%。海外TI、英飞凌、ST同步第二轮涨价：英飞凌自7月1日AI服务器电源芯片、车规IGBT、高压MOSFET涨10-20%；AI服务器功率半导体用量是传统服务器3倍以上，高端机型可达5倍。",
        "category": "功率器件",
        "source_title": "上海证券报 半导体第二轮涨价15-25% 2026-07-03"
    },
    {
        "description": "2026年7月全球半导体全产业链第二轮集体涨价，近20家海内外厂商集中调价（7月1日或7月6日生效）：存储DRAM/NAND Q3环比30-32%；功率/AI电源芯片15-25%；模拟/电源IC 5-15%；硅片10-15%；MLCC 20-35%。主因AI需求爆发、8寸晶圆产能吃紧（扩产18-24个月）、铜/硅片/特气成本上行、存储转HBM缩减普通产能。",
        "category": "模拟芯片",
        "source_title": "东方财富股吧 7月全产业链第二轮集体涨价 2026-07-05"
    },
    {
        "description": "2026年7月1日全球近20家模拟及功率半导体企业启动年内第三轮涨价，AI服务器、数据中心专用电源管理IC及高压信号链模拟芯片涨幅达15-25%，工业自动化、储能隔离芯片涨10-15%。AI产业链几乎所有环节涨价：存储、晶圆代工、模拟芯片、PCB等，半导体设备需求激增。韩国宣布6月29日半导体扩产计划，800万亿韩元5年内DRAM产能翻倍。",
        "category": "电源管理IC",
        "source_title": "金融界 半导体产业链迎7月涨价潮 2026-07-03"
    },
    {
        "description": "2026年7月1日起芯片涨价最全整理：士兰微全产品线15%起；联发科发函调价；华大电子、极海半导体、矽力杰模拟芯片调价；TE全线调涨5-12%（高速/AI/液冷品类10-12%）；辉芒微8位MCU涨5%；上海贝岭10-30%；ST 6月28日再次上调；华新科技电阻调价；NXP 6月1日再调价；联电预告下半年晶圆价格涨10-15%（7月1日起）。",
        "category": "通用MCU",
        "source_title": "21ic电子网 今天这些芯片涨价最全整理 2026-07-01"
    },
]

print(f"  ✅ 共加载 {len(raw_search_events)} 条原始搜索事件")

# ============ 步骤 3：对搜索结果去重，跳过已入库事件 ============
print("\n" + "=" * 60)
print("步骤 3：对搜索结果按前30字符去重，跳过已入库事件")
print("=" * 60)

new_events_to_process = []
for evt in raw_search_events:
    desc_key = evt["description"][:30]
    if desc_key and desc_key not in existing_descriptions:
        new_events_to_process.append(evt)
        # 加入临时去重集合，防止同一批内重复
        existing_descriptions.add(desc_key)
    else:
        print(f"  ⏭️  跳过（已入库/重复）：{desc_key[:30]}...")

print(f"  ✅ 去重后剩余 {len(new_events_to_process)} 条新事件待处理")
total_queries_count = 24  # 6品类 × 4关键词
total_websearch_results_count = len(raw_search_events)

# ============ 步骤 4：初始化 pipeline，逐一分析新事件 ============
print("\n" + "=" * 60)
print("步骤 4：初始化 AutoCyclePipeline，逐一分析新事件")
print("=" * 60)

from auto_cycle_pipeline import AutoCyclePipeline

pipeline = AutoCyclePipeline(KG_PATH)

# 收集统计
added_count = 0
red_alert_events = []
orange_alert_count = 0
green_alert_count = 0
red_alert_details = []  # 用于写入 alerts.log 和发送飞书

alerts_log_path = os.path.join(BASE_DIR, "reports", "alerts.log")
lark_send_failures = []

for idx, evt in enumerate(new_events_to_process):
    print(f"\n--- 处理事件 {idx+1}/{len(new_events_to_process)}：{evt['category']} ---")
    print(f"    描述前60字：{evt['description'][:60]}...")
    try:
        result = pipeline.auto_analyze_new_event(
            event_description=evt["description"],
            category=evt["category"],
            source=f"WebSearch 自动扫描 | {evt['source_title']}"
        )
        added_count += 1

        # 检查 warning_template 的预警级别
        has_red = False
        for wt in result.get("warning_template", []):
            level = wt.get("level", "")
            if "🔴红色预警" in level or "红色" in level:
                has_red = True
                red_alert_details.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "category": evt["category"],
                    "cycle_type": result.get("cycle_type", ""),
                    "event_desc_80": evt["description"][:80],
                    "signal": wt.get("signal", ""),
                    "prediction": wt.get("prediction", ""),
                    "full_event_desc": evt["description"]
                })
            elif "🟠橙色预警" in level or "橙色" in level:
                orange_alert_count += 1
            elif "🟢绿色预警" in level or "绿色" in level:
                green_alert_count += 1

        if has_red:
            red_alert_events.append({
                "event_id": result.get("event_id"),
                "category": evt["category"],
                "cycle_type": result.get("cycle_type"),
                "desc_80": evt["description"][:80]
            })
            print(f"    🚨 触发 🔴红色预警！cycle_type={result.get('cycle_type')}")

    except Exception as e:
        print(f"    ❌ 处理失败：{e}")
        import traceback
        traceback.print_exc()

print(f"\n  ✅ 入库成功 {added_count} 条新事件")
print(f"  🚨 🔴红色预警事件：{len(red_alert_events)} 条")
print(f"  🟠橙色预警触发次数：{orange_alert_count} 次")
print(f"  🟢绿色预警触发次数：{green_alert_count} 次")

# ============ 步骤 5：红色预警处理 - 写 alerts.log + 飞书消息 ============
print("\n" + "=" * 60)
print("步骤 5：处理红色预警 - 写 alerts.log + 飞书 P2P 消息")
print("=" * 60)

os.makedirs(os.path.join(BASE_DIR, "reports"), exist_ok=True)

# 5a) 追加写入 alerts.log
for detail in red_alert_details:
    log_line = (
        f"[{detail['timestamp']}] [{detail['category']}] [{detail['cycle_type']}] "
        f"[{detail['event_desc_80'].replace(chr(10), ' ')}] "
        f"[{detail['signal'].replace(chr(10), ' ')}] "
        f"[{detail['prediction'].replace(chr(10), ' ')}]\n"
    )
    with open(alerts_log_path, "a", encoding="utf-8") as f:
        f.write(log_line)
    print(f"  ✍️  写入 alerts.log：{detail['category']} - {detail['cycle_type']}")

# 5b) 通过 lark-im 发飞书消息
lark_success = False
if red_alert_details:
    try:
        print("  📨 准备发送飞书 P2P 消息...")
        # 构造消息内容
        msg_parts = ["【电子元器件周期智能体 - 🔴红色预警自动通知】\n"]
        msg_parts.append(f"扫描时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        msg_parts.append(f"触发红色预警事件数：{len(red_alert_details)}\n")
        msg_parts.append("-" * 40 + "\n")
        for i, d in enumerate(red_alert_details, 1):
            msg_parts.append(f"【预警 {i}】\n")
            msg_parts.append(f"  品类：{d['category']}\n")
            msg_parts.append(f"  周期类型：{d['cycle_type']}\n")
            msg_parts.append(f"  预警信号：{d['signal']}\n")
            msg_parts.append(f"  预测：{d['prediction']}\n")
            msg_parts.append(f"  事件摘要：{d['event_desc_80']}...\n")
            msg_parts.append("\n")
        lark_msg_content = "".join(msg_parts)

        # 通过 Skill 调用 lark-im - 在脚本外处理，这里先把内容存到临时文件供主流程用
        lark_msg_path = os.path.join(BASE_DIR, "reports", "_lark_msg_content.txt")
        with open(lark_msg_path, "w", encoding="utf-8") as f:
            f.write(lark_msg_content)
        print(f"  ✅ 飞书消息内容已暂存到 {lark_msg_path}")
        lark_success = None  # 由外层 skill 决定是否成功

    except Exception as e:
        err_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 飞书发送失败：{str(e)}\n"
        with open(alerts_log_path, "a", encoding="utf-8") as f:
            f.write(err_msg)
        print(f"  ⚠️  飞书消息失败，已记录到 alerts.log：{e}")
        lark_success = False
else:
    print("  🟢 本次无红色预警，跳过飞书消息")
    lark_success = True  # 无消息则默认成功

# ============ 步骤 6：写入 daily_scan 日志 + run_full_validation ============
print("\n" + "=" * 60)
print("步骤 6：写入 daily_scan 日志 + 调用 run_full_validation()")
print("=" * 60)

now = datetime.now()
# 取当前小时，08 或 20 就近原则（按要求写 08 或 20，按实际当前小时 14 点取最近的 08）
current_hh = now.strftime("%H")
# 按任务要求：HH 用 08 或 20，根据当前时间（今天 14:xx）选择更接近的 08
hh_for_log = "08" if now.hour < 14 else "20"
daily_scan_filename = f"daily_scan_{now.strftime('%Y%m%d')}_{hh_for_log}.log"
daily_scan_path = os.path.join(BASE_DIR, "reports", daily_scan_filename)
print(f"  📄 扫描日志文件名：{daily_scan_filename}")

# 6b) 调用 run_full_validation()
print("  🔍 正在调用 pipeline.run_full_validation()...")
try:
    validation_result = pipeline.run_full_validation()
except Exception as e:
    print(f"    ⚠️  run_full_validation 出错，用 analyzer 替代：{e}")
    try:
        validation_result = pipeline.analyzer.run_mcp_analysis("validate_causality", {})
    except Exception as e2:
        validation_result = {"error": str(e2), "fallback": True}

# 6a) 构造日志内容
scan_log_content = []
scan_log_content.append("=" * 60)
scan_log_content.append("电子元器件周期智能体 - 每日自动扫描报告")
scan_log_content.append("=" * 60)
scan_log_content.append(f"扫描时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
scan_log_content.append(f"执行小时标识（HH）：{hh_for_log}")
scan_log_content.append("")
scan_log_content.append("--- 扫描统计 ---")
scan_log_content.append(f"查询的 query 数量：{total_queries_count}")
scan_log_content.append(f"WebSearch 返回总结果数：{total_websearch_results_count}")
scan_log_content.append(f"去重后新增事件数：{len(new_events_to_process)}")
scan_log_content.append(f"入库成功数：{added_count}")
scan_log_content.append("")
scan_log_content.append("--- 预警统计 ---")
scan_log_content.append(f"🔴红色预警触发事件数：{len(red_alert_events)}")
scan_log_content.append(f"🟠橙色预警触发次数：{orange_alert_count}")
scan_log_content.append(f"🟢绿色预警触发次数：{green_alert_count}")
scan_log_content.append("")
scan_log_content.append("--- 🔴红色预警事件列表 ---")
if red_alert_events:
    for i, e in enumerate(red_alert_events, 1):
        scan_log_content.append(f"  {i}. [{e['event_id']}] [{e['category']}] [{e['cycle_type']}] {e['desc_80']}")
else:
    scan_log_content.append("  （本次无红色预警事件）")
scan_log_content.append("")
scan_log_content.append("--- run_full_validation() 校验结果 ---")
scan_log_content.append(json.dumps(validation_result, ensure_ascii=False, indent=2))
scan_log_content.append("")
scan_log_content.append("=" * 60)
scan_log_content.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
scan_log_content.append("=" * 60)

with open(daily_scan_path, "w", encoding="utf-8") as f:
    f.write("\n".join(scan_log_content))

print(f"  ✅ 扫描日志已写入：{daily_scan_path}")

# ============ 最终总结输出 ============
print("\n" + "=" * 60)
print("📊 本次扫描最终总结")
print("=" * 60)
summary = {
    "新增入库事件数": added_count,
    "红色预警事件数": len(red_alert_events),
    "飞书消息发送状态": "待外层 Skill 调用确认（内容已暂存）",
    "alerts.log 写入": f"已追加 {len(red_alert_details)} 条预警",
    "daily_scan_log": daily_scan_filename,
}
print(json.dumps(summary, ensure_ascii=False, indent=2))

# 把总结写入 json 文件供外层读取
summary_path = os.path.join(BASE_DIR, "reports", "_scan_summary.json")
with open(summary_path, "w", encoding="utf-8") as f:
    json.dump({
        "added_count": added_count,
        "red_alert_count": len(red_alert_events),
        "lark_content_path": os.path.join(BASE_DIR, "reports", "_lark_msg_content.txt") if red_alert_details else None,
        "daily_scan_path": daily_scan_path,
        "alerts_log_path": alerts_log_path,
        "red_alert_details": red_alert_details
    }, f, ensure_ascii=False, indent=2)
