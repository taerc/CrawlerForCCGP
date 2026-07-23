# -*- coding=utf-8 -*-
"""爬虫抽象基类: 定义检索模块的统一接口"""
from abc import ABC, abstractmethod
from src.models import TenderItem


class BaseCrawler(ABC):
    """爬虫基类，新站点爬虫只需继承此类并实现 search/fetch_detail"""

    @abstractmethod
    def search(self, config: dict) -> list[TenderItem]:
        """搜索公告列表，返回 TenderItem 列表(含详情链接)

        Args:
            config: 配置字典(config['crawler'])

        Returns:
            TenderItem 列表
        """
        ...

    @abstractmethod
    def fetch_detail(self, item: TenderItem, config: dict) -> str:
        """抓取公告详情页正文内容

        Args:
            item: 公告数据项(需含 detail_url)
            config: 配置字典

        Returns:
            详情页正文文本
        """
        ...
