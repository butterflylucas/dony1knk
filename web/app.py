#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web 管理界面 - Flask 应用
Web Management Interface - Flask Application
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json
import logging
from pathlib import Path
from datetime import datetime
import sys
import os

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from main import BatchSiteBuilder
from utils import setup_logging, load_config

app = Flask(__name__, template_folder='templates')
CORS(app)

# 设置日志
logger = setup_logging('web_app')

# 初始化建站系统
try:
    builder = BatchSiteBuilder(config_path='config/config.yaml')
except Exception as e:
    logger.error(f"初始化建站系统失败: {e}")
    builder = None


@app.route('/')
def dashboard():
    """仪表板"""
    try:
        stats = {
            'total_sites': 100,
            'deployed': 75,
            'pending': 20,
            'failed': 5
        }
        
        activities = [
            {
                'time': '2024-01-15 14:30',
                'event': '网站生成',
                'status': 'success',
                'details': '成功生成 50 个网站'
            },
            {
                'time': '2024-01-15 14:20',
                'event': '网站部署',
                'status': 'success',
                'details': '部署 45 个网站到云端'
            }
        ]
        
        return render_template('dashboard.html', stats=stats, activities=activities)
    
    except Exception as e:
        logger.error(f"仪表板加载失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def api_stats():
    """获取统计信息"""
    try:
        stats = {
            'total_sites': 100,
            'deployed': 75,
            'pending': 20,
            'failed': 5,
            'timestamp': datetime.now().isoformat()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """生成网站 API"""
    try:
        data = request.get_json()
        data_source = data.get('data_source', 'data/sites.csv')
        template = data.get('template', 'default')
        
        logger.info(f"开始生成网站: {data_source}, 模板: {template}")
        
        sites_data = builder.process_data(data_source)
        if not sites_data:
            return jsonify({'error': '数据处理失败'}), 400
        
        results = builder.generate_sites(sites_data, template, 'output')
        
        return jsonify({
            'success': True,
            'total': len(results),
            'results': results
        })
    
    except Exception as e:
        logger.error(f"生成网站失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/deploy', methods=['POST'])
def api_deploy():
    """部署网站 API"""
    try:
        logger.info("开始部署网站")
        
        deployed_sites = builder.deploy_sites('output', max_workers=4)
        
        return jsonify({
            'success': True,
            'total': len(deployed_sites),
            'results': deployed_sites
        })
    
    except Exception as e:
        logger.error(f"部署网站失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/sites')
def api_sites():
    """获取网站列表"""
    try:
        output_dir = Path('output')
        sites = []
        
        if output_dir.exists():
            for site_dir in output_dir.iterdir():
                if site_dir.is_dir():
                    config_file = site_dir / 'config.json'
                    if config_file.exists():
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                            sites.append(config)
        
        return jsonify(sites)
    
    except Exception as e:
        logger.error(f"获取网站列表失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs')
def api_logs():
    """获取日志"""
    try:
        log_dir = Path('logs')
        logs = []
        
        if log_dir.exists():
            for log_file in log_dir.glob('*.log'):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()[-100:]  # 获取最后 100 行
                        logs.append({
                            'file': log_file.name,
                            'lines': lines
                        })
                except Exception as e:
                    logger.warning(f"读取日志失败 {log_file}: {e}")
        
        return jsonify(logs)
    
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'app': 'batch-site-builder'
    })


@app.errorhandler(404)
def not_found(error):
    """404 处理"""
    return jsonify({'error': 'Not Found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 处理"""
    logger.error(f"Internal Server Error: {error}")
    return jsonify({'error': 'Internal Server Error'}), 500


if __name__ == '__main__':
    logger.info("启动 Web 管理界面")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
