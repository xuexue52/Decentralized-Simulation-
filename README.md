# Decentralized Social Network Simulation

A multi-agent simulation system for studying social network dynamics, information polarization, and user migration patterns in decentralized social media platforms.

## Overview

This project simulates a decentralized social network environment where AI-powered agents interact across multiple servers, make decisions based on their personality traits, and migrate between servers based on satisfaction levels. The simulation uses Large Language Models (LLMs) to generate realistic social media interactions and track how information flows and opinions evolve over time.

## Features

- **Multi-Server Architecture**: Simulates three independent servers (A, B, C) where users can migrate based on satisfaction
- **Big Five Personality Model**: Agents are generated with personality traits (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism)
- **AI-Powered Decision Making**: Uses LLMs to generate posts, comments, and interaction decisions
- **Dynamic Stance Evolution**: Tracks how user opinions change through interactions
- **Memory System**: Implements reflection and memory compression based on Generative Agents paper
- **Network Analysis**: Comprehensive social network analysis with visualization
- **Detailed Logging**: Complete CSV logging for actions, stance changes, migrations, and token usage

## Project Structure

```
src/
├── main.py                 # Main simulation entry point
├── agents/
│   └── social_agent.py    # Agent implementation with LLM integration
├── models/
│   └── social_network.py  # Social network graph and analysis
└── utils/
    ├── config.py          # Configuration settings
    ├── logger.py          # CSV logging utilities
    ├── prompts.py         # LLM prompt templates
    ├── big5_profile_generator.py  # User profile generation
    ├── log_viewer.py      # HTML log viewer
    └── token_usage_viewer.py  # Token usage analyzer
```

## Requirements

- Python 3.8+
- Required packages:
  - `networkx` - Social network graph analysis
  - `matplotlib` - Network visualization
  - `requests` - API calls
  - `numpy` - Numerical operations

## Installation

1. Clone the repository:
```bash
git clone https://github.com/xuexue52/Decentralized-Simulation-.git
cd Decentralized-Simulation-
```

2. Install dependencies:
```bash
pip install networkx matplotlib requests numpy
```

3. Configure API settings in `utils/config.py`:
   - Set your `API_KEY`
   - Configure `API_BASE_URL`
   - Adjust other parameters as needed

4. Generate user profiles:
```bash
python utils/big5_profile_generator.py
```

This will create `big5_user_profiles.json` with agent profiles.

## Usage

### Running the Simulation

```bash
python main.py
```

The simulation will:
1. Load user profiles from `big5_user_profiles.json`
2. Distribute agents evenly across three servers
3. Run multiple rounds of interactions
4. Save network state after each round
5. Generate analysis reports for key rounds

### Configuration

Key parameters in `utils/config.py`:

- `TOTAL_ROUNDS`: Number of simulation rounds (default: 30)
- `SERVERS`: List of available servers (default: ['A', 'B', 'C'])
- `MAX_MEMORY_ITEMS`: Maximum behavior memories per agent (default: 100)
- `MAX_FOLLOWING_POSTS`: Posts from followed users (default: 3)
- `MAX_SERVER_POSTS`: Posts from current server (default: 6)

### Output Files

The simulation generates:

- **Network Graphs**: `social_network_round_{N}.png` - Visual network representations
- **Analysis Reports**: `network_analysis_round_{N}.txt` - Detailed network metrics
- **CSV Logs**:
  - `logs_actions.csv` - All user actions
  - `logs_stance_changes.csv` - Stance evolution history
  - `logs_satisfaction.csv` - Server satisfaction scores
  - `logs_migrations.csv` - Server migration events
  - `logs_token_usage.csv` - API token consumption
- **Final Statistics**: `final_statistics.txt` - Overall simulation summary

## Key Concepts

### Agent Behavior

Each agent:
- Has a stance on AI (-2 to 2 scale: Strongly Oppose to Strongly Support)
- Possesses Big Five personality traits
- Maintains a memory of past interactions
- Generates reflections on behavior patterns
- Makes decisions using LLM-based reasoning

### Interaction Types

- **Post**: Create original content about AI
- **Comment**: Respond to posts
- **Retweet**: Share posts
- **Like**: Express approval
- **Follow/Unfollow**: Manage social connections
- **Silent**: Choose not to interact

### Server Migration

Agents evaluate their current server environment and migrate if satisfaction score < 6 (on a 1-10 scale).

### Memory System

- **Behavior Memory**: Records all interactions with importance scores
- **Reflections**: High-level insights generated when cumulative importance exceeds threshold
- **Memory Compression**: Recent memories prioritized, older ones summarized

## Analysis Features

The system tracks:

- **Polarization Index**: Variance in stance distribution
- **Network Centrality**: Betweenness and closeness centrality
- **Cohesion Metrics**: Same-stance vs. different-stance interaction density
- **Information Islands**: Count of disconnected clusters
- **Content Diversity**: Shannon diversity index
- **Silence Ratio**: Proportion of inactive users

## Viewing Logs

### HTML Log Viewer

```bash
python utils/log_viewer.py logs_actions.csv
```

Generates an HTML file with color-coded log entries.

### Token Usage Analysis

```bash
python utils/token_usage_viewer.py logs_token_usage.csv
```

Displays detailed token consumption statistics and cost estimates.

## State Management

The simulation supports:
- **Save State**: Network state saved after each round
- **Resume**: Continue from last saved round on restart
- **Checkpoint Recovery**: Load specific round states

## Research Applications

This simulation can be used to study:

- Information polarization in social networks
- Echo chamber formation
- User migration patterns
- Influence of personality on information consumption
- Effects of algorithmic filtering
- Network topology evolution

