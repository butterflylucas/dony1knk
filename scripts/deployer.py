#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
云服务部署模块 - 支持多个云服务商
Cloud Deployer - Supports multiple cloud providers
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any
from utils import load_config

logger = logging.getLogger(__name__)


class CloudDeployer:
    """云服务部署器"""

    def __init__(self, config_path: str = 'config/cloud.yaml'):
        """初始化部署器"""
        self.config = load_config(config_path)
        self.provider = self.config.get('cloud_provider', 'aliyun').lower()
        self.deployer = self._get_deployer()

    def _get_deployer(self):
        """获取对应的部署器"""
        if self.provider == 'aliyun':
            return AliyunDeployer(self.config)
        elif self.provider == 'aws':
            return AWSDeployer(self.config)
        elif self.provider == 'tencentcloud':
            return TencentCloudDeployer(self.config)
        elif self.provider == 'qiniu':
            return QiniuDeployer(self.config)
        else:
            raise ValueError(f"不支持的云服务商: {self.provider}")

    def deploy(self, local_path: str) -> Dict[str, Any]:
        """
        部署网站到云服务
        
        Args:
            local_path: 本地网站路径
        
        Returns:
            部署结果
        """
        logger.info(f"使用 {self.provider} 部署网站: {local_path}")
        return self.deployer.upload(local_path)

    def deploy_batch(self, sites_dir: str, max_workers: int = 4) -> list:
        """
        批量部署网站
        
        Args:
            sites_dir: 网站目录
            max_workers: 并发工作线程数
        
        Returns:
            部署结果列表
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        sites_path = Path(sites_dir)
        site_dirs = [d for d in sites_path.iterdir() if d.is_dir()]
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.deploy, str(d)): d.name for d in site_dirs}
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"部署失败: {e}")
                    results.append({'success': False, 'error': str(e)})
        
        return results


class BaseDeployer:
    """基础部署器"""

    def __init__(self, config: Dict):
        """初始化部署器"""
        self.config = config
        self.region = config.get('region')
        self.bucket = config.get('bucket')

    def upload(self, local_path: str) -> Dict[str, Any]:
        """上传网站"""
        raise NotImplementedError

    def _walk_directory(self, path: str):
        """遍历目录"""
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, path)
                yield file_path, rel_path


class AliyunDeployer(BaseDeployer):
    """阿里云部署器"""

    def __init__(self, config: Dict):
        """初始化阿里云部署器"""
        super().__init__(config)
        self._init_client()

    def _init_client(self):
        """初始化阿里云客户端"""
        try:
            import oss2
            
            auth = oss2.Auth(
                self.config.get('access_key'),
                self.config.get('secret_key')
            )
            
            endpoint = f"https://oss-{self.region}.aliyuncs.com"
            self.client = oss2.Bucket(auth, endpoint, self.bucket)
            
            logger.info("阿里云 OSS 客户端初始化成功")
        except ImportError:
            logger.error("未安装 oss2 库，请执行: pip install oss2")
            raise
        except Exception as e:
            logger.error(f"阿里云客户端初始化失败: {e}")
            raise

    def upload(self, local_path: str) -> Dict[str, Any]:
        """上传网站到阿里云 OSS"""
        try:
            local_path = Path(local_path)
            site_id = local_path.name
            remote_path = f"sites/{site_id}"
            
            file_count = 0
            for local_file, rel_path in self._walk_directory(str(local_path)):
                remote_file = f"{remote_path}/{rel_path}"
                remote_file = remote_file.replace('\\', '/')
                
                with open(local_file, 'rb') as f:
                    self.client.put_object(remote_file, f)
                
                file_count += 1
                logger.debug(f"上传文件: {remote_file}")
            
            url = f"https://{self.bucket}.oss-{self.region}.aliyuncs.com/{remote_path}/index.html"
            
            logger.info(f"✓ 阿里云部署成功: {url}")
            return {
                'success': True,
                'site_id': site_id,
                'url': url,
                'provider': 'aliyun',
                'files_uploaded': file_count
            }
        
        except Exception as e:
            logger.error(f"阿里云部署失败: {e}")
            return {
                'success': False,
                'site_id': local_path.name,
                'error': str(e),
                'provider': 'aliyun'
            }


class AWSDeployer(BaseDeployer):
    """AWS S3 部署器"""

    def __init__(self, config: Dict):
        """初始化 AWS 部署器"""
        super().__init__(config)
        self._init_client()

    def _init_client(self):
        """初始化 AWS 客户端"""
        try:
            import boto3
            
            self.s3 = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=self.config.get('access_key'),
                aws_secret_access_key=self.config.get('secret_key')
            )
            
            logger.info("AWS S3 客户端初始化成功")
        except ImportError:
            logger.error("未安装 boto3 库，请执行: pip install boto3")
            raise
        except Exception as e:
            logger.error(f"AWS 客户端初始化失败: {e}")
            raise

    def upload(self, local_path: str) -> Dict[str, Any]:
        """上传网站到 AWS S3"""
        try:
            local_path = Path(local_path)
            site_id = local_path.name
            remote_path = f"sites/{site_id}"
            
            file_count = 0
            for local_file, rel_path in self._walk_directory(str(local_path)):
                remote_file = f"{remote_path}/{rel_path}"
                remote_file = remote_file.replace('\\', '/')
                
                self.s3.upload_file(local_file, self.bucket, remote_file)
                
                file_count += 1
                logger.debug(f"上传文件: {remote_file}")
            
            url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{remote_path}/index.html"
            
            logger.info(f"✓ AWS 部署成功: {url}")
            return {
                'success': True,
                'site_id': site_id,
                'url': url,
                'provider': 'aws',
                'files_uploaded': file_count
            }
        
        except Exception as e:
            logger.error(f"AWS 部署失败: {e}")
            return {
                'success': False,
                'site_id': local_path.name,
                'error': str(e),
                'provider': 'aws'
            }


class TencentCloudDeployer(BaseDeployer):
    """腾讯云部署器"""

    def __init__(self, config: Dict):
        """初始化腾讯云部署器"""
        super().__init__(config)
        self._init_client()

    def _init_client(self):
        """初始化腾讯云客户端"""
        try:
            from cos_python_sdk.cos import CosConfig, CosS3Client
            
            config = CosConfig(
                Region=self.region,
                SecretId=self.config.get('access_key'),
                SecretKey=self.config.get('secret_key')
            )
            
            self.client = CosS3Client(config)
            logger.info("腾讯云 COS 客户端初始化成功")
        except ImportError:
            logger.error("未安装 cos-python-sdk-v5 库，请执行: pip install cos-python-sdk-v5")
            raise
        except Exception as e:
            logger.error(f"腾讯云客户端初始化失败: {e}")
            raise

    def upload(self, local_path: str) -> Dict[str, Any]:
        """上传网站到腾讯云 COS"""
        try:
            local_path = Path(local_path)
            site_id = local_path.name
            remote_path = f"sites/{site_id}"
            
            file_count = 0
            for local_file, rel_path in self._walk_directory(str(local_path)):
                remote_file = f"{remote_path}/{rel_path}"
                remote_file = remote_file.replace('\\', '/')
                
                self.client.upload_file(
                    Bucket=self.bucket,
                    Key=remote_file,
                    LocalFilePath=local_file
                )
                
                file_count += 1
                logger.debug(f"上传文件: {remote_file}")
            
            url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{remote_path}/index.html"
            
            logger.info(f"✓ 腾讯云部署成功: {url}")
            return {
                'success': True,
                'site_id': site_id,
                'url': url,
                'provider': 'tencentcloud',
                'files_uploaded': file_count
            }
        
        except Exception as e:
            logger.error(f"腾讯云部署失败: {e}")
            return {
                'success': False,
                'site_id': local_path.name,
                'error': str(e),
                'provider': 'tencentcloud'
            }


class QiniuDeployer(BaseDeployer):
    """七牛云部署器"""

    def __init__(self, config: Dict):
        """初始化七牛云部署器"""
        super().__init__(config)
        self._init_client()

    def _init_client(self):
        """初始化七牛云客户端"""
        try:
            from qiniu import Auth, BucketManager
            
            self.auth = Auth(
                self.config.get('access_key'),
                self.config.get('secret_key')
            )
            
            self.bucket_manager = BucketManager(self.auth)
            logger.info("七牛云客户端初始化成功")
        except ImportError:
            logger.error("未安装 qiniu 库，请执行: pip install qiniu")
            raise
        except Exception as e:
            logger.error(f"七牛云客户端初始化失败: {e}")
            raise

    def upload(self, local_path: str) -> Dict[str, Any]:
        """上传网站到七牛云"""
        try:
            local_path = Path(local_path)
            site_id = local_path.name
            remote_path = f"sites/{site_id}"
            
            file_count = 0
            for local_file, rel_path in self._walk_directory(str(local_path)):
                remote_file = f"{remote_path}/{rel_path}"
                remote_file = remote_file.replace('\\', '/')
                
                self.bucket_manager.put_file(
                    self.bucket,
                    remote_file,
                    local_file
                )
                
                file_count += 1
                logger.debug(f"上传文件: {remote_file}")
            
            url = f"https://{self.config.get('domain')}/{remote_path}/index.html"
            
            logger.info(f"✓ 七牛云部署成功: {url}")
            return {
                'success': True,
                'site_id': site_id,
                'url': url,
                'provider': 'qiniu',
                'files_uploaded': file_count
            }
        
        except Exception as e:
            logger.error(f"七牛云部署失败: {e}")
            return {
                'success': False,
                'site_id': local_path.name,
                'error': str(e),
                'provider': 'qiniu'
            }
