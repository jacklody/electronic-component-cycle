#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电子元器件周期自动分析工作流
Auto-Pipeline for Electronic Component Cycle Analysis
参考 doubao-industry-analysis 的成熟pipeline设计
版本：v1.4
功能：自动发现历史事件 → 自动收集信息 → 自动RCA分析 → 自动时序校验 → 自动入库经验库
所有配置从 config.json 读取，不用改代码
"""

import json
import re
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import os

# 加载配置文件
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

# 导入我们已有的分析器
from cycle_analyzer import ComponentCycleAnalyzer, Confidence, CycleEvent


class EventDiscovery:
    """事件发现模块：自动搜索历史涨价/缺货/降价事件"""
    
    def __init__(self):
        # 从配置文件读取品类
        self.categories = CONFIG.get("categories", [])
        self.years = range(2016, 2027)  # 2016-2026共11年
        # 不仅涨价，还有降价、过剩、周期反转
        self.event_keywords = [
            "涨价", "提价", "缺货", "交期延长", "供应紧张", "产能不足",
            "降价", "价格战", "产能过剩", "库存高企", "去库存", "周期反转"
        ]
        
    def generate_search_queries(self) -> List[str]:
        """生成所有需要搜索的query"""
        queries = []
        for year in self.years:
            for category in self.categories:
                for keyword in self.event_keywords:
                    queries.append(f"{year}年 {category} {keyword} 原因 时间线 复盘")
        return queries
    
    def filter_new_events(self, events: List[Dict], existing_kg: Dict) -> List[Dict]:
        """过滤掉已经入库的事件，去重"""
        existing_descriptions = set()
        for evt in existing_kg.get("events", []):
            # 简化去重：取描述前30个字符
            existing_descriptions.add(evt["description"][:30])

        new_events = []
        for evt in events:
            desc_key = evt.get("description", "")[:30]
            if desc_key and desc_key not in existing_descriptions:
                new_events.append(evt)
        return new_events


class InformationGrader:
    """信息自动分级模块：根据来源自动打A/B/C可信度标签"""
    
    # A级来源：权威第三方、官方公告、事后复盘
    A_LEVEL_SOURCES = [
        "trendforce", "counterpoint", "ihs", "omdia", "gartner", "ic insights",
        "中国电子元件行业协会", "官方公告", "涨价函", "财报", "反垄断",
        "天风证券", "山西证券", "集微网", "电子工程专辑", "国际电子商情",
        "瑞萨", "意法", "英飞凌", "恩智浦", "村田", "国巨", "京东方", "三星"
    ]
    
    # B级来源：当时媒体报道、产业访谈
    B_LEVEL_SOURCES = [
        "财新", "第一财经", "36氪", "晚点LatePost", "虎嗅",
        "电子发烧友", "芯片超人", "供应链", "代理商", "业内人士"
    ]
    
    # C级来源：自媒体、股吧、传言
    C_LEVEL_SOURCES = [
        "自媒体", "股吧", "微博", "微信", "网传", "据传", "听说",
        "网友", "有人说", "市场传言"
    ]
    
    @classmethod
    def grade_source(cls, source: str) -> str:
        """根据来源字符串自动分级"""
        source_lower = source.lower()
        
        for a_source in cls.A_LEVEL_SOURCES:
            if a_source.lower() in source_lower:
                return "A"
        
        for b_source in cls.B_LEVEL_SOURCES:
            if b_source.lower() in source_lower:
                return "B"
        
        for c_source in cls.C_LEVEL_SOURCES:
            if c_source.lower() in source_lower:
                return "C"
        
        # 默认B级
        return "B"
    
    @classmethod
    def extract_price_data(cls, text: str) -> Optional[Dict]:
        """从文本中自动提取价格数据"""
        price_patterns = [
            r"涨(?:幅|了)?(\d+)[%％]",
            r"从(\d+(?:\.\d+)?)[元美元美金].*?(?:涨|到).*?(\d+(?:\.\d+)?)[元美元美金]",
            r"交期(\d+)周",
            r"产能(?:减少|损失|影响)(\d+)[%％]",
        ]
        
        result = {}
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if "%" in pattern:
                    result["price_change_pct"] = int(matches[0])
                elif "交期" in pattern:
                    result["lead_time_weeks"] = int(matches[0])
                elif "产能" in pattern:
                    result["capacity_impact_pct"] = int(matches[0])
                elif len(matches[0]) == 2:
                    result["start_price"] = float(matches[0][0])
                    result["peak_price"] = float(matches[0][1])
        
        return result if result else None
    
    @classmethod
    def extract_time(cls, text: str) -> Optional[str]:
        """从文本中自动提取时间，转换为YYYYQn格式"""
        # 匹配 2017Q3
        q_match = re.search(r"(20\d{2})Q([1-4])", text)
        if q_match:
            return f"{q_match.group(1)}Q{q_match.group(2)}"
        
        # 匹配 2021年3月 / 2021年3季度
        year_match = re.search(r"(20\d{2})年", text)
        if year_match:
            year = year_match.group(1)
            if "1季度" in text or "Q1" in text or "一季度" in text:
                return f"{year}Q1"
            elif "2季度" in text or "Q2" in text or "二季度" in text:
                return f"{year}Q2"
            elif "3季度" in text or "Q3" in text or "三季度" in text:
                return f"{year}Q3"
            elif "4季度" in text or "Q4" in text or "四季度" in text:
                return f"{year}Q4"
            # 月份转季度
            month_match = re.search(r"(\d{1,2})月", text)
            if month_match:
                month = int(month_match.group(1))
                quarter = (month - 1) // 3 + 1
                return f"{year}Q{quarter}"
            return year
        
        return None


class RCAAnalyzer:
    """自动RCA根因分析模块，覆盖涨跌双向周期"""
    
    # 所有配置从config.json读取
    ROOT_CAUSE_KEYWORDS = CONFIG.get("root_cause_keywords", {})
    DOWNTURN_CAUSE_KEYWORDS = CONFIG.get("downturn_cause_keywords", {})
    CATALYST_KEYWORDS = CONFIG.get("catalyst_keywords", [])
    AMPLIFIER_KEYWORDS = CONFIG.get("amplifier_keywords", [])
    FALSE_NARRATIVES = CONFIG.get("false_narratives", [])
    WARNING_TEMPLATES = CONFIG.get("warning_templates", {})
    
    @classmethod
    def classify_cause(cls, text: str) -> Dict:
        """自动分类原因类型，支持涨跌双向"""
        result = {
            "root_cause": [],
            "downturn_cause": [],
            "catalysts": [],
            "amplifiers": [],
            "false_narratives": [],
            "cycle_direction": "上涨"  # 默认上涨
        }
        
        # 判断周期方向
        if any(kw in text for kw in ["降价", "价格战", "产能过剩", "库存高企", "去库存", "下跌"]):
            result["cycle_direction"] = "下跌"
        
        # 上涨根因
        for cause_type, keywords in cls.ROOT_CAUSE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    result["root_cause"].append(cause_type)
                    break
        
        # 下跌根因
        for cause_type, keywords in cls.DOWNTURN_CAUSE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    result["downturn_cause"].append(cause_type)
                    break
        
        # 催化剂
        for kw in cls.CATALYST_KEYWORDS:
            if kw in text:
                result["catalysts"].append(kw)
        
        # 放大器
        for kw in cls.AMPLIFIER_KEYWORDS:
            if kw in text:
                result["amplifiers"].append(kw)
        
        # 错误传言
        for narr in cls.FALSE_NARRATIVES:
            if narr in text:
                result["false_narratives"].append(narr)
        
        # 去重
        for k in result:
            if isinstance(result[k], list):
                result[k] = list(set(result[k]))
        
        return result
    
    @classmethod
    def determine_cycle_type(cls, cause_analysis: Dict) -> str:
        """根据根因判断周期类型，支持涨跌双向"""
        if cause_analysis["cycle_direction"] == "下跌":
            if "产能过剩" in cause_analysis["downturn_cause"]:
                return "产能过剩型下跌"
            elif "需求下滑" in cause_analysis["downturn_cause"]:
                return "需求疲软型下跌"
            elif "价格战" in cause_analysis["downturn_cause"]:
                return "价格战型下跌"
            elif "黑天鹅需求冲击" in cause_analysis["downturn_cause"]:
                return "需求冲击型下跌"
            else:
                return "混合型下跌"
        else:
            # 上涨周期
            if "产能收缩" in cause_analysis["root_cause"] or "产能出清" in cause_analysis["root_cause"]:
                return "供给收缩型上涨"
            elif "需求错配" in cause_analysis["root_cause"]:
                return "供需错配+黑天鹅型上涨"
            elif "成本推动" in cause_analysis["root_cause"]:
                return "成本推动型上涨"
            elif "需求革命" in cause_analysis["root_cause"]:
                return "需求革命型上涨"
            elif "政策/贸易" in cause_analysis["root_cause"]:
                return "政策驱动型上涨"
            else:
                return "混合型上涨"
    
    @classmethod
    def generate_warning_template(cls, cycle_type: str, signals: List[str]) -> List[Dict]:
        """根据周期类型自动生成预警模板，从配置文件读取"""
        return cls.WARNING_TEMPLATES.get(cycle_type, [])


class AutoKnowledgeGraphUpdater:
    """自动知识图谱更新器"""
    
    def __init__(self, kg_path: str):
        self.kg_path = kg_path
        with open(kg_path, 'r', encoding='utf-8') as f:
            self.kg = json.load(f)
        self.next_event_id = self._get_next_id("EVT")
        self.next_case_id = self._get_next_id("CASE", prefix="CASE")
        self.next_caus_id = self._get_next_id("CAUS")
    
    def _get_next_id(self, prefix: str, case_prefix: bool = False) -> int:
        """获取下一个ID"""
        max_id = 0
        if case_prefix:
            key = "case_studies"
            id_field = "case_id"
            id_prefix = "CASE"
        elif prefix == "EVT":
            key = "events"
            id_field = "id"
            id_prefix = "EVT"
        else:
            key = "causal_relations"
            id_field = "id"
            id_prefix = "CAUS"
            
        for item in self.kg.get(key, []):
            id_str = item.get(id_field, "")
            if id_str.startswith(id_prefix):
                try:
                    num = int(id_str[len(id_prefix):])
                    max_id = max(max_id, num)
                except:
                    pass
        return max_id + 1
    
    def add_event(self, event_data: Dict) -> str:
        """添加一个新事件"""
        event_id = f"EVT{self.next_event_id:03d}"
        self.next_event_id += 1
        
        event = {
            "id": event_id,
            "time": event_data.get("time", "unknown"),
            "subject": event_data.get("subject", ""),
            "predicate": event_data.get("predicate", "价格波动"),
            "object": event_data.get("object"),
            "description": event_data.get("description", ""),
            "confidence": event_data.get("confidence", "B"),
            "source": event_data.get("source", "自动收集"),
        }
        
        # 添加价格数据（如果有）
        price_data = event_data.get("price_data")
        if price_data:
            event.update(price_data)
        
        self.kg["events"].append(event)
        return event_id
    
    def add_case_study(self, case_data: Dict) -> str:
        """添加一个完整的标杆案例"""
        case_id = f"CASE{self.next_case_id:03d}"
        self.next_case_id += 1
        
        case = {
            "case_id": case_id,
            "case_name": case_data.get("case_name", ""),
            "category": case_data.get("category", ""),
            "cycle_type": case_data.get("cycle_type", "混合型"),
            "start_time": case_data.get("start_time", ""),
            "peak_time": case_data.get("peak_time", ""),
            "end_time": case_data.get("end_time", ""),
            "rise_duration_months": case_data.get("rise_duration_months", 0),
            "max_price_increase_pct": case_data.get("max_price_increase_pct", 0),
            "root_cause": ",".join(case_data.get("root_cause", [])),
            "catalyst": ",".join(case_data.get("catalysts", [])),
            "amplifier": ",".join(case_data.get("amplifiers", [])),
            "false_narratives": case_data.get("false_narratives", []),
            "warning_template": case_data.get("warning_template", []),
            "auto_generated": True,
            "generated_time": datetime.now().isoformat()
        }
        
        self.kg["case_studies"].append(case)
        return case_id
    
    def add_causal_relation(self, from_events: List[str], to_events: List[str], relation_type: str, description: str) -> str:
        """添加因果关系"""
        caus_id = f"CAUS{self.next_caus_id:03d}"
        self.next_caus_id += 1
        
        # 自动时间校验
        event_time_map = {}
        for evt in self.kg["events"]:
            event_time_map[evt["id"]] = evt.get("time", "")
        
        # 简单时间校验
        def time_to_q(t_str):
            match = re.match(r"(\d{4})Q(\d)", t_str)
            if match:
                return int(match.group(1)) * 4 + int(match.group(2))
            return 0
        
        max_from = max([time_to_q(event_time_map.get(e, "")) for e in from_events if e in event_time_map], default=0)
        min_to = min([time_to_q(event_time_map.get(e, "")) for e in to_events if e in event_time_map], default=99999)
        time_valid = max_from <= min_to
        
        relation = {
            "id": caus_id,
            "from_event": ",".join(from_events),
            "to_event": ",".join(to_events),
            "relation_type": relation_type,
            "strength": "中",
            "time_order_valid": time_valid,
            "description": description,
            "auto_generated": True
        }
        
        self.kg["causal_relations"].append(relation)
        return caus_id, time_valid
    
    def save(self):
        """保存更新后的知识图谱"""
        # 更新元数据
        self.kg["metadata"]["version"] = "1.3"
        self.kg["metadata"]["update_time"] = datetime.now().strftime("%Y-%m-%d")
        self.kg["metadata"]["update_note"] = "自动工作流新增事件和案例"
        
        # 更新验证结果
        total_events = len(self.kg["events"])
        a_count = sum(1 for e in self.kg["events"] if e.get("confidence") == "A")
        b_count = sum(1 for e in self.kg["events"] if e.get("confidence") == "B")
        c_count = sum(1 for e in self.kg["events"] if e.get("confidence") == "C")
        valid_caus = sum(1 for r in self.kg["causal_relations"] if r.get("time_order_valid", True))
        
        self.kg["validation_result"] = {
            "total_events": total_events,
            "events_with_timestamp": sum(1 for e in self.kg["events"] if e.get("time") and e["time"] != "unknown"),
            "events_with_confidence": total_events,
            "a_level_events": a_count,
            "b_level_events": b_count,
            "c_level_events": c_count,
            "total_case_studies": len(self.kg["case_studies"]),
            "total_causal_relations": len(self.kg["causal_relations"]),
            "time_order_valid_relations": valid_caus,
            "time_order_invalid_relations": len(self.kg["causal_relations"]) - valid_caus,
            "validation_passed": (len(self.kg["causal_relations"]) - valid_caus) == 0
        }
        
        with open(self.kg_path, 'w', encoding='utf-8') as f:
            json.dump(self.kg, f, ensure_ascii=False, indent=2)
        
        return self.kg["validation_result"]


class AutoCyclePipeline:
    """全自动周期分析pipeline主类"""
    
    def __init__(self, kg_path: str):
        self.kg_path = kg_path
        self.discovery = EventDiscovery()
        self.grader = InformationGrader()
        self.rca = RCAAnalyzer()
        self.updater = AutoKnowledgeGraphUpdater(kg_path)
        self.analyzer = ComponentCycleAnalyzer(kg_path)
        
        print(f"🚀 自动周期分析pipeline初始化完成")
        print(f"📊 当前知识图谱版本：{self.updater.kg['metadata']['version']}")
        print(f"📈 已有事件：{len(self.updater.kg['events'])}个")
        print(f"📚 已有案例：{len(self.updater.kg['case_studies'])}个")
    
    def manual_add_event_from_search_result(self, search_results: List[Dict]) -> Dict:
        """
        从搜索结果手动添加事件（因为自动搜索需要调用LLM/搜索API，
        这里提供入口，把搜索结果喂进来自动处理）
        """
        print("\n🔍 开始处理新事件...")
        added_events = []
        added_cases = []
        invalid_caus = []
        
        for result in search_results:
            # 1. 信息提取和分级
            text = result.get("content", "") + result.get("title", "")
            source = result.get("source", "")
            confidence = self.grader.grade_source(source)
            event_time = self.grader.extract_time(text)
            price_data = self.grader.extract_price_data(text)
            
            # 2. 构建事件
            event_data = {
                "time": event_time or "unknown",
                "description": result.get("title", "")[:100],
                "confidence": confidence,
                "source": source,
                "price_data": price_data,
                "subject": result.get("category", ""),
                "predicate": "价格波动"
            }
            
            # 3. 添加事件
            event_id = self.updater.add_event(event_data)
            added_events.append(event_id)
            print(f"  ✅ 添加事件 {event_id}: {event_data['description'][:50]}... [{confidence}级]")
        
        # 4. 保存
        validation = self.updater.save()
        
        print(f"\n🎉 处理完成！")
        print(f"📊 新增事件：{len(added_events)}个")
        print(f"✅ 时序校验：{validation['time_order_valid_relations']}/{validation['total_causal_relations']}条因果关系有效")
        
        return {
            "added_events": added_events,
            "added_cases": added_cases,
            "validation": validation
        }
    
    def auto_analyze_new_event(self, event_description: str, category: str, source: str = "自动分析") -> Dict:
        """
        一键自动分析单个新事件：输入事件描述，自动完成RCA分析、生成预警、入库
        这是最常用的入口函数
        """
        print(f"\n🤖 开始自动分析新事件：{event_description[:50]}...")
        
        # 1. 信息提取
        event_time = self.grader.extract_time(event_description)
        confidence = self.grader.grade_source(source)
        price_data = self.grader.extract_price_data(event_description)
        
        # 2. RCA原因分析
        cause_analysis = self.rca.classify_cause(event_description)
        cycle_type = self.rca.determine_cycle_type(cause_analysis)
        warning_template = self.rca.generate_warning_template(cycle_type, cause_analysis["root_cause"] + cause_analysis["downturn_cause"])
        
        # 3. 添加事件
        event_data = {
            "time": event_time or "unknown",
            "description": event_description,
            "confidence": confidence,
            "source": source,
            "price_data": price_data,
            "subject": category,
            "predicate": "价格波动"
        }
        event_id = self.updater.add_event(event_data)
        
        # 4. 如果信息足够完整，添加为标杆案例
        case_id = None
        if event_time and price_data and cause_analysis["root_cause"]:
            case_data = {
                "case_name": event_description[:30],
                "category": category,
                "cycle_type": cycle_type,
                "start_time": event_time,
                "peak_time": event_time,
                "end_time": "",
                "max_price_increase_pct": price_data.get("price_change_pct", 0) if price_data else 0,
                **cause_analysis,
                "warning_template": warning_template
            }
            case_id = self.updater.add_case_study(case_data)
            print(f"  📚 添加为标杆案例：{case_id} [{cycle_type}]")
        
        # 5. 保存
        validation = self.updater.save()
        
        print(f"  ✅ 事件ID：{event_id}")
        print(f"  🧠 根因分析：{cause_analysis['root_cause']}")
        print(f"  ⚡ 催化剂：{cause_analysis['catalysts']}")
        print(f"  📢 排除传言：{cause_analysis['false_narratives']}")
        print(f"  🎯 周期类型：{cycle_type}")
        print(f"  ⚠️  生成预警规则：{len(warning_template)}条")
        
        return {
            "event_id": event_id,
            "case_id": case_id,
            "cycle_type": cycle_type,
            "cause_analysis": cause_analysis,
            "warning_template": warning_template,
            "validation": validation
        }
    
    def run_full_validation(self) -> Dict:
        """运行完整的知识图谱校验"""
        print("\n🔍 运行完整知识图谱校验...")
        result = self.analyzer.run_mcp_analysis("validate_causality", {})
        print(f"✅ 因果关系校验：{result['valid_relations']}/{result['total_relations']}条有效")
        if result['invalid_relations'] > 0:
            print(f"❌ 发现{result['invalid_relations']}条时序错误：")
            for inv in result.get('invalid_details', []):
                print(f"   - {inv['relation_id']}: {inv['description']}")
        return result


def demo():
    """演示自动pipeline功能"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kg_path = os.path.join(base_dir, "graphiti", "cycle_knowledge_graph.json")
    
    pipeline = AutoCyclePipeline(kg_path)
    
    # 演示：自动分析一个新事件
    print("\n" + "="*60)
    print("演示：自动分析一个新事件")
    print("="*60)
    
    test_event = """
    2018年MLCC涨价事件：2017Q2村田、TDK、太阳诱电砍中低端MLCC产能转车规，
    2017Q3三星停电事故影响3.5%产能，2018Q1国巨华新科涨价20%-100%，
    0402通用MLCC涨幅200%-500%，当时市场传言游资爆炒，事后证明是产能主动调整，
    2018Q3价格见顶后下跌。
    """
    
    result = pipeline.auto_analyze_new_event(
        event_description=test_event,
        category="MLCC",
        source="产业事后复盘"
    )
    
    # 完整校验
    pipeline.run_full_validation()
    
    print("\n🎉 自动pipeline演示完成！")
    print("\n💡 使用方法：")
    print("1. 调用 auto_analyze_new_event() 一键分析单个事件并入库")
    print("2. 调用 manual_add_event_from_search_result() 批量导入搜索结果")
    print("3. 调用 run_full_validation() 校验整个知识图谱")
    print("4. 知识图谱会自动更新版本、自动校验因果时序、自动生成预警规则")


if __name__ == "__main__":
    demo()
