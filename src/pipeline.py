# -*- coding=utf-8 -*-
"""主流程编排: 检索 -> 分析 -> 推送"""
import time
import pandas as pd
from datetime import datetime

from src.config import load_config
from src.models import TenderItem
from src.crawlers.ccgp_crawler import CCGPCrawler
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.notifiers.email_notifier import EmailNotifier
from src.utils.excel import save_excel


def load_existing_data(file_path: str) -> pd.DataFrame | None:
    """加载已有的 Excel 数据"""
    try:
        return pd.read_excel(file_path)
    except Exception as e:
        print(f"读取历史数据文件失败: {e}")
        return None


def get_existing_titles(df: pd.DataFrame | None) -> set:
    """提取已有数据的标题"""
    if df is not None and '名称' in df.columns:
        return set(df['名称'].tolist())
    return set()


def filter_duplicates(items: list[TenderItem], existing_titles: set) -> list[TenderItem]:
    """过滤掉重复的数据"""
    return [item for item in items if item.title not in existing_titles]


def run():
    """主流程入口"""
    print("=" * 60)
    print(f"招标公告分析推送系统 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 加载配置
    config = load_config()

    # 2. 检索模块: 抓取列表
    print("\n[1/4] 检索模块 - 抓取公告列表...")
    crawler = CCGPCrawler()
    items = crawler.search(config)
    print(f"抓取到 {len(items)} 条公告")

    if not items:
        print("未抓取到数据，流程结束。")
        return

    # 去重
    storage_cfg = config.get('storage', {})
    history_file = storage_cfg.get('history_file', 'existing_data.xlsx')
    existing_df = load_existing_data(history_file)
    existing_titles = get_existing_titles(existing_df)
    items = filter_duplicates(items, existing_titles)
    print(f"去重后剩余 {len(items)} 条公告")

    if not items:
        print("无新数据，流程结束。")
        return

    # 3. 检索模块: 抓取详情
    crawler_cfg = config.get('crawler', {})
    if crawler_cfg.get('fetch_detail', True):
        print("\n[2/4] 检索模块 - 抓取公告详情...")
        for i, item in enumerate(items, 1):
            print(f"  [{i}/{len(items)}] 抓取详情: {item.title[:40]}")
            item.detail_content = crawler.fetch_detail(item, config)

    # 4. 分析模块: LLM 分析
    analyzer_cfg = config.get('analyzer', {})
    if not analyzer_cfg.get('enabled', True):
        print("\n[3/4] 分析模块未启用，跳过 LLM 分析。")
        relevant_items = items
    else:
        print("\n[3/4] 分析模块 - LLM 分析公告内容...")
        analyzer = LLMAnalyzer()
        relevant_items = []
        for i, item in enumerate(items, 1):
            print(f"  [{i}/{len(items)}] 分析: {item.title[:40]}")
            result = analyzer.analyze(item, config)
            item.analysis = result
            if result.related:
                relevant_items.append(item)
                print(f"    -> 相关! 领域: {result.category}, 理由: {result.reason[:50]}")
            time.sleep(1)  # 避免 API 限流

        print(f"分析完成，相关项目 {len(relevant_items)} 条")

    # 5. 推送模块: 邮件通知
    if relevant_items:
        print("\n[4/4] 推送模块 - 发送邮件通知...")
        notifier = EmailNotifier()
        notifier.notify(relevant_items, config)

        # 保存 Excel
        print("\n保存结果到 Excel...")
        save_excel(relevant_items)
    else:
        print("\n无相关项目，跳过推送。")

    print("\n" + "=" * 60)
    print(f"流程完成 - 原始: {len(items)} 条, 相关: {len(relevant_items)} 条")
    print("=" * 60)
