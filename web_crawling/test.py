import requests
import re
from urllib.parse import quote_plus

# Bright Data配置
headers = {
    "Authorization": "Bearer bb8030e2eec9cb8c59fe142d25d4dd4758c0f43946f547cd234760af4cbed3ce",
    "Content-Type": "application/json"
}

# 测试：搜索一篇论文
paper_title = "Attention Is All You Need"
encoded_title = quote_plus(paper_title)


scholar_url = "https://scholar.google.com/citations?user=IxrYJ6EAAAAJ"

data = {
    "zone": "yuheng_serp",
    "url": scholar_url,
    "format": "raw"  # 返回原始HTML
}

print(f"搜索论文: {paper_title}")
print(f"URL: {scholar_url}\n")

response = requests.post(
    "https://api.brightdata.com/request",
    json=data,
    headers=headers
)

print(f"状态码: {response.status_code}")
print(f"响应头: {dict(response.headers)}\n")

if response.status_code == 200:
    html = response.text
    print(f"HTML长度: {len(html)}")
    
    if len(html) == 0:
        print("\n⚠️  返回的HTML为空！")
        print("可能的原因:")
        print("  1. API token或zone配置有问题")
        print("  2. 需要在Bright Data后台激活zone")
        print("  3. 账户余额不足")
        print("\n完整响应:")
        print(response.text)
        print("\n响应体（原始）:")
        print(repr(response.content))
    else:
        # 提取Google Scholar IDs
        pattern = r'/citations\?user=([^&"\']+)'
        scholar_ids = list(set(re.findall(pattern, html)))
        
        if scholar_ids:
            print(f"\n✓ 找到 {len(scholar_ids)} 个Scholar IDs:")
            for sid in scholar_ids:
                print(f"  - {sid}")
                print(f"    Profile: https://scholar.google.com/citations?user={sid}")
        else:
            print("\n未找到Scholar IDs")
            print("\nHTML前1000个字符:")
            print(html[:1000])
else:
    print(f"\n❌ 请求失败: {response.status_code}")
    print("错误详情:")
    print(response.text)