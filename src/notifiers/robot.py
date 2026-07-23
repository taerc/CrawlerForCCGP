#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钉钉机器人模块

提供钉钉机器人消息发送功能，包括签名计算和 Markdown 消息推送。
"""

import time
import hmac
import hashlib
import base64
from urllib.parse import quote_plus

import requests


class Robot:
    def __init__(self, access_token: str, secret: str = ""):
        """
        初始化钉钉机器人
        :param access_token: 钉钉机器人的access_token（必填）
        :param secret: 钉钉机器人的密钥（可选，未启用加签时为空）
        """
        if not access_token:
            raise ValueError("access_token 不能为空")
        self.access_token = access_token
        self.secret = secret

    def signature(self) -> str:
        """
        生成钉钉机器人签名
        :return: 完整的webhook URL
        """
        webhook_url = f"https://oapi.dingtalk.com/robot/send?access_token={self.access_token}"
        # 未配置加签密钥时，直接返回基础webhook URL
        if not self.secret:
            return webhook_url

        # 获取当前毫秒级时间戳
        timestamp = int(time.time() * 1000)
        string_to_sign = f"{timestamp}\n{self.secret}"

        # 使用HMAC-SHA256计算签名
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()

        # Base64编码
        sign = base64.b64encode(hmac_code).decode('utf-8')

        # URL编码签名
        sign_encoded = quote_plus(sign)

        hook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign_encoded}"
        return hook_url

    def send(self, params: dict) -> dict:
        """
        发送消息到钉钉群
        :param params: 钉钉消息体 (msgtype/markdown/at 等字段)
        :return: 钉钉接口返回的 JSON 结果
        """
        hook_url = self.signature()
        resp = requests.post(hook_url, json=params, timeout=10)
        result = resp.json()
        if result.get("errcode") != 0:
            print(f"钉钉消息发送失败: {result}")
        return result

    def send_markdown(
        self,
        title: str,
        text: str,
        at_mobiles: list = None,
        at_userids: list = None,
        is_at_all: bool = False
    ) -> dict:
        """
        发送Markdown文本
        :param title: 标题
        :param text: 文本内容
        :param at_mobiles: 需要@的用户手机号码列表
        :param at_userids: 需要@的用户id列表
        :param is_at_all: 是否需要@全体成员
        :return: 钉钉接口返回的 JSON 结果
        """
        params = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "atMobiles": at_mobiles if at_mobiles else [],
                "atUserIds": at_userids if at_userids else [],
                "isAtAll": is_at_all
            }
        }
        return self.send(params)
