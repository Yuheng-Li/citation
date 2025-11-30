#!/usr/bin/env python3
"""
示例：如何使用 profile_reader.py 从目录或zip文件中读取author profile

注意：实际使用时应该直接使用 profile_reader.py 中的函数，
这个文件只是展示用法示例。
"""
from pathlib import Path
from profile_reader import collect_all_papers, read_all_profiles


if __name__ == "__main__":
    # 示例1: 从zip文件收集论文
    print("=" * 60)
    print("示例1: 从zip文件收集论文")
    print("=" * 60)
    zip_file = "all_author_profiles.zip"
    papers = collect_all_papers(zip_file, num_authors=10)
    print(f"✅ 收集了 {len(papers)} 篇论文\n")
    
    # 示例2: 从目录收集论文（如果zip不存在，会自动使用目录）
    print("=" * 60)
    print("示例2: 从目录收集论文")
    print("=" * 60)
    profiles_dir = "all_author_profiles"
    if Path(profiles_dir).exists():
        papers = collect_all_papers(profiles_dir, num_authors=10)
        print(f"✅ 收集了 {len(papers)} 篇论文\n")
    else:
        print(f"⚠️  目录不存在: {profiles_dir}\n")
    
    # 示例3: 读取完整的profile数据
    print("=" * 60)
    print("示例3: 读取完整的profile数据")
    print("=" * 60)
    profiles = read_all_profiles(zip_file, num_authors=5)
    print(f"✅ 读取了 {len(profiles)} 个profiles")
    if profiles:
        print(f"\n第一个profile的keys: {list(profiles[0].keys())}")
        print(f"作者姓名: {profiles[0].get('author_info', {}).get('name', 'N/A')}")
        print(f"论文数量: {len(profiles[0].get('papers', []))}")

