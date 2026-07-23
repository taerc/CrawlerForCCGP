# -*- coding=utf-8 -*-
"""LangChain + LLM 分析器: 从 Markdown 加载提示词，调用大模型分析公告"""
import os
import re
import json
from pathlib import Path

from src.models import TenderItem, AnalysisResult
from src.analyzers.base import BaseAnalyzer


def load_prompt_file(file_path: str) -> dict:
    """从 Markdown 文件解析提示词

    按 ## 标题分段，提取 keywords / system_prompt / user_prompt_template

    Args:
        file_path: Markdown 文件路径(相对于项目根目录)

    Returns:
        {
            'keywords': ['无人机', '桥梁', ...],
            'system_prompt': '...',
            'user_prompt_template': '...'
        }
    """
    # 解析项目根目录
    base_dir = Path(__file__).resolve().parent.parent.parent
    full_path = base_dir / file_path

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()

    result = {'keywords': [], 'system_prompt': '', 'user_prompt_template': ''}

    # 按 ## 标题分段
    sections = re.split(r'^##\s+', content, flags=re.MULTILINE)

    for section in sections:
        if not section.strip():
            continue
        # 提取标题名和内容
        lines = section.split('\n', 1)
        title = lines[0].strip().lower()
        body = lines[1].strip() if len(lines) > 1 else ''

        if title == 'keywords':
            # 每行一个关键词
            result['keywords'] = [k.strip() for k in body.split('\n') if k.strip()]
        elif title == 'system_prompt':
            result['system_prompt'] = body
        elif title == 'user_prompt_template':
            result['user_prompt_template'] = body

    return result


class LLMAnalyzer(BaseAnalyzer):
    """LangChain + LLM 分析器"""

    def __init__(self):
        self._llm = None
        self._prompt_data = None

    def _init_llm(self, config: dict):
        """延迟初始化 LLM(避免未使用时加载)"""
        if self._llm is not None:
            return

        analyzer_cfg = config.get('analyzer', {})
        llm_cfg = config.get('llm', {})

        from langchain_openai import ChatOpenAI

        self._llm = ChatOpenAI(
            model=analyzer_cfg.get('model', 'qwen-plus'),
            temperature=analyzer_cfg.get('temperature', 0.1),
            max_tokens=analyzer_cfg.get('max_tokens', 1000),
            api_key=llm_cfg.get('api_key', os.environ.get('LLM_API_KEY', '')),
            base_url=llm_cfg.get('base_url', os.environ.get('LLM_BASE_URL', '')),
        )

    def _load_prompt(self, config: dict) -> dict:
        """加载提示词文件"""
        if self._prompt_data is not None:
            return self._prompt_data

        analyzer_cfg = config.get('analyzer', {})
        prompt_file = analyzer_cfg.get('prompt_file', 'prompts/tender_analysis.md')
        self._prompt_data = load_prompt_file(prompt_file)
        return self._prompt_data

    def analyze(self, item: TenderItem, config: dict) -> AnalysisResult:
        """分析单个公告"""
        analyzer_cfg = config.get('analyzer', {})
        if not analyzer_cfg.get('enabled', True):
            return AnalysisResult(related=False)

        # 获取分析内容(优先用详情正文，没有则用摘要)
        content = item.detail_content or item.summary
        if not content.strip():
            return AnalysisResult(related=False)

        self._init_llm(config)
        prompt_data = self._load_prompt(config)

        # 填充模板变量
        keywords_str = '、'.join(prompt_data['keywords'])
        user_prompt = prompt_data['user_prompt_template'].format(
            keywords=keywords_str,
            content=content
        )
        system_prompt = prompt_data['system_prompt']

        # 构建消息并调用 LLM
        from langchain_core.messages import SystemMessage, HumanMessage
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            response = self._llm.invoke(messages)
            result_text = response.content
            return self._parse_result(result_text)
        except Exception as e:
            print(f"  LLM 分析失败: {e}")
            return AnalysisResult(related=False)

    def _parse_result(self, text: str) -> AnalysisResult:
        """解析 LLM 返回的 JSON 结果，做容错处理"""
        # 尝试直接解析 JSON
        try:
            data = json.loads(text)
            return self._build_result(data)
        except json.JSONDecodeError:
            pass

        # 容错: 用正则提取 JSON 块
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return self._build_result(data)
            except json.JSONDecodeError:
                pass

        # 容错: 提取 ```json ... ``` 块
        code_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if code_match:
            try:
                data = json.loads(code_match.group(1))
                return self._build_result(data)
            except json.JSONDecodeError:
                pass

        print(f"  无法解析 LLM 返回结果: {text[:200]}")
        return AnalysisResult(related=False)

    @staticmethod
    def _build_result(data: dict) -> AnalysisResult:
        """从解析后的字典构建 AnalysisResult"""
        matched_keywords = data.get('matched_keywords', [])
        if not isinstance(matched_keywords, list):
            matched_keywords = []
        return AnalysisResult(
            related=bool(data.get('related', False)),
            category=str(data.get('category', '')),
            reason=str(data.get('reason', '')),
            confidence=float(data.get('confidence', 0.0)),
            matched_keywords=matched_keywords,
            integration_level=str(data.get('integration_level', '')),
        )
