# -*- coding=utf-8 -*-
"""分析器抽象基类: 定义分析模块的统一接口"""
from abc import ABC, abstractmethod
from src.models import TenderItem, AnalysisResult


class BaseAnalyzer(ABC):
    """分析器基类，新分析器只需继承此类并实现 analyze"""

    @abstractmethod
    def analyze(self, item: TenderItem, config: dict) -> AnalysisResult:
        """分析单个公告，返回分析结果

        Args:
            item: 公告数据项(需含 detail_content)
            config: 配置字典

        Returns:
            AnalysisResult
        """
        ...
