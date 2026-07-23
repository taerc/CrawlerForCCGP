# -*- coding=utf-8 -*-
"""数据模型定义"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TenderItem:
    """招标公告数据项"""
    index: int                        # 序号
    notice_type: str                  # 公告类型
    title: str                        # 名称
    date: str                         # 日期
    buyer: str                        # 招标人
    agent: str                        # 代理机构
    region: str                       # 区域
    detail_url: str                   # 详情链接
    summary: str                      # 项目概况(列表页摘要)
    detail_content: str = ""          # 详情页正文
    analysis: Optional["AnalysisResult"] = None  # LLM 分析结果


@dataclass
class AnalysisResult:
    """LLM 分析结果"""
    related: bool                     # 是否相关
    category: str = ""                # 匹配领域
    reason: str = ""                  # 判断理由
    confidence: float = 0.0           # 置信度
