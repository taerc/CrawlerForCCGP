# -*- coding=utf-8 -*-
"""HTTP 请求工具: 随机 UA + 延迟 + 编码检测"""
import random
import time
import requests
from chardet import detect


def get_request_headers(referer=None, host=None):
    """生成随机 HTTP 请求头"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36'
    ]
    ua = random.choice(user_agents)

    headers = {
        "User-Agent": ua,
        "Host": host or "search.ccgp.gov.cn",
        "Referer": referer if referer else "http://search.ccgp.gov.cn/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    return headers


def open_url(url, params=None, refer=None, host=None, delay=True):
    """发送 HTTP GET 请求并返回响应

    Args:
        url: 请求 URL
        params: 查询参数
        refer: Referer 地址
        host: Host 头
        delay: 是否随机延迟(避免反爬)
    """
    headers = get_request_headers(referer=refer, host=host)
    if delay:
        time.sleep(random.randint(2, 6))
    response = requests.get(url, headers=headers, params=params, allow_redirects=True)
    if response.status_code != 200:
        print(f"请求失败: {response.status_code} - {url}")
    return response


def decode_response(response):
    """检测并解码响应内容"""
    encoding = detect(response.content).get('encoding', 'utf-8')
    return response.content.decode(encoding, errors='replace')
