import csv
import json
import os
import sys
import pickle
import numpy as np

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.config import OUTPUT_DIR, TOTAL_ROUNDS, PROFILES_FILE
from utils.logger import load_profiles
from FJ.fj_metrics import (
    calculate_network_centrality_index,
    calculate_engagement_centrality_index,
    calculate_global_disagreement,
    calculate_delta_polarization,
    calculate_initial_stances
)


def get_fj_output_dir():
    fj_dir = os.path.join(OUTPUT_DIR, "FJ")
    os.makedirs(fj_dir, exist_ok=True)
    return fj_dir


def load_round_data(round_num, output_dir):
    state_file = os.path.join(output_dir, f'network_state_round_{round_num}.json')
    graph_file = os.path.join(output_dir, f'network_graph_round_{round_num}.pkl')
    
    if not os.path.exists(state_file) or not os.path.exists(graph_file):
        return None, None
    
    try:
        from models.social_network import SocialNetwork
        
        network = SocialNetwork()
        with open(graph_file, 'rb') as f:
            network.graph = pickle.load(f)
        
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        profiles_file = os.path.join(output_dir, f'final_user_profiles_round_{round_num}.json')
        if not os.path.exists(profiles_file):
            profiles_file = PROFILES_FILE
        
        profiles = load_profiles(profiles_file)
        
        class MockAgent:
            def __init__(self, profile, user_id):
                self.profile = profile
                self.user_id = user_id
        
        agents = [MockAgent(p, p.get('name', f'user_{i}')) for i, p in enumerate(profiles)]
        
        return network, agents
    except Exception as e:
        print(f"Error loading round {round_num}: {e}")
        return None, None


def generate_fj_metrics_table(output_dir=None, output_file="fj_metrics_table.csv"):
    if output_dir is None:
        output_dir = OUTPUT_DIR
    
    if not os.path.exists(output_dir):
        print(f"Output directory not found: {output_dir}")
        return None
    
    fj_output_dir = get_fj_output_dir()
    initial_stances = calculate_initial_stances(50)
    
    header = ["NCI_thr", "ECI", "DeltaPol", "GlobalDis", "MeanNCI"]
    rows = []
    
    for round_num in range(1, TOTAL_ROUNDS + 1):
        network, agents = load_round_data(round_num, output_dir)
        
        if network is None or agents is None:
            continue
        
        try:
            final_stances = [agent.profile.get('stance', 0) for agent in agents]
            
            mean_nci = calculate_network_centrality_index(network.graph, agents)
            eci = calculate_engagement_centrality_index(network.graph, agents)
            global_dis = calculate_global_disagreement(agents)
            delta_pol = calculate_delta_polarization(initial_stances, final_stances)
            
            nci_thr = mean_nci * 0.33
            
            row = [
                round(nci_thr, 4),
                round(eci, 4),
                round(delta_pol, 4),
                round(global_dis, 4),
                round(mean_nci, 4)
            ]
            rows.append(row)
            
        except Exception as e:
            print(f"Error calculating metrics for round {round_num}: {e}")
            continue
    
    if rows:
        output_path = os.path.join(fj_output_dir, output_file)
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        
        print(f"FJ metrics table saved to: {output_path}")
        print(f"Total rows: {len(rows)}")
        
        if rows:
            avg_row = [
                round(np.mean([r[0] for r in rows]), 4),
                round(np.mean([r[1] for r in rows]), 4),
                round(np.mean([r[2] for r in rows]), 4),
                round(np.mean([r[3] for r in rows]), 4),
                round(np.mean([r[4] for r in rows]), 4)
            ]
            print("\nAverage values across all rounds:")
            print(f"NCI_thr: {avg_row[0]}")
            print(f"ECI: {avg_row[1]}")
            print(f"DeltaPol: {avg_row[2]}")
            print(f"GlobalDis: {avg_row[3]}")
            print(f"MeanNCI: {avg_row[4]}")
        
        return output_path
    else:
        print("No data found. Please run the simulation first.")
        return None


if __name__ == "__main__":
    generate_fj_metrics_table()

