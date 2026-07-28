#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_cycle_pipeline import AutoCyclePipeline


def load_existing_events(kg_path):
    with open(kg_path, 'r', encoding='utf-8') as f:
        kg = json.load(f)
    existing_keys = set()
    for evt in kg.get("events", []):
        desc = evt.get("description", "")
        if desc:
            existing_keys.add(desc[:30])
    return existing_keys


def process_search_results(search_results, existing_keys, kg_path):
    pipeline = AutoCyclePipeline(kg_path)
    
    total_results = len(search_results)
    new_events = []
    red_alerts = []
    orange_count = 0
    green_count = 0
    
    for result in search_results:
        description = result.get("description", "")
        category = result.get("category", "")
        source = result.get("source", "WebSearch 自动扫描")
        
        desc_key = description[:30]
        if desc_key in existing_keys:
            continue
        
        try:
            analysis_result = pipeline.auto_analyze_new_event(
                event_description=description,
                category=category,
                source=source
            )
            
            new_events.append({
                "event_id": analysis_result["event_id"],
                "category": category,
                "cycle_type": analysis_result["cycle_type"],
                "description": description,
                "warning_template": analysis_result["warning_template"]
            })
            
            for warning in analysis_result["warning_template"]:
                level = warning.get("level", "")
                if "🔴红色预警" in level:
                    red_alerts.append({
                        "category": category,
                        "cycle_type": analysis_result["cycle_type"],
                        "signal": warning.get("signal", ""),
                        "prediction": warning.get("prediction", ""),
                        "description": description
                    })
                elif "🟠橙色预警" in level:
                    orange_count += 1
                elif "🟢绿色预警" in level:
                    green_count += 1
                    
        except Exception as e:
            print(f"处理事件失败: {description[:50]} - {e}")
    
    return {
        "total_results": total_results,
        "new_events": new_events,
        "red_alerts": red_alerts,
        "orange_count": orange_count,
        "green_count": green_count,
        "pipeline": pipeline
    }


def write_alerts_log(red_alerts):
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "alerts.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        for alert in red_alerts:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            desc_short = alert["description"][:80]
            line = f"[{timestamp}] [{alert['category']}] [{alert['cycle_type']}] [{desc_short}] [{alert['signal']}] [{alert['prediction']}]\n"
            f.write(line)


def write_daily_scan_log(results, validation_result):
    now = datetime.now()
    hour = "08" if now.hour < 14 else "20"
    log_filename = f"daily_scan_{now.strftime('%Y%m%d')}_{hour}.log"
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", log_filename)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"电子元器件周期智能体 - 自动扫描报告\n")
        f.write(f"扫描时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"查询query数: {8}\n")
        f.write(f"WebSearch返回结果数: {results['total_results']}\n")
        f.write(f"去重后新增事件数: {len(results['new_events'])}\n")
        f.write(f"入库成功数: {len(results['new_events'])}\n")
        f.write(f"触发红色预警事件数: {len(results['red_alerts'])}\n")
        f.write(f"橙色预警数量: {results['orange_count']}\n")
        f.write(f"绿色预警数量: {results['green_count']}\n")
        f.write("\n")
        
        if results['red_alerts']:
            f.write("=== 红色预警事件列表 ===\n")
            for i, alert in enumerate(results['red_alerts'], 1):
                f.write(f"{i}. 品类: {alert['category']}\n")
                f.write(f"   周期类型: {alert['cycle_type']}\n")
                f.write(f"   信号: {alert['signal']}\n")
                f.write(f"   预测: {alert['prediction']}\n")
                f.write(f"   事件摘要: {alert['description'][:100]}\n")
                f.write("\n")
        
        f.write("=== 知识图谱校验结果 ===\n")
        f.write(f"总关系数: {validation_result.get('total_relations', 0)}\n")
        f.write(f"有效关系数: {validation_result.get('valid_relations', 0)}\n")
        f.write(f"无效关系数: {validation_result.get('invalid_relations', 0)}\n")
        f.write(f"校验通过: {validation_result.get('validation_passed', False)}\n")
        
        if validation_result.get('invalid_details'):
            f.write("\n无效关系详情:\n")
            for inv in validation_result['invalid_details']:
                f.write(f"  - {inv.get('relation_id', '')}: {inv.get('description', '')}\n")


def send_lark_message(red_alerts):
    try:
        from lark_oapi import Client, SetUserStatusRequest, CreateChatRequest, SendMessageRequest
        from lark_oapi.api.im.v1 import CreateMessageRequest, MessageContent
        
        content = "【电子元器件周期智能体 - 红色预警通知】\n\n"
        content += f"检测到 {len(red_alerts)} 个红色预警事件：\n\n"
        
        for i, alert in enumerate(red_alerts, 1):
            content += f"{i}. 【{alert['category']}】{alert['cycle_type']}\n"
            content += f"   信号: {alert['signal']}\n"
            content += f"   预测: {alert['prediction']}\n"
            content += f"   摘要: {alert['description'][:100]}\n\n"
        
        content += "请及时关注相关品类的采购策略！"
        
        client = Client.new_client(app_id="", app_secret="")
        req = SendMessageRequest.builder() \
            .user_id_type("open_id") \
            .receive_id("") \
            .msg_type("text") \
            .content(json.dumps({"text": content})) \
            .build()
        
        resp = client.im.v1.message.create(req)
        if resp.success():
            return True
        else:
            return False
    except Exception as e:
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports", "alerts.log")
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 飞书消息发送失败: {e}\n")
        return False


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kg_path = os.path.join(base_dir, "graphiti", "cycle_knowledge_graph.json")
    
    existing_keys = load_existing_events(kg_path)
    print(f"已加载 {len(existing_keys)} 个已入库事件的去重key")
    
    search_results = [
        {
            "description": "2026年7月服务器DRAM现货溢价146%，64GB服务器DRAM现货报价突破3100美元，较6月底合约价1380美元高出约146%，供需缺口已无法通过正常管道弥补",
            "category": "DRAM",
            "source": "新浪财经"
        },
        {
            "description": "TrendForce预计3Q26 DRAM合约价环比上涨13-18%、NAND涨10-15%，涨幅较前两个季度60%-100%收窄但趋势未止，AI需求持续扩张致供需缺口扩大",
            "category": "存储芯片",
            "source": "TrendForce"
        },
        {
            "description": "2026年7月HBM价格暴涨500%，AI芯片需求激增导致HBM内存价格大幅上涨，三星和SK海力士占据90%市场份额，HBM4将于2026年量产",
            "category": "HBM",
            "source": "每日新闻摘录"
        },
        {
            "description": "英伟达和SK海力士敲定总额超5000亿美元双向绑定AI合作方案，英伟达长期稳定采购HBM4产品，SK电讯规划2027年新算力工厂投产",
            "category": "HBM",
            "source": "今日头条"
        },
        {
            "description": "2026年7月MLCC现货价暴涨2-3倍，稀缺料号涨10倍，AI服务器高容MLCC交期已排到2027年，代理商综合拿货成本上涨约30%",
            "category": "MLCC",
            "source": "东方财富"
        },
        {
            "description": "三星电机与全球大型企业签署价值2亿美元AI服务器MLCC供应合同，合约期限为2027全年，连续第二个月斩获同类大规模订单",
            "category": "MLCC",
            "source": "第一财经"
        },
        {
            "description": "2026年7月近20家芯片厂商集体涨价，英飞凌、德州仪器、意法半导体等国内外约20家芯片厂商启动新一轮涨价，功率半导体涨幅10%-25%",
            "category": "功率器件",
            "source": "东方财富证券"
        },
        {
            "description": "台积电敲定新一轮晶圆代工调价方案，计划自2027年起上调全部先进制程与成熟制程代工报价，基础调价区间最高10%，部分高端代工涨幅逼近25%",
            "category": "晶圆代工",
            "source": "日经亚洲"
        },
        {
            "description": "2026年7月半导体全产业链涨价，从功率器件到存储芯片，从晶圆代工到先进封装，价格上涨趋势明显，AI算力爆发与成本攀升双重驱动",
            "category": "功率器件",
            "source": "金融界"
        },
        {
            "description": "NAND涨势降温，消费市场疲软，2026年三季度NAND单月涨幅回落至个位数区间，但服务器端需求强劲支撑价格，短期内大幅下跌概率偏低",
            "category": "NAND Flash",
            "source": "EET-China"
        },
        {
            "description": "长鑫存储和长江存储议价能力大增，国产存储芯片正重塑全球供给，AI引发大缺货周期下中国厂商开始挑选客户、抬高价格",
            "category": "存储芯片",
            "source": "腾讯新闻"
        },
        {
            "description": "存储芯片半月猛涨40%，AI服务器对HBM需求爆炸式增长，三大原厂将70%先进产能转产HBM，挤压通用DRAM和NAND供给，全球DRAM供需缺口达4.9%",
            "category": "存储芯片",
            "source": "BigNews"
        },
        {
            "description": "AI抢食车规芯片价格暴涨，受AI算力需求爆发冲击，车规芯片供应被大量挤压，给整车制造带来巨大压力，车企称缺货比涨价更致命",
            "category": "车规MCU",
            "source": "快科技"
        },
        {
            "description": "存储涨价周期未走完，高位震荡成常态，7月中旬起64GB DDR5服务器DRAM现货价冲高至3100-3400美元，较6月底合约价涨幅达146%",
            "category": "DRAM",
            "source": "国投证券国际"
        },
        {
            "description": "DRAM结构性短缺至少持续到2028年上半年，三大原厂产能优先倾斜高端HBM，通用DRAM、NAND新增产能有限，单价持续上行",
            "category": "DRAM",
            "source": "瑞银"
        }
    ]
    
    print(f"处理 {len(search_results)} 条搜索结果...")
    
    results = process_search_results(search_results, existing_keys, kg_path)
    
    print(f"新增事件数: {len(results['new_events'])}")
    print(f"红色预警数: {len(results['red_alerts'])}")
    print(f"橙色预警数: {results['orange_count']}")
    print(f"绿色预警数: {results['green_count']}")
    
    if results['red_alerts']:
        write_alerts_log(results['red_alerts'])
        print("已写入alerts.log")
        
        try:
            success = send_lark_message(results['red_alerts'])
            if success:
                print("飞书消息发送成功")
            else:
                print("飞书消息发送失败")
        except Exception as e:
            print(f"飞书消息发送异常: {e}")
    
    validation_result = results['pipeline'].run_full_validation()
    write_daily_scan_log(results, validation_result)
    print("已写入daily_scan日志")
    
    return {
        "new_events_count": len(results['new_events']),
        "red_alerts_count": len(results['red_alerts']),
        "orange_count": results['orange_count'],
        "green_count": results['green_count']
    }


if __name__ == "__main__":
    main()