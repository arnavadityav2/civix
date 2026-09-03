import joblib
import json

def inspect_model():
    model_path = "models/phase3_backup/behavioral_xgboost_20260829T143327/model.pkl"
    try:
        model = joblib.load(model_path)
        print(f"Model type: {type(model)}")
        if hasattr(model, 'feature_names_in_'):
            features = list(model.feature_names_in_)
            print(f"Features ({len(features)}): {features}")
            with open("model_features.json", "w") as f:
                json.dump(features, f)
        else:
            print("No feature_names_in_ attribute.")
            if hasattr(model, 'get_booster'):
                features = model.get_booster().feature_names
                print(f"Features from booster ({len(features)}): {features}")
                with open("model_features.json", "w") as f:
                    json.dump(features, f)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_model()
