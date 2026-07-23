# -*- coding=utf-8 -*-
"""Excel 输出工具"""
import xlsxwriter
from datetime import datetime

from src.models import TenderItem


# Excel 表头(含分析列)
EXCEL_HEADERS = [
    '序号', '名称', '日期', '招标人', '代理机构', '区域',
    '关联领域', '分析理由', '详情链接', '项目概况'
]


def items_to_rows(items: list[TenderItem]) -> list[list]:
    """将 TenderItem 列表转为行数据"""
    rows = []
    for i, item in enumerate(items, 1):
        category = item.analysis.category if item.analysis else ""
        reason = item.analysis.reason if item.analysis else ""
        rows.append([
            i,
            item.title,
            item.date,
            item.buyer,
            item.agent,
            item.region,
            category,
            reason,
            item.detail_url,
            item.summary,
        ])
    return rows


def save_excel(items: list[TenderItem], filename: str = None) -> str:
    """将数据保存到 Excel 文件

    Args:
        items: TenderItem 列表
        filename: 文件名(不含扩展名)，默认带时间戳

    Returns:
        保存的文件路径
    """
    if filename is None:
        filename = "filtered_data_" + datetime.now().strftime("%Y%m%d_%H%M%S")

    rows = items_to_rows(items)

    workbook = xlsxwriter.Workbook(filename + '.xlsx')
    worksheet = workbook.add_worksheet('中标公告')

    # 写入表头
    for col, header in enumerate(EXCEL_HEADERS):
        worksheet.write(0, col, header)

    # 写入数据
    for row_idx, row_data in enumerate(rows, start=1):
        for col, value in enumerate(row_data):
            worksheet.write(row_idx, col, value)

    workbook.close()
    print(f"Excel 文件已保存: {filename}.xlsx")
    return filename + '.xlsx'
