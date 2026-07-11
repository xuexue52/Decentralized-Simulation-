#!/usr/bin/env python
"""快速重新生成网络图（从已保存的网络状态）"""

import sys
sys.path.append('src')

from models.social_network import SocialNetwork
from utils.logger import load_profiles

# 加载已保存的网络状态
network_state_file = '../output/Multi-server_time_50agents/network_state_round_1.json'
profiles_file = '../big5_user_profiles.json'
output_dir = '../output/Multi-server_time_50agents'

try:
    # 创建新的网络对象并加载状态
    social_network = SocialNetwork(output_dir='../output/Multi-server_time_50agents')
    if not social_network.load_network_state(1):
        raise Exception("Failed to load network state")
    
    # 加载profiles以获取agents数据
    profiles = load_profiles(profiles_file)
    
    # 创建简单的agent对象来模拟agents列表
    class SimpleAgent:
        def __init__(self, profile, user_id):
            self.user_id = f"user_{user_id}"
            self.profile = profile
    
    agents = [SimpleAgent(prof, i) for i, prof in enumerate(profiles)]
    
    # 重新生成可视化
    print("Regenerating network visualization...")
    social_network.visualize_network(round_num=1, output_dir=output_dir, agents=agents)
    print(f"Network visualization saved to: {output_dir}/social_network_round_1.png")
    
except FileNotFoundError as e:
    print(f"Error: File not found - {e}")
    print("\nPlease ensure:")
    print(f"  1. Network state file exists: {network_state_file}")
    print(f"  2. Profiles file exists: {profiles_file}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

