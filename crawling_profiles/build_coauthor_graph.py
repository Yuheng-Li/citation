#!/usr/bin/env python3
"""
构建学术界co-author关系图，并生成HTML可视化
"""
import zipfile
import json
from pathlib import Path
from collections import defaultdict
import random

try:
    from pyvis.network import Network
    HAS_PYVIS = True
except ImportError:
    HAS_PYVIS = False
    print("警告: pyvis未安装，将使用D3.js生成HTML")


def build_graph_from_zip(zip_path, max_nodes=5000, min_connections=1):
    """
    从zip文件构建co-author关系图
    
    Args:
        zip_path: zip文件路径
        max_nodes: 最大节点数（如果节点太多，会采样）
        min_connections: 最小连接数（只保留至少有min_connections个连接的节点）
    
    Returns:
        tuple: (nodes_dict, edges_list)
        - nodes_dict: {scholar_id: {'name': name, 'connections': count}}
        - edges_list: [(id1, id2), ...]
    """
    zip_path = Path(zip_path)
    nodes = {}  # {scholar_id: {'name': name, 'connections': count}}
    edges = []  # [(id1, id2), ...]
    author_id_to_name = {}  # 用于存储作者ID到姓名的映射
    
    print(f"开始构建图...")
    print(f"最大节点数: {max_nodes}, 最小连接数: {min_connections}\n")
    
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        json_files = [name for name in zipf.namelist() 
                     if name.startswith("author_") and name.endswith(".json")]
        
        total_files = len(json_files)
        print(f"找到 {total_files} 个profile文件")
        
        # 第一步：收集所有节点和边
        # 使用set来加速边的去重检查
        edges_set = set()
        
        for idx, filename in enumerate(json_files, 1):
            try:
                with zipf.open(filename) as f:
                    content = f.read().decode('utf-8')
                    profile_data = json.loads(content)
                
                # 获取当前作者的ID和姓名
                author_id = filename.replace("author_", "").replace(".json", "")
                author_name = profile_data.get('author_info', {}).get('name', 'Unknown')
                author_id_to_name[author_id] = author_name
                
                # 初始化节点
                if author_id not in nodes:
                    nodes[author_id] = {'name': author_name, 'connections': 0}
                
                # 处理co_authors
                co_authors = profile_data.get('co_authors', [])
                if co_authors:
                    for co_author in co_authors:
                        co_id = co_author.get('scholar_id')
                        co_name = co_author.get('name', 'Unknown')
                        
                        if co_id:
                            # 添加co-author节点
                            if co_id not in nodes:
                                nodes[co_id] = {'name': co_name, 'connections': 0}
                            else:
                                # 更新姓名（如果之前没有）
                                if nodes[co_id]['name'] == 'Unknown' and co_name != 'Unknown':
                                    nodes[co_id]['name'] = co_name
                            
                            # 添加边（无向图，所以只添加一次，按ID排序确保一致性）
                            edge = tuple(sorted([author_id, co_id]))
                            if edge not in edges_set:
                                edges_set.add(edge)
                                edges.append(edge)
                                nodes[author_id]['connections'] += 1
                                nodes[co_id]['connections'] += 1
                
                # 更频繁地打印进度（每100个文件）
                if idx % 100 == 0:
                    elapsed = idx / total_files * 100
                    print(f"[{elapsed:.1f}%] 已处理 {idx}/{total_files} 个文件... "
                          f"节点: {len(nodes)}, 边: {len(edges)}")
                    
            except Exception as e:
                print(f"⚠️  处理 {filename} 时出错: {e}")
                continue
        
        print(f"\n✅ 完成！总共处理了 {total_files} 个文件")
    
    print(f"\n初始图统计:")
    print(f"  节点数: {len(nodes)}")
    print(f"  边数: {len(edges)}")
    
    # 第二步：过滤节点（只保留有足够连接的节点）
    if min_connections > 0:
        filtered_nodes = {nid: node for nid, node in nodes.items() 
                          if node['connections'] >= min_connections}
        filtered_edges = [(n1, n2) for n1, n2 in edges 
                         if n1 in filtered_nodes and n2 in filtered_nodes]
        
        print(f"\n过滤后（最小连接数 >= {min_connections}）:")
        print(f"  节点数: {len(filtered_nodes)}")
        print(f"  边数: {len(filtered_edges)}")
        
        nodes = filtered_nodes
        edges = filtered_edges
    
    # 第三步：如果节点太多，采样
    if len(nodes) > max_nodes:
        print(f"\n节点数 ({len(nodes)}) 超过最大限制 ({max_nodes})，开始采样...")
        
        # 按连接数排序，优先保留连接数多的节点
        sorted_nodes = sorted(nodes.items(), key=lambda x: x[1]['connections'], reverse=True)
        sampled_node_ids = set([nid for nid, _ in sorted_nodes[:max_nodes]])
        
        # 只保留采样节点之间的边
        sampled_edges = [(n1, n2) for n1, n2 in edges 
                        if n1 in sampled_node_ids and n2 in sampled_node_ids]
        sampled_nodes = {nid: nodes[nid] for nid in sampled_node_ids}
        
        print(f"采样后:")
        print(f"  节点数: {len(sampled_nodes)}")
        print(f"  边数: {len(sampled_edges)}")
        
        nodes = sampled_nodes
        edges = sampled_edges
    
    return nodes, edges


def generate_html_with_pyvis(nodes, edges, output_file):
    """使用pyvis生成HTML可视化"""
    net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white")
    net.barnes_hut()
    
    # 添加节点（节点ID是scholar_id，label显示name）
    for node_id, node_data in nodes.items():
        name = node_data['name']
        connections = node_data['connections']
        
        # 根据连接数设置节点大小
        size = min(10 + connections * 2, 50)
        
        # 根据连接数设置颜色（连接越多越亮）
        if connections > 20:
            color = "#FF6B6B"  # 红色 - 高度连接
        elif connections > 10:
            color = "#4ECDC4"  # 青色 - 中度连接
        else:
            color = "#95E1D3"  # 浅青色 - 低度连接
        
        # 节点ID是scholar_id，label显示name
        net.add_node(node_id, label=name, size=size, color=color, 
                    title=f"{name}<br>ID: {node_id}<br>连接数: {connections}")
    
    # 添加边（基于scholar_id）
    for n1, n2 in edges:
        net.add_edge(n1, n2)
    
    # 保存
    net.save_graph(output_file)
    print(f"\n✅ HTML文件已生成: {output_file}")


def generate_html_with_d3js(nodes, edges, output_file):
    """使用D3.js生成HTML可视化"""
    # 准备数据（节点ID是scholar_id，name用于显示）
    nodes_list = [{'id': nid, 'name': data['name'], 'connections': data['connections']} 
                  for nid, data in nodes.items()]
    edges_list = [{'source': n1, 'target': n2} for n1, n2 in edges]
    
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>学术界 Co-Author 关系图</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background-color: #1a1a1a;
            color: #fff;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 10px;
        }}
        .stats {{
            text-align: center;
            margin-bottom: 20px;
            color: #aaa;
        }}
        #graph {{
            border: 1px solid #333;
            border-radius: 8px;
            background-color: #222;
        }}
        .node {{
            cursor: pointer;
        }}
        .node:hover {{
            stroke: #fff;
            stroke-width: 2px;
        }}
        .link {{
            stroke: #555;
            stroke-opacity: 0.6;
            stroke-width: 1px;
        }}
        .tooltip {{
            position: absolute;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.8);
            border: 1px solid #555;
            border-radius: 4px;
            pointer-events: none;
            font-size: 12px;
            max-width: 200px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>学术界 Co-Author 关系图</h1>
        <div class="stats">
            节点数: {len(nodes_list)} | 边数: {len(edges_list)}
        </div>
        <svg id="graph"></svg>
    </div>
    
    <div class="tooltip" id="tooltip" style="display: none;"></div>
    
    <script>
        const nodes = {json.dumps(nodes_list)};
        const links = {json.dumps(edges_list)};
        
        const width = 1400;
        const height = 800;
        
        const svg = d3.select("#graph")
            .attr("width", width)
            .attr("height", height);
        
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(20));
        
        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link");
        
        const node = svg.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", d => Math.min(5 + d.connections * 0.5, 20))
            .attr("fill", "#4ECDC4")  // 统一颜色：青色
            .call(drag(simulation));
        
        const label = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .text(d => d.name.length > 15 ? d.name.substring(0, 15) + "..." : d.name)
            .attr("font-size", "10px")
            .attr("fill", "#fff")
            .attr("dx", 12)
            .attr("dy", 4);
        
        const tooltip = d3.select("#tooltip");
        
        node.on("mouseover", function(event, d) {{
            tooltip.style("display", "block")
                .html("<strong>" + d.name + "</strong><br>ID: " + d.id + "<br>连接数: " + d.connections)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px");
        }})
        .on("mouseout", function() {{
            tooltip.style("display", "none");
        }});
        
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});
        
        
        function drag(simulation) {{
            function dragstarted(event) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }}
            
            function dragged(event) {{
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }}
            
            function dragended(event) {{
                if (!event.active) simulation.alphaTarget(0);
                event.subject.fx = null;
                event.subject.fy = null;
            }}
            
            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }}
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"\n✅ HTML文件已生成: {output_file}")


if __name__ == "__main__":
    zip_file = "/Users/yuhli/Desktop/citation/crawling_profiles/all_author_profiles.zip"
    output_html = "/Users/yuhli/Desktop/citation/crawling_profiles/coauthor_graph.html"
    
    # 构建图
    # 参数说明：
    # max_nodes: 最大节点数（如果节点太多，会采样连接数最多的节点）
    # min_connections: 最小连接数（只保留至少有这个数量连接的节点）
    nodes, edges = build_graph_from_zip(zip_file, max_nodes=5000, min_connections=2)
    
    # 生成HTML可视化
    if HAS_PYVIS:
        print("\n使用 pyvis 生成可视化...")
        generate_html_with_pyvis(nodes, edges, output_html)
    else:
        print("\n使用 D3.js 生成可视化...")
        generate_html_with_d3js(nodes, edges, output_html)
    
    print(f"\n图统计:")
    print(f"  节点数: {len(nodes)}")
    print(f"  边数: {len(edges)}")
    print(f"\n可以在浏览器中打开 {output_html} 查看可视化结果")

