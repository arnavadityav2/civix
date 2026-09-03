import os
import joblib
import pandas as pd
import xgboost as xgb
import numpy as np
from typing import Dict, Any, List, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# The exact 70-feature contract verified via the forensic audit
EXPECTED_FEATURES = [
    "total_calls", "active_days", "unique_contacts", "unique_cell_sectors", 
    "voice_calls", "sms_count", "data_sessions", "median_duration_sec", 
    "short_call_ratio", "night_call_count", "night_call_ratio", "weekend_call_ratio", 
    "calls_per_active_day", "contact_concentration", "unique_counterparties", 
    "txn_type_diversity", "total_sent_amount", "avg_txn_amount", "median_txn_amount", 
    "max_txn_amount", "min_txn_amount", "std_txn_amount", "high_value_txn_count", 
    "high_value_txn_ratio", "amount_concentration", "unique_sectors", "unique_regions", 
    "geo_spread_degrees", "lat_stddev", "lon_stddev", "location_active_days", 
    "cross_region_ratio", "active_day_delta", "calls_per_txn", "call_duration_cv", 
    "txn_amount_cv", "comm_span_days", "txn_span_days", "dual_concentration", 
    "total_network_size", "gender_MALE", "gender_OTHER",
    "occupation_Businessman", "occupation_Carpenter", "occupation_Contractor",
    "occupation_Doctor", "occupation_Driver", "occupation_Electrician",
    "occupation_Engineer", "occupation_Farmer", "occupation_Government Employee",
    "occupation_Hawker", "occupation_Housewife", "occupation_Laborer",
    "occupation_Mechanic", "occupation_Police Officer", "occupation_Shopkeeper",
    "occupation_Student", "occupation_Tailor", "occupation_Teacher",
    "occupation_Trader", "home_region_alwar", "home_region_bharatpur",
    "home_region_bikaner", "home_region_jaipur", "home_region_jodhpur",
    "home_region_kota", "home_region_pali", "home_region_sikar", "home_region_udaipur"
]

class MLService:
    _instance = None
    _model = None

    @classmethod
    def initialize(cls, model_path: str = None):
        if cls._model is not None:
            return
            
        if not model_path:
            # Resolve default path relative to this file
            base_dir = Path(__file__).resolve().parent.parent.parent
            model_path = base_dir / "models" / "phase3_backup" / "behavioral_xgboost_20260829T143327" / "model.pkl"
            
        if not os.path.exists(model_path):
            raise RuntimeError(f"XGBoost model artifact not found at {model_path}")
            
        logger.info(f"Loading ML model from {model_path}")
        model = joblib.load(model_path)
        
        # Verify model class
        if type(model).__name__ != 'XGBClassifier':
            raise RuntimeError(f"Expected XGBClassifier, got {type(model).__name__}")
            
        # Verify feature count and ordering
        features = list(model.feature_names_in_)
        if len(features) != 70:
            raise RuntimeError(f"Model has {len(features)} features, expected exactly 70.")
            
        for i, expected_feat in enumerate(EXPECTED_FEATURES):
            if features[i] != expected_feat:
                raise RuntimeError(f"Feature mismatch at index {i}. Expected {expected_feat}, got {features[i]}")
                
        cls._model = model
        logger.info("ML model successfully loaded and validated.")

    @classmethod
    def is_loaded(cls) -> bool:
        return cls._model is not None

    @classmethod
    def predict_leads(cls, candidate_features: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
        """
        Takes a dict of {candidate_id: {feature_name: value}}
        Returns ranked list of candidates with score and top contributing features.
        """
        if not cls.is_loaded():
            raise RuntimeError("ML model is not loaded.")
            
        if not candidate_features:
            return []
            
        candidates = list(candidate_features.keys())
        
        # Construct DataFrame ensuring strict column ordering
        rows = []
        for cid in candidates:
            feats = candidate_features[cid]
            row = [float(feats.get(f, 0.0)) for f in EXPECTED_FEATURES]
            rows.append(row)
            
        df = pd.DataFrame(rows, columns=EXPECTED_FEATURES)
        
        # Inference
        probs = cls._model.predict_proba(df)
        
        # We assume the positive class (anomaly/fraud/lead) is at index 1
        scores = probs[:, 1]
        
        results = []
        for idx, cid in enumerate(candidates):
            score = float(scores[idx])
            results.append({
                "candidate_id": cid,
                "score": score
            })
            
        # Rank by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Add rank
        for rank, res in enumerate(results, start=1):
            res["rank"] = rank
            
        return results

def get_ml_service():
    if not MLService.is_loaded():
        MLService.initialize()
    return MLService
