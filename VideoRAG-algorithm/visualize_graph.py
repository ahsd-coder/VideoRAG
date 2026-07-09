"""
可视化 graph_chunk_entity_relation.graphml 知识图谱
用法:
    python visualize_graph.py                          # 生成静态图 + 交互式HTML
    python visualize_graph.py --mode interactive       # 仅交互式HTML (推荐服务器环境)
    python visualize_graph.py --mode static            # 仅静态PNG
"""

import argparse
import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import Counter

GRAPHML_PATH = "./videorag-workdir/graph_chunk_entity_relation.graphml"


def load_graph(path: str) -> nx.Graph:
    """加载 graphml 文件"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"图文件不存在: {path}")
    G = nx.read_graphml(path)
    print(f"✅ 加载图: {G.number_of_nodes()} 个节点, {G.number_of_edges()} 条边")
    return G


def print_graph_info(G: nx.Graph):
    """打印图的基本统计信息"""
    print("\n" + "=" * 60)
    print("📊 知识图谱统计")
    print("=" * 60)

    # 节点类型分布
    node_types = []
    for n, data in G.nodes(data=True):
        etype = data.get("entity_type", "UNKNOWN")
        node_types.append(etype)

    type_counts = Counter(node_types)
    print("\n📌 实体类型分布:")
    for etype, count in type_counts.most_common():
        bar = "█" * max(1, count)
        print(f"  {etype:<20} {count:>3} {bar}")

    # 度数分布
    degrees = [d for _, d in G.degree()]
    print(f"\n🔗 度数统计:")
    print(f"  平均度数: {np.mean(degrees):.2f}")
    print(f"  最大度数: {max(degrees)}")
    print(f"  孤立节点: {sum(1 for d in degrees if d == 0)}")

    # Top 实体
    print(f"\n🌟 核心实体 (按度数):")
    top_nodes = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:10]
    for node, deg in top_nodes:
        data = G.nodes[node]
        name = data.get("entity_name", node)[:40]
        etype = data.get("entity_type", "?")
        print(f"  [{etype}] {name} (度={deg})")

    # 关系样例
    print(f"\n📝 关系样例:")
    for i, (u, v, data) in enumerate(G.edges(data=True)):
        if i >= 5:
            print(f"  ... 共 {G.number_of_edges()} 条边")
            break
        desc = data.get("description", "?")[:80]
        weight = data.get("weight", "?")
        print(f"  {u[:25]} --[{desc}]--> {v[:25]}  w={weight}")

    print("=" * 60)


def draw_static(G: nx.Graph, output_path: str = "./videorag-workdir/knowledge_graph.png"):
    """使用 matplotlib 绘制静态图"""
    print(f"\n🎨 绘制静态图 → {output_path}")

    # 按实体类型着色
    type_colors = {
        "ORGANIZATION": "#FF6B6B",
        "PERSON": "#4ECDC4",
        "CONCEPT": "#FFD93D",
        "LOCATION": "#6BCB77",
        "EVENT": "#9B59B6",
        "DATE": "#E67E22",
        "TOPIC": "#45B7D1",
    }
    default_color = "#AAAAAA"

    node_colors = []
    for n, data in G.nodes(data=True):
        etype = data.get("entity_type", "").upper()
        node_colors.append(type_colors.get(etype, default_color))

    # 节点大小按度数
    degrees = dict(G.degree())
    max_deg = max(degrees.values()) if degrees else 1
    node_sizes = [300 + 1500 * (degrees[n] / max_deg) for n in G.nodes()]

    fig, axes = plt.subplots(1, 2, figsize=(20, 9))

    # ---- 子图1: 力导向布局 ----
    ax1 = axes[0]
    pos = nx.spring_layout(G, seed=42, k=2, iterations=50)

    nx.draw_networkx_edges(G, pos, ax=ax1, alpha=0.2, edge_color="gray", width=0.8)
    nx.draw_networkx_nodes(G, pos, ax=ax1, node_color=node_colors,
                           node_size=node_sizes, alpha=0.9, edgecolors="white", linewidths=0.5)
    # 只标注度数高的节点
    labels = {n: data.get("entity_name", n)[:20]
              for n, data in G.nodes(data=True)
              if degrees[n] >= max(2, np.percentile(list(degrees.values()), 70))}
    nx.draw_networkx_labels(G, pos, labels, ax=ax1, font_size=7,
                            font_family="sans-serif")

    ax1.set_title("Force-Directed Layout", fontsize=14, fontweight="bold")
    ax1.axis("off")

    # 图例
    used_types = set(data.get("entity_type", "").upper() for _, data in G.nodes(data=True))
    legend_patches = [mpatches.Patch(color=c, label=t)
                      for t, c in type_colors.items() if t in used_types]
    if legend_patches:
        ax1.legend(handles=legend_patches, loc="lower left",
                  fontsize=8, title="Entity Types", title_fontsize=9)

    # ---- 子图2: 圆形布局 (更好看关系) ----
    ax2 = axes[1]
    pos2 = nx.circular_layout(G)

    nx.draw_networkx_edges(G, pos2, ax=ax2, alpha=0.3, edge_color="steelblue",
                           width=0.8, connectionstyle="arc3,rad=0.1")
    nx.draw_networkx_nodes(G, pos2, ax=ax2, node_color=node_colors,
                           node_size=node_sizes, alpha=0.9, edgecolors="white", linewidths=0.5)
    # 所有节点都标注
    labels2 = {n: data.get("entity_name", n)[:15]
               for n, data in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos2, labels2, ax=ax2, font_size=6,
                            font_family="sans-serif")

    ax2.set_title("Circular Layout", fontsize=14, fontweight="bold")
    ax2.axis("off")

    plt.suptitle("VideoRAG Knowledge Graph", fontsize=16, fontweight="bold", y=0.98)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"   ✅ 已保存")


def draw_interactive(G: nx.Graph, output_path: str = "./videorag-workdir/knowledge_graph.html"):
    """
    使用 pyvis 生成交互式 HTML (适合服务器环境，本地浏览器打开即可)
    如果没有安装 pyvis: pip install pyvis
    """
    try:
        from pyvis.network import Network
    except ImportError:
        print("⚠️  pyvis 未安装，请执行: pip install pyvis")
        print("   改用 plotly 方案...")
        return draw_interactive_plotly(G, output_path)

    print(f"\n🌐 生成交互式图 → {output_path}")

    net = Network(height="750px", width="100%", bgcolor="#1a1a2e",
                  font_color="white", directed=False)
    net.set_options("""
    var options = {
      "nodes": {
        "font": {"size": 14, "face": "Microsoft YaHei, sans-serif"},
        "borderWidth": 2,
        "borderWidthSelected": 4
      },
      "edges": {
        "color": {"inherit": false, "color": "#888888", "opacity": 0.5},
        "smooth": {"type": "continuous"},
        "font": {"size": 10, "color": "#cccccc"}
      },
      "physics": {
        "barnesHut": {"gravitationalConstant": -3000, "springLength": 200},
        "minVelocity": 0.75
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true
      }
    }
    """)

    # 类型颜色映射
    type_colors = {
        "ORGANIZATION": "#FF6B6B",
        "PERSON": "#4ECDC4",
        "CONCEPT": "#FFD93D",
        "LOCATION": "#6BCB77",
        "EVENT": "#9B59B6",
        "TOPIC": "#45B7D1",
    }

    degrees = dict(G.degree())
    max_deg = max(degrees.values()) if degrees else 1

    for node, data in G.nodes(data=True):
        etype = data.get("entity_type", "").upper()
        name = data.get("entity_name", node)
        desc = data.get("description", "")[:200]
        color = type_colors.get(etype, "#AAAAAA")
        size = 10 + 30 * (degrees[node] / max_deg)

        tooltip = f"""
        <div style='max-width:300px;padding:10px;background:#222;border-radius:8px;color:#eee'>
          <b>{name}</b><br>
          <span style='color:#aaa'>类型:</span> {etype}<br>
          <span style='color:#aaa'>描述:</span> {desc}<br>
          <span style='color:#aaa'>度数:</span> {degrees[node]}
        </div>
        """
        net.add_node(node, label=name[:25], title=tooltip,
                     color=color, size=size, shape="dot")

    for u, v, data in G.edges(data=True):
        weight = float(data.get("weight", 1.0))
        desc = data.get("description", "")[:100]
        net.add_edge(u, v, title=desc, value=weight,
                     label=desc[:30] if desc else "")

    # pyvis 的 show() 在某些版本有模板加载bug，直接用 save_graph
    net.save_graph(output_path)
    print(f"   ✅ 已保存，在浏览器中打开: {output_path}")


def draw_interactive_plotly(G: nx.Graph, output_path: str = "./videorag-workdir/knowledge_graph.html"):
    """使用 plotly 作为 pyvis 的备选方案"""
    import plotly.graph_objects as go

    print(f"\n🌐 使用 plotly 生成交互式图 → {output_path}")

    pos = nx.spring_layout(G, seed=42, k=1.5, iterations=100, dim=3)

    # 边
    edge_x, edge_y, edge_z = [], [], []
    edge_text = []
    for u, v, data in G.edges(data=True):
        x0, y0, z0 = pos[u]
        x1, y1, z1 = pos[v]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])
        desc = data.get("description", "")[:60]
        edge_text.append(desc)

    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode="lines",
        line=dict(color="#888888", width=1),
        hoverinfo="none",
        name="Relations"
    )

    # 节点
    type_colors = {
        "ORGANIZATION": "#FF6B6B",
        "PERSON": "#4ECDC4",
        "CONCEPT": "#FFD93D",
        "LOCATION": "#6BCB77",
        "EVENT": "#9B59B6",
        "TOPIC": "#45B7D1",
    }

    node_x, node_y, node_z = [], [], []
    node_text, node_color, node_size = [], [], []
    degrees = dict(G.degree())
    max_deg = max(degrees.values()) if degrees else 1

    for node, data in G.nodes(data=True):
        x, y, z = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        name = data.get("entity_name", node)
        etype = data.get("entity_type", "").upper()
        desc = data.get("description", "")[:150]
        node_text.append(f"<b>{name}</b><br>类型: {etype}<br>{desc}")
        node_color.append(type_colors.get(etype, "#AAAAAA"))
        node_size.append(5 + 25 * (degrees[node] / max_deg))

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode="markers+text",
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=1, color="white"),
            opacity=0.9,
        ),
        text=[data.get("entity_name", n)[:12] for n, data in G.nodes(data=True)],
        textposition="top center",
        textfont=dict(size=9),
        hovertext=node_text,
        hoverinfo="text",
        name="Entities"
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        title=dict(text="VideoRAG Knowledge Graph", font=dict(size=20)),
        showlegend=False,
        scene=dict(
            xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            zaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            bgcolor="#f8f9fa",
        ),
        paper_bgcolor="white",
        margin=dict(l=0, r=0, t=40, b=0),
    )

    fig.write_html(output_path)
    print(f"   ✅ 已保存，在浏览器中打开: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="VideoRAG 知识图谱可视化")
    parser.add_argument("--input", "-i", default=GRAPHML_PATH,
                        help="输入的 graphml 文件路径")
    parser.add_argument("--output-dir", "-o", default="./videorag-workdir",
                        help="输出目录")
    parser.add_argument("--mode", "-m", choices=["static", "interactive", "both"],
                        default="both", help="可视化模式")
    args = parser.parse_args()

    G = load_graph(args.input)
    print_graph_info(G)

    if args.mode in ("static", "both"):
        png_path = os.path.join(args.output_dir, "knowledge_graph.png")
        draw_static(G, png_path)

    if args.mode in ("interactive", "both"):
        html_path = os.path.join(args.output_dir, "knowledge_graph.html")
        draw_interactive(G, html_path)

    print(f"\n✨ 完成!")


if __name__ == "__main__":
    main()
