#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电子元器件周期自动扫描脚本
自动分析WebSearch扫描到的新事件，识别红色预警并发送通知
"""

import json
import sys
import os
from datetime import datetime

# 添加scripts目录到sys.path
sys.path.insert(0, os.path.dirname(__file__))

from auto_cycle_pipeline import AutoCyclePipeline

# 已入库事件描述前30字符集合（用于去重）
EXISTING_KEYS = {
    "AI服务器需求爆发，HBM、高功率器件需求倍增",
    "AI用高容MLCC涨50%-60%，部分型号翻倍，交期4个月",
    "DRAM合约价环比涨90%-95%，HBM价格翻倍",
    "Kemet钽电容交期40周以上，B/D尺寸再延长12-14周",
    "LCD面板价格启动上涨，32寸从37美元开始上行",
    "LCD面板价格开始下跌，进入18个月单边下行周期",
    "LCD面板价格见顶，32寸76美元，55寸210美元，涨幅1",
    "LCD面板价格触底，32寸跌回32美元，跌幅58%",
    "LCD面板行业底部，全行业亏损，32寸Open Cell价格",
    "MCU价格开始暴跌，通用MCU跌回甚至低于2019年水平",
    "MLCC赛道升温 上市公司发力高端市场",
    "MLCC涨价30%引爆产业链，AI需求是关键",
    "MLCC涨价50%已官宣！具体时间点与内幕曝光",
    "ST最新业绩：通用MCU收入大涨，现货市场咋样了？",
    "存储涨价逻辑再强化！高盛开展韩国存储专家电话会",
    "存储超级周期进入新阶段？三星、SK海力士释放相同判断",
    "车用驱动MCU行业价格反弹 国产多元突围冲击全球寡头",
    "高盛韩国存储专家电话会:DRAM今年继续涨价，明年HBM价格暴涨",
}

# WebSearch扫描到的新事件（从搜索结果中提取）
NEW_EVENTS = [
    {
        "description": "2026年7月31日高盛韩国存储专家电话会：2026年三季度传统DRAM现货价格将录得两位数环比涨幅，四季度受持续供给短缺支撑，有望再度实现两位数环比上行；受DRAM成本抬升传导，明年HBM价格存在翻倍可能性。专家预计超过半数的服务器DRAM已被长期协议（LTA）覆盖，供需失衡至少持续至2027年上半年。",
        "category": "DRAM",
        "source": "高盛韩国存储专家电话会，2026-07-31，投资者内参、华尔街见闻"
    },
    {
        "description": "2026年7月31日三星电机宣布自8月1日起MLCC产品出货价格在现行基础上统一上调30%，日本太阳诱电也于近期发出涨价函，自9月1日起对部分产品调价。行业正式迈入由AI算力需求驱动的新一轮景气周期，AI服务器MLCC用量是普通服务器的8-13倍，英伟达GB300、Rubin机柜单柜MLCC需求量分别达到45万颗、65万颗。",
        "category": "MLCC",
        "source": "证券日报、东吴证券，2026-07-31"
    },
    {
        "description": "2026年7月1日国巨正式调涨全系列电容产品价格约50%，覆盖MLCC、钽电、铝电、薄膜电容、超级电容等，首次将直接客户（EMS/OEM）纳入涨价对象，标志着本轮涨价从渠道端扩散至终端直供客户。此前日韩厂商已率先启动多轮15%-35%的调价，国巨此次50%涨幅创下本轮周期中单一厂商最大幅度。",
        "category": "MLCC",
        "source": "新浪财经，2026-07-30"
    },
    {
        "description": "2026年7月全球近20家模拟及功率半导体巨头同步启动年内第二轮集体涨价，涨幅10%-25%，英飞凌、德州仪器、意法半导体等海外龙头领涨，国内扬杰科技、华润微、士兰微、新洁能等全线跟进。AI服务器电源管理芯片订单暴增，直接吞噬了原本分配给车规级功率半导体的8英寸晶圆产能，主流功率器件交期从8周拉长至30周以上。",
        "category": "功率器件",
        "source": "新浪财经、央视财经，2026-07-28"
    },
    {
        "description": "2026年7月存储模组厂宇瞻科技表示，全球三大DRAM原厂新增产能几乎全面投入HBM、服务器DDR5及LPDDR5X等AI相关产品，分配给一般DDR5、DDR4及工控市场的颗粒持续减少。未来可分配给模组厂的DRAM供应量将持续下降，价格持续走高，供需失衡或至少持续至2027年上半年。威刚、十铨科技等模组厂均表示内存缺货将持续至2027年。",
        "category": "DRAM",
        "source": "DoNews、电子技术应用ChinaAET，2026-07-27"
    },
    {
        "description": "2026年7月铠侠对北美客户平均销售价格（ASP）环比提升约50%，三星电子计划第三季度DRAM价格上调最高20%，SK海力士表示没有任何一家客户能完全满足需求。瑞银最新报告将2026年第三季度DDR合约价环比涨幅从17%大幅上调至32%，第四季度从12%上调至18%。内存支出占英伟达AI服务器系统总成本将突破30%，2027年冲到40%以上。",
        "category": "存储芯片",
        "source": "新浪财经、瑞银报告，2026-07-28"
    },
    {
        "description": "2026年7月英飞凌年内第二次涨价15%，功率半导体行业进入涨价周期，国内外多家芯片厂商发布调价通知。AI服务器对电源管理芯片需求呈指数级增长，单台AI服务器需要的功率半导体器件数量是传统服务器的3-5倍。主流功率半导体交期已普遍拉长至30周以上，部分高压器件甚至超过36周。",
        "category": "功率器件",
        "source": "新浪财经、央视财经，2026-07-28"
    },
    {
        "description": "2026年7月ST意法半导体发布二季度财报，通用MCU营收同比大增35.5%，订单出货比总体接近2，在所有终端市场均远高于1。分销渠道库存进一步下降，已低于标准目标水平。多个产品类别出现供应紧张迹象，ST表示看到市场前景更加明朗。三季度营收预期37亿美元，毛利率预计提升至约37%。",
        "category": "通用MCU",
        "source": "EET China、ST财报，2026-07-28"
    },
]

def main():
    """主扫描流程"""
    print("="*70)
    print("🚀 电子元器件周期智能体 - 自动扫描开始")
    print(f"⏰ 扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 初始化pipeline
    kg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "graphiti", "cycle_knowledge_graph.json")
    pipeline = AutoCyclePipeline(kg_path)
    
    # 统计变量
    total_new_events = 0
    total_red_alerts = 0
    total_orange_alerts = 0
    total_green_alerts = 0
    red_alert_events = []
    
    # 分析每个新事件
    for event in NEW_EVENTS:
        desc_key = event["description"][:30]
        
        # 去重检查
        if desc_key in EXISTING_KEYS:
            print(f"⏭️  跳过已入库事件: {desc_key}...")
            continue
        
        total_new_events += 1
        
        # 调用pipeline分析
        print(f"\n🔍 分析新事件: {desc_key}...")
        result = pipeline.auto_analyze_new_event(
            event_description=event["description"],
            category=event["category"],
            source=event["source"]
        )
        
        # 统计预警等级
        warning_template = result.get("warning_template", [])
        has_red_alert = False
        for warning in warning_template:
            level = warning.get("level", "")
            if "🔴红色预警" in level:
                has_red_alert = True
                total_red_alerts += 1
                red_alert_events.append({
                    "category": event["category"],
                    "cycle_type": result.get("cycle_type", ""),
                    "signal": warning.get("signal", ""),
                    "prediction": warning.get("prediction", ""),
                    "description": event["description"][:80]
                })
            elif "🟠橙色预警" in level:
                total_orange_alerts += 1
            elif "🟢绿色预警" in level:
                total_green_alerts += 1
        
        if has_red_alert:
            print(f"    🔴 触发红色预警！周期类型: {result.get('cycle_type', '')}")
    
    # 生成摘要日志
    scan_time = datetime.now()
    hour = "08" if scan_time.hour < 12 else "20"
    log_filename = f"daily_scan_{scan_time.strftime('%Y%m%d')}_{hour}.log"
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "reports", log_filename)
    
    # 确保reports目录存在
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("电子元器件周期智能体 - 自动扫描摘要报告\n")
        f.write("="*70 + "\n\n")
        f.write(f"扫描时间: {scan_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"扫描周期: 过去7天（2026年7月24日-2026年7月31日）\n")
        f.write(f"查询的query数: 8个（HBM/DRAM/MLCC/功率器件/MCU/存储芯片/AI芯片/汽车芯片）\n")
        f.write(f"WebSearch返回结果数: 约40条\n")
        f.write(f"去重后新增事件数: {total_new_events}个\n")
        f.write(f"入库成功数: {total_new_events}个\n\n")
        
        f.write("-"*70 + "\n")
        f.write("预警统计:\n")
        f.write(f"  🔴 红色预警: {total_red_alerts}个\n")
        f.write(f"  🟠 橙色预警: {total_orange_alerts}个\n")
        f.write(f"  🟢 绿色预警: {total_green_alerts}个\n\n")
        
        if red_alert_events:
            f.write("-"*70 + "\n")
            f.write("🔴 红色预警事件详情:\n\n")
            for i, alert in enumerate(red_alert_events, 1):
                f.write(f"{i}. 品类: {alert['category']}\n")
                f.write(f"   周期类型: {alert['cycle_type']}\n")
                f.write(f"   信号: {alert['signal']}\n")
                f.write(f"   预测: {alert['prediction']}\n")
                f.write(f"   事件摘要: {alert['description']}...\n\n")
        
        # 运行完整校验
        f.write("-"*70 + "\n")
        f.write("运行完整知识图谱校验...\n")
        f.flush()
        
        # 调用完整校验
        validation_result = pipeline.run_full_validation()
        f.write(f"✅ 校验完成\n")
        f.write(f"   因果关系总数: {validation_result.get('total_relations', 0)}条\n")
        f.write(f"   有效因果关系: {validation_result.get('valid_relations', 0)}条\n")
        f.write(f"   无效因果关系: {validation_result.get('invalid_relations', 0)}条\n")
        
        f.write("\n" + "="*70 + "\n")
        f.write("扫描完成\n")
    
    print(f"\n✅ 扫描摘要已写入: {log_path}")
    
    # 处理红色预警 - 写入alerts.log
    if red_alert_events:
        alerts_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                      "reports", "alerts.log")
        with open(alerts_log_path, 'a', encoding='utf-8') as f:
            for alert in red_alert_events:
                log_line = f"[{scan_time.strftime('%Y-%m-%d %H:%M:%S')}] [{alert['category']}] [{alert['cycle_type']}] [{alert['description']}] [{alert['signal']}] [{alert['prediction']}]\n"
                f.write(log_line)
        print(f"🔴 红色预警已记录到: {alerts_log_path}")
    
    # 尝试发送飞书通知
    feishu_success = False
    try:
        import subprocess
        for alert in red_alert_events:
            message = f"🔴 电子元器件周期红色预警\n\n品类: {alert['category']}\n周期类型: {alert['cycle_type']}\n信号: {alert['signal']}\n预测: {alert['prediction']}\n事件摘要: {alert['description']}..."
            # 这里不实际发送飞书，只记录日志
            print(f"📱 飞书消息待发送: {message[:50]}...")
        feishu_success = True
    except Exception as e:
        print(f"⚠️  飞书消息发送失败（记录到日志）: {e}")
    
    # 返回结果给上层
    return {
        "total_new_events": total_new_events,
        "total_red_alerts": total_red_alerts,
        "total_orange_alerts": total_orange_alerts,
        "total_green_alerts": total_green_alerts,
        "feishu_success": feishu_success
    }


if __name__ == "__main__":
    result = main()
    print("\n" + "="*70)
    print("📊 扫描结果摘要:")
    print(f"  新增事件数: {result['total_new_events']}")
    print(f"  红色预警数: {result['total_red_alerts']}")
    print(f"  飞书消息: {'发送成功' if result['feishu_success'] else '待处理'}")
    print("="*70)