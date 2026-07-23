# -*- coding=utf-8 -*-
"""钉钉机器人通知器: 生成精简 Markdown 并推送到钉钉群"""
from src.models import TenderItem
from src.notifiers.base import BaseNotifier
from src.notifiers.robot import Robot


class RobotNotifier(BaseNotifier):
    """钉钉机器人通知器"""

    def notify(self, items: list[TenderItem], config: dict) -> bool:
        if not items:
            print("无相关项目，未发送钉钉消息。")
            return False

        dingtalk_cfg = config.get('dingtalk', {})
        dt_opt = config.get('notifier', {}).get('dingtalk', {})

        access_token = dingtalk_cfg.get('access_token') or dt_opt.get('access_token', '')
        secret = dingtalk_cfg.get('secret') or dt_opt.get('secret', '')

        if not access_token or not secret:
            print("钉钉机器人未配置 access_token/secret，跳过推送。")
            return False

        title = dt_opt.get('title', '[招标公告分析报告] 发现 {count} 条相关项目').format(count=len(items))
        text = self._generate_markdown(items)
        at_mobiles = dt_opt.get('at_mobiles', [])
        is_at_all = dt_opt.get('is_at_all', False)

        robot = Robot(access_token, secret)
        result = robot.send_markdown(
            title=title,
            text=text,
            at_mobiles=at_mobiles,
            is_at_all=is_at_all
        )

        if result.get('errcode') == 0:
            print(f"钉钉消息发送成功! 共 {len(items)} 条相关项目")
            return True
        return False

    def _generate_markdown(self, items: list[TenderItem]) -> str:
        """生成精简的钉钉 Markdown 内容"""
        lines = [f"### 招标公告分析报告（共 {len(items)} 条）\n"]

        for i, item in enumerate(items, 1):
            analysis = item.analysis
            category = analysis.category if analysis else ""
            reason = analysis.reason if analysis else ""
            matched_keywords = '、'.join(analysis.matched_keywords) if analysis else ""
            integration_level = analysis.integration_level if analysis else ""

            # 标题作为可点击的链接
            lines.append(f"**{i}. [{item.title}]({item.detail_url})**")

            meta = []
            if item.date:
                meta.append(f"日期: {item.date}")
            if item.region:
                meta.append(f"区域: {item.region}")
            if item.buyer:
                meta.append(f"招标人: {item.buyer}")
            if meta:
                lines.append(f"- {' | '.join(meta)}")

            detail = []
            if category:
                detail.append(f"领域: {category}")
            if matched_keywords:
                detail.append(f"关键词: {matched_keywords}")
            if integration_level:
                detail.append(f"融合: {integration_level}")
            if reason:
                detail.append(f"理由: {reason}")
            if detail:
                lines.append(f"- {' | '.join(detail)}")

            lines.append("")

        lines.append("> 以上为经大模型分析筛选后的相关项目，详情可点击标题查看。")
        return "\n".join(lines)
