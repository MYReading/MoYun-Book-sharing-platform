"""通用工具服务"""
import os
from yaml import load, FullLoader
from typing import Union
from pathlib import Path


DEFAULT_CONFIG_PATH = Path(f"{os.getcwd()}/myConfig.yaml")
PROJECT_CONFIG_PATH = Path(f"{os.getcwd()}/config.yaml")


if DEFAULT_CONFIG_PATH.exists():
    config_path = DEFAULT_CONFIG_PATH
elif PROJECT_CONFIG_PATH.exists():
    config_path = PROJECT_CONFIG_PATH
else:
    print({os.getcwd()})
    raise FileNotFoundError("config file not found")
with open(config_path, encoding="utf-8") as f:
    Config: dict = load(f, Loader=FullLoader)


def queryConfig(category: str = None, key: str = None) -> dict or Union[str, int]:
    """
    获取配置文件中特定的配置项(优先读取myConfig.yaml，若不存在则读取config.yaml)
    :param category: 配置项类别
    :param key: 配置项key
    :return:
    """
    if not category:
        return Config
    elif category not in Config:
        raise ValueError(f"Parameter category {category} not found")
    else:
        if not key:
            return Config[category]
        elif key not in Config[category]:
            raise ValueError(f"Parameter key {key} not found")
        else:
            return Config[category][key]
