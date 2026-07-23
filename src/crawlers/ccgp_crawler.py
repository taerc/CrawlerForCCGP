# -*- coding=utf-8 -*-
"""中国政府采购网 (ccgp.gov.cn) 爬虫实现"""
import math
from datetime import datetime, timedelta
from urllib.parse import urlparse
from lxml import etree

from src.models import TenderItem
from src.utils.http import open_url, decode_response
from src.crawlers.base import BaseCrawler


class CCGPCrawler(BaseCrawler):
    """中国政府采购网爬虫"""

    SEARCH_URL = 'http://search.ccgp.gov.cn/bxsearch?'

    # 详情页正文候选 XPath 选择器(不同公告类型可能不同)
    DETAIL_XPATHS = [
        '//div[@class="vF_decontent_main"]',
        '//div[contains(@class, "vF_decontent")]',
        '//div[contains(@class, "content")]',
        '//div[@class="content"]',
        '//div[@id="content"]',
    ]

    def search(self, config: dict) -> list[TenderItem]:
        """抓取公告列表(支持逗号分隔的多关键词分开检索后合并去重)"""
        crawler_cfg = config.get('crawler', {})
        kw_raw = crawler_cfg.get('kw', '')
        keywords = [k.strip() for k in kw_raw.split(',') if k.strip()]

        # 空关键词 = 全部，保持单次空检索的原行为
        if not keywords:
            keywords = ['']

        all_items: list[TenderItem] = []
        seen_keys: set = set()
        multi = len(keywords) > 1

        for idx, kw in enumerate(keywords, 1):
            if multi:
                print(f"\n--- 关键词 [{idx}/{len(keywords)}]: {kw or '(全部)'} ---")
            items = self._search_single(kw, config)
            for item in items:
                # 批内去重: 以 detail_url 为主键，为空时回退到 title
                key = item.detail_url or item.title
                if key and key in seen_keys:
                    continue
                if key:
                    seen_keys.add(key)
                all_items.append(item)

        # 合并后重排序号，保证连续
        for i, item in enumerate(all_items, 1):
            item.index = i

        if multi:
            print(f"\n多关键词合并去重完成，共 {len(all_items)} 条公告")

        return all_items

    def _search_single(self, kw: str, config: dict) -> list[TenderItem]:
        """按单个关键词检索公告列表"""
        crawler_cfg = config.get('crawler', {})
        days_back = crawler_cfg.get('days_back', 7)
        max_pages = crawler_cfg.get('max_pages', 10)

        curr_date = datetime.now()
        start_date = curr_date - timedelta(days=days_back)
        start_time = start_date.strftime("%Y:%m:%d")
        end_time = curr_date.strftime("%Y:%m:%d")

        params = {
            'searchtype': 1,
            'page_index': 1,
            'bidSort': 0,
            'buyerName': '',
            'projectId': '',
            'pinMu': 0,
            'bidType': crawler_cfg.get('bid_type', 1),  # 1=公开招标
            'dbselect': 'bidx',
            'kw': kw,
            'start_time': start_time,
            'end_time': end_time,
            'timeType': 6,
            'displayZone': crawler_cfg.get('display_zone', ''),
            'zoneId': crawler_cfg.get('zone_id', ''),
            'pppStatus': 0,
            'agentName': ''
        }

        resp = open_url(self.SEARCH_URL, params)
        resp.raise_for_status()
        html = decode_response(resp)
        tree = etree.HTML(html)

        # 获取总数据量
        try:
            total = int(tree.xpath('/html/body/div[5]/div[1]/div/p[1]/span[2]')[0].text.strip())
        except (IndexError, ValueError):
            print("未找到数据总数")
            return []

        if total <= 0:
            return []

        pagesize = math.ceil(total / 20)
        pages_to_crawl = min(pagesize, max_pages)
        print(f"共 {total} 条数据, {pagesize} 页, 本次抓取前 {pages_to_crawl} 页")

        items = []
        for curr_page in range(1, pages_to_crawl + 1):
            li_list = tree.xpath('/html/body/div[5]/div[2]/div/div/div[1]/ul/li')
            print(f"正在处理第 {curr_page}/{pages_to_crawl} 页, {len(li_list)} 条数据")

            for li in li_list:
                item = self._parse_list_item(li, len(items))
                if item:
                    items.append(item)
                    print(f"  [{len(items)}] {item.title}")

            # 翻页
            if curr_page < pages_to_crawl:
                params['page_index'] = curr_page + 1
                resp = open_url(self.SEARCH_URL, params, refer=resp.url)
                if resp.status_code != 200:
                    continue
                html = decode_response(resp)
                tree = etree.HTML(html)

        return items

    def _parse_list_item(self, li, index: int) -> TenderItem | None:
        """解析列表页单条数据"""
        try:
            title_el = li[0]
            summary_el = li[1]
            span = li[2]
            info = span.xpath('string()').replace(' ', '').replace('\r', '').replace('\n', '').replace('\t', '')

            str1 = info[:info.index('公告')]
            str2 = info[info.index('公告'):].replace('公告', '')
            strs = str2.split('|')
            parts = str1.split('|')

            if len(strs) <= 1:
                return None

            link_href = title_el.get('href', '')
            title = title_el.xpath('string()').strip()

            # 跳过已中标/成交的公告(已被别人中标,不再关注)
            if '中标' in title or '成交' in title:
                return None

            return TenderItem(
                index=index + 1,
                notice_type='公告',
                title=title,
                date=parts[0][:10] if len(parts) > 0 else '',
                buyer=parts[1].replace('采购人：', '') if len(parts) > 1 else '',
                agent=parts[2].replace('代理机构：', '') if len(parts) > 2 else '',
                region=strs[0],
                detail_url=link_href,
                summary=(summary_el.text or '').strip(),
            )
        except (ValueError, IndexError, AttributeError) as e:
            print(f"  跳过格式异常的条目: {e}")
            return None

    def fetch_detail(self, item: TenderItem, config: dict) -> str:
        """抓取公告详情页正文"""
        crawler_cfg = config.get('crawler', {})
        max_length = crawler_cfg.get('detail_max_length', 5000)

        if not item.detail_url:
            return ""

        # 从详情 URL 提取 host
        parsed = urlparse(item.detail_url)
        host = parsed.hostname or 'www.ccgp.gov.cn'

        resp = open_url(item.detail_url, host=host)
        if resp.status_code != 200:
            print(f"详情页请求失败: {resp.status_code} - {item.detail_url}")
            return ""

        html = decode_response(resp)
        tree = etree.HTML(html)

        # 尝试多个候选 XPath，取最长文本
        best_text = ""
        for xpath in self.DETAIL_XPATHS:
            nodes = tree.xpath(xpath)
            for node in nodes:
                text = node.xpath('string()').strip()
                text = ' '.join(text.split())  # 合并空白字符
                if len(text) > len(best_text):
                    best_text = text

        # 截取最大长度
        if len(best_text) > max_length:
            best_text = best_text[:max_length]

        return best_text
