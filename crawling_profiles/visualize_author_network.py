#!/usr/bin/env python3
"""
可视化单个author的co-author网络
用法: python visualize_author_network.py <author_id> [layers]
    layers: 显示的层级数，默认为1（只显示co-authors）
            2表示显示co-authors的co-authors，以此类推
"""
import zipfile
import json
import sys
from pathlib import Path


def get_author_network(zip_path, author_id, layers=1):
    """
    从zip文件中获取指定author及其co-authors的网络（支持多层）
    包括co-authors之间的连接
    
    Args:
        zip_path: zip文件路径
        author_id: 要查找的author ID
        layers: 显示的层级数（1=只显示co-authors, 2=显示co-authors的co-authors, ...）
    
    Returns:
        tuple: (author_node, co_author_nodes, edges)
    """
    zip_path = Path(zip_path)
    
    author_node = None
    all_nodes_dict = {}  # {id: {'name': name, 'is_center': bool, 'layer': int}}
    edges = []
    
    filename = f"author_{author_id}.json"
    
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        if filename not in zipf.namelist():
            return None, [], []
        
        # 读取author的profile
        with zipf.open(filename) as f:
            content = f.read().decode('utf-8')
            profile_data = json.loads(content)
        
        # 获取author信息
        author_name = profile_data.get('author_info', {}).get('name', 'Unknown')
        author_node = {
            'id': author_id,
            'name': author_name,
            'is_center': True,
            'layer': 0
        }
        all_nodes_dict[author_id] = {
            'name': author_name,
            'is_center': True,
            'layer': 0
        }
        
        # 逐层查找co-authors
        current_layer_ids = {author_id}  # 当前层的节点ID
        
        for layer in range(1, layers + 1):
            next_layer_ids = set()
            
            # 遍历当前层的所有节点，找到他们的co-authors
            for node_id in current_layer_ids:
                node_filename = f"author_{node_id}.json"
                if node_filename not in zipf.namelist():
                    continue
                
                try:
                    with zipf.open(node_filename) as f:
                        node_content = f.read().decode('utf-8')
                        node_profile = json.loads(node_content)
                    
                    # 获取co-authors
                    co_authors = node_profile.get('co_authors', [])
                    for co_author in co_authors:
                        co_id = co_author.get('scholar_id')
                        co_name = co_author.get('name', 'Unknown')
                        
                        if co_id:
                            # 添加边
                            edge = tuple(sorted([node_id, co_id]))
                            if edge not in edges:
                                edges.append(edge)
                            
                            # 如果这个co-author还没被添加过，添加到下一层
                            if co_id not in all_nodes_dict:
                                all_nodes_dict[co_id] = {
                                    'name': co_name,
                                    'is_center': False,
                                    'layer': layer
                                }
                                next_layer_ids.add(co_id)
                except:
                    continue
            
            current_layer_ids = next_layer_ids
        
        # 构建co_author_nodes列表
        co_author_nodes = []
        for node_id, node_info in all_nodes_dict.items():
            if node_id != author_id:
                co_author_nodes.append({
                    'id': node_id,
                    'name': node_info['name'],
                    'is_center': node_info['is_center'],
                    'layer': node_info['layer']
                })
        
        # 检查所有节点之间的连接（包括跨层连接）
        all_node_ids = set(all_nodes_dict.keys())
        for node_id in all_node_ids:
            node_filename = f"author_{node_id}.json"
            if node_filename not in zipf.namelist():
                continue
            
            try:
                with zipf.open(node_filename) as f:
                    node_content = f.read().decode('utf-8')
                    node_profile = json.loads(node_content)
                
                co_authors = node_profile.get('co_authors', [])
                for co_author in co_authors:
                    co_id = co_author.get('scholar_id')
                    # 如果这个co-author也在我们的节点列表中，添加边
                    if co_id and co_id in all_node_ids and co_id != node_id:
                        edge = tuple(sorted([node_id, co_id]))
                        # 避免重复边
                        if edge not in edges:
                            edges.append(edge)
            except:
                continue
    
    return author_node, co_author_nodes, edges


def generate_html(author_node, co_author_nodes, edges, output_file):
    """生成HTML可视化"""
    all_nodes = [author_node] + co_author_nodes
    
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{author_node['name']} - Co-Author Network</title>
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
            stroke-width: 3px;
        }}
        .link {{
            stroke: #555;
            stroke-opacity: 0.6;
            stroke-width: 2px;
        }}
        .tooltip {{
            position: absolute;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.9);
            border: 1px solid #555;
            border-radius: 4px;
            pointer-events: none;
            font-size: 12px;
            max-width: 200px;
        }}
        .zoom-controls {{
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }}
        .zoom-btn {{
            background-color: #333;
            color: #fff;
            border: 1px solid #555;
            padding: 8px 15px;
            margin: 2px;
            cursor: pointer;
            border-radius: 4px;
            font-size: 14px;
        }}
        .zoom-btn:hover {{
            background-color: #444;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{author_node['name']} - Co-Author Network</h1>
        <div class="stats">
            Nodes: {len(all_nodes)} | Edges: {len(edges)}
        </div>
        <div class="zoom-controls">
            <button class="zoom-btn" onclick="zoomIn()">Zoom In</button>
            <button class="zoom-btn" onclick="zoomOut()">Zoom Out</button>
            <button class="zoom-btn" onclick="resetZoom()">Reset</button>
        </div>
        <svg id="graph"></svg>
    </div>
    
    <div class="tooltip" id="tooltip" style="display: none;"></div>
    
    <script>
        const nodes = {json.dumps(all_nodes)};
        const links = {json.dumps([{'source': e[0], 'target': e[1]} for e in edges])};
        
        const width = 1400;
        const height = 800;
        
        const svg = d3.select("#graph")
            .attr("width", width)
            .attr("height", height);
        
        // 添加缩放功能
        const g = svg.append("g");
        let currentZoom = 1;
        
        function zoomIn() {{
            currentZoom *= 1.2;
            g.attr("transform", "scale(" + currentZoom + ")");
        }}
        
        function zoomOut() {{
            currentZoom /= 1.2;
            g.attr("transform", "scale(" + currentZoom + ")");
        }}
        
        function resetZoom() {{
            currentZoom = 1;
            g.attr("transform", "scale(" + currentZoom + ")");
        }}
        
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(30));
        
        const link = g.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link");
        
        const node = g.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", d => d.is_center ? 25 : (d.layer === 1 ? 15 : 12))  // 中心节点最大，第1层中等，其他层较小
            .attr("fill", d => {{
                if (d.is_center) return "#FF6B6B";  // 中心节点红色
                if (d.layer === 1) return "#4ECDC4";  // 第1层青色
                return "#95E1D3";  // 其他层浅青色
            }})
            .call(drag(simulation));
        
        const label = g.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .text(d => d.name.length > 20 ? d.name.substring(0, 20) + "..." : d.name)
            .attr("font-size", d => d.is_center ? "14px" : (d.layer === 1 ? "12px" : "10px"))
            .attr("font-weight", d => d.is_center ? "bold" : "normal")
            .attr("fill", "#fff")
            .attr("dx", d => d.is_center ? 30 : 20)
            .attr("dy", 5);
        
        const tooltip = d3.select("#tooltip");
        
        node.on("mouseover", function(event, d) {{
            let layerText = "";
            if (d.is_center) {{
                layerText = "<br><em>(Center Node)</em>";
            }} else {{
                layerText = "<br><em>Layer " + d.layer + "</em>";
            }}
            tooltip.style("display", "block")
                .html("<strong>" + d.name + "</strong><br>ID: " + d.id + layerText)
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
                // 考虑缩放的影响
                const point = d3.pointer(event, svg.node());
                event.subject.fx = point[0] / currentZoom;
                event.subject.fy = point[1] / currentZoom;
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
    
    print(f"✅ HTML文件已生成: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python visualize_author_network.py <author_id> [layers]")
        print("示例: python visualize_author_network.py qpnsWPoAAAAJ 1")
        print("      python visualize_author_network.py qpnsWPoAAAAJ 2  # 显示2层关系")
        sys.exit(1)
    
    author_id = sys.argv[1]
    layers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    zip_file = "/Users/yuhli/Desktop/citation/crawling_profiles/all_author_profiles.zip"
    output_html = "/Users/yuhli/Desktop/citation/crawling_profiles/author_network.html"
    
    print(f"正在查找 author ID: {author_id}...")
    print(f"显示层级: {layers} 层")
    
    author_node, co_author_nodes, edges = get_author_network(zip_file, author_id, layers)
    
    if author_node is None:
        print(f"❌ 未找到 author ID: {author_id}")
        sys.exit(1)
    
    print(f"✅ 找到作者: {author_node['name']}")
    print(f"   Co-authors数量: {len(co_author_nodes)}")
    print(f"   边数: {len(edges)}")
    
    generate_html(author_node, co_author_nodes, edges, output_html)
    
    print(f"\n可以在浏览器中打开 {output_html} 查看可视化结果")

