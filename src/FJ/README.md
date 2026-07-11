# FJ Model Metrics Calculator

This folder contains scripts for calculating Friedkin-Johnsen (FJ) model metrics from the social network simulation.

## Files

- **`fj_metrics.py`**: Core functions for calculating FJ model metrics
  - `calculate_network_centrality_index()`: Calculates Network Centrality Index (NCI)
  - `calculate_engagement_centrality_index()`: Calculates Engagement Centrality Index (ECI)
  - `calculate_global_disagreement()`: Calculates Global Disagreement
  - `calculate_delta_polarization()`: Calculates polarization change (ΔPol)
  - `calculate_initial_stances()`: Generates initial stance distribution
  - `calculate_fj_metrics()`: Main function to calculate all FJ metrics

- **`generate_fj_table.py`**: Generates CSV table with FJ metrics for all rounds
  - Output: `fj_metrics_table.csv` in the FJ folder
  - Contains: NCI_thr, ECI, DeltaPol, GlobalDis, MeanNCI for each round

- **`extract_fj_timeseries.py`**: Generates time series data for polarization analysis
  - Output: `fj_polarization_timeseries_data.csv` in the FJ folder

## Usage

### Generate FJ Metrics Table

From the `src` directory:

```bash
python FJ/generate_fj_table.py
```

This will:
1. Load network state and agent data from each round
2. Calculate FJ metrics for each round
3. Generate `fj_metrics_table.csv` in the `output/[OUTPUT_DIR]/FJ/` folder

### Generate Time Series Data

```bash
python FJ/extract_fj_timeseries.py
```

This generates polarization time series data in CSV format.

## Output Location

All output files are saved to:
```
output/[OUTPUT_DIR]/FJ/
```

## Metrics Description

- **NCI_thr**: Network Centrality Index threshold (33% of MeanNCI)
- **ECI**: Engagement Centrality Index (average interaction engagement)
- **DeltaPol**: Change in polarization (final - initial stance variance)
- **GlobalDis**: Global Disagreement (average stance difference between all user pairs)
- **MeanNCI**: Mean Network Centrality Index (average of betweenness and closeness centrality)

## Initial Stance Distribution

The initial stance distribution follows:
- 40% of users: stance = 0 (Neutral)
- 15% of users: stance = -2 (Strongly Against)
- 15% of users: stance = -1 (Against)
- 15% of users: stance = 1 (Support)
- 15% of users: stance = 2 (Strongly Support)

