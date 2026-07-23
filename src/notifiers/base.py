# -*- coding=utf-8 -*-
"""通知器抽象基类: 定义推送模块的统一接口"""
from abc import ABC, abstractmethod
from src.models import TenderItem


class BaseNotifier(ABC):
    """通知器基类，新通知器只需继承此类并实现 notify"""

    @abstractmethod
    def notify(self, items: list[TenderItem], config: dict) -> bool:
        """推送通知，传入筛选后的相关项目列表

        Args:
            items: 筛选后的 TenderItem 列表
            config: 配置字典

        Returns:
            是否推送成功
        """
        ...
