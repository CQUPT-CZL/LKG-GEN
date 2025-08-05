import json
import os
import streamlit as st
import networkx as nx
from pyvis.network import Network

# 配置目录
RE_OUTPUT_DIR = '/Users/cuiziliang/Projects/LKG-GEN/src/data/re_output'

st.set_page_config(page_title="知识图谱可视化", page_icon="🕸️", layout="wide")

st.title("🕸️ 知识图谱可视化工具")
st.markdown("这个工具读取 re_output 目录下的 JSON 文件，展示交互式知识图谱。选择一个文件开始探索！")

# 获取所有 JSON 文件
json_files = [f for f in os.listdir(RE_OUTPUT_DIR) if f.endswith('.json')]
if not json_files:
    st.warning("⚠️ re_output 目录下没有找到 JSON 文件。")
else:
    selected_file = st.selectbox("选择 JSON 文件", json_files)
    
    if selected_file:
        file_path = os.path.join(RE_OUTPUT_DIR, selected_file)
        with open(file_path, 'r', encoding='utf-8') as f:
            triples = json.load(f)
        
        # 构建图
        G = nx.DiGraph()
        for triple in triples:
            head = triple.get('head', '')
            relation = triple.get('relation', '')
            tail = triple.get('tail', '')
            if head and tail:
                G.add_edge(head, tail, label=relation)
        
        # 使用 pyvis 创建交互图
        net = Network(notebook=False, height="750px", width="100%", bgcolor="#222222", font_color="white", directed=True)
        net.from_nx(G)
        net.show_buttons(filter_=['physics'])
        html_path = 'graph.html'
        net.save_graph(html_path)
        
        # 在 Streamlit 中显示
        with open(html_path, 'r', encoding='utf-8') as f:
            html_data = f.read()
        st.components.v1.html(html_data, height=800)
        
        st.markdown("### 图谱统计")
        st.write(f"节点数: {G.number_of_nodes()}")
        st.write(f"边数: {G.number_of_edges()}")
        
        # 下载选项
        st.download_button("下载 HTML 图谱", data=html_data, file_name="knowledge_graph.html", mime="text/html")

st.sidebar.title("关于")
st.sidebar.info("这个应用使用 NetworkX 和 Pyvis 构建交互式知识图谱。物理模拟使节点可拖拽，鼠标悬停显示关系。")