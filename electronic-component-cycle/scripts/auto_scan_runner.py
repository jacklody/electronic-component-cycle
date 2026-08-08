#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动扫描运行脚本：去重 → pipeline分析 → 红色预警检测 → 日志写入
由外部 agent 调用，不在项目源码中
"""
import json
import sys
import os
from datetime import datetime

# 确保 scripts/ 在 sys.path 中
scripts_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, scripts_dir)

# 修复 cycle_analyzer.py 中中文引号语法问题：用 exec 绕过直接 import
# 先读取源码，替换中文引号后再加载
_cycle_analyzer_path = os.path.join(scripts_dir, "cycle_analyzer.py")
_auto_pipeline_path = os.path.join(scripts_dir, "auto_cycle_pipeline.py")

def _load_module_from_file(filepath, modname):
    """从文件加载模块，修复中文引号语法问题"""
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    # 替换Unicode中文引号
    code = code.replace('\u201c', "'").replace('\u201d', "'")
    # 修复已知的问题行：替换"不要相信"游资炒作"传言"中的内层双引号
    code = code.replace('"不要相信"游资炒作"传言，核心是供给收缩"',
                         '"不要相信游资炒作传言，核心是供给收缩"')
    code = code.replace('"华为制裁导致缺货"', "'华为制裁导致缺货'")
    code = code.replace('"缺芯持续3-5年"', "'缺芯持续3-5年'")
    code = code.replace('"美国卡脖子导致"', "'美国卡脖子导致'")
    code = code.replace('"国巨又要像2018年一样炒MLCC，涨3-5倍"',
                         "'国巨又要像2018年一样炒MLCC，涨3-5倍'")
    code = code.replace('"人民币汇率贬值/铜价上涨导致面板涨价"',
                         "'人民币汇率贬值/铜价上涨导致面板涨价'")
    code = code.replace('"AI将导致芯片永久通胀，再也不会降价"',
                         "'AI将导致芯片永久通胀，再也不会降价'")
    code = code.replace('"游资爆炒MLCC"', "'游资爆炒MLCC'")
    code = code.replace('"渠道囤货居奇"', "'渠道囤货居奇'")
    # 修复 _get_next_id 双重参数 bug
    code = code.replace('self.next_case_id = self._get_next_id("CASE", prefix="CASE")',
                         'self.next_case_id = self._get_next_id("CASE", case_prefix=True)')
    # 修复 _parse_category NoneType bug
    code = code.replace('if k in obj:', 'if obj and k in obj:')
    import types
    mod = types.ModuleType(modname)
    mod.__file__ = filepath
    mod.__dict__['__name__'] = modname
    exec(compile(code, filepath, 'exec'), mod.__dict__)
    return mod

cycle_analyzer_mod = _load_module_from_file(_cycle_analyzer_path, 'cycle_analyzer')
sys.modules['cycle_analyzer'] = cycle_analyzer_mod

auto_pipeline_mod = _load_module_from_file(_auto_pipeline_path, 'auto_cycle_pipeline')
AutoCyclePipeline = auto_pipeline_mod.AutoCyclePipeline

# ========== 配置 ==========
KG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "graphiti", "cycle_knowledge_graph.json")
REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")
ALERTS_LOG = os.path.join(REPORTS_DIR, "alerts.log")

# ========== 步骤1: 提取已入库事件去重key ==========
with open(KG_PATH, 'r', encoding='utf-8') as f:
    kg = json.load(f)

existing_keys = set()
for evt in kg.get("events", []):
    desc = evt.get("description", "")
    existing_keys.add(desc[:30])

print(f"已有入库事件: {len(existing_keys)} 个去重key")

# ========== 步骤2: WebSearch 结果汇总 ==========
# 从搜索结果中提取的新事件列表 (description, category, source)
raw_events = [
    ("2026年8月，存储芯片Q2大涨：DRAM涨57%，NAND涨67%，原厂锁5年长协，美光签16份SCA约220亿美元，三星与五大CSP签5年滚动长协，SK海力士HBM4提前批量出货锁定10家核心客户多年长协", "DRAM", "东吴证券8月7日报告"),
    ("2026年8月5日，TrendForce报告：DRAM现货涨势放缓，DDR4/DDR3继续小幅上行，DDR5 16Gb现货均价$51.60环比涨0.19%，NAND Flash 512Gb TLC wafer涨4.55%至$20.125", "DRAM", "TrendForce 8月5日"),
    ("2026年8月7日，存储三巨头2027年产能已售罄，三星、SK海力士、美光已完成2027年全年产能分配谈判，DRAM和HBM产能均提前售罄，英伟达测试HBM规格下调的Rubin Ultra GPU备选方案", "HBM", "财联社8月7日"),
    ("2026年8月4日，三星在FMS2026发布zHBM，将高带宽内存垂直堆叠于AI加速器之上，SK海力士联手闪迪发布HBF首个标准规范，全球HBM产能缺口50%-60%", "HBM", "FMS 2026峰会"),
    ("2026年8月初，华强北显卡一日一价，RTX 5090卖3.5万一周涨4000，HBM挤占GDDR产能，16GB GDDR7模组从年初80-90美元涨至200-300美元，英伟达7月24日发GPU Kit涨价通知，AMD 8月1日起渠道价上调10%+", "DRAM", "21世纪经济报道8月初"),
    ("2026年8月7日，伯恩斯坦报告：存储涨价天花板快到，Q3 DRAM和NAND涨幅均收窄至约20%，较Q2大幅放缓，LTA价格上限压制涨价空间，消费端需求疲软", "NAND Flash", "伯恩斯坦8月7日"),
    ("2026年8月1日，三星电机全线MLCC出货价统一上调30%，覆盖消费电子、工控、汽车、AI服务器全品类，太阳诱电9月1日起调价，国巨7月1日全品类电容涨约50%，华新科消费MLCC涨5%-15%", "MLCC", "朝鲜日报/上海证券报8月4日"),
    ("2026年8月7日，MLCC价格冰火两重天：22μF、47μF中高容量MLCC普遍缺货，原厂暂停接单，1μF、10μF普通消费级供应平稳甚至促销，村田三星太阳诱电6月出货创五年新高，BB Ratio达1.30+", "MLCC", "21世纪经济报道8月7日"),
    ("2026年8月3日，盛群半导体官宣全产品线MCU涨价10%-20%，交期延长至6-8个月，2027年晶圆代工涨价已纳入定价策略", "通用MCU", "盛群半导体8月3日公告"),
    ("2026年7月24日，TechInsights报告：ST STM32G0交期从18周延长到32周，因马来西亚封测厂火灾，多家传感器厂商启动替代方案验证，换料周期6-8周", "通用MCU", "TechInsights 7月24日"),
    ("2026年8月14日起，Microchip全产品线涨价，覆盖MCU、模拟、功率、存储，反映原材料、人工、物流成本持续上升", "通用MCU", "Market Update 8月3日"),
    ("2026年7月起，全球超20家功率半导体企业开启年内第二轮涨价，幅度10%-25%，覆盖硅基MOSFET/IGBT、SiC、GaN全品类，英飞凌7月1日二轮提价，TI同期跟进，华润微全品类涨15%", "MOSFET", "新浪财经7月16日"),
    ("2026年8月3日，超22家功率器件企业涨价，斯达半导IGBT/SiC MOSFET涨15%起，芯联集成Q3上调15%-25%，扬杰科技全系列涨10%-15%，基本半导体最高涨25%", "IGBT", "EET China 7月14日"),
    ("2026年8月，ST MCU交期约54周，Infineon MOSFET交期24-32周、IGBT交期26-52周，JST GHR系列交期从5-6个月延至12个月，KEMET钽电容8月1日起涨25%", "功率器件", "UniKeyic Market Update 8月3日"),
    ("2026年8月4-6日，成熟制程晶圆代工涨价蔓延至2027年，世界先进董事长明确2027年涨幅将比今年更大，联电8英寸涨10%-15%、12英寸涨5%-10%，力积电DRAM代工涨45%", "晶圆代工", "EET China 8月6日"),
    ("2026年8月7日，钽价半年飙涨158%，国内钽锭6150元/千克较年初涨138.83%，刚果金鲁巴亚矿区两次塌方占全球钽供给15%，AI服务器钽电容用量是传统服务器的100倍，KEMET对AI专用聚合物钽电容第四轮调价涨幅25%-40%", "钽电容", "上海证券报/钛媒体8月7日"),
    ("2026年8月，PCB超级周期持续，电子布年内六轮涨价，8月主流型号单月涨17%-18%，年内累计涨幅165%，全行业库存压缩至3-7天，高端低介电电子布订单排产至2027年", "PCB", "花旗/证券日报8月7日"),
    ("2026年8月3日，OLED电视面板连续8季度下跌，55寸降至$376环比跌2.2%，65寸降至$552环比跌2.3%，无偏光片型低成本OLED产品拉低价格，液晶电视面板价格持平", "OLED面板", "日经中文网8月3日"),
    ("2026年8月初，IT面板需求走弱，笔记本库存高企，8月IT面板价格持平，友达群创加速削减LCD产能转先进封装，台积电计划2027年关停部分8英寸厂", "LCD面板", "DigiTimes 8月8日"),
    ("2026年8月，被动元件全品类涨价，电感磁珠跟涨，国巨旗下PULSE对铁氧体磁珠涨价因白银价格飙升，AI服务器用高功率电感持续涨价，白银2025年累计涨超130%推高厚膜电阻、片式电感、磁珠制造成本", "电感", "AXTEK/东方财富8月8日"),
    ("2026年8月初，Xilinx FPGA XC7A/XC7Z市场价涨40%，交期70周，渠道库存有限，ADI部分产品交期超6个月报价有效期缩短", "FPGA", "UniKeyic Market Update 8月3日"),
    ("2026年8月，车规芯片暴涨180%，车规DRAM/NAND闪存Q2涨幅180%部分型号300%，AI挤占半导体产能，小米SU7全系涨4000元，问界M9涨1万元，车企集体涨价", "车规MCU", "华尔街见闻/华夏时报8月"),
]

# ========== 步骤3: 去重 ==========
new_events = []
for desc, cat, src in raw_events:
    key = desc[:30]
    if key not in existing_keys:
        new_events.append((desc, cat, src))
        existing_keys.add(key)  # 防止本次扫描内重复
    else:
        print(f"  跳过已入库: {key}...")

print(f"\n去重后新增事件: {len(new_events)} 条 (原始 {len(raw_events)} 条)")

# ========== 步骤4: 调用 Pipeline 分析 ==========
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
pipeline = AutoCyclePipeline(KG_PATH)

results = []
red_alerts = []
orange_count = 0
green_count = 0

for desc, cat, src in new_events:
    try:
        result = pipeline.auto_analyze_new_event(
            event_description=desc,
            category=cat,
            source=f"WebSearch自动扫描-{src}"
        )
        results.append(result)
        
        # 检查红色预警
        is_red = False
        for w in result.get("warning_template", []):
            level = w.get("level", "")
            if "🔴红色预警" in level:
                is_red = True
                red_alerts.append({
                    "category": cat,
                    "cycle_type": result.get("cycle_type", ""),
                    "description": desc,
                    "signal": w.get("signal", ""),
                    "prediction": w.get("prediction", ""),
                    "level": level
                })
            elif "🟠橙色预警" in level:
                orange_count += 1
            elif "🟢绿色预警" in level:
                green_count += 1
        
        print(f"  {'🔴' if is_red else '✅'} {cat} | {result.get('cycle_type','')} | {desc[:50]}...")
    except Exception as e:
        print(f"  ❌ 处理失败: {cat} - {str(e)}")
        results.append(None)

print(f"\n===== 分析完成 =====")
print(f"新增事件入库: {sum(1 for r in results if r is not None)} 条")
print(f"红色预警: {len(red_alerts)} 条")
print(f"橙色预警: {orange_count} 条")
print(f"绿色预警: {green_count} 条")

# ========== 步骤5: 红色预警 → alerts.log ==========
os.makedirs(REPORTS_DIR, exist_ok=True)

now = datetime.now()
feishu_success = False

if red_alerts:
    with open(ALERTS_LOG, 'a', encoding='utf-8') as f:
        for alert in red_alerts:
            line = f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] [{alert['category']}] [{alert['cycle_type']}] [{alert['description'][:80]}] [{alert['signal']}] [{alert['prediction']}]\n"
            f.write(line)
    print(f"\n已写入 alerts.log: {len(red_alerts)} 条红色预警")

# ========== 步骤6: daily_scan 日志 + run_full_validation ==========
hour_str = "08" if now.hour < 12 else "20"
daily_scan_file = os.path.join(REPORTS_DIR, f"daily_scan_{now.strftime('%Y%m%d')}_{hour_str}.log")

# 运行完整校验
try:
    validation_result = pipeline.run_full_validation()
except Exception as e:
    validation_result = {"error": str(e)}
    print(f"  ⚠️ run_full_validation 异常: {e}")

with open(daily_scan_file, 'w', encoding='utf-8') as f:
    f.write(f"========== 电子元器件周期自动扫描日报 ==========\n")
    f.write(f"扫描时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"查询query数: 12\n")
    f.write(f"WebSearch返回结果数: ~60\n")
    f.write(f"去重后新增事件数: {len(new_events)}\n")
    f.write(f"入库成功数: {sum(1 for r in results if r is not None)}\n")
    f.write(f"\n----- 红色预警事件 -----\n")
    if red_alerts:
        for alert in red_alerts:
            f.write(f"  品类: {alert['category']} | 周期类型: {alert['cycle_type']} | 信号: {alert['signal']} | 预测: {alert['prediction']}\n")
            f.write(f"  事件摘要: {alert['description'][:100]}\n")
    else:
        f.write("  无\n")
    f.write(f"\n橙色预警数量: {orange_count}\n")
    f.write(f"绿色预警数量: {green_count}\n")
    f.write(f"\n----- 完整校验结果 -----\n")
    f.write(json.dumps(validation_result, ensure_ascii=False, indent=2, default=str))
    f.write("\n")

print(f"\n已写入: {daily_scan_file}")

# ========== 输出汇总 ==========
print(f"\n===== 最终汇总 =====")
print(f"新增事件数: {sum(1 for r in results if r is not None)}")
print(f"红色预警数: {len(red_alerts)}")
print(f"飞书消息: 未发送 (需lark-im skill)")

# 输出红色预警详情供后续飞书通知使用
if red_alerts:
    print("\n===== 红色预警详情 =====")
    for i, alert in enumerate(red_alerts):
        print(f"[{i+1}] {alert['category']} | {alert['cycle_type']} | {alert['signal'][:60]}... | {alert['prediction'][:60]}...")
