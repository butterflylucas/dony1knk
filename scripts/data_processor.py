#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据处理模块 - 支持 CSV 和 JSON 格式
Data Processor - Supports CSV and JSON formats
"""

import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Union

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理器"""

    @staticmethod
    def load_data(source_path: str) -> List[Dict]:
        """
        加载数据源 (CSV 或 JSON)
        
        Args:
            source_path: 数据源文件路径
        
        Returns:
            网站配置列表
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        source_path = Path(source_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"数据源文件不存在: {source_path}")
        
        suffix = source_path.suffix.lower()
        
        if suffix == '.csv':
            return DataProcessor._load_csv(source_path)
        elif suffix == '.json':
            return DataProcessor._load_json(source_path)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")

    @staticmethod
    def _load_csv(file_path: Path) -> List[Dict]:
        """加载 CSV 文件"""
        logger.info(f"加载 CSV 文件: {file_path}")
        
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for idx, row in enumerate(reader, 1):
                    # 清理数据
                    cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v 
                                  for k, v in row.items()}
                    
                    # 验证必需字段
                    if not cleaned_row.get('site_id'):
                        cleaned_row['site_id'] = f"site_{idx}"
                    
                    data.append(cleaned_row)
            
            logger.info(f"成功加载 {len(data)} 行数据")
            return data
        
        except Exception as e:
            logger.error(f"CSV 文件解析失败: {e}")
            raise

    @staticmethod
    def _load_json(file_path: Path) -> List[Dict]:
        """加载 JSON 文件"""
        logger.info(f"加载 JSON 文件: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 确保返回列表
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                raise ValueError("JSON 必须是数组或对象")
            
            # 为每条记录添加 site_id
            for idx, item in enumerate(data, 1):
                if not item.get('site_id'):
                    item['site_id'] = f"site_{idx}"
            
            logger.info(f"成功加载 {len(data)} 条数据")
            return data
        
        except Exception as e:
            logger.error(f"JSON 文件解析失败: {e}")
            raise

    @staticmethod
    def validate_site_data(site_data: Dict) -> tuple[bool, List[str]]:
        """
        验证网站数据完整性
        
        Args:
            site_data: 网站配置
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 必需字段
        required_fields = ['site_id', 'site_name', 'domain']
        for field in required_fields:
            if not site_data.get(field):
                errors.append(f"缺少必需字段: {field}")
        
        # 验证域名格式
        domain = site_data.get('domain', '')
        if domain and not DataProcessor._validate_domain(domain):
            errors.append(f"无效的域名格式: {domain}")
        
        # 验证 URL 格式
        for url_field in ['logo_url', 'image_url']:
            if url_field in site_data and site_data[url_field]:
                if not DataProcessor._validate_url(site_data[url_field]):
                    errors.append(f"无效的 URL 格式: {site_data[url_field]}")
        
        return len(errors) == 0, errors

    @staticmethod
    def _validate_domain(domain: str) -> bool:
        """验证域名格式"""
        import re
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))

    @staticmethod
    def _validate_url(url: str) -> bool:
        """验证 URL 格式"""
        import re
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url, re.IGNORECASE))

    @staticmethod
    def merge_with_defaults(site_data: Dict, defaults: Dict) -> Dict:
        """
        将网站数据与默认值合并
        
        Args:
            site_data: 网站数据
            defaults: 默认值
        
        Returns:
            合并后的数据
        """
        merged = defaults.copy()
        merged.update(site_data)
        return merged

    @staticmethod
    def transform_data(data: List[Dict], transformers: Dict) -> List[Dict]:
        """
        转换数据
        
        Args:
            data: 数据列表
            transformers: 转换器字典 {字段名: 转换函数}
        
        Returns:
            转换后的数据
        """
        transformed = []
        
        for item in data:
            new_item = item.copy()
            
            for field, transformer in transformers.items():
                if field in new_item:
                    try:
                        new_item[field] = transformer(new_item[field])
                    except Exception as e:
                        logger.warning(f"字段 {field} 转换失败: {e}")
            
            transformed.append(new_item)
        
        return transformed

    @staticmethod
    def filter_data(data: List[Dict], condition_func) -> List[Dict]:
        """
        过滤数据
        
        Args:
            data: 数据列表
            condition_func: 过滤函数
        
        Returns:
            过滤后的数据
        """
        return [item for item in data if condition_func(item)]

    @staticmethod
    def export_data(data: List[Dict], output_path: str, format: str = 'json'):
        """
        导出数据
        
        Args:
            data: 数据列表
            output_path: 输出文件路径
            format: 输出格式 (json 或 csv)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            if format == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            elif format == 'csv':
                if not data:
                    logger.warning("没有数据要导出")
                    return
                
                fieldnames = list(data[0].keys())
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            
            logger.info(f"数据已导出到: {output_path}")
        
        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            raise
