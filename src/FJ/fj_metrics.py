import numpy as np
import networkx as nx
from typing import List
import sys
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def calculate_network_centrality_index(graph, agents):
    if len(graph.nodes()) == 0:
        return 0.0
    
    try:
        betweenness = nx.betweenness_centrality(graph)
        closeness = nx.closeness_centrality(graph)
        
        nci_values = []
        for node in graph.nodes():
            btw = betweenness.get(node, 0)
            cls = closeness.get(node, 0)
            nci = (btw + cls) / 2
            nci_values.append(nci)
        
        return np.mean(nci_values) if nci_values else 0.0
    except:
        return 0.0


def calculate_engagement_centrality_index(graph, agents):
    if len(graph.nodes()) == 0:
        return 0.0
    
    try:
        engagement_scores = []
        for agent in agents:
            user_id = agent.user_id
            if user_id in graph:
                out_degree = graph.out_degree(user_id)
                in_degree = graph.in_degree(user_id)
                total_interactions = out_degree + in_degree
                
                if len(graph.nodes()) > 1:
                    max_possible = 2 * (len(graph.nodes()) - 1)
                    engagement = total_interactions / max_possible if max_possible > 0 else 0
                    engagement_scores.append(engagement)
        
        return np.mean(engagement_scores) if engagement_scores else 0.0
    except:
        return 0.0


def calculate_global_disagreement(agents):
    if not agents:
        return 0.0
    
    stances = [agent.profile.get('stance', 0) for agent in agents]
    
    if len(stances) < 2:
        return 0.0
    
    disagreements = []
    for i in range(len(stances)):
        for j in range(i + 1, len(stances)):
            disagreement = abs(stances[i] - stances[j])
            disagreements.append(disagreement)
    
    return np.mean(disagreements) if disagreements else 0.0


def calculate_delta_polarization(initial_stances: List[float], final_stances: List[float]) -> float:
    initial_pol = np.var(initial_stances) if initial_stances else 0.0
    final_pol = np.var(final_stances) if final_stances else 0.0
    return final_pol - initial_pol


def calculate_initial_stances(num_users: int = 50) -> List[int]:
    stances = []
    num_zero = int(num_users * 0.4)
    num_others = num_users - num_zero
    
    stances.extend([0] * num_zero)
    
    num_per_stance = num_others // 4
    stances.extend([-2] * num_per_stance)
    stances.extend([-1] * num_per_stance)
    stances.extend([1] * num_per_stance)
    stances.extend([2] * (num_others - 3 * num_per_stance))
    
    return stances


def calculate_fj_metrics(network, agents, initial_stances: List[float] = None):
    if initial_stances is None:
        initial_stances = calculate_initial_stances(len(agents))
    
    final_stances = [agent.profile.get('stance', 0) for agent in agents]
    
    mean_nci = calculate_network_centrality_index(network.graph, agents)
    eci = calculate_engagement_centrality_index(network.graph, agents)
    global_dis = calculate_global_disagreement(agents)
    delta_pol = calculate_delta_polarization(initial_stances, final_stances)
    
    nci_thr = mean_nci * 0.33
    
    return {
        'NCI_thr': round(nci_thr, 4),
        'ECI': round(eci, 4),
        'DeltaPol': round(delta_pol, 4),
        'GlobalDis': round(global_dis, 4),
        'MeanNCI': round(mean_nci, 4)
    }

