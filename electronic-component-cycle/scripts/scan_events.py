#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动扫描过去7天行情事件并入库
"""

import json
import os
import sys
from datetime import datetime

# 添加scripts目录到sys.path
sys.path.insert(0, os.path.dirname(__file__))

from auto_cycle_pipeline import AutoCyclePipeline

def load_existing_events(kg_path):
    """加载已入库事件的去重key"""
    with open(kg_path, 'r', encoding='utf-8') as f:
        kg = json.load(f)
    
    existing_keys = set()
    for evt in kg.get("events", []):
        existing_keys.add(evt["description"][:30])
    
    return existing_keys

def process_search_results():
    """处理WebSearch结果并去重"""
    
    # WebSearch结果（从工具返回中提取的关键事件）
    search_results = [
        # DRAM/HBM相关
        {
            "title": "瑞银大幅上调DRAM价格预测32%，三星通知涨价20%",
            "category": "DRAM",
            "summary": "2026年7月4日瑞银发布报告，将第三季度DDR合约价格环比涨幅从17%上调至32%，三星电子已正式通知客户三季度DRAM均价上调20%。AI服务器对DRAM需求量是传统服务器的8-10倍，三大原厂将超70%的先进产能转向HBM，导致通用DRAM产能严重挤兑，价格持续飙升。"
        },
        {
            "title": "三星电子年内第三次推动DRAM涨价，通用DRAM重回市场中心",
            "category": "DRAM",
            "summary": "三星电子与下游客户展开第三季度DRAM价格谈判，目标将通用DRAM平均售价较上季度提高20%。2026年第一季度DRAM均价暴涨约90%，第二季度涨幅在50%至60%之间。AI推理工作负载放量，LPDDR被越来越多AI芯片选为片外缓存。"
        },
        {
            "title": "SK海力士登顶韩国梦中情企，HBM占DRAM业务收入将提升至58%",
            "category": "HBM",
            "summary": "SK海力士以14.2%得票率蝉联韩国大学生最想就职企业榜首。HBM技术改写存储产业价值分配，SK海力士控制全球HBM市场约56%份额。三大原厂已将约70%的新增产能向HBM倾斜，HBM产能缺口仍达50%-60%。"
        },
        {
            "title": "美光启动日本广岛工厂扩建工程，斥资93亿美元布局HBM产线",
            "category": "HBM",
            "summary": "美光科技启动日本广岛工厂扩建工程，斥资约93亿美元布局HBM产线，预计2028年出货。三巨头新增产能向高毛利、高附加值的AI产线倾斜，消费级DRAM的产能扩张极为有限。"
        },
        
        # MLCC相关
        {
            "title": "AI需求引发MLCC短缺，价格飙升20-25%",
            "category": "MLCC",
            "summary": "AI服务器生产导致通用MLCC出现供应短缺和价格上涨，村田、三星电机、太阳诱电三大厂商月出货量创五年新高。通用MLCC库存已降至30天以下，分销商提价20-25%，现货市场价格飙升至之前的2-3倍。"
        },
        {
            "title": "三星电机8月起MLCC全线涨价30%，太阳诱电9月1日调价",
            "category": "MLCC",
            "summary": "三星电机已向全球客户下发调价通知，决定自8月1日起旗下全线MLCC产品出货价格在现有定价基础上统一上调30%。太阳诱电也已向客户出具正式涨价函，确定自9月1日起执行新的出货价格。"
        },
        {
            "title": "国巨3月1日起调涨全系列电容产品价格",
            "category": "MLCC",
            "summary": "被动元器件大厂国巨向客户端通知价格调整，自7月1日开始调涨全系列电容产品价格，涉及的产品覆盖国巨约50%营收，且涨价对象首次纳入直接客户(EMS/OEM)。"
        },
        
        # 功率器件相关
        {
            "title": "全球超20家功率半导体企业集中开启年内第二轮涨价",
            "category": "功率器件",
            "summary": "7月起全球超20家功率半导体企业集中开启年内第二轮涨价，幅度10%-25%，覆盖硅基MOSFET/IGBT、SiC、GaN全品类。AI数据中心功率密度跃升驱动，单台AI服务器功率半导体使用量是传统服务器的3倍以上。"
        },
        {
            "title": "英飞凌年内二次涨价，车规IGBT涨价10%-20%",
            "category": "功率器件",
            "summary": "英飞凌7月1日启动年内第二次提价，AI服务器电源芯片、车规级IGBT、高压MOSFET涨幅区间10%-20%。AI服务器电源管理芯片订单暴增，直接吞噬了原本分配给车规级功率半导体的8英寸晶圆产能，主流功率器件交期从8周拉长至30周以上。"
        },
        {
            "title": "士兰微官宣全线涨价15%起，华润微、扬杰科技同步跟进",
            "category": "功率器件",
            "summary": "士兰微6月29日发布调价函，自7月1日起全产品线价格上调15%起。华润微、扬杰科技、新洁能等国内功率半导体厂商全线跟进。涨价源于上游原材料、晶圆制造、封测环节成本持续走高，叠加AI、新能源等需求爆发。"
        },
        
        # MCU相关
        {
            "title": "成熟制程产能排挤，MCU厂商坦言晶圆紧张、交期拉长",
            "category": "通用MCU",
            "summary": "AI需求持续吸纳半导体产能，成熟制程从晶圆制造至封装测试都有供应紧张情况，MCU厂商交期约为六至八个月。AI相关芯片获利较高，晶圆及封装资源优先移往AI服务器，压缩一般消费性IC可取得的供给量。"
        },
        {
            "title": "中微半导宣布MCU产品全线涨价15%-50%",
            "category": "通用MCU",
            "summary": "中微半导宣布对MCU产品全线涨价15%至50，明确提及调价核心原因是代工交期加长、部分产品缺货严重。全球8英寸晶圆产能向功率器件、逻辑芯片倾斜，MCU专用晶圆产能占比持续下降。"
        },
        {
            "title": "意法半导体、英飞凌、TI计划三季度跟进MCU涨价",
            "category": "车规MCU",
            "summary": "意法半导体6月底落地调价，英飞凌与TI计划三季度跟进。辉芒微电子已上调8位MCU产品价格，涨幅5%。MCU市场逐步复苏，价格逐步反弹，2026年行业景气度向好。"
        },
        
        # LCD面板相关
        {
            "title": "七月LCD TV面板价格向下温和调整",
            "category": "LCD面板",
            "summary": "群智咨询发文指出，七月电视面板市场供应增长强于需求恢复，整体供需环境趋于宽松，促使LCD TV面板价格出现温和下行调整。32寸价格下降1美元，55寸下降2美元，65寸下降3美元。"
        },
        {
            "title": "机构：7月电视面板市场供需错配加剧，价格全线走弱",
            "category": "LCD面板",
            "summary": "CINNO Research研报指出，进入7月，国内618大促收官后终端品牌开启去库存周期，欧美旺季备货尚未启动，LCD TV面板短期需求走弱。头部面板厂预计持续高稼动生产，行业供需错配矛盾扩大，全尺寸面板价格同步小幅下调。"
        },
        
        # NAND Flash相关
        {
            "title": "NAND涨势降温，消费市场疲软",
            "category": "NAND Flash",
            "summary": "2026年下半年NAND闪存涨价节奏逐步放缓，市场观望氛围持续升温，行业共识判断闪存价格已迈入高位平台期。三季度NAND单月涨幅回落至个位数区间，全年累计涨幅仍预计达25%-30%。"
        },
        {
            "title": "存储三巨头重仓HBM，消费级DRAM涨价潮持续蔓延",
            "category": "NAND Flash",
            "summary": "一套32GB DDR5内存套装去年售价900元，现在已经涨到3800元，深圳华强北渠道商反馈价格翻了超四倍。美光、三星、SK海力士将超70%的先进产能转向高带宽存储，导致通用DRAM和NAND产能严重挤兑。"
        },
        
        # 晶圆代工相关
        {
            "title": "力积电大幅上调代工报价45%",
            "category": "晶圆代工",
            "summary": "力积电总经理朱宪国表示，自7月起存储代工报价上调45%。客户第三季度逻辑代工订单已达公司产能的1.4倍，供不应求的局面持续加剧。AI服务器正持续消耗全球内存产能，头部云厂商已提前锁定未来数年的DRAM供应。"
        },
        {
            "title": "台积电与三星启动新一轮调价，涨幅5%-15%",
            "category": "晶圆代工",
            "summary": "台积电通知英伟达、苹果、AMD等核心客户，计划将3nm、5nm及7nm制程价格上调5%-10%。三星电子针对4nm、5nm及部分车规8nm制程，将新客户供货价格提高约15%。AI订单爆发导致先进产能长期紧缺。"
        },
        
        # 模拟芯片/PMIC相关
        {
            "title": "德州仪器年内第四次调价，电源管理IC涨幅15%-85%",
            "category": "模拟芯片",
            "summary": "德州仪器已明确计划自7月1日起上调电源管理IC等核心产品报价，这是该公司一年内第四次价格调整。此前德州仪器已于4月1日启动过一轮大规模涨价，电源管理IC等核心产品涨幅达15%-85%。"
        },
        {
            "title": "全球近20家模拟及功率半导体企业启动年内第三轮涨价",
            "category": "模拟芯片",
            "summary": "7月1日，全球近20家模拟及功率半导体企业启动了年内第三轮涨价。AI服务器、数据中心专用电源管理芯片及高压信号链模拟芯片涨幅达15%至25%，工业自动化、储能隔离芯片涨幅为10%至15%。"
        },
        
        # 连接器相关
        {
            "title": "莫仕、安费诺宣布涨价，连接器行业成本风暴来临",
            "category": "连接器",
            "summary": "莫仕、安费诺这两家连接器世界的双子星几乎同时宣布从7月1日起对所有新增订单执行新价格体系。全球三大连接器巨头泰科电子、安费诺、莫仕相继调价，涨幅集中在5%-30%，其中高压高速连接器涨幅最高。"
        },
        {
            "title": "芯片缺货+铜价破万+巨头涨价，2026连接器行业陷入三重风暴",
            "category": "连接器",
            "summary": "一场从上游芯片、原材料到物流运输的全链路成本危机正将连接器行业推向变局拐点。海外主流芯片常规出货周期从过往3-4周拉长至7-8周甚至更久，AI服务器用高速背板连接器交期已拉长至30周以上。"
        },
        
        # PCB相关
        {
            "title": "AI算力需求爆发，高端PCB供不应求，价格涨超300%",
            "category": "PCB",
            "summary": "高端PCB价格已经远远超过三到四倍。AI服务器所用PCB的层数可达30层以上，高端产品达70到100层。2026年全球AI服务器出货量预计突破200万台，同比增长55%，直接拉动高端PCB的需求增长超110%。"
        },
        {
            "title": "建滔再发涨价函，FR4/PP同步大涨，全行业缺货涨价持久战开启",
            "category": "PCB",
            "summary": "建滔积层板7月6日发布涨价函，宣布FR-4覆铜板上调15%、PP半固化片上调15%。FR-4覆铜板价格从2025年7月均价70元/张一路飙升至2026年6月260元/张，一年涨幅超过270%。行业库存见底，无缓冲空间。"
        },
        
        # 传感器相关
        {
            "title": "全球半导体价格暴涨传导至传感器，车规/工业级产品涨价10%-50%",
            "category": "传感器",
            "summary": "从2026年第一季度开始，全球半导体供应链的价格波动持续加剧，这轮涨价已明确传导至传感器板块，覆盖主流车规和工业级品类。意法半导体、Allegro等原厂先后发布正式调价通知，宣布从一季度起多款产品线工厂价上调10%-50%。"
        },
        {
            "title": "驾驶员状态监测仪（DMS）市场价格普遍上涨8%-15%",
            "category": "传感器",
            "summary": "2026年7月，受全球车规芯片供应链紧张与高阶智驾功能包集体调价传导，驾驶员状态监测仪（DMS）市场价格普遍上涨8%-15%，成为智能驾驶硬件涨价潮中涨幅最集中的传感器模块之一。"
        },
        
        # NOR Flash/SLC NAND相关
        {
            "title": "NOR Flash合约价上半年涨幅100%-120%，下半年仍有60%-75%上涨空间",
            "category": "NOR Flash",
            "summary": "2026年上半年NOR Flash合约价累计涨幅达100%-120%。由于供应商未有大规模扩产计划，预估下半年价格将继续调升。美光持续缩减NOR产能，全球供给高度集中于旺宏、华邦等厂商。"
        },
        {
            "title": "聚辰股份发布涨价函：Nor flash全系列上调25%",
            "category": "NOR Flash",
            "summary": "聚辰股份发布涨价函：近期受全球半导体产业链波动影响，Nor Flash芯片核心原材料及晶圆、封测等生产环节成本持续攀升，导致公司整体生产成本上浮。公司决定对Nor flash全系列在现有价格基础上上调25%，自7月6日起执行。"
        },
    ]
    
    return search_results

def main():
    # 设置工作目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kg_path = os.path.join(base_dir, "graphiti", "cycle_knowledge_graph.json")
    
    # 加载已入库事件
    existing_keys = load_existing_events(kg_path)
    print(f"已入库事件去重key数量: {len(existing_keys)}")
    
    # 初始化pipeline
    pipeline = AutoCyclePipeline(kg_path)
    
    # 获取搜索结果
    search_results = process_search_results()
    print(f"WebSearch返回结果数: {len(search_results)}")
    
    # 去重
    new_events = []
    for result in search_results:
        desc_key = result["summary"][:30]
        if desc_key not in existing_keys:
            new_events.append(result)
            existing_keys.add(desc_key)  # 防止本次扫描中的重复事件
    
    print(f"去重后新增事件数: {len(new_events)}")
    
    # 分析并入库
    added_count = 0
    red_alert_events = []
    orange_alert_count = 0
    green_alert_count = 0
    
    for event in new_events:
        try:
            result = pipeline.auto_analyze_new_event(
                event_description=event["summary"],
                category=event["category"],
                source="WebSearch 自动扫描"
            )
            
            added_count += 1
            
            # 统计预警级别
            for warning in result.get("warning_template", []):
                level = warning.get("level", "")
                if "🔴红色预警" in level:
                    red_alert_events.append({
                        "category": event["category"],
                        "cycle_type": result.get("cycle_type", ""),
                        "signal": warning.get("signal", ""),
                        "prediction": warning.get("prediction", ""),
                        "event_summary": event["summary"][:80]
                    })
                elif "🟠橙色预警" in level:
                    orange_alert_count += 1
                elif "🟢绿色预警" in level:
                    green_alert_count += 1
            
        except Exception as e:
            print(f"处理事件失败: {event['title']}, 错误: {str(e)}")
            continue
    
    print(f"\n入库成功数: {added_count}")
    print(f"触发红色预警数: {len(red_alert_events)}")
    print(f"橙色预警数量: {orange_alert_count}")
    print(f"绿色预警数量: {green_alert_count}")
    
    # 运行完整校验
    print("\n运行完整知识图谱校验...")
    validation_result = pipeline.run_full_validation()
    
    # 返回统计结果
    return {
        "query_count": 13,  # WebSearch查询数
        "search_results": len(search_results),
        "new_events": len(new_events),
        "added_count": added_count,
        "red_alert_events": red_alert_events,
        "orange_alert_count": orange_alert_count,
        "green_alert_count": green_alert_count,
        "validation": validation_result
    }

if __name__ == "__main__":
    result = main()
    print("\n=== 扫描完成 ===")
    print(f"查询数: {result['query_count']}")
    print(f"WebSearch返回结果数: {result['search_results']}")
    print(f"去重后新增事件数: {result['new_events']}")
    print(f"入库成功数: {result['added_count']}")
    print(f"红色预警数: {len(result['red_alert_events'])}")
    print(f"橙色预警数: {result['orange_alert_count']}")
    print(f"绿色预警数: {result['green_alert_count']}")
    
    if result['red_alert_events']:
        print("\n=== 红色预警事件列表 ===")
        for evt in result['red_alert_events']:
            print(f"[{evt['category']}] [{evt['cycle_type']}] {evt['event_summary']}")
            print(f"  信号: {evt['signal']}")
            print(f"  预测: {evt['prediction']}")