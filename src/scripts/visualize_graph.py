import json
import os
import streamlit as st
import networkx as nx
from pyvis.network import Network
import pandas as pd
from collections import Counter

# 配置目录
RE_OUTPUT_DIR = '/Users/cuiziliang/Projects/LKG-GEN/src/data/re_output'

# 页面配置
st.set_page_config(
    page_title="知识图谱可视化", 
    page_icon="🕸️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .stSelectbox > div > div {
        background-color: #f0f2f6;
        border-radius: 8px;
    }
    .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 主标题
st.markdown("""
<div class="main-header">
    <h1>🕸️ 知识图谱可视化工具</h1>
    <p>探索数据中的实体关系，构建智能知识网络</p>
</div>
""", unsafe_allow_html=True)

# 侧边栏配置
with st.sidebar:
    st.markdown("""
    <div class="sidebar-content">
        <h3>🎛️ 控制面板</h3>
        <p>调整图谱参数和显示选项</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 获取所有 JSON 文件
    json_files = [f for f in os.listdir(RE_OUTPUT_DIR) if f.endswith('.json')]
    
    if not json_files:
        st.error("⚠️ re_output 目录下没有找到 JSON 文件")
        st.stop()
    
    st.subheader("📁 文件选择")
    selected_file = st.selectbox(
        "选择知识图谱数据文件", 
        json_files,
        help="选择要可视化的JSON数据文件"
    )
    
    # 图谱参数设置
    st.subheader("🎨 图谱设置")
    
    # 物理引擎设置
    physics_enabled = st.checkbox("启用物理引擎", value=True, help="启用后节点会有物理交互效果")
    
    # 节点大小设置
    node_size = st.slider("节点大小", min_value=10, max_value=50, value=25, help="调整图谱中节点的大小")
    
    # 边的长度
    edge_length = st.slider("边长度", min_value=50, max_value=300, value=150, help="调整节点之间连线的长度")
    
    # 颜色主题
    color_theme = st.selectbox(
        "颜色主题",
        ["深色主题", "浅色主题", "彩虹主题"],
        help="选择图谱的颜色风格"
    )

# 主内容区域
if selected_file:
    # 加载数据
    file_path = os.path.join(RE_OUTPUT_DIR, selected_file)
    with st.spinner("🔄 正在加载数据..."):
        with open(file_path, 'r', encoding='utf-8') as f:
            triples = json.load(f)
    
    st.success(f"✅ 成功加载 {len(triples)} 条三元组数据")
    
    # 数据预处理和统计
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>📊 三元组总数</h4>
            <h2>{}</h2>
        </div>
        """.format(len(triples)), unsafe_allow_html=True)
    
    # 构建图
    G = nx.DiGraph()
    relations = []
    entities = set()
    
    for triple in triples:
        head = triple.get('head', '').strip()
        relation = triple.get('relation', '').strip()
        tail = triple.get('tail', '').strip()
        if head and tail and relation:
            G.add_edge(head, tail, label=relation)
            relations.append(relation)
            entities.add(head)
            entities.add(tail)
    
    # 统计信息
    relation_counts = Counter(relations)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>🔗 实体总数</h4>
            <h2>{}</h2>
        </div>
        """.format(len(entities)), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>🌐 关系总数</h4>
            <h2>{}</h2>
        </div>
        """.format(G.number_of_edges()), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h4>🏷️ 关系类型</h4>
            <h2>{}</h2>
        </div>
        """.format(len(relation_counts)), unsafe_allow_html=True)
    
    # 图谱可视化
    st.markdown("---")
    st.subheader("🕸️ 交互式知识图谱")
    
    # 根据主题设置颜色
    if color_theme == "深色主题":
        bg_color = "#1e1e1e"
        font_color = "white"
        node_color = "#667eea"
    elif color_theme == "浅色主题":
        bg_color = "#ffffff"
        font_color = "black"
        node_color = "#4a90e2"
    else:  # 彩虹主题
        bg_color = "#2d3748"
        font_color = "white"
        node_color = "#ff6b6b"
    
    # 检查图是否为空
    if G.number_of_nodes() == 0:
        st.warning("⚠️ 没有找到有效的节点数据，请检查JSON文件格式")
        st.stop()
    
    # 创建pyvis网络图 - 使用更简单的配置
    net = Network(
        height="800px", 
        width="100%", 
        bgcolor=bg_color, 
        font_color=font_color, 
        directed=True,
        notebook=False
    )
    
    # 批量添加节点 - 使用更稳定的方式
    try:
        # 为节点添加颜色和大小
        node_list = list(G.nodes())
        for i, node in enumerate(node_list):
            # 为不同节点设置不同颜色（如果是彩虹主题）
            if color_theme == "彩虹主题":
                colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7", "#dda0dd"]
                node_color_final = colors[i % len(colors)]
            else:
                node_color_final = node_color
            
            net.add_node(
                node, 
                label=str(node)[:20] + "..." if len(str(node)) > 20 else str(node),  # 限制标签长度
                size=node_size,
                color=node_color_final,
                title=str(node)  # 悬停显示完整名称
            )
        
        # 批量添加边
        for edge in G.edges(data=True):
            relation_label = edge[2].get('label', '')
            net.add_edge(
                edge[0], 
                edge[1], 
                label=relation_label[:15] + "..." if len(relation_label) > 15 else relation_label,  # 限制关系标签长度
                title=relation_label,  # 悬停显示完整关系
                length=edge_length,
                width=2
            )
        
        # 设置物理引擎 - 使用更稳定的配置
        if physics_enabled:
            net.set_options("""
            {
              "physics": {
                "enabled": true,
                "barnesHut": {
                  "gravitationalConstant": -8000,
                  "centralGravity": 0.3,
                  "springLength": 95,
                  "springConstant": 0.04,
                  "damping": 0.09
                },
                "stabilization": {
                  "enabled": true,
                  "iterations": 100,
                  "updateInterval": 25
                }
              },
              "interaction": {
                "dragNodes": true,
                "dragView": true,
                "zoomView": true
              }
            }
            """)
        else:
            net.set_options("""
            {
              "physics": {"enabled": false},
              "interaction": {
                "dragNodes": true,
                "dragView": true,
                "zoomView": true
              }
            }
            """)
        
        # 创建三元组数据的JavaScript对象
        triples_js_data = {}
        for triple in triples:
            head = triple.get('head', '').strip()
            relation = triple.get('relation', '').strip()
            tail = triple.get('tail', '').strip()
            if head and relation and tail:
                if head not in triples_js_data:
                    triples_js_data[head] = []
                triples_js_data[head].append({
                    'head': head,
                    'relation': relation,
                    'tail': tail
                })
        
        # 保存并显示图谱
        html_path = os.path.join(os.getcwd(), 'graph.html')
        net.save_graph(html_path)
        
        # 检查文件是否成功生成
        if os.path.exists(html_path):
            with open(html_path, 'r', encoding='utf-8') as f:
                html_data = f.read()
            
            # 修改HTML以添加交互功能
            enhanced_html = html_data.replace(
                '</body>',
                f'''
                <div id="node-info" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #667eea; display: none;">
                    <h3 style="margin-top: 0; color: #333;">🔍 节点详情</h3>
                    <p id="selected-node" style="font-weight: bold; color: #667eea;"></p>
                    <div id="triples-table"></div>
                </div>
                
                <script>
                // 三元组数据
                const triplesData = {json.dumps(triples_js_data, ensure_ascii=False)};
                
                // 监听节点点击事件
                network.on("click", function(params) {{
                    if (params.nodes.length > 0) {{
                        const nodeId = params.nodes[0];
                        showNodeTriples(nodeId);
                    }} else {{
                        hideNodeInfo();
                    }}
                }});
                
                function showNodeTriples(nodeId) {{
                    const nodeInfo = document.getElementById('node-info');
                    const selectedNode = document.getElementById('selected-node');
                    const triplesTable = document.getElementById('triples-table');
                    
                    selectedNode.textContent = `选中节点: ${{nodeId}}`;
                    
                    if (triplesData[nodeId] && triplesData[nodeId].length > 0) {{
                        let tableHTML = `
                        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                            <thead>
                                <tr style="background: #667eea; color: white;">
                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">头实体</th>
                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">关系</th>
                                    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">尾实体</th>
                                </tr>
                            </thead>
                            <tbody>`;
                        
                        triplesData[nodeId].forEach((triple, index) => {{
                            const bgColor = index % 2 === 0 ? '#f8f9fa' : '#ffffff';
                            tableHTML += `
                            <tr style="background: ${{bgColor}};">
                                <td style="padding: 8px; border: 1px solid #ddd;">${{triple.head}}</td>
                                <td style="padding: 8px; border: 1px solid #ddd; color: #667eea; font-weight: bold;">${{triple.relation}}</td>
                                <td style="padding: 8px; border: 1px solid #ddd;">${{triple.tail}}</td>
                            </tr>`;
                        }});
                        
                        tableHTML += '</tbody></table>';
                        triplesTable.innerHTML = tableHTML;
                    }} else {{
                        triplesTable.innerHTML = '<p style="color: #666; font-style: italic;">该节点没有作为头实体的三元组</p>';
                    }}
                    
                    nodeInfo.style.display = 'block';
                }}
                
                function hideNodeInfo() {{
                    const nodeInfo = document.getElementById('node-info');
                    nodeInfo.style.display = 'none';
                }}
                </script>
                </body>'''
            )
            
            # 显示图谱
            st.components.v1.html(enhanced_html, height=850, scrolling=True)
            
            # 显示成功消息和使用提示
            st.success("✅ 知识图谱加载成功！点击节点查看相关三元组")
            st.info("💡 提示：点击图谱中的任意节点，下方会显示以该节点为头实体的所有三元组")
        else:
            st.error("❌ 图谱文件生成失败，请重试")
            
    except Exception as e:
        st.error(f"❌ 图谱生成过程中出现错误: {str(e)}")
        st.info("💡 建议：尝试减小节点大小或关闭物理引擎")
    
    # 详细统计信息
    st.markdown("---")
    st.subheader("📈 详细统计分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏷️ 关系类型分布")
        if relation_counts:
            relation_df = pd.DataFrame(list(relation_counts.items()), columns=['关系类型', '出现次数'])
            st.dataframe(relation_df, use_container_width=True)
    
    with col2:
        st.markdown("#### 🔗 图谱拓扑信息")
        st.write(f"**节点数量**: {G.number_of_nodes()}")
        st.write(f"**边数量**: {G.number_of_edges()}")
        st.write(f"**图密度**: {nx.density(G):.4f}")
        if G.number_of_nodes() > 0:
            st.write(f"**平均度数**: {sum(dict(G.degree()).values()) / G.number_of_nodes():.2f}")
    
    # 下载选项
    st.markdown("---")
    st.subheader("💾 导出选项")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "📄 下载 HTML 图谱", 
            data=html_data, 
            file_name=f"knowledge_graph_{selected_file.replace('.json', '')}.html", 
            mime="text/html",
            help="下载交互式HTML图谱文件"
        )
    
    with col2:
        if relation_counts:
            csv_data = relation_df.to_csv(index=False, encoding='utf-8')
            st.download_button(
                "📊 下载统计数据", 
                data=csv_data, 
                file_name=f"statistics_{selected_file.replace('.json', '')}.csv", 
                mime="text/csv",
                help="下载关系统计CSV文件"
            )
    
    with col3:
        json_data = json.dumps(triples, ensure_ascii=False, indent=2)
        st.download_button(
            "📋 下载原始数据", 
            data=json_data, 
            file_name=f"data_{selected_file}", 
            mime="application/json",
            help="下载原始JSON数据文件"
        )

    # 侧边栏底部信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div class="sidebar-content">
        <h3>ℹ️ 关于工具</h3>
        <p>这是一个强大的知识图谱可视化工具</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar.expander("🔧 功能特性"):
        st.markdown("""
        - 🎨 **多种主题**: 支持深色、浅色、彩虹主题
        - ⚙️ **参数调节**: 可调节节点大小、边长度等
        - 🔄 **物理引擎**: 支持动态物理交互效果
        - 📊 **统计分析**: 提供详细的图谱统计信息
        - 💾 **多格式导出**: 支持HTML、CSV、JSON格式
        """)
    
    with st.sidebar.expander("📖 使用说明"):
        st.markdown("""
        1. **选择文件**: 从下拉菜单选择JSON数据文件
        2. **调整参数**: 使用左侧控件调整图谱显示效果
        3. **交互操作**: 在图谱中拖拽节点、缩放视图
        4. **查看统计**: 滚动查看详细的统计分析
        5. **导出数据**: 使用底部按钮导出不同格式文件
        """)
    
    with st.sidebar.expander("🛠️ 技术栈"):
        st.markdown("""
        - **Streamlit**: Web应用框架
        - **NetworkX**: 图数据结构和算法
        - **Pyvis**: 交互式网络可视化
        - **Plotly**: 数据可视化
        - **Pandas**: 数据处理和分析
        """)
    
    st.sidebar.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding: 1rem; background: #f0f2f6; border-radius: 8px;">
        <p style="margin: 0; color: #666;">💡 提示：鼠标悬停在节点上可查看详细信息</p>
    </div>
    """, unsafe_allow_html=True)