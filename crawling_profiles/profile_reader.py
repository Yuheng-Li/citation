#!/usr/bin/env python3
"""
通用工具：从目录或zip文件中读取author profile JSON文件
支持两种模式：
1. 从目录读取（原有方式）
2. 从zip文件读取（新方式，节省磁盘空间）
"""
import json
import zipfile
import random
from pathlib import Path
from typing import List, Dict, Union, Optional


def collect_all_papers(profiles_source: Union[str, Path], num_authors: int = 100) -> List[Dict]:
    """
    收集指定数量作者的所有论文
    
    支持两种输入：
    - 目录路径：包含多个JSON文件的目录
    - zip文件路径：包含所有JSON文件的zip压缩包
    
    Args:
        profiles_source: 目录路径或zip文件路径
        num_authors: 要处理的作者数量
    
    Returns:
        list: 包含所有论文的列表
    """
    profiles_source = Path(profiles_source)
    
    # 判断是目录还是zip文件
    if profiles_source.is_dir():
        return _collect_from_directory(profiles_source, num_authors)
    elif profiles_source.suffix == '.zip' and profiles_source.exists():
        return _collect_from_zip(profiles_source, num_authors)
    else:
        raise ValueError(f"无效的路径: {profiles_source}。必须是目录或zip文件")


def _collect_from_directory(profiles_dir: Path, num_authors: int) -> List[Dict]:
    """从目录中收集论文（原有方式）"""
    all_files = list(profiles_dir.glob("author_*.json"))
    
    print(f"找到 {len(all_files)} 个 profile 文件")
    
    # 随机采样作者
    sampled_files = random.sample(all_files, min(num_authors, len(all_files)))
    print(f"随机采样 {len(sampled_files)} 个作者\n")
    
    all_papers = []
    
    for idx, profile_file in enumerate(sampled_files, 1):
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            author_name = profile_data.get('author_info', {}).get('name', 'Unknown')
            papers = profile_data.get('papers', [])
            
            # 为每篇论文添加作者信息
            for paper in papers:
                paper_with_author = {
                    'title': paper.get('title', ''),
                    'author_name': author_name,
                    'venue': paper.get('venue', ''),
                    'year': paper.get('year', ''),
                    'citations': paper.get('citations', 0)
                }
                if paper_with_author['title']:
                    all_papers.append(paper_with_author)
            
            if idx % 10 == 0:
                print(f"已处理 {idx}/{len(sampled_files)} 个作者，收集到 {len(all_papers)} 篇论文")
                
        except Exception as e:
            print(f"处理 {profile_file.name} 时出错: {e}")
            continue
    
    print(f"\n总共收集到 {len(all_papers)} 篇论文")
    return all_papers


def _collect_from_zip(zip_path: Path, num_authors: int) -> List[Dict]:
    """从zip文件中收集论文（新方式）"""
    all_papers = []
    
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        # 获取所有JSON文件名（支持带路径的文件）
        json_files = [name for name in zipf.namelist() 
                     if 'author_' in name and name.endswith(".json")]
        
        print(f"zip文件中找到 {len(json_files)} 个 profile 文件")
        
        # 随机采样
        if num_authors < len(json_files):
            sampled_files = random.sample(json_files, num_authors)
        else:
            sampled_files = json_files
        
        print(f"随机采样 {len(sampled_files)} 个作者\n")
        
        # 读取每个JSON文件
        for idx, filename in enumerate(sampled_files, 1):
            try:
                # 直接从zip文件读取内容
                with zipf.open(filename) as f:
                    content = f.read().decode('utf-8')
                    profile_data = json.loads(content)
                
                author_name = profile_data.get('author_info', {}).get('name', 'Unknown')
                papers = profile_data.get('papers', [])
                
                # 为每篇论文添加作者信息
                for paper in papers:
                    paper_with_author = {
                        'title': paper.get('title', ''),
                        'author_name': author_name,
                        'venue': paper.get('venue', ''),
                        'year': paper.get('year', ''),
                        'citations': paper.get('citations', 0)
                    }
                    if paper_with_author['title']:
                        all_papers.append(paper_with_author)
                
                if idx % 10 == 0:
                    print(f"已处理 {idx}/{len(sampled_files)} 个作者，收集到 {len(all_papers)} 篇论文")
                    
            except Exception as e:
                print(f"处理 {filename} 时出错: {e}")
                continue
    
    print(f"\n总共收集到 {len(all_papers)} 篇论文")
    return all_papers


def read_all_profiles(profiles_source: Union[str, Path], num_authors: Optional[int] = None) -> List[Dict]:
    """
    读取所有author profile数据
    
    支持两种输入：
    - 目录路径：包含多个JSON文件的目录
    - zip文件路径：包含所有JSON文件的zip压缩包
    
    Args:
        profiles_source: 目录路径或zip文件路径
        num_authors: 要读取的作者数量，None表示读取全部
    
    Returns:
        list: 包含所有profile数据的列表
    """
    profiles_source = Path(profiles_source)
    profiles = []
    
    # 判断是目录还是zip文件
    if profiles_source.is_dir():
        json_files = list(profiles_source.glob("author_*.json"))
        
        if num_authors and num_authors < len(json_files):
            json_files = random.sample(json_files, num_authors)
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    profiles.append(json.load(f))
            except Exception as e:
                print(f"读取 {json_file.name} 时出错: {e}")
                continue
                
    elif profiles_source.suffix == '.zip' and profiles_source.exists():
        with zipfile.ZipFile(profiles_source, 'r') as zipf:
            json_files = [name for name in zipf.namelist() 
                         if 'author_' in name and name.endswith(".json")]
            
            if num_authors and num_authors < len(json_files):
                json_files = random.sample(json_files, num_authors)
            
            for filename in json_files:
                try:
                    with zipf.open(filename) as f:
                        content = f.read().decode('utf-8')
                        profiles.append(json.loads(content))
                except Exception as e:
                    print(f"读取 {filename} 时出错: {e}")
                    continue
    else:
        raise ValueError(f"无效的路径: {profiles_source}。必须是目录或zip文件")
    
    return profiles

