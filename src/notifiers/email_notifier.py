# -*- coding=utf-8 -*-
"""邮件通知器: 生成 HTML 表格并发送邮件"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd

from src.models import TenderItem
from src.notifiers.base import BaseNotifier


class EmailNotifier(BaseNotifier):
    """邮件通知器"""

    def notify(self, items: list[TenderItem], config: dict) -> bool:
        if not items:
            print("无相关项目，未发送邮件。")
            return False

        smtp_cfg = config.get('smtp', {})
        notifier_cfg = config.get('notifier', {})
        email_cfg = notifier_cfg.get('email', {})

        subject = email_cfg.get('subject', '[招标公告分析报告] 发现 {count} 条相关项目').format(count=len(items))
        body = self._generate_email_body(items)

        msg = MIMEMultipart()
        msg["From"] = smtp_cfg.get('sender_email', '')
        msg["To"] = smtp_cfg.get('receiver_email', '')
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        try:
            port = smtp_cfg.get('port', 587)
            if port == 465:
                server = smtplib.SMTP_SSL(smtp_cfg.get('server', ''), port)
            else:
                server = smtplib.SMTP(smtp_cfg.get('server', ''), port)
                server.starttls()
            with server:
                server.login(smtp_cfg.get('sender_email', ''), smtp_cfg.get('sender_password', ''))
                server.sendmail(
                    smtp_cfg.get('sender_email', ''),
                    smtp_cfg.get('receiver_email', ''),
                    msg.as_string()
                )
            print(f"邮件发送成功! 共 {len(items)} 条相关项目")
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False

    def _generate_email_body(self, items: list[TenderItem]) -> str:
        """生成 HTML 格式的邮件内容"""
        # 构建表格数据
        table_data = []
        for i, item in enumerate(items, 1):
            category = item.analysis.category if item.analysis else ""
            reason = item.analysis.reason if item.analysis else ""
            table_data.append([
                i,                # 序号
                item.title,       # 名称
                item.date,        # 日期
                item.buyer,       # 招标人
                item.agent,       # 代理机构
                item.region,      # 区域
                category,         # 关联领域
                reason,           # 分析理由
                f'<a href="{item.detail_url}">查看详情</a>',  # 详情链接
                item.summary,     # 项目概况
            ])

        columns = ['序号', '名称', '日期', '招标人', '代理机构', '区域', '关联领域', '分析理由', '详情', '项目概况']
        df = pd.DataFrame(table_data, columns=columns)
        html_table = df.to_html(index=False, border=0, classes="data-table", escape=False)

        style = """
        <style>
            .data-table { width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px; color: #333; }
            .data-table th, .data-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            .data-table th { background-color: #f8f9fa; font-weight: bold; color: #333; }
            .data-table tr:hover { background-color: #f1f1f1; }
            .data-table a { color: #007bff; text-decoration: none; }
            .data-table a:hover { text-decoration: underline; }
        </style>
        """

        body = f"""
        <html>
            <head>{style}</head>
            <body>
                <h3>发现 {len(items)} 条相关招标公告：</h3>
                {html_table}
                <p>以上为经大模型分析筛选后的相关项目，请及时查看详情获取更多信息。</p>
            </body>
        </html>
        """
        return body
