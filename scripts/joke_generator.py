#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
随机笑话生成器 - 使用外部 API
Random Joke Generator - Using External APIs
"""

import requests
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class JokeGenerator:
    """笑话生成器基类"""

    def get_joke(self) -> Optional[Dict]:
        """获取笑话"""
        raise NotImplementedError

    def get_jokes_batch(self, count: int = 5) -> List[Dict]:
        """批量获取笑话"""
        jokes = []
        for _ in range(count):
            try:
                joke = self.get_joke()
                if joke:
                    jokes.append(joke)
            except Exception as e:
                logger.warning(f"获取笑话失败: {e}")
        return jokes


class JokeAPIGenerator(JokeGenerator):
    """Joke API 笑话生成器 (英文笑话)"""

    BASE_URL = "https://v2.jokeapi.dev/joke"

    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.timeout = 10

    def get_joke(self) -> Optional[Dict]:
        """获取单个笑话"""
        try:
            # 获取任意类别的笑话，排除冒犯性内容
            url = f"{self.BASE_URL}/Any?format=json&safe-mode"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('error'):
                logger.warning(f"API 返回错误: {data.get('message')}")
                return None
            
            joke_type = data.get('type', 'single')
            
            if joke_type == 'single':
                joke_text = data.get('joke', '')
            else:  # 'twopart'
                setup = data.get('setup', '')
                delivery = data.get('delivery', '')
                joke_text = f"{setup}\n{delivery}"
            
            category = data.get('category', 'General')
            
            return {
                'source': 'JokeAPI',
                'joke': joke_text,
                'category': category,
                'type': joke_type,
                'timestamp': datetime.now().isoformat(),
                'language': 'en'
            }
        
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析笑话失败: {e}")
            return None

    def get_jokes_by_category(self, category: str = 'Any', count: int = 5) -> List[Dict]:
        """按类别获取笑话"""
        jokes = []
        
        for _ in range(count):
            try:
                url = f"{self.BASE_URL}/{category}?format=json&safe-mode"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get('error'):
                    joke_type = data.get('type', 'single')
                    
                    if joke_type == 'single':
                        joke_text = data.get('joke', '')
                    else:
                        setup = data.get('setup', '')
                        delivery = data.get('delivery', '')
                        joke_text = f"{setup}\n{delivery}"
                    
                    jokes.append({
                        'source': 'JokeAPI',
                        'joke': joke_text,
                        'category': data.get('category', 'General'),
                        'type': joke_type,
                        'timestamp': datetime.now().isoformat(),
                        'language': 'en'
                    })
            
            except Exception as e:
                logger.warning(f"获取笑话失败: {e}")
        
        return jokes


class ChuckNorrisJokeGenerator(JokeGenerator):
    """Chuck Norris 笑话生成器"""

    BASE_URL = "https://api.chucknorris.io/jokes"

    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.timeout = 10

    def get_joke(self) -> Optional[Dict]:
        """获取单个笑话"""
        try:
            url = f"{self.BASE_URL}/random"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'source': 'Chuck Norris API',
                'joke': data.get('value', ''),
                'category': data.get('categories', ['General'])[0] if data.get('categories') else 'General',
                'url': data.get('url', ''),
                'timestamp': datetime.now().isoformat(),
                'language': 'en'
            }
        
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析笑话失败: {e}")
            return None

    def get_jokes_by_category(self, category: str = None, count: int = 5) -> List[Dict]:
        """按类别获取笑话"""
        jokes = []
        
        try:
            # 先获取可用类别
            categories_url = f"{self.BASE_URL}/categories"
            categories_response = self.session.get(categories_url, timeout=10)
            categories = categories_response.json() if categories_response.status_code == 200 else []
            
            if category and category not in categories:
                logger.warning(f"类别不存在: {category}")
                return jokes
            
            for _ in range(count):
                if category:
                    url = f"{self.BASE_URL}/random?category={category}"
                else:
                    url = f"{self.BASE_URL}/random"
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                jokes.append({
                    'source': 'Chuck Norris API',
                    'joke': data.get('value', ''),
                    'category': category or 'General',
                    'timestamp': datetime.now().isoformat(),
                    'language': 'en'
                })
        
        except Exception as e:
            logger.warning(f"获取笑话失败: {e}")
        
        return jokes


class QuotableGenerator(JokeGenerator):
    """可引用的名言生成器"""

    BASE_URL = "https://api.quotable.io"

    def __init__(self):
        """初始化"""
        self.session = requests.Session()
        self.session.timeout = 10

    def get_joke(self) -> Optional[Dict]:
        """获取单个名言"""
        try:
            url = f"{self.BASE_URL}/random"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'source': 'Quotable API',
                'joke': data.get('content', ''),
                'author': data.get('author', 'Unknown'),
                'tags': data.get('tags', []),
                'timestamp': datetime.now().isoformat(),
                'language': 'en'
            }
        
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析名言失败: {e}")
            return None


class MultiSourceJokeGenerator:
    """多源笑话生成器 - 支持多个 API 源"""

    def __init__(self):
        """初始化所有笑话生成器"""
        self.generators = {
            'joke_api': JokeAPIGenerator(),
            'chuck_norris': ChuckNorrisJokeGenerator(),
            'quotable': QuotableGenerator()
        }

    def get_joke(self, source: str = None) -> Optional[Dict]:
        """
        获取笑话
        
        Args:
            source: 笑话来源 (如果为 None，随机选择)
        
        Returns:
            笑话字典
        """
        if source and source in self.generators:
            return self.generators[source].get_joke()
        
        # 随机选择一个源
        import random
        random_source = random.choice(list(self.generators.keys()))
        return self.generators[random_source].get_joke()

    def get_jokes_random(self, count: int = 5) -> List[Dict]:
        """获取随机源的多个笑话"""
        jokes = []
        
        for _ in range(count):
            import random
            source = random.choice(list(self.generators.keys()))
            joke = self.generators[source].get_joke()
            if joke:
                jokes.append(joke)
        
        return jokes

    def get_all_sources_jokes(self) -> Dict:
        """从所有源获取笑话"""
        all_jokes = {}
        
        for source_name, generator in self.generators.items():
            try:
                joke = generator.get_joke()
                if joke:
                    all_jokes[source_name] = joke
            except Exception as e:
                logger.warning(f"从 {source_name} 获取笑话失败: {e}")
        
        return all_jokes


class JokeCache:
    """笑话缓存管理"""

    def __init__(self, cache_file: str = 'logs/joke_cache.json'):
        """初始化缓存"""
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """加载缓存"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载缓存失败: {e}")
        
        return {}

    def _save_cache(self):
        """保存缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")

    def add_joke(self, joke: Dict):
        """添加笑话到缓存"""
        joke_id = f"{joke.get('source')}_{len(self.cache)}"
        self.cache[joke_id] = joke
        self._save_cache()

    def get_random_cached(self) -> Optional[Dict]:
        """获取随机缓存的笑话"""
        if not self.cache:
            return None
        
        import random
        return random.choice(list(self.cache.values()))

    def get_all_cached(self) -> List[Dict]:
        """获取所有缓存的笑话"""
        return list(self.cache.values())

    def clear_cache(self):
        """清除缓存"""
        self.cache = {}
        self._save_cache()


def print_joke(joke: Dict):
    """打印笑话"""
    print(f"\n{'='*60}")
    print(f"📝 来源: {joke.get('source', 'Unknown')}")
    print(f"🏷️  类别: {joke.get('category', 'N/A')}")
    if 'author' in joke:
        print(f"✍️  作者: {joke.get('author')}")
    print(f"{'-'*60}")
    print(f"{joke.get('joke', 'N/A')}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建多源笑话生成器
    generator = MultiSourceJokeGenerator()
    
    # 获取随机笑话
    print("\n🎭 随机笑话生成器 - 演示\n")
    
    print("1️⃣  从 JokeAPI 获取笑话:")
    joke = generator.generators['joke_api'].get_joke()
    if joke:
        print_joke(joke)
    
    print("2️⃣  从 Chuck Norris 获取笑话:")
    joke = generator.generators['chuck_norris'].get_joke()
    if joke:
        print_joke(joke)
    
    print("3️⃣  从 Quotable 获取名言:")
    joke = generator.generators['quotable'].get_joke()
    if joke:
        print_joke(joke)
    
    print("4️⃣  从任意源获取随机笑话:")
    jokes = generator.get_jokes_random(count=3)
    for joke in jokes:
        print_joke(joke)
