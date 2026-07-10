#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
工具函数模块
Utility Functions Module
"""

import os
import sys
import json
import logging
import yaml
from pathlib import Path
from datetime import datetime

# 颜色常量
class Colors:
    """终端颜色常量"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def setup_logging(name: str, log_dir: str = 'logs', level=logging.INFO):
    """
    设置日志记录
    
    Args:
        name: 日志记录器名称
        log_dir: 日志目录
        level: 日志级别
    
    Returns:
        日志记录器
    """
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器
    file_handler = logging.FileHandler(
        log_path / f'{name}_{datetime.now().strftime("%Y%m%d")}.log'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def load_config(config_path: str) -> dict:
    """
    加载配置文件 (YAML 或 JSON)
    
    Args:
        config_path: 配置文件路径
    
    Returns:
        配置字典
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    try:
        if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        
        elif config_path.suffix.lower() == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        else:
            raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
        
        return config
    
    except Exception as e:
        raise RuntimeError(f"加载配置文件失败: {e}")


def save_config(config: dict, config_path: str):
    """
    保存配置文件
    
    Args:
        config: 配置字典
        config_path: 配置文件路径
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if config_path.suffix.lower() in ['.yaml', '.yml']:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        elif config_path.suffix.lower() == '.json':
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        
        else:
            raise ValueError(f"不支持的配置文件格式: {config_path.suffix}")
    
    except Exception as e:
        raise RuntimeError(f"保存配置文件失败: {e}")


def print_progress(current: int, total: int, prefix: str = '', width: int = 50):
    """
    打印进度条
    
    Args:
        current: 当前进度
        total: 总数
        prefix: 前缀
        width: 进度条宽度
    """
    if total == 0:
        return
    
    percent = current / total
    filled = int(width * percent)
    
    bar = '█' * filled + '░' * (width - filled)
    percentage = f"{percent * 100:.1f}%"
    
    print(f"\r{prefix} |{bar}| {percentage} ({current}/{total})", end='', flush=True)
    
    if current == total:
        print()  # 换行


def print_success(message: str):
    """打印成功信息"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """打印错误信息"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message: str):
    """打印警告信息"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message: str):
    """打印信息"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_header(message: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 60}")
    print(f"{message}")
    print(f"{'=' * 60}{Colors.ENDC}\n")


def format_bytes(bytes_size: int) -> str:
    """
    格式化字节大小
    
    Args:
        bytes_size: 字节大小
    
    Returns:
        格式化的大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} PB"


def format_time(seconds: float) -> str:
    """
    格式化时间
    
    Args:
        seconds: 秒数
    
    Returns:
        格式化的时间字符串
    """
    if seconds < 60:
        return f"{seconds:.2f}s"
    
    minutes = seconds / 60
    if minutes < 60:
        return f"{minutes:.2f}m"
    
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.2f}h"
    
    days = hours / 24
    return f"{days:.2f}d"


def get_env(key: str, default: str = None) -> str:
    """
    获取环境变量，支持 .env 文件
    
    Args:
        key: 环境变量名
        default: 默认值
    
    Returns:
        环境变量值
    """
    # 首先尝试从 .env 文件加载
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    return os.getenv(key, default)


def ensure_directory(path: str) -> Path:
    """
    确保目录存在
    
    Args:
        path: 目录路径
    
    Returns:
        目录 Path 对象
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_filename(filename: str) -> str:
    """
    生成安全的文件名
    
    Args:
        filename: 原始文件名
    
    Returns:
        安全的文件名
    """
    import re
    # 移除不安全的字符
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # 移除连续的点
    filename = re.sub(r'\.+', '.', filename)
    # 移除前导/尾部的点
    filename = filename.strip('.')
    return filename


def is_valid_url(url: str) -> bool:
    """
    验证 URL 是否有效
    
    Args:
        url: URL 字符串
    
    Returns:
        是否有效
    """
    import re
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def merge_dicts(base: dict, override: dict) -> dict:
    """
    深度合并字典
    
    Args:
        base: 基础字典
        override: 覆盖字典
    
    Returns:
        合并后的字典
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def parse_csv_line(line: str, delimiter: str = ',') -> list:
    """
    解析 CSV 行
    
    Args:
        line: CSV 行
        delimiter: 分隔符
    
    Returns:
        字段列表
    """
    import csv
    from io import StringIO
    
    reader = csv.reader(StringIO(line), delimiter=delimiter)
    return next(reader)


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    将列表分块
    
    Args:
        lst: 列表
        chunk_size: 块大小
    
    Returns:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(d: dict, parent_key: str = '', sep: str = '_') -> dict:
    """
    扁平化字典
    
    Args:
        d: 字典
        parent_key: 父键
        sep: 分隔符
    
    Returns:
        扁平化的字典
    """
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)
