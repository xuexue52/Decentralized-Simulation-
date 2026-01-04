import random
import time
import os
import json
from models.social_network import SocialNetwork
from agents.social_agent import SocialAgent
from utils.logger import (
    load_profiles, 
    set_output_directory
)
from utils.config import (
    TOTAL_ROUNDS, KEY_ROUNDS, SERVERS, PROFILES_FILE,
    OUTPUT_DIR, FINAL_STATISTICS_TXT, FINAL_PROFILES_JSON,
    NETWORK_ANALYSIS_PREFIX
)


def main():
    output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    
    set_output_directory(output_dir)
    
    network = SocialNetwork()
    profiles = load_profiles(PROFILES_FILE)
    
    latest_round = network.get_latest_saved_round()
    if latest_round is not None:
        print(f"\nFound saved state: Round {latest_round}")
        choice = input("Continue from saved state? (y/n): ").lower()
        if choice == 'y':
            if network.load_network_state(latest_round):
                start_round = latest_round + 1
                print(f"Will continue from round {start_round}")
            else:
                print("Failed to load saved state, starting from beginning")
                start_round = 1
        else:
            print("Starting from beginning")                  
            start_round = 1
    else:
        print("No saved state found, starting from beginning")
        start_round = 1
    
    agents = []
    for i, profile in enumerate(profiles):
        initial_server = SERVERS[i % 3]
        agent = SocialAgent(profile, i, network, initial_server)
        agents.append(agent)
    
    if start_round == 1:
        print("\n=== Initial Server Distribution ===")
        server_stats = {'A': 0, 'B': 0, 'C': 0}
        for agent in agents:
            server_stats[agent.get_current_server()] += 1
        for server, count in server_stats.items():
            print(f"Server {server}: {count} users")
    
    for round_num in range(start_round, TOTAL_ROUNDS + 1):
        print(f"\n{'='*20} Round {round_num} Interaction Start {'='*20}")
        
        for agent in agents:
            agent.current_round = round_num
        
        server_stats = {'A': 0, 'B': 0, 'C': 0}
        for agent in agents:
            server_stats[agent.get_current_server()] += 1
        print("\nCurrent server distribution:")
        for server, count in server_stats.items():
            print(f"Server {server}: {count} users")
        
        min_posters = 3
        max_posters = max(min_posters + 1, len(agents) // 4)
        num_posters = random.randint(min_posters, max_posters)
        
        posters = random.sample(agents, num_posters)
        print(f"\nThis round will have {num_posters} users posting (out of {len(agents)} total)")
        
        for agent in posters:
            agent.create_post()
        
        active_users = set()
        poster_ids = {agent.user_id for agent in posters}
        for agent in agents:
            before = len(network.graph.edges())
            has_posted = agent.user_id in poster_ids
            agent.interact_with_posts(round_num, has_posted)
            after = len(network.graph.edges())
            if after > before:
                active_users.add(agent.user_id)
        network.last_active_users = active_users

        print("\n=== Server Distribution After This Round ===")
        server_stats = {'A': 0, 'B': 0, 'C': 0}
        for agent in agents:
            server_stats[agent.get_current_server()] += 1
        for server, count in server_stats.items():
            print(f"Server {server}: {count} users")
        
        print("\n=== Stance Distribution After This Round ===")
        stance_counts = {-2: 0, -1: 0, 0: 0, 1: 0, 2: 0}
        stance_label = {-2: "Strongly Against", -1: "Against", 0: "Neutral", 1: "Support", 2: "Strongly Support"}
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
        
        for stance, count in stance_counts.items():
            print(f"{stance_label[stance]}({stance}): {count} users")
        
        if round_num in KEY_ROUNDS:
            print(f"\n=== Round {round_num} Analysis ===")
            
            network.visualize_network(round_num, output_dir, agents)
            
            network.analyze_network_metrics(round_num, output_dir, agents)
            
            print(f"- Round {round_num} network graph saved to '{output_dir}/social_network_round_{round_num}.png'")
            print(f"- Round {round_num} analysis results saved to '{output_dir}/network_analysis_round_{round_num}.txt'")
        
        network.save_network_state(round_num)
        
        
        time.sleep(0.5)
    
    print("\n=== Generating Final Statistics Report ===")
    
    network.save_satisfaction_history(output_dir)
    
    with open(os.path.join(output_dir, FINAL_STATISTICS_TXT), 'w', encoding='utf-8') as f:
        f.write("=== Social Network Simulation Final Statistics ===\n\n")
        
        f.write("Overall Statistics:\n")
        f.write(f"- Total Rounds: {TOTAL_ROUNDS}\n")
        f.write(f"- Total Posts: {len(network.posts_A) + len(network.posts_B) + len(network.posts_C)}\n")
        f.write(f"- Total Users: {len(agents)}\n")
        f.write(f"- Active Users: {len(network.graph.nodes)}\n")
        f.write(f"- Total Interactions: {len(network.graph.edges)}\n\n")
        
        f.write("=== Final Stance Distribution Statistics ===\n")
        stance_counts = {-2: 0, -1: 0, 0: 0, 1: 0, 2: 0}
        stance_users = {-2: [], -1: [], 0: [], 1: [], 2: []}
        stance_label = {-2: "Strongly Against", -1: "Against", 0: "Neutral", 1: "Support", 2: "Strongly Support"}
        
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
        
        for stance, count in stance_counts.items():
            f.write(f"{stance_label[stance]}({stance}): {count} users\n")
            if count > 0:
                f.write(f"  Users: {', '.join(stance_users[stance])}\n")
        f.write("\n" + "-"*50 + "\n\n")
        
        f.write("=== Stance Change History Statistics ===\n")
        total_changes = 0
        change_types = {}
        
        for agent in agents:
            if 'stance_history' in agent.profile and agent.profile['stance_history']:
                f.write(f"\n{agent.user_id} stance change history:\n")
                for change in agent.profile['stance_history']:
                    total_changes += 1
                    change_type = change['change_type']
                    if change_type not in change_types:
                        change_types[change_type] = 0
                    change_types[change_type] += 1
                    
                    f.write(f"  Round {change.get('round_info', 'unknown')}: {change['old_stance']} -> {change['new_stance']} - {change_type}\n")
                    if 'reason' in change:
                        f.write(f"    Reason: {change['reason']}\n")
                    if 'timestamp' in change:
                        f.write(f"    Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(change['timestamp']))}\n")
        
        f.write(f"\nOverall Statistics:\n")
        f.write(f"Total Stance Changes: {total_changes}\n")
        f.write(f"Change Type Distribution:\n")
        for change_type, count in change_types.items():
            f.write(f"  {change_type}: {count} times\n")
        f.write("\n" + "-"*50 + "\n\n")
        
        f.write("Key Round Statistics:\n")
        for round_num in KEY_ROUNDS:
            f.write(f"\nRound {round_num}:\n")
            analysis_file = os.path.join(output_dir, f'{NETWORK_ANALYSIS_PREFIX}{round_num}.txt')
            if os.path.exists(analysis_file):
                with open(analysis_file, 'r', encoding='utf-8') as round_file:
                    f.write(round_file.read())
            else:
                f.write(f"Warning: Round {round_num} analysis file does not exist\n")
            f.write("\n" + "-"*50 + "\n")
    
    print("\n=== Saving Final User Profiles ===")
    final_profiles = []
    for agent in agents:
        final_profiles.append(agent.profile)
    
    final_profiles_file = os.path.join(output_dir, FINAL_PROFILES_JSON)
    with open(final_profiles_file, 'w', encoding='utf-8') as f:
        json.dump(final_profiles, f, ensure_ascii=False, indent=2)
    print(f"- Final user profiles saved to '{final_profiles_file}'")
    
    print("\nSimulation completed!")
    print(f"- Final statistics report saved to '{os.path.join(output_dir, FINAL_STATISTICS_TXT)}'")

if __name__ == "__main__":
    main() 
