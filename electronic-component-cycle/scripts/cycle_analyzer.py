#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电子元器件周期分析工具
DataAnalyst-Agent 可调用模块
支持：周期识别、拐点检测、信号预警、相似案例匹配、时序因果校验
遵循MCP函数调用规范
版本：v1.1
更新：增加时序因果自动校验功能
"""

import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import re


class Confidence(Enum):
    """可信度等级"""
    A = "A - 事后证实事实"
    B = "B - 同期市场传闻"
    C = "C - 无法确认信息"


@dataclass
class CycleEvent:
    """周期事件数据结构"""
    event_id: str
    time: str
    category: str
    event_type: str
    subject: str
    description: str
    confidence: str
    price_impact: float  # 价格影响幅度，正数上涨，负数下跌
    duration_impact: int  # 影响持续月数


class ComponentCycleAnalyzer:
    """电子元器件周期分析器"""
    
    def __init__(self, knowledge_graph_path: str = None):
        """
        初始化分析器
        :param knowledge_graph_path: 时序知识图谱JSON路径
        """
        self.events: List[CycleEvent] = []
        self.cycle_rules = self._load_default_rules()
        self.knowledge_graph_path = knowledge_graph_path
        
        if knowledge_graph_path:
            self.load_knowledge_graph(knowledge_graph_path)
    
    def load_knowledge_graph(self, path: str) -> None:
        """加载Graphiti时序知识图谱"""
        with open(path, 'r', encoding='utf-8') as f:
            kg = json.load(f)
        
        # 解析事件
        for evt in kg.get('events', []):
            self.events.append(CycleEvent(
                event_id=evt['id'],
                time=evt['time'],
                category=self._parse_category(evt.get('object', '')),
                event_type=evt['predicate'],
                subject=evt['subject'],
                description=evt['description'],
                confidence=evt['confidence'],
                price_impact=self._estimate_price_impact(evt),
                duration_impact=self._estimate_duration(evt)
            ))
    
    def _parse_category(self, obj: str) -> str:
        """解析品类"""
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
        if not obj:
            return '全品类'
        for k, v in category_map.items():
            if k in obj:
                return v
        return '全品类'
    
    def _estimate_price_impact(self, evt: Dict) -> float:
        """估算事件价格影响"""
        impact_map = {
            '价格上涨': 0.3,
            '缺货涨价': 1.0,
            '跟随涨价': 0.2,
            '价格见顶': 0.0,
            '生产事故': 0.15,
            '产能中断': 0.2,
            '关停产线': 0.25,
            '产能调整': 0.3,
            '产能转移': 0.2,
            '大规模扩产': -0.4,
            '需求下滑': -0.3,
            '产能收缩': 0.2,
            '需求爆发': 0.5,
            '发布涨价函': 0.15,
        }
        return impact_map.get(evt['predicate'], 0.0)
    
    def _estimate_duration(self, evt: Dict) -> int:
        """估算事件影响持续月数"""
        duration_map = {
            '产能调整': 18,
            '产能转移': 12,
            '大规模扩产': 24,
            '需求爆发': 24,
            '产能收缩': 12,
            '生产事故': 3,
            '产能中断': 2,
        }
        return duration_map.get(evt['predicate'], 6)
    
    def _load_default_rules(self) -> List[Dict]:
        """加载默认预警规则"""
        return [
            {
                "rule_id": "R001",
                "rule_name": "供给收缩型涨价预警",
                "conditions": [
                    "头部厂商宣布减产/关产线",
                    "行业资本开支增速连续2个季度为负",
                    "B/B值连续2个月大于1.2",
                    "12个月内无大规模新产能投产计划"
                ],
                "probability": 0.85,
                "expected_duration": "12-18个月",
                "expected_price_range": "50%-200%",
                "confidence": "A"
            },
            {
                "rule_id": "R002",
                "rule_name": "周期见顶预警",
                "conditions": [
                    "价格连续上涨4个季度",
                    "主要厂商宣布大规模扩产计划",
                    "渠道库存大于3个月",
                    "经销商开始出现抛货现象"
                ],
                "probability": 0.90,
                "expected_timing": "6个月内见顶",
                "expected_drawdown": "30%-70%",
                "confidence": "A"
            },
            {
                "rule_id": "R003",
                "rule_name": "周期底部预警",
                "conditions": [
                    "全行业出现大面积亏损",
                    "产能利用率低于60%",
                    "连续2个季度没有新的扩产计划",
                    "主要厂商开始减产"
                ],
                "probability": 0.80,
                "expected_timing": "12个月内启动新周期",
                "confidence": "A"
            },
            {
                "rule_id": "R004",
                "rule_name": "黑天鹅冲击预警",
                "conditions": [
                    "主要厂商工厂发生事故/自然灾害",
                    "事故发生时供需已经处于紧平衡状态",
                    "事故影响全球5%以上产能"
                ],
                "probability": 0.70,
                "expected_duration": "1-3个月短期冲击",
                "expected_price_range": "20%-50%脉冲上涨",
                "confidence": "A"
            }
        ]
    
    def detect_cycle_phase(self, current_signals: Dict) -> Dict:
        """
        检测当前周期阶段
        :param current_signals: 当前市场信号字典
        :return: 周期阶段判断结果
        """
        score = 0
        max_score = 0
        triggered_rules = []
        
        for rule in self.cycle_rules:
            rule_score = 0
            for cond in rule['conditions']:
                max_score += 1
                if any(keyword in str(current_signals) for keyword in cond.split('，')[0:2]):
                    rule_score += 1
            
            if rule_score >= len(rule['conditions']) * 0.6:
                triggered_rules.append({
                    "rule_id": rule['rule_id'],
                    "rule_name": rule['rule_name'],
                    "match_rate": f"{rule_score}/{len(rule['conditions'])}",
                    "probability": rule['probability'],
                    "prediction": {k: v for k, v in rule.items() if k not in ['rule_id', 'rule_name', 'conditions', 'probability']}
                })
                score += rule_score
        
        # 周期阶段判断
        if score >= max_score * 0.6:
            phase = "上行周期 - 涨价阶段"
        elif score <= max_score * 0.2:
            phase = "下行周期 - 去库存阶段"
        else:
            phase = "震荡阶段 - 信号不明确"
        
        return {
            "analysis_time": datetime.now().isoformat(),
            "current_phase": phase,
            "confidence_score": f"{score}/{max_score}",
            "triggered_rules": triggered_rules,
            "recommendation": self._generate_recommendation(phase, triggered_rules)
        }
    
    def _generate_recommendation(self, phase: str, rules: List[Dict]) -> str:
        """生成操作建议"""
        if "上行周期" in phase:
            return "建议：适当增加安全库存，锁定长期供货协议，关注产能释放进度"
        elif "下行周期" in phase:
            return "建议：控制库存水平，避免高价拿货，等待价格触底信号"
        else:
            return "建议：观望为主，密切跟踪关键信号变化，不要盲目囤货或抛货"
    
    def find_similar_cases(self, current_features: Dict, top_k: int = 3) -> List[Dict]:
        """
        相似历史案例匹配
        :param current_features: 当前市场特征
        :param top_k: 返回最相似的k个案例
        :return: 相似历史案例列表
        """
        # 历史案例库
        historical_cases = [
            {
                "case_id": "C001",
                "case_name": "2017-2018 MLCC超级周期",
                "features": ["头部厂商产能调整", "中低端产能退出", "需求稳定增长", "渠道囤货"],
                "duration": "15个月上涨",
                "price_range": "200%-500%",
                "key_lesson": "不要相信「游资炒作」传言，核心是供给收缩"
            },
            {
                "case_id": "C002",
                "case_name": "2020-2022全球缺芯潮",
                "features": ["需求预测错误", "疫情黑天鹅", "产能错配", "牛鞭效应"],
                "duration": "18个月紧张",
                "price_range": "500%-1000%",
                "key_lesson": "黑天鹅只是放大器，需求错配才是根本"
            },
            {
                "case_id": "C003",
                "case_name": "2016-2018存储超级周期",
                "features": ["寡头控产", "技术转型阵痛", "需求升级", "反垄断调查"],
                "duration": "21个月上涨",
                "price_range": "300%-500%",
                "key_lesson": "高集中度品类容易产生协同控产行为"
            }
        ]
        
        # 简单相似度计算
        for case in historical_cases:
            case['similarity'] = len(
                set(current_features.get('features', [])) & set(case['features'])
            ) / len(set(case['features']))
        
        # 按相似度排序
        sorted_cases = sorted(historical_cases, key=lambda x: x['similarity'], reverse=True)
        return sorted_cases[:top_k]
    
    def get_price_inflection_points(self, category: str = None) -> List[Dict]:
        """
        获取历史价格拐点
        :param category: 指定品类，None返回全部
        :return: 拐点列表
        """
        inflection_types = ['价格见顶', '价格上涨', '缺货涨价']
        points = []
        
        for evt in self.events:
            if evt.event_type in inflection_types:
                if category is None or evt.category == category:
                    points.append({
                        "time": evt.time,
                        "category": evt.category,
                        "event_type": evt.event_type,
                        "description": evt.description,
                        "confidence": evt.confidence
                    })
        
        return sorted(points, key=lambda x: x['time'])
    
    def run_mcp_analysis(self, query_type: str, params: Dict) -> Dict:
        """
        MCP统一调用入口
        :param query_type: 查询类型：cycle_phase/similar_cases/inflection_points/validate_causality
        :param params: 查询参数
        :return: 分析结果
        """
        if query_type == "cycle_phase":
            return self.detect_cycle_phase(params)
        elif query_type == "similar_cases":
            return {"similar_cases": self.find_similar_cases(params)}
        elif query_type == "inflection_points":
            return {"inflection_points": self.get_price_inflection_points(params.get('category'))}
        elif query_type == "validate_causality":
            return self.validate_time_causality()
        else:
            return {"error": f"不支持的查询类型: {query_type}"}
    
    def _parse_time_to_quarter(self, time_str: str) -> int:
        """将时间字符串转换为季度序号，用于比较先后"""
        # 处理 2017Q3 格式
        match = re.match(r'(\d{4})Q(\d)', time_str)
        if match:
            year = int(match.group(1))
            quarter = int(match.group(2))
            return year * 4 + quarter
        # 处理 2023-2024 格式，取起始年份Q1
        match = re.match(r'(\d{4})-(\d{4})', time_str)
        if match:
            year = int(match.group(1))
            return year * 4 + 1
        # 处理 2021Q2-Q4 格式，取起始季度
        match = re.match(r'(\d{4})Q(\d)-Q(\d)', time_str)
        if match:
            year = int(match.group(1))
            quarter = int(match.group(2))
            return year * 4 + quarter
        return 0
    
    def validate_time_causality(self) -> Dict:
        """
        时序因果校验：检查所有因果关系是否满足"原因发生时间早于结果"
        :return: 校验结果
        """
        # 构建事件时间映射
        event_time_map = {}
        for evt in self.events:
            event_time_map[evt.event_id] = self._parse_time_to_quarter(evt.time)
        
        # 加载因果关系（从知识图谱重新加载以获取完整关系）
        kg_path = self.knowledge_graph_path if hasattr(self, 'knowledge_graph_path') else None
        causal_relations = []
        if kg_path:
            with open(kg_path, 'r', encoding='utf-8') as f:
                kg = json.load(f)
                causal_relations = kg.get('causal_relations', [])
        
        valid_count = 0
        invalid_count = 0
        invalid_relations = []
        
        for rel in causal_relations:
            from_events = rel['from_event'].split(',')
            to_events = rel['to_event'].split(',') if rel['to_event'] else []
            
            if not to_events:
                valid_count += 1
                continue
            
            # 取原因的最晚时间和结果的最早时间比较
            max_from_time = max([event_time_map.get(e.strip(), 0) for e in from_events])
            min_to_time = min([event_time_map.get(e.strip(), 99999) for e in to_events])
            
            if max_from_time <= min_to_time:
                valid_count += 1
            else:
                invalid_count += 1
                invalid_relations.append({
                    "relation_id": rel['id'],
                    "description": rel['description'],
                    "from_time": max_from_time,
                    "to_time": min_to_time,
                    "error": "原因发生时间晚于结果，违反时间因果铁则"
                })
        
        return {
            "validation_time": datetime.now().isoformat(),
            "total_relations": len(causal_relations),
            "valid_relations": valid_count,
            "invalid_relations": invalid_count,
            "invalid_details": invalid_relations,
            "validation_passed": invalid_count == 0
        }


def main():
    """示例用法"""
    print("=" * 60)
    print("电子元器件周期分析工具 v1.0")
    print("=" * 60)
    
    # 初始化分析器
    analyzer = ComponentCycleAnalyzer(
        knowledge_graph_path="../graphiti/cycle_knowledge_graph.json"
    )
    
    # 示例：检测2026年当前周期阶段
    print("\n【示例：2026年当前周期阶段检测】")
    current_signals_2026 = {
        "features": ["头部厂商发布涨价函", "AI需求爆发", "产能收缩", "交期拉长"],
        "capex_growth": "连续2年低增长",
        "bb_ratio": 1.3,
        "channel_inventory": "1.5个月",
        "capacity_utilization": "90%+"
    }
    result = analyzer.detect_cycle_phase(current_signals_2026)
    print(f"当前周期阶段: {result['current_phase']}")
    print(f"信号匹配度: {result['confidence_score']}")
    print(f"操作建议: {result['recommendation']}")
    print("\n触发的规则:")
    for rule in result['triggered_rules']:
        print(f"  - {rule['rule_name']} (匹配度: {rule['match_rate']}, 概率: {rule['probability']*100:.0f}%)")
    
    # 示例：历史拐点查询
    print("\n【示例：MLCC历史价格拐点】")
    points = analyzer.get_price_inflection_points("MLCC")
    for p in points:
        print(f"  {p['time']}: {p['description']} (可信度: {p['confidence']})")
    
    # 示例：相似案例匹配
    print("\n【示例：2026年行情相似历史案例】")
    similar = analyzer.find_similar_cases(current_signals_2026)
    for case in similar:
        print(f"  {case['case_name']} (相似度: {case['similarity']*100:.0f}%)")
        print(f"    教训: {case['key_lesson']}")


if __name__ == "__main__":
    main()
