# -*- coding=utf-8 -*-
"""全局配置加载器: 加载 YAML 配置 + .env 环境变量"""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


def load_config(config_path: str = None) -> dict:
    """加载配置: 先加载 .env，再加载 config.yaml

    Args:
        config_path: 配置文件路径(相对于项目根目录)，默认为 config.yaml

    Returns:
        合并后的配置字典
    """
    # 加载 .env
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # 加载 YAML 配置
    if config_path is None:
        config_path = BASE_DIR / "config.yaml"
    else:
        config_path = BASE_DIR / config_path

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 注入环境变量
    config["llm"] = {
        "api_key": os.environ.get("LLM_API_KEY", ""),
        "base_url": os.environ.get("LLM_BASE_URL", ""),
    }
    config["smtp"] = {
        "server": os.environ.get("SMTP_SERVER", ""),
        "port": int(os.environ.get("SMTP_PORT", 587)),
        "sender_email": os.environ.get("SENDER_EMAIL", ""),
        "sender_password": os.environ.get("SENDER_PASSWORD", ""),
        "receiver_email": os.environ.get("RECEIVER_EMAIL", ""),
    }

    return config
