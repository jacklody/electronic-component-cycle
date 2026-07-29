#!/usr/bin/env python3
"""运行知识图谱完整校验"""

import sys
import os
import json

# 添加 scripts 目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auto_cycle_pipeline import AutoCyclePipeline

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kg_path = os.path.join(base_dir, "graphiti", "cycle_knowledge_graph.json")

    pipeline = AutoCyclePipeline(kg_path)
    result = pipeline.run_full_validation()

    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()