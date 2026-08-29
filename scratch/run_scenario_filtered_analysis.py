import pyarrow.parquet as pq
import pandas as pd
from pathlib import Path
import json
import duckdb

def analyze():
    # 1. Check primary label integrity (V2A)
    v2a_labels_path = "D:/civix_data/synthetic/profile_v2_v2a/ground_truth/person_labels"
    v2a_labels = duckdb.query(f"SELECT scenario_class, is_positive_label, COUNT(*) as cnt FROM read_parquet('{v2a_labels_path}/*.parquet') GROUP BY scenario_class, is_positive_label").to_df()
    
    print("=== Primary Label Integrity (V2A) ===")
    print(v2a_labels.to_string())
    print("\n")

    # 2. Score analysis for V2B and V2C (filtered by scenario_class == 'false_positive')
    for d in ['v2b', 'v2c']:
        pred_file = f"D:/civix_data/models/predictions/{d}_predictions.parquet"
        labels_path = f"D:/civix_data/synthetic/profile_v2_{d}/ground_truth/person_labels"
        
        # Read predictions and labels
        query = f"""
            SELECT 
                p.person_id, 
                p.prediction_score, 
                l.scenario_class,
                l.is_positive_label,
                l.is_false_positive
            FROM read_parquet('{pred_file}') p
            JOIN read_parquet('{labels_path}/*.parquet') l ON p.person_id = l.entity_id
        """
        df = duckdb.query(query).to_df()
        
        # True Positives
        tp = df[df['is_positive_label'] == True]
        
        # Ordinary Negatives (Normal class)
        # We define ordinary negatives as scenario_class == 'normal' (excluding the buggy hard negatives)
        ordinary = df[(df['is_positive_label'] == False) & (df['scenario_class'] == 'normal')]
        
        # True Hard Negatives (scenario_class == 'false_positive')
        true_hn = df[df['scenario_class'] == 'false_positive']
        
        print(f"=== {d.upper()} True Hard Negative Analysis ===")
        print(f"Total Entities: {len(df)}")
        print(f"True Positives: {len(tp)} (Mean Score: {tp['prediction_score'].mean():.4f})")
        print(f"Ordinary Negatives (Normal): {len(ordinary)} (Mean Score: {ordinary['prediction_score'].mean():.4f})")
        print(f"True Hard Negatives (scenario_class='false_positive'): {len(true_hn)} (Mean Score: {true_hn['prediction_score'].mean():.4f})")
        
        # Top-K Penetration
        df_sorted = df.sort_values(by='prediction_score', ascending=False).reset_index(drop=True)
        top_1_pct_budget = int(0.01 * len(df))
        top_5_pct_budget = int(0.05 * len(df))
        
        top_1_df = df_sorted.head(top_1_pct_budget)
        top_5_df = df_sorted.head(top_5_pct_budget)
        
        hn_in_top_1 = len(top_1_df[top_1_df['scenario_class'] == 'false_positive'])
        hn_in_top_5 = len(top_5_df[top_5_df['scenario_class'] == 'false_positive'])
        
        # Max rank of a true hard negative
        true_hn_indices = df_sorted.index[df_sorted['scenario_class'] == 'false_positive'].tolist()
        max_rank = true_hn_indices[0] + 1 if true_hn_indices else -1
        
        print(f"Top 1% Penetration (Budget={top_1_pct_budget}): {hn_in_top_1}")
        print(f"Top 5% Penetration (Budget={top_5_pct_budget}): {hn_in_top_5}")
        print(f"Highest Rank of a True Hard Negative: {max_rank}")
        print("\n")

if __name__ == "__main__":
    analyze()
