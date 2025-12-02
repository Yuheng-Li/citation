#!/usr/bin/env python3
"""
Google Scholar 工具函数
"""
import requests
import re
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

# Bright Data configuration
headers = {
    "Authorization": "Bearer 95f1e5b4c7ef79702fb77666561a234104bba6d008706c56d95f27dcae3daa9a",
    "Content-Type": "application/json"
}

def build_google_scholar_search_url(title, authors):
    """构建 Google Scholar 搜索 URL
    
    Args:
        title: 论文标题
        authors: 作者列表
    
    Returns:
        str: Google Scholar 搜索 URL
    """
    # 构建搜索查询：标题 + 前5个作者
    query_parts = [title]
    top_authors = authors[:5] if len(authors) > 5 else authors
    query_parts.extend(top_authors)
    
    search_query = " ".join(query_parts)
    encoded_query = quote_plus(search_query)
    
    # 构建 Google Scholar 搜索 URL
    url = f"https://scholar.google.com/scholar?q={encoded_query}"
    return url

def fetch_google_scholar_page(title, authors, timeout=30):
    """使用 Bright Data API 获取 Google Scholar 页面
    使用标题 + 前5个作者构建搜索查询
    
    Args:
        title: 论文标题
        authors: 作者列表
        timeout: 超时时间（秒）
    
    Returns:
        str: HTML 内容，如果失败返回 None
    """
    # 构建 Google Scholar 搜索 URL
    url = build_google_scholar_search_url(title, authors)
    
    print(f"  Google Scholar URL: {url}")
    
    data = {
        "zone": "yuheng_serp",
        "url": url,
        "format": "raw"
    }
    
    try:
        response = requests.post(
            "https://api.brightdata.com/request",
            json=data,
            headers=headers,
            timeout=timeout
        )
        
        if response.status_code == 200:
            # 检查是否是错误消息或空响应
            if "not supported" in response.text.lower():
                return None
            if len(response.text) < 100:
                return None
            return response.text
        else:
            return None
            
    except Exception as e:
        print(f"  ⚠️  错误: {e}")
        return None

def extract_authors_from_gs_html(html, title=None):
    """
    从 Google Scholar HTML 中提取作者列表（混合方法：分别解析 gs_fma_s 和 gs_fma_p）
    
    Args:
        html: Google Scholar HTML 内容
        title: 论文标题（可选，用于匹配正确的论文）
    
    Returns:
        tuple: (authors_list, is_truncated, raw_text)
        - authors_list: 作者列表，每个作者格式为 {'name': '...', 'id': '...'} 或 {'name': '...', 'id': None}
        - is_truncated: 是否被截断
        - raw_text: 原始作者文本
    """
    soup = BeautifulSoup(html, 'html.parser')
    authors = []
    is_truncated = False
    raw_text = ""
    
    # 查找匹配的论文（如果提供了标题）
    matched_gs_r = None
    if title:
        gs_r_elems = soup.find_all('div', class_='gs_r')
        title_keywords = set(title.lower().split())
        
        best_match_score = 0
        matched_results = []  # 存储所有匹配的结果
        
        for gs_r in gs_r_elems:
            title_elem = gs_r.find('h3', class_='gs_rt')
            if title_elem:
                result_title = title_elem.get_text().lower()
                result_keywords = set(result_title.split())
                match_score = len(title_keywords & result_keywords)
                
                if match_score > best_match_score:
                    best_match_score = match_score
                    matched_results = [gs_r]  # 重置列表
                elif match_score == best_match_score and match_score > 0:
                    matched_results.append(gs_r)  # 添加相同分数的结果
        
        # 如果找到多个匹配的结果（可能是同一篇论文的不同版本），跳过
        if len(matched_results) > 1 and best_match_score >= 3:
            # 返回特殊值表示有多个匹配结果
            return None, False, ""
        
        if matched_results:
            matched_gs_r = matched_results[0]
    
    # 从 gs_a 元素提取作者（只解析文本，不使用链接）
    # Google Scholar 会在 gs_fma_s 和 gs_fma_p 两个class中都包含作者信息
    # 分别解析这两个，选择包含最多作者的那个
    
    # 查找 gs_fma_s 中的 gs_a
    fma_s_elems = soup.find_all('div', class_=lambda x: x and 'gs_a' in x and 'gs_fma_s' in x)
    # 查找 gs_fma_p 中的 gs_a  
    fma_p_elems = soup.find_all('div', class_=lambda x: x and 'gs_a' in x and 'gs_fma_p' in x)
    
    # 合并所有候选元素
    author_elems = []
    if fma_s_elems:
        author_elems.extend(fma_s_elems)
    if fma_p_elems:
        author_elems.extend(fma_p_elems)
    
    # 如果找不到 gs_a 元素，尝试查找所有 gs_a（向后兼容）
    if not author_elems:
        author_elems = soup.find_all('div', class_='gs_a')
    
    # 如果还是找不到，返回空列表
    if not author_elems:
        return [], False, ""
    
    # 处理所有 gs_a 元素，选择包含最多作者的那个
    best_authors = []
    best_raw_text = ""
    best_is_truncated = False
    
    for author_elem in author_elems:
        raw_text_current = author_elem.get_text()
        
        # 提取作者链接信息（建立作者名到ID的映射）
        author_links = {}  # {author_name: user_id}
        links = author_elem.find_all('a')
        for link in links:
            href = link.get('href', '')
            link_text = link.get_text().strip()
            # 提取user ID
            user_match = re.search(r'user=([^&]+)', href)
            if user_match and link_text:
                user_id = user_match.group(1)
                author_links[link_text] = user_id
        
        # 规范化空格
        raw_text_current = raw_text_current.replace('\xa0', ' ').replace('\u2009', ' ').replace('\u202f', ' ')
        
        # 提取作者部分
        author_part = None
        keywords = ['arxiv', 'preprint', 'proceedings', 'conference', 'journal', 'workshop', 'symposium']
        end_positions = []
        
        for keyword in keywords:
            # 查找关键词位置（包括没有空格分隔的情况，如 "X DiarXiv"）
            # 先查找有空格或标点分隔的
            pos_with_space = raw_text_current.lower().find(' ' + keyword)
            if pos_with_space > 0:
                end_positions.append(pos_with_space)
            # 再查找直接连接的（如 "X DiarXiv" 或 "P SingharXiv"）
            pos = raw_text_current.lower().find(keyword)
            if pos > 0:
                # 检查前面是否是作者名字的一部分
                # 如果关键词前面是小写字母，可能是作者名的一部分（如 "SingharXiv"）
                if pos > 2 and raw_text_current[pos-1].islower():
                    # 向前查找最近的空格或逗号（扩大查找范围，最多向前查找20个字符）
                    search_start = max(0, pos - 20)
                    space_pos = raw_text_current.rfind(' ', search_start, pos)
                    comma_pos = raw_text_current.rfind(',', search_start, pos)
                    
                    # 优先使用空格位置
                    separator_pos = space_pos if space_pos > comma_pos else comma_pos
                    
                    if separator_pos > 0 and separator_pos < pos - 1:
                        # 检查分隔符前是否是大写字母（作者名的首字母，如 "P"）
                        if raw_text_current[separator_pos-1].isupper():
                            # 这是作者名字的一部分，应该在关键词前截断
                            end_positions.append(pos)
                # 或者前面直接是大写字母+空格（较少见）
                elif pos > 2 and raw_text_current[pos-1].isupper() and raw_text_current[pos-2] == ' ':
                    end_positions.append(pos)
        
        year_match = re.search(r'\b(19|20)\d{2}\b', raw_text_current)
        if year_match:
            year_pos = year_match.start()
            if year_pos > 0 and (raw_text_current[year_pos-1] in ', \t'):
                end_positions.append(year_pos)
        
        url_match = re.search(r'\b[a-z0-9-]+\.[a-z]{2,}(?:\.[a-z]{2,})?\b', raw_text_current.lower())
        if url_match:
            url_pos = url_match.start()
            if url_pos > 0:
                end_positions.append(url_pos)
        
        if end_positions:
            author_part = raw_text_current[:min(end_positions)].strip()
        
        if author_part is None:
            # 使用正则表达式匹配，包括没有空格的情况（如 "X DiarXiv"）
            # 匹配模式：作者列表 + (空格+破折号 或 … 或 空格+arXiv 或 直接arXiv 或 preprint)
            author_part_match = re.search(r'^(.+?)(?:\s+-\s+|…|\s+arXiv|arXiv|preprint)', raw_text_current, re.IGNORECASE)
            if author_part_match:
                author_part = author_part_match.group(1).strip()
            elif '…' in raw_text_current:
                author_part = raw_text_current.split('…')[0].strip()
            else:
                author_part = raw_text_current.strip()
        
        # 检查截断标记
        elem_is_truncated = False
        if '…' in author_part:
            truncate_pos = author_part.find('…')
            if truncate_pos > 0:
                before_truncate = author_part[:truncate_pos].strip()
                if ',' in before_truncate:
                    elem_is_truncated = True
                    author_part = before_truncate.strip()
        elif '...' in author_part:
            truncate_pos = author_part.find('...')
            if truncate_pos > 0:
                before_truncate = author_part[:truncate_pos].strip()
                if ',' in before_truncate:
                    elem_is_truncated = True
                    author_part = before_truncate.strip()
        
        if not elem_is_truncated and re.search(r'\bet al\b', author_part, re.IGNORECASE):
            et_al_match = re.search(r',\s*\bet al\b', author_part, re.IGNORECASE)
            if et_al_match:
                elem_is_truncated = True
        
        # 清理并分割
        author_part_clean = re.sub(r'\bet al\b', '', author_part, flags=re.IGNORECASE)
        parsed_authors = [a.strip() for a in author_part_clean.split(',') if a.strip()]
        
        # 过滤并添加作者ID信息
        filtered_authors = []
        non_author_keywords = ['proceedings', 'conference', 'journal', 'workshop', 'symposium', 
                              'arxiv', 'preprint', 'ojs', 'com', 'www']
        url_keywords = ['org', 'edu']
        
        for author in parsed_authors:
            original_author = author
            author_lower = author.lower()
            
            if re.search(r'\.[a-z]{2,}(?:\.[a-z]{2,})?$', author_lower):
                continue
            
            keyword_positions = []
            for keyword in non_author_keywords:
                pos = author_lower.find(keyword)
                if pos > 0:
                    keyword_positions.append(pos)
            
            for keyword in url_keywords:
                if re.search(r'\.' + keyword + r'(?:\.[a-z]{2,})?$', author_lower):
                    pos = author_lower.find(keyword)
                    if pos > 0:
                        keyword_positions.append(pos)
            
            if keyword_positions:
                author = author[:min(keyword_positions)].strip()
            
            if any(keyword in author_lower for keyword in non_author_keywords):
                continue
            
            if any(re.search(r'\.' + keyword + r'(?:\.[a-z]{2,})?$', author_lower) for keyword in url_keywords):
                continue
            
            if author.isdigit() or len(author) < 2 or re.match(r'^\d{4}$', author):
                continue
            
            # 查找作者ID（尝试精确匹配和模糊匹配）
            author_id = None
            if author in author_links:
                author_id = author_links[author]
            else:
                # 尝试模糊匹配（忽略大小写和空格）
                author_normalized = author.replace(' ', '').lower()
                for link_name, link_id in author_links.items():
                    link_normalized = link_name.replace(' ', '').lower()
                    if author_normalized == link_normalized:
                        author_id = link_id
                        break
            
            # 存储为字典格式：{'name': author_name, 'id': author_id}
            filtered_authors.append({'name': author, 'id': author_id})
        
        # 如果这个元素提取到的作者更多，更新最佳结果
        if len(filtered_authors) > len(best_authors):
            best_authors = filtered_authors
            best_raw_text = raw_text_current
            best_is_truncated = elem_is_truncated
    
    if best_authors:
        authors = best_authors
        raw_text = best_raw_text
        is_truncated = best_is_truncated
    
    return authors, is_truncated, raw_text

def extract_citation_count_from_gs_html(html, title=None):
    """
    从 Google Scholar HTML 中提取论文的引用数量
    
    Args:
        html: Google Scholar HTML 内容
        title: 论文标题（可选，用于匹配正确的论文）
    
    Returns:
        int: 引用数量，如果找不到则返回 None
    """
    soup = BeautifulSoup(html, 'html.parser')
    citation_count = None
    
    # 查找匹配的论文（如果提供了标题）
    matched_gs_r = None
    if title:
        gs_r_elems = soup.find_all('div', class_='gs_r')
        title_keywords = set(title.lower().split())
        
        best_match_score = 0
        matched_results = []
        
        for gs_r in gs_r_elems:
            title_elem = gs_r.find('h3', class_='gs_rt')
            if title_elem:
                result_title = title_elem.get_text().lower()
                result_keywords = set(result_title.split())
                match_score = len(title_keywords & result_keywords)
                
                if match_score > best_match_score:
                    best_match_score = match_score
                    matched_results = [gs_r]
                elif match_score == best_match_score and match_score > 0:
                    matched_results.append(gs_r)
        
        if matched_results:
            matched_gs_r = matched_results[0]
    
    # 如果找到了匹配的论文，从该元素中提取引用数量
    # 否则，从第一个结果中提取
    target_elem = matched_gs_r if matched_gs_r else soup.find('div', class_='gs_r')
    
    if target_elem:
        # 查找 "Cited by" 链接
        # Google Scholar 通常使用 <a> 标签包含 "Cited by" 文本
        cited_by_links = target_elem.find_all('a', string=re.compile(r'Cited by', re.IGNORECASE))
        
        if not cited_by_links:
            # 尝试查找包含 "Cited by" 文本的任何元素
            cited_by_elems = target_elem.find_all(string=re.compile(r'Cited by\s+(\d+)', re.IGNORECASE))
            for elem in cited_by_elems:
                match = re.search(r'Cited by\s+(\d+)', elem, re.IGNORECASE)
                if match:
                    try:
                        citation_count = int(match.group(1))
                        break
                    except:
                        pass
        
        # 如果还没找到，尝试从链接文本中提取
        if citation_count is None:
            for link in cited_by_links:
                link_text = link.get_text()
                match = re.search(r'Cited by\s+(\d+)', link_text, re.IGNORECASE)
                if match:
                    try:
                        citation_count = int(match.group(1))
                        break
                    except:
                        pass
        
        # 如果还没找到，尝试查找所有包含数字的链接（可能是引用链接）
        if citation_count is None:
            all_links = target_elem.find_all('a')
            for link in all_links:
                href = link.get('href', '')
                link_text = link.get_text()
                # 检查是否是引用链接（通常包含 "citations" 或 "scholar?cites"）
                if 'citations' in href.lower() or 'cites' in href.lower():
                    # 尝试从链接文本中提取数字
                    match = re.search(r'(\d+)', link_text)
                    if match:
                        try:
                            citation_count = int(match.group(1))
                            break
                        except:
                            pass
    
    return citation_count

