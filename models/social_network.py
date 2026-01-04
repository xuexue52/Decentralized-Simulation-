import networkx as nx
import matplotlib.pyplot as plt
import json
import csv
import time
import os
import pickle
from datetime import datetime
from utils.config import (
    OUTPUT_DIR,
    SATISFACTION_HISTORY_JSON,
    NETWORK_GRAPH_PREFIX,
    NETWORK_ANALYSIS_PREFIX,
    NETWORK_STATE_PREFIX
)

class SocialNetwork:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.servers = ['A', 'B', 'C']
        self.posts_A = []
        self.posts_B = []
        self.posts_C = []
        self.post_counter = 0
        self.user_likes = {}
        self.user_comments = {}
        self.user_following = {}
        self.user_servers = {}
        self.migration_reasons = []
        self.server_satisfaction_history = {}
        
        self.save_dir = OUTPUT_DIR
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
    
    def add_post(self, post, server):
        if "post_id" not in post:
            post["post_id"] = self.post_counter
        if "likes" not in post:
            post["likes"] = 0
        if "comments" not in post:
            post["comments"] = []
            
        if "author" not in post:
            print(f"Error: Post missing author information")
            return
            
        if server == 'A':
            self.posts_A.append(post)
        elif server == 'B':
            self.posts_B.append(post)
        else:
            self.posts_C.append(post)
            
        self.sort_posts_by_time(server)
        self.post_counter += 1
    
    def sort_posts_by_time(self, server):
        if server == 'A':
            self.posts_A.sort(key=lambda x: x['timestamp'])
        elif server == 'B':
            self.posts_B.sort(key=lambda x: x['timestamp'])
        else:
            self.posts_C.sort(key=lambda x: x['timestamp'])
    
    def get_server_posts(self, server):
        if server == 'A':
            return self.posts_A
        elif server == 'B':
            return self.posts_B
        else:
            return self.posts_C
    
    def get_mixed_posts_for_user(self, user_id, server, max_following_posts=3, max_server_posts=6):
        following = self.user_following.get(user_id, set())
        
        following_posts = []
        for srv in self.servers:
            server_posts = self.get_server_posts(srv)
            for post in server_posts:
                if post.get('author') in following:
                    following_posts.append(post)
        
        following_posts.sort(key=lambda x: x.get('timestamp', 0))
        recent_following_posts = following_posts[-max_following_posts:] if len(following_posts) > max_following_posts else following_posts
        
        current_server_posts = self.get_server_posts(server)
        non_following_posts = [post for post in current_server_posts if post.get('author') not in following]
        recent_server_posts = non_following_posts[-max_server_posts:] if len(non_following_posts) > max_server_posts else non_following_posts
        
        mixed_posts = recent_following_posts + recent_server_posts
        
        return mixed_posts
    
    def change_user_server(self, user_id, new_server):
        self.user_servers[user_id] = new_server
        print(f"{user_id} migrated to server {new_server}")
    
    def record_satisfaction(self, user_id, server, satisfaction_data):
        if user_id not in self.server_satisfaction_history:
            self.server_satisfaction_history[user_id] = {}
        
        if server not in self.server_satisfaction_history[user_id]:
            self.server_satisfaction_history[user_id][server] = []
        
        satisfaction_record = {
            "score": satisfaction_data.get("score", 0),
            "reason": satisfaction_data.get("reason", ""),
            "round": satisfaction_data.get("round", "")
        }
        
        self.server_satisfaction_history[user_id][server].append(satisfaction_record)
        
        try:
            from utils.logger import log_satisfaction
            log_satisfaction({
                "timestamp": datetime.now().isoformat(),
                "user": user_id,
                "server": server,
                "score": satisfaction_data.get("score", 0),
                "reason": satisfaction_data.get("reason", ""),
                "round": satisfaction_data.get("round", ""),
                "prompt": satisfaction_data.get("prompt", ""),
            })
        except Exception as e:
            print(f"Failed to record satisfaction CSV: {e}")
    
    def save_satisfaction_history(self, output_dir):
        satisfaction_file = os.path.join(output_dir, SATISFACTION_HISTORY_JSON)
        with open(satisfaction_file, 'w', encoding='utf-8') as f:
            json.dump(self.server_satisfaction_history, f, ensure_ascii=False, indent=2)
        print(f"Satisfaction history saved to: {satisfaction_file}")

    def add_user(self, user_id):
        if user_id not in self.graph:
            self.graph.add_node(user_id)
            print(f"Added user node: {user_id}")
    
    def add_interaction(self, user_id, post_id, action, content=None):
        try:
            post = next((p for p in self.posts_A if p["post_id"] == int(post_id)), None)
            if not post:
                post = next((p for p in self.posts_B if p["post_id"] == int(post_id)), None)
                if not post:
                    post = next((p for p in self.posts_C if p["post_id"] == int(post_id)), None)
                if not post:
                    print(f"Post ID not found: {post_id}")
                    return
            
            post_author = post["author"]
            if post_author == "System" or user_id == post_author:
                return
            
            print(f"Processing interaction: {user_id} -> {post_author} ({action})")
            
            if action == "like_post":
                if user_id not in self.user_likes:
                    self.user_likes[user_id] = set()
                
                if post_id in self.user_likes[user_id]:
                    print(f"User {user_id} has already liked post {post_id}")
                    return
                
                self.user_likes[user_id].add(post_id)
            
            elif action == "create_comment":
                if user_id not in self.user_comments:
                    self.user_comments[user_id] = set()
                
                if post_id in self.user_comments[user_id]:
                    print(f"User {user_id} has already commented on post {post_id}")
                    return
                
                self.user_comments[user_id].add(post_id)
            
            self.add_user(user_id)
            self.add_user(post_author)
            
            if self.graph.has_edge(user_id, post_author):
                self.graph[user_id][post_author]['weight'] += 1
                self.graph[user_id][post_author]['types'].add(action)
            else:
                self.graph.add_edge(user_id, post_author, weight=1, types={action})
            
            if action == 'like_post':
                post['likes'] += 1
            elif action == 'create_comment':
                post['comments'].append({
                    'author': user_id,
                    'content': content or 'Comment content'
                })
            
            print(f"Added/updated edge: {user_id} -> {post_author}")
            
        except Exception as e:
            print(f"Error processing interaction: {e}")
    
    def follow_user(self, follower_id, target_user_id):
        if follower_id == target_user_id:
            return False
        
        if follower_id not in self.user_following:
            self.user_following[follower_id] = set()
        
        if target_user_id not in self.user_following[follower_id]:
            self.user_following[follower_id].add(target_user_id)
            print(f"{follower_id} followed {target_user_id}")
            
            self.add_user(follower_id)
            self.add_user(target_user_id)
            if self.graph.has_edge(follower_id, target_user_id):
                self.graph[follower_id][target_user_id]['weight'] += 1
                self.graph[follower_id][target_user_id]['types'].add('follow')
            else:
                self.graph.add_edge(follower_id, target_user_id, weight=1, types={'follow'})
            
            return True
        else:
            print(f"{follower_id} is already following {target_user_id}")
            return False
    
    def unfollow_user(self, follower_id, target_user_id):
        if follower_id not in self.user_following:
            return False
        
        if target_user_id in self.user_following[follower_id]:
            self.user_following[follower_id].remove(target_user_id)
            print(f"{follower_id} unfollowed {target_user_id}")
            
            if self.graph.has_edge(follower_id, target_user_id):
                self.graph[follower_id][target_user_id]['types'].discard('follow')
                if 'follow' in self.graph[follower_id][target_user_id]['types']:
                    pass
                else:
                    remaining_types = self.graph[follower_id][target_user_id]['types']
                    if not remaining_types:
                        self.graph.remove_edge(follower_id, target_user_id)
            
            return True
        else:
            print(f"{follower_id} is not following {target_user_id}")
            return False
    
    def get_following(self, user_id):
        return self.user_following.get(user_id, set())
    
    def get_followers(self, user_id):
        followers = set()
        for follower, following_set in self.user_following.items():
            if user_id in following_set:
                followers.add(follower)
        return followers
    
    def is_following(self, follower_id, target_user_id):
        return follower_id in self.user_following and target_user_id in self.user_following[follower_id]
    
    def visualize_network(self, round_num=None, output_dir=None, agents=None):
        if len(self.graph.edges()) == 0:
            print("Warning: No interaction edges in the network!")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))
        
        active_nodes = set()
        for u, v in self.graph.edges():
            active_nodes.add(u)
            active_nodes.add(v)
        
        self._draw_server_network(ax1, round_num)
        
        self._draw_centrality_network(ax2, round_num)
        
        self._draw_interaction_network(ax3, round_num)
        
        if agents:
            self._draw_stance_network(ax4, round_num, agents)
        else:
            ax4.text(0.5, 0.5, 'No user data', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Stance Distribution Network')
        
        plt.tight_layout()
        
        filename = f'{NETWORK_GRAPH_PREFIX}{round_num}.png' if round_num else 'social_network.png'
        if output_dir:
            filename = os.path.join(output_dir, filename)
        plt.savefig(filename, format='png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self._print_network_stats(round_num, active_nodes)
    
    def _draw_server_network(self, ax, round_num):
        if len(self.graph.edges()) == 0:
            ax.text(0.5, 0.5, 'No network data', ha='center', va='center', transform=ax.transAxes)
            return
        
        pos = self._get_hierarchical_layout()
        
        server_colors = {'A': 'red', 'B': 'blue', 'C': 'green'}
        node_colors = []
        node_sizes = []
        
        for node in self.graph.nodes():
            server = self.user_servers.get(node, 'Unknown')
            if server in server_colors:
                node_colors.append(server_colors[server])
            else:
                node_colors.append('gray')
            
            out_degree = self.graph.out_degree(node)
            node_sizes.append(max(300, out_degree * 100))
        
        nx.draw_networkx_nodes(self.graph, pos, ax=ax,
                             node_color=node_colors,
                             node_size=node_sizes,
                             alpha=0.8)
        
        edges = self.graph.edges(data=True)
        edge_colors = []
        edge_widths = []
        
        for u, v, data in edges:
            if 'follow' in data['types']:
                edge_colors.append('red')
            elif 'like_post' in data['types']:
                edge_colors.append('orange')
            elif 'create_comment' in data['types']:
                edge_colors.append('blue')
            else:
                edge_colors.append('gray')
            
            edge_widths.append(max(1, data['weight'] * 2))
        
        nx.draw_networkx_edges(self.graph, pos, ax=ax,
                             edge_color=edge_colors,
                             width=edge_widths,
                             alpha=0.6,
                             arrows=True,
                             arrowsize=15)
        
        labels = {node: str(node).replace('user_', '') for node in self.graph.nodes()}
        nx.draw_networkx_labels(self.graph, pos, labels=labels, ax=ax,
                              font_size=8)
        
        ax.set_title(f'Server Distribution Network\n(Red=A, Blue=B, Green=C)')
        ax.axis('off')
    
    def _draw_centrality_network(self, ax, round_num):
        if len(self.graph.edges()) == 0:
            ax.text(0.5, 0.5, 'No network data', ha='center', va='center', transform=ax.transAxes)
            return
        
        try:
            betweenness = nx.betweenness_centrality(self.graph)
            closeness = nx.closeness_centrality(self.graph)
            
            pos = nx.spring_layout(self.graph, k=3, iterations=100)
            
            node_sizes = [max(300, betweenness[node] * 3000) * 2 for node in self.graph.nodes()]
            
            closeness_values = [closeness[node] for node in self.graph.nodes()]
            
            nodes = nx.draw_networkx_nodes(self.graph, pos, ax=ax,
                                         node_size=node_sizes,
                                         node_color=closeness_values,
                                         cmap='viridis',
                                         alpha=0.8)
            
            nx.draw_networkx_edges(self.graph, pos, ax=ax,
                                 alpha=0.3, arrows=True, arrowsize=10)
            
            labels = {node: str(node).replace('user_', '') for node in self.graph.nodes()}
            nx.draw_networkx_labels(self.graph, pos, labels=labels, ax=ax,
                                  font_size=20)
            
            cbar = plt.colorbar(nodes, ax=ax)
            cbar.set_label('Closeness Centrality', fontsize=20)
            cbar.ax.tick_params(labelsize=20)
            
            ax.axis('off')
            
        except Exception as e:
            ax.text(0.5, 0.5, f'Error calculating centrality: {e}', ha='center', va='center', transform=ax.transAxes)
    
    def _draw_interaction_network(self, ax, round_num):
        if len(self.graph.edges()) == 0:
            ax.text(0.5, 0.5, 'No network data', ha='center', va='center', transform=ax.transAxes)
            return
        
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        interaction_counts = {'follow': 0, 'like_post': 0, 'create_comment': 0}
        for u, v, data in self.graph.edges(data=True):
            for interaction_type in data['types']:
                if interaction_type in interaction_counts:
                    interaction_counts[interaction_type] += 1
        
        nx.draw_networkx_nodes(self.graph, pos, ax=ax,
                             node_color='lightblue',
                             node_size=500,
                             alpha=0.8)
        
        follow_edges = [(u, v) for u, v, data in self.graph.edges(data=True) if 'follow' in data['types']]
        like_edges = [(u, v) for u, v, data in self.graph.edges(data=True) if 'like_post' in data['types']]
        comment_edges = [(u, v) for u, v, data in self.graph.edges(data=True) if 'create_comment' in data['types']]
        
        if follow_edges:
            nx.draw_networkx_edges(self.graph, pos, ax=ax, edgelist=follow_edges,
                                 edge_color='red', width=2, alpha=0.8, arrows=True, arrowsize=15)
        if like_edges:
            nx.draw_networkx_edges(self.graph, pos, ax=ax, edgelist=like_edges,
                                 edge_color='orange', width=1.5, alpha=0.6, arrows=True, arrowsize=12)
        if comment_edges:
            nx.draw_networkx_edges(self.graph, pos, ax=ax, edgelist=comment_edges,
                                 edge_color='blue', width=1, alpha=0.4, arrows=True, arrowsize=10)
        
        labels = {node: str(node).replace('user_', '') for node in self.graph.nodes()}
        nx.draw_networkx_labels(self.graph, pos, labels=labels, ax=ax,
                              font_size=8)
        
        legend_text = f"Follow: {interaction_counts['follow']}\nLike: {interaction_counts['like_post']}\nComment: {interaction_counts['create_comment']}"
        ax.text(0.02, 0.98, legend_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax.set_title('Interaction Type Network\n(Red=Follow, Orange=Like, Blue=Comment)')
        ax.axis('off')
    
    def _draw_stance_network(self, ax, round_num, agents):
        if len(self.graph.edges()) == 0:
            ax.text(0.5, 0.5, 'No network data', ha='center', va='center', transform=ax.transAxes)
            return
        
        stance_map = {agent.user_id: agent.profile.get('stance', 0) for agent in agents}
        
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        node_colors = []
        for node in self.graph.nodes():
            stance = stance_map.get(node, 0)
            if stance < -1:
                node_colors.append('red')
            elif stance < 0:
                node_colors.append('orange')
            elif stance == 0:
                node_colors.append('gray')
            elif stance <= 1:
                node_colors.append('lightgreen')
            else:
                node_colors.append('darkgreen')
        
        nx.draw_networkx_nodes(self.graph, pos, ax=ax,
                             node_color=node_colors,
                             node_size=500,
                             alpha=0.8)
        
        nx.draw_networkx_edges(self.graph, pos, ax=ax,
                             edge_color='gray',
                             alpha=0.3,
                             arrows=True,
                             arrowsize=10)
        
        labels = {node: str(node).replace('user_', '') for node in self.graph.nodes()}
        nx.draw_networkx_labels(self.graph, pos, labels=labels, ax=ax,
                              font_size=8)
        
        legend_text = "Stance Distribution:\nRed=Strongly Against\nOrange=Against\nGray=Neutral\nLight Green=Support\nDark Green=Strongly Support"
        ax.text(0.02, 0.98, legend_text, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax.set_title('Stance Distribution Network')
        ax.axis('off')
    
    def _get_hierarchical_layout(self):
        try:
            pos = nx.spring_layout(self.graph, k=3, iterations=100)
            
            server_groups = {'A': [], 'B': [], 'C': []}
            for node in self.graph.nodes():
                server = self.user_servers.get(node, 'Unknown')
                if server in server_groups:
                    server_groups[server].append(node)
            
            for i, (server, nodes) in enumerate(server_groups.items()):
                if nodes:
                    x_coords = [pos[node][0] for node in nodes]
                    y_coords = [pos[node][1] for node in nodes]
                    center_x = sum(x_coords) / len(x_coords)
                    center_y = sum(y_coords) / len(y_coords)
                    
                    offset_x = (i - 1) * 2
                    offset_y = 0
                    
                    for node in nodes:
                        pos[node] = (pos[node][0] + offset_x, pos[node][1] + offset_y)
            
            return pos
        except:
            return nx.spring_layout(self.graph, k=2, iterations=50)
    
    def _print_network_stats(self, round_num, active_nodes):
        print(f"\n=== {'Round ' + str(round_num) + ' ' if round_num else ''}Network Statistics ===")
        print(f"Nodes: {len(active_nodes)}")
        print(f"Edges: {len(self.graph.edges())}")
        
        server_stats = {'A': 0, 'B': 0, 'C': 0}
        for user_id, server in self.user_servers.items():
            if server in server_stats:
                server_stats[server] += 1
        
        print(f"\nServer Distribution:")
        for server, count in server_stats.items():
            print(f"  Server {server}: {count} users")
        
        interaction_stats = {'follow': 0, 'like_post': 0, 'create_comment': 0}
        for u, v, data in self.graph.edges(data=True):
            for interaction_type in data['types']:
                if interaction_type in interaction_stats:
                    interaction_stats[interaction_type] += 1
        
        print(f"\nInteraction Type Statistics:")
        for interaction_type, count in interaction_stats.items():
            print(f"  {interaction_type}: {count} times")
        
        print("\nDetailed Interactions:")
        for u, v, data in self.graph.edges(data=True):
            user_u = str(u).replace('user_', '')
            user_v = str(v).replace('user_', '')
            print(f"  {user_u} -> {user_v}: {data['weight']} times ({','.join(data['types'])})")

    def compute_stance_distribution(self, agents):
        stance_counts = {-2: 0, -1: 0, 0: 0, 1: 0, 2: 0}
        stance_users = {-2: [], -1: [], 0: [], 1: [], 2: []}
        
        for agent in agents:
            stance = agent.profile.get('stance', 0)
            stance = max(-2, min(2, stance))
            if stance < -1.5:
                stance_key = -2
            elif stance < -0.5:
                stance_key = -1
            elif stance < 0.5:
                stance_key = 0
            elif stance < 1.5:
                stance_key = 1
            else:
                stance_key = 2
            stance_counts[stance_key] += 1
            stance_users[stance_key].append(agent.user_id)
        
        return stance_counts, stance_users

    def compute_polarization_index(self, agents):
        stances = [a.profile.get('stance', 0) for a in agents]
        if not stances:
            return 0, 0
        mean = sum(stances) / len(stances)
        var = sum((s - mean) ** 2 for s in stances) / len(stances)
        left = [s for s in stances if s < 0]
        right = [s for s in stances if s > 0]
        if left and right:
            left_mean = sum(left) / len(left)
            right_mean = sum(right) / len(right)
            pole_dist = abs(right_mean - left_mean)
        else:
            pole_dist = 0
        return var, pole_dist

    def compute_cohesion(self, agents):
        same, diff, total = 0, 0, 0
        for u, v, data in self.graph.edges(data=True):
            u_agent = next((a for a in agents if a.user_id == u), None)
            v_agent = next((a for a in agents if a.user_id == v), None)
            if u_agent and v_agent:
                if u_agent.profile.get('stance', 0) * v_agent.profile.get('stance', 0) > 0 or u_agent.profile.get('stance', 0) == v_agent.profile.get('stance', 0):
                    same += data['weight']
                else:
                    diff += data['weight']
                total += data['weight']
        same_density = same / total if total else 0
        diff_density = diff / total if total else 0
        return same_density, diff_density

    def compute_island_count(self, agents):
        import networkx as nx
        undirected = self.graph.to_undirected()
        stance_map = {a.user_id: a.profile.get('stance', 0) for a in agents}
        subgraph = undirected.subgraph([a.user_id for a in agents])
        clusters = list(nx.connected_components(subgraph))
        return len(clusters)

    def compute_silence_ratio(self, agents):
        if not hasattr(self, 'last_active_users'):
            return 0
        silent = [a for a in agents if a.user_id not in self.last_active_users]
        return len(silent) / len(agents) if agents else 0

    def compute_content_diversity(self):
        from collections import Counter
        import math
        all_posts = self.posts_A + self.posts_B + self.posts_C
        contents = [p['content'] for p in all_posts if 'content' in p]
        if not contents:
            return 0
        counter = Counter(contents)
        total = sum(counter.values())
        shannon = -sum((count/total) * math.log(count/total+1e-10) for count in counter.values())
        return shannon


    def analyze_stance_changes(self, agents):
        stance_changes = []
        total_changes = 0
        
        for agent in agents:
            if 'stance_history' in agent.profile and agent.profile['stance_history']:
                for change in agent.profile['stance_history']:
                    stance_changes.append({
                        'user': agent.user_id,
                        'old_stance': change['old_stance'],
                        'new_stance': change['new_stance'],
                        'change_type': change['change_type']
                    })
                    total_changes += 1
        
        stance_changes.sort(key=lambda x: x['user'])
        
        change_types = {}
        for change in stance_changes:
            change_type = change['change_type']
            if change_type not in change_types:
                change_types[change_type] = 0
            change_types[change_type] += 1
        
        return stance_changes, total_changes, change_types

    def analyze_network_metrics(self, round_num=None, output_dir=None, agents=None):
        print(f"\n=== {'Round ' + str(round_num) + ' ' if round_num else ''}Social Network Analysis Results ===")
        try:
            betweenness = nx.betweenness_centrality(self.graph)
            print("\nBetweenness Centrality (reflects user importance in information propagation):")
            for user, score in sorted(betweenness.items(), key=lambda x: x[1], reverse=True):
                print(f"{user}: {score:.4f}")
        except Exception as e:
            print(f"Error calculating betweenness centrality: {e}")
        try:
            closeness = nx.closeness_centrality(self.graph)
            print("\nCloseness Centrality (reflects average distance to other users):")
            for user, score in sorted(closeness.items(), key=lambda x: x[1], reverse=True):
                print(f"{user}: {score:.4f}")
        except Exception as e:
            print(f"Error calculating closeness centrality: {e}")
        try:
            undirected_graph = self.graph.to_undirected()
            clustering_coef = nx.average_clustering(undirected_graph)
            print(f"\nAverage Clustering Coefficient: {clustering_coef:.4f}")
        except Exception as e:
            print(f"Error calculating clustering coefficient: {e}")
        try:
            density = nx.density(self.graph)
            print(f"Network Density: {density:.4f}")
        except Exception as e:
            print(f"Error calculating network density: {e}")
        if agents is not None:
            stance_counts, stance_users = self.compute_stance_distribution(agents)
            print(f"\n=== Stance Distribution Statistics ===")
            for stance, count in stance_counts.items():
                stance_label = {-2: "Strongly Against", -1: "Against", 0: "Neutral", 1: "Support", 2: "Strongly Support"}
                print(f"{stance_label[stance]}({stance}): {count} users")
                if count > 0:
                    print(f"  Users: {', '.join(stance_users[stance])}")
            
            var, pole_dist = self.compute_polarization_index(agents)
            same_density, diff_density = self.compute_cohesion(agents)
            island_count = self.compute_island_count(agents)
            diversity = self.compute_content_diversity()
            silence_ratio = self.compute_silence_ratio(agents)
            print(f"\nPolarization Index (Stance Variance): {var:.4f}")
            print(f"Polarization Pole Mean Distance: {pole_dist:.4f}")
            print(f"Same-stance Interaction Density: {same_density:.4f}")
            print(f"Different-stance Interaction Density: {diff_density:.4f}")
            print(f"Information Island Count: {island_count}")
            print(f"Content Diversity (Shannon): {diversity:.4f}")
            print(f"Silence Ratio: {silence_ratio:.4f}")
            
            stance_changes, total_changes, change_types = self.analyze_stance_changes(agents)
            if total_changes > 0:
                print(f"\n=== Stance Change Analysis ===")
                print(f"Total Changes: {total_changes}")
                print(f"Change Type Statistics:")
                for change_type, count in change_types.items():
                    print(f"  {change_type}: {count} times")
                
                print(f"\nLast 5 Stance Changes:")
                for change in stance_changes[-5:]:
                    print(f"  {change['user']}: {change['old_stance']} → {change['new_stance']} ({change['change_type']})")
                    if 'reason' in change:
                        print(f"    Reason: {change['reason']}")
                    if 'round_info' in change:
                        print(f"    Round: {change['round_info']}")
        
        self.save_analysis_results(betweenness, closeness, clustering_coef, density, round_num, output_dir, agents)

    def save_analysis_results(self, betweenness, closeness, clustering_coef, density, round_num, output_dir=None, agents=None):
        try:
            filename = f'{NETWORK_ANALYSIS_PREFIX}{round_num}.txt'
            if output_dir:
                filename = os.path.join(output_dir, filename)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"=== Round {round_num} Social Network Analysis ===\n\n")
                server_stats = {'A': 0, 'B': 0, 'C': 0}
                for user_id, server in self.user_servers.items():
                    server_stats[server] += 1
                for server, count in server_stats.items():
                    f.write(f"Server {server}: {count} users\n")
                f.write("\n" + "-"*50 + "\n\n")
                f.write("This Round User Migration Records:\n")
                for reason in self.migration_reasons:
                    f.write(f"{reason}\n")
                f.write("\n" + "-"*50 + "\n\n")
                f.write("Post Count by Server:\n")
                f.write(f"Server A: {len(self.posts_A)} posts\n")
                f.write(f"Server B: {len(self.posts_B)} posts\n")
                f.write(f"Server C: {len(self.posts_C)} posts\n")
                f.write("\n" + "-"*50 + "\n\n")
                f.write(f"Total Posts: {len(self.posts_A) + len(self.posts_B) + len(self.posts_C)}\n")
                f.write(f"Active Users: {len(self.graph.nodes)}\n")
                f.write(f"Total Interactions: {len(self.graph.edges)}\n\n")
                f.write("Betweenness Centrality:\n")
                for user, score in sorted(betweenness.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"{user}: {score:.4f}\n")
                f.write("\nCloseness Centrality:\n")
                for user, score in sorted(closeness.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"{user}: {score:.4f}\n")
                f.write(f"\nAverage Clustering Coefficient: {clustering_coef:.4f}\n")
                f.write(f"Network Density: {density:.4f}\n")
                if agents is not None:
                    stance_counts, stance_users = self.compute_stance_distribution(agents)
                    f.write(f"\n=== Stance Distribution Statistics ===\n")
                    stance_label = {-2: "Strongly Against", -1: "Against", 0: "Neutral", 1: "Support", 2: "Strongly Support"}
                    for stance, count in stance_counts.items():
                        f.write(f"{stance_label[stance]}({stance}): {count} users\n")
                        if count > 0:
                            f.write(f"  Users: {', '.join(stance_users[stance])}\n")
                    f.write("\n" + "-"*50 + "\n\n")
                    
                    var, pole_dist = self.compute_polarization_index(agents)
                    same_density, diff_density = self.compute_cohesion(agents)
                    island_count = self.compute_island_count(agents)
                    diversity = self.compute_content_diversity()
                    silence_ratio = self.compute_silence_ratio(agents)
                    f.write(f"\nPolarization Index (Stance Variance): {var:.4f}\n")
                    f.write(f"Polarization Pole Mean Distance: {pole_dist:.4f}\n")
                    f.write(f"Same-stance Interaction Density: {same_density:.4f}\n")
                    f.write(f"Different-stance Interaction Density: {diff_density:.4f}\n")
                    f.write(f"Information Island Count: {island_count}\n")
                    f.write(f"Content Diversity (Shannon): {diversity:.4f}\n")
                    f.write(f"Silence Ratio: {silence_ratio:.4f}\n")
                    
                    stance_changes, total_changes, change_types = self.analyze_stance_changes(agents)
                    if total_changes > 0:
                        f.write(f"\n=== Stance Change Analysis ===\n")
                        f.write(f"Total Changes: {total_changes}\n")
                        f.write(f"Change Type Statistics:\n")
                        for change_type, count in change_types.items():
                            f.write(f"  {change_type}: {count} times\n")
                        
                        f.write(f"\nAll Stance Change Details:\n")
                        for change in stance_changes:
                            f.write(f"  {change['user']}: {change['old_stance']} -> {change['new_stance']} ({change['change_type']})\n")
            
            self.migration_reasons = []
            print(f"\nAnalysis results saved to {filename}")
        except Exception as e:
            print(f"Error saving analysis results: {e}")
        
    def save_network_state(self, round_num):
        try:
            state = {
                'posts_A': self.posts_A,
                'posts_B': self.posts_B,
                'posts_C': self.posts_C,
                'post_counter': self.post_counter,
                'user_likes': {k: list(v) for k, v in self.user_likes.items()},
                'user_following': {k: list(v) for k, v in self.user_following.items()},
                'user_servers': self.user_servers,
                'migration_reasons': self.migration_reasons,
                'server_satisfaction_history': self.server_satisfaction_history
            }
            
            graph_file = os.path.join(self.save_dir, f'network_graph_round_{round_num}.pkl')
            with open(graph_file, 'wb') as f:
                pickle.dump(self.graph, f)
            
            state_file = os.path.join(self.save_dir, f'{NETWORK_STATE_PREFIX}{round_num}.json')
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            print(f"Network state saved to round {round_num}")
            return True
        except Exception as e:
            print(f"Error saving network state: {e}")
            return False
    
    def load_network_state(self, round_num):
        try:
            graph_file = os.path.join(self.save_dir, f'network_graph_round_{round_num}.pkl')
            with open(graph_file, 'rb') as f:
                self.graph = pickle.load(f)
            
            state_file = os.path.join(self.save_dir, f'{NETWORK_STATE_PREFIX}{round_num}.json')
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self.posts_A = state['posts_A']
            self.posts_B = state['posts_B']
            self.posts_C = state['posts_C']
            self.post_counter = state['post_counter']
            self.user_likes = {k: set(v) for k, v in state['user_likes'].items()}
            self.user_following = {k: set(v) for k, v in state['user_following'].items()}
            self.user_servers = state['user_servers']
            self.migration_reasons = state['migration_reasons']
            self.server_satisfaction_history = state.get('server_satisfaction_history', {})
            
            print(f"Loaded network state for round {round_num}")
            return True
        except Exception as e:
            print(f"Error loading network state: {e}")
            return False
    
    def get_latest_saved_round(self):
        try:
            state_files = [f for f in os.listdir(self.save_dir) if f.startswith(NETWORK_STATE_PREFIX)]
            if not state_files:
                return None
            
            rounds = [int(f.split('_')[-1].split('.')[0]) for f in state_files]
            return max(rounds)
        except Exception as e:
            print(f"Error getting latest saved round: {e}")
            return None 
