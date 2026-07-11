#!/usr/bin/env python3
"""从已保存的网络状态绘制中心性子图（只绘制右上角子图），并保存图片。
要求：使用 project 根目录 运行脚本，脚本会寻找 ../output/Multi-server_time_50agents 下的文件。
"""
import os
import pickle
import json
import matplotlib.pyplot as plt
import sys
# 将项目的 src 目录加入模块搜索路径，确保能导入 models 包
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from models.social_network import SocialNetwork
import networkx as nx
from matplotlib.lines import Line2D


def main(round_num=30):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    output_dir = os.path.abspath(os.path.join(base_dir, '..', 'output', 'Multi-server_time_50agents'))

    pkl_path = os.path.join(output_dir, f'network_graph_round_{round_num}.pkl')
    state_path = os.path.join(output_dir, f'network_state_round_{round_num}.json')

    if not os.path.exists(pkl_path):
        print(f"找不到 pickle 文件: {pkl_path}")
        return
    if not os.path.exists(state_path):
        print(f"找不到状态文件: {state_path}")
        return

    # 加载图与状态
    with open(pkl_path, 'rb') as f:
        graph = pickle.load(f)
    with open(state_path, 'r', encoding='utf-8') as f:
        state = json.load(f)

    # 创建 SocialNetwork 对象并注入已保存的数据（只需 graph 与 user_servers）
    sn = SocialNetwork()
    sn.graph = graph
    sn.user_servers = state.get('user_servers', {})
    # 其它字段可以留空或从 state 恢复（非必要）
    sn.posts_A = state.get('posts_A', [])
    sn.posts_B = state.get('posts_B', [])
    sn.posts_C = state.get('posts_C', [])

    # 单独绘制中心性子图（直接在此脚本中绘制，以便精确控制字体与节点大小）
    try:
        betweenness = nx.betweenness_centrality(sn.graph)
        closeness = nx.closeness_centrality(sn.graph)

        pos = nx.spring_layout(sn.graph, k=3, iterations=100)

        # 节点大小基于介数中心性，乘以 3000 并放大 2 倍（与 social_network 中一致）
        node_sizes = [max(300, betweenness[node] * 3000) * 2 for node in sn.graph.nodes()]
        closeness_values = [closeness[node] for node in sn.graph.nodes()]

        fig, ax = plt.subplots(1, 1, figsize=(12, 10))

        node_list = list(sn.graph.nodes())
        # 便于按节点查找大小与颜色值
        node_size_map = {n: s for n, s in zip(node_list, node_sizes)}
        closeness_map = {n: c for n, c in zip(node_list, closeness_values)}

        # 选择 top_k 个 hub（按介数中心性）
        top_k = 5
        hubs = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:top_k]
        hub_nodes = [n for n, _ in hubs]

        # 绘制非 hub 节点
        other_nodes = [n for n in node_list if n not in hub_nodes]
        other_sizes = [node_size_map[n] for n in other_nodes]
        other_colors = [closeness_map[n] for n in other_nodes]
        base_nodes = nx.draw_networkx_nodes(sn.graph, pos, nodelist=other_nodes, ax=ax,
                                            node_size=other_sizes,
                                            node_color=other_colors,
                                            cmap='viridis',
                                            alpha=0.8)

        # 绘制 hub 节点（更大、醒目并带黑色边框）
        hub_sizes = [node_size_map[n] * 1.5 for n in hub_nodes]
        hub_colors = [closeness_map[n] for n in hub_nodes]
        hub_nodes_collection = nx.draw_networkx_nodes(sn.graph, pos, nodelist=hub_nodes, ax=ax,
                                                      node_size=hub_sizes,
                                                      node_color=hub_colors,
                                                      cmap='viridis',
                                                      edgecolors='black',
                                                      linewidths=2.0,
                                                      alpha=1.0)

        # 绘制边（置于节点下方）
        nx.draw_networkx_edges(sn.graph, pos, ax=ax, alpha=0.3, arrows=True, arrowsize=10)

        # 标签：所有节点的标签字体 20，但对 hub 使用粗体并略作偏移以便识别
        labels = {node: str(node).replace('user_', '') for node in node_list}
        nx.draw_networkx_labels(sn.graph, pos, labels=labels, ax=ax, font_size=20)
        # 为 hub 添加加注（粗体、稍微上移）
        for hub in hub_nodes:
            x, y = pos[hub]
            ax.text(x, y + 0.02, str(hub).replace('user_', ''), fontsize=20, fontweight='bold',
                    ha='center', va='bottom', color='black')

        # 颜色条，放大标签与刻度
        cbar = plt.colorbar(base_nodes, ax=ax)
        cbar.set_label('Closeness Centrality', fontsize=20)
        cbar.ax.tick_params(labelsize=20)

        # 添加图例标注 hub
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', label=f'Top {top_k} Hubs',
                   markerfacecolor='gold', markeredgecolor='k', markersize=12),
        ]
        ax.legend(handles=legend_elements, loc='lower left', fontsize=12)

        # 不显示子图标题（用户要求）
        ax.axis('off')

        out_fname = os.path.join(output_dir, f'centrality_only_round_{round_num}.png')
        plt.tight_layout()
        plt.savefig(out_fname, dpi=300, bbox_inches='tight')
        plt.close(fig)
        print(f"已保存中心性子图到: {out_fname}")
    except Exception as e:
        print(f"绘制中心性子图出错: {e}")
        return


if __name__ == '__main__':
    main(30)


