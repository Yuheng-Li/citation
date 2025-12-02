#!/usr/bin/env python3
"""
作者名字匹配工具
用于比较 arXiv 作者名和 Google Scholar 作者名是否匹配
结合使用 rapidfuzz 和 nameparser 库
"""
import re
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

try:
    from nameparser import HumanName
    NAMEPARSER_AVAILABLE = True
except ImportError:
    NAMEPARSER_AVAILABLE = False


def normalize_name(name):
    """
    标准化名字，用于比较
    
    Args:
        name: 原始名字字符串
    
    Returns:
        标准化后的名字字符串
    """
    if not name:
        return ""
    
    # 转换为小写
    name = name.lower()
    
    # 移除多余的空格
    name = re.sub(r'\s+', ' ', name)
    
    # 移除首尾空格
    name = name.strip()
    
    # 移除常见的标点符号（保留空格和点号用于缩写）
    # name = re.sub(r'[^\w\s.]', '', name)
    
    return name


def extract_name_parts(name):
    """
    提取名字的各个部分（姓、名等）
    
    Args:
        name: 名字字符串
    
    Returns:
        list: 名字部分的列表
    """
    # 先处理驼峰命名（CamelCase），在转换为小写之前
    # 处理驼峰命名（CamelCase），如 "JunGyu" -> "Jun Gyu"
    # 在单词边界（小写后跟大写）之间插入空格
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    
    # 处理连字符名字（如 "Joon-Young"），将连字符替换为空格
    name = name.replace('-', ' ')
    
    # 现在标准化（转换为小写等）
    normalized = normalize_name(name)
    
    # 按空格分割
    parts = [p.strip() for p in normalized.split() if p.strip()]
    
    # 移除每个部分末尾的点号（用于处理 "J." 这样的缩写）
    parts = [p.rstrip('.') for p in parts if p.rstrip('.')]
    
    return parts


def generate_initials(parts):
    """
    生成名字的首字母缩写
    
    Args:
        parts: 名字部分的列表
    
    Returns:
        str: 首字母缩写（如 "Ho Kei" -> "HK"）
    """
    initials = []
    for part in parts:
        if part:
            # 移除点号
            part_clean = part.rstrip('.')
            if part_clean:
                initials.append(part_clean[0])
    return ''.join(initials)


def _match_given_names(parts_a, parts_b):
    """
    检查名字部分是否匹配，允许缩写和中间名
    
    Args:
        parts_a: 第一个名字的名字部分列表
        parts_b: 第二个名字的名字部分列表
    
    Returns:
        bool: 如果匹配返回 True
    """
    # 清理点号
    parts_a = [p.rstrip('.') for p in parts_a if p.rstrip('.')]
    parts_b = [p.rstrip('.') for p in parts_b if p.rstrip('.')]
    
    if not parts_a or not parts_b:
        return False
    
    # 特殊情况：如果 parts_b 只有一个部分，且是多字母缩写（如 "HK", "SW", "JY"）
    if len(parts_b) == 1 and len(parts_b[0]) > 1:
        abbrev = parts_b[0]
        if abbrev.isalpha() and len(abbrev) <= len(parts_a):
            initials_a = generate_initials(parts_a)
            if initials_a.lower() == abbrev.lower():
                return True
    
    # 特殊情况：如果 parts_a 只有一个部分，且是多字母缩写
    if len(parts_a) == 1 and len(parts_a[0]) > 1:
        abbrev = parts_a[0]
        if abbrev.isalpha() and len(abbrev) <= len(parts_b):
            initials_b = generate_initials(parts_b)
            if initials_b.lower() == abbrev.lower():
                return True
    
    # 如果 parts_a 的所有部分都能在 parts_b 中找到匹配
    matched_indices = set()
    for part_a in parts_a:
        found = False
        for i, part_b in enumerate(parts_b):
            if i in matched_indices:
                continue
            # 完全匹配
            if part_a.lower() == part_b.lower():
                matched_indices.add(i)
                found = True
                break
            # 缩写匹配：part_a 是 part_b 的缩写
            if len(part_a) == 1 and part_b.lower().startswith(part_a.lower()):
                matched_indices.add(i)
                found = True
                break
            # 缩写匹配：part_b 是 part_a 的缩写
            if len(part_b) == 1 and part_a.lower().startswith(part_b.lower()):
                matched_indices.add(i)
                found = True
                break
            # 部分匹配：较长的部分包含较短的部分
            if len(part_a) > 1 and part_b.lower().startswith(part_a.lower()):
                matched_indices.add(i)
                found = True
                break
            if len(part_b) > 1 and part_a.lower().startswith(part_b.lower()):
                matched_indices.add(i)
                found = True
                break
        if not found:
            return False
    return True


def match_author_names(name1, name2):
    """
    判断两个作者名字是否匹配
    
    匹配规则：
    1. 完全匹配（忽略大小写和多余空格）
    2. 使用 rapidfuzz 进行快速模糊匹配（作为初步筛选）
    3. 使用 nameparser 解析人名结构
    4. 姓氏必须匹配（最后一个部分）
    5. 名字部分允许缩写匹配（如 "John" 匹配 "J" 或 "J."）
    6. 支持多字母缩写（如 "Ho Kei" 匹配 "HK"）
    7. 允许中间名存在或不存在（如 "John Smith" 匹配 "John A. Smith"）
    
    Args:
        name1: 第一个名字（通常是 arXiv 作者名）
        name2: 第二个名字（通常是 Google Scholar 作者名）
    
    Returns:
        bool: 如果匹配返回 True，否则返回 False
    """
    if not name1 or not name2:
        return False
    
    # 标准化两个名字
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)
    
    # 完全匹配
    if norm1 == norm2:
        return True
    
    # 使用 rapidfuzz 进行快速初步筛选
    # 如果相似度太低，直接返回 False（节省计算时间）
    if RAPIDFUZZ_AVAILABLE:
        # 使用 token_sort_ratio（词序无关匹配）和 partial_ratio（部分匹配）
        token_sort_score = fuzz.token_sort_ratio(norm1, norm2)
        partial_score = fuzz.partial_ratio(norm1, norm2)
        max_fuzz_score = max(token_sort_score, partial_score)
        
        # 如果相似度太低（< 50），很可能不匹配
        if max_fuzz_score < 50:
            return False
        
        # 如果相似度很高（>= 90），很可能匹配（但还需要验证姓氏）
        if max_fuzz_score >= 90:
            # 高相似度时，继续下面的详细检查以确保姓氏匹配
            pass
    
    # 使用 nameparser 解析人名（如果可用）
    if NAMEPARSER_AVAILABLE:
        try:
            parsed1 = HumanName(name1)
            parsed2 = HumanName(name2)
            
            # 获取姓氏
            last1 = parsed1.last.lower().strip()
            last2 = parsed2.last.lower().strip()
            
            # 姓氏必须匹配（这是最重要的条件）
            if last1 and last2 and last1 != last2:
                # 允许姓氏的缩写匹配
                if not (len(last1) == 1 and last2.startswith(last1)) and \
                   not (len(last2) == 1 and last1.startswith(last2)):
                    return False
            
            # 获取名字部分
            first1 = parsed1.first.lower().strip()
            middle1 = parsed1.middle.lower().strip()
            first2 = parsed2.first.lower().strip()
            middle2 = parsed2.middle.lower().strip()
            
            # 组合名字和中间名
            given1_parts = [p for p in [first1, middle1] if p]
            given2_parts = [p for p in [first2, middle2] if p]
            
            # 如果都没有名字部分，只有姓氏，且姓氏匹配，则匹配
            if not given1_parts and not given2_parts:
                if last1 == last2 or (last1 and last2):
                    return True
            
            # 检查名字部分是否匹配
            if given1_parts and given2_parts:
                # 使用现有的多字母缩写匹配逻辑
                if _match_given_names(given1_parts, given2_parts):
                    return True
            
            # 如果一方有名字，另一方没有，检查是否是单字符缩写
            if not given1_parts and given2_parts:
                if len(given2_parts) == 1 and len(given2_parts[0]) == 1:
                    return True
            if given1_parts and not given2_parts:
                if len(given1_parts) == 1 and len(given1_parts[0]) == 1:
                    return True
            
        except Exception:
            # 如果 nameparser 解析失败，回退到原有逻辑
            pass
    
    # 回退到原有的完整匹配逻辑（如果 nameparser 不可用或解析失败）
    # 处理名字顺序问题（如 "Smith, John"）
    def reorder_name_parts(name_str, parts):
        """如果名字是 "Last, First" 格式，重新排序"""
        if ',' in name_str:
            # 找到逗号位置
            comma_pos = name_str.find(',')
            # 重新分割：逗号前是姓氏，逗号后是名字
            before_comma = normalize_name(name_str[:comma_pos])
            after_comma = normalize_name(name_str[comma_pos+1:])
            # 重新组合：名字在前，姓氏在后
            reordered = extract_name_parts(after_comma) + extract_name_parts(before_comma)
            return reordered if reordered else parts
        return parts
    
    # 提取名字部分
    parts1 = reorder_name_parts(name1, extract_name_parts(name1))
    parts2 = reorder_name_parts(name2, extract_name_parts(name2))
    
    if not parts1 or not parts2:
        return False
    
    # 如果部分数量差异太大，不太可能匹配
    if abs(len(parts1) - len(parts2)) > 2:
        return False
    
    # 获取姓氏部分（可能包含连字符，所以姓氏可能是最后几个部分）
    # 从后往前匹配，找到最长的匹配姓氏部分
    def match_lastname_parts(parts_a, parts_b):
        """从后往前匹配姓氏部分，返回匹配的部分数量"""
        i = 1
        while i <= len(parts_a) and i <= len(parts_b):
            last_a = ' '.join(parts_a[-i:])
            last_b = ' '.join(parts_b[-i:])
            if last_a == last_b:
                i += 1
            else:
                break
        return i - 1
    
    # 找到匹配的姓氏部分数量
    matched_lastname_parts = match_lastname_parts(parts1, parts2)
    
    if matched_lastname_parts == 0:
        # 姓氏完全不匹配，检查是否是缩写
        lastname1 = parts1[-1]
        lastname2 = parts2[-1]
        if not (len(lastname1) == 1 and lastname2.startswith(lastname1)) and \
           not (len(lastname2) == 1 and lastname1.startswith(lastname2)):
            return False
        # 如果姓氏是缩写匹配，姓氏部分数量是1
        matched_lastname_parts = 1
    
    # 获取名字部分（除了姓氏之外的所有部分）
    firstnames1 = parts1[:-matched_lastname_parts] if matched_lastname_parts > 0 else parts1[:-1]
    firstnames2 = parts2[:-matched_lastname_parts] if matched_lastname_parts > 0 else parts2[:-1]
    
    # 如果都没有名字部分，只有姓氏，且姓氏匹配，则匹配
    if not firstnames1 and not firstnames2:
        return True
    
    # 如果一方有名字部分，另一方没有，需要检查
    if not firstnames1 and firstnames2:
        # 如果另一方只有一个单字符名字（如 "J"），可能是缩写，允许匹配
        if len(firstnames2) == 1 and len(firstnames2[0]) == 1:
            return True
        return False
    if firstnames1 and not firstnames2:
        # 如果这一方只有一个单字符名字（如 "J"），可能是缩写，允许匹配
        if len(firstnames1) == 1 and len(firstnames1[0]) == 1:
            return True
        return False
    
    # 使用辅助函数检查名字部分是否匹配
    match_1_to_2 = _match_given_names(firstnames1, firstnames2)
    match_2_to_1 = _match_given_names(firstnames2, firstnames1)
    
    # 如果两个方向都匹配，则匹配
    if match_1_to_2 and match_2_to_1:
        return True
    
    # 如果一方是另一方的子集（允许中间名），也认为匹配
    # 例如 "John Smith" 匹配 "John A. Smith"
    if match_1_to_2 and len(firstnames1) <= len(firstnames2):
        return True
    if match_2_to_1 and len(firstnames2) <= len(firstnames1):
        return True
    
    return False


if __name__ == "__main__":
    # 测试用例
    test_cases = [
        ("H. Umut Suluhan", "H Umut Suluhan", True),
        ("Yuhang Yang", "Y Yang", True),
        ("John Smith", "J. Smith", True),
        ("John Smith", "Smith, John", True),
        ("John Smith", "John A. Smith", True),
        ("John Smith", "Jane Smith", False),
        ("John", "John", True),
        ("", "", False),
        # 多字母缩写测试
        ("Ho Kei Cheng", "HK Cheng", True),
        ("Seoung Wug Oh", "SW Oh", True),
        ("Joon-Young Lee", "JY Lee", True),
        ("JunGyu Lee", "JG Lee", True),  # 驼峰命名
        ("Brian Price", "B Price", True),
        # 连字符姓氏测试
        ("Tinh-Anh Nguyen-Nhu", "TA Nguyen-Nhu", True),
        ("Huu-Phong Phan-Nguyen", "HP Phan-Nguyen", True),
        ("Nhat-Minh Nguyen-Dich", "NM Nguyen-Dich", True),
    ]
    
    print("测试 name_matcher:")
    for name1, name2, expected in test_cases:
        result = match_author_names(name1, name2)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{name1}' <-> '{name2}': {result} (期望: {expected})")

