"""
ML Pipeline to predict 2025 JoSAA cutoff closing ranks
Trains on 2021-2024 data and generates predictions for 2025
"""
import pandas as pd
import numpy as np
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
from xgboost import XGBRegressor
import joblib

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "JEE and NEET csv files"
OUTPUT_DIR = BASE_DIR / "backend" / "data"

# Institute name canonicalization
INSTITUTE_MAP = {
    "indian institute of technology bombay": "IIT Bombay",
    "indian institute of technology delhi": "IIT Delhi",
    "indian institute of technology madras": "IIT Madras",
    "indian institute of technology kharagpur": "IIT Kharagpur",
    "indian institute of technology roorkee": "IIT Roorkee",
    "indian institute of technology kanpur": "IIT Kanpur",
    "indian institute of technology guwahati": "IIT Guwahati",
    "indian institute of technology hyderabad": "IIT Hyderabad",
    "indian institute of technology indore": "IIT Indore",
    "indian institute of technology bhubaneswar": "IIT Bhubaneswar",
    "indian institute of technology gandhinagar": "IIT Gandhinagar",
    "indian institute of technology jodhpur": "IIT Jodhpur",
    "indian institute of technology patna": "IIT Patna",
    "indian institute of technology ropar": "IIT Ropar",
    "indian institute of technology mandi": "IIT Mandi",
    "indian institute of technology (bhu) varanasi": "IIT BHU",
    "indian institute of technology (ism) dhanbad": "IIT ISM Dhanbad",
    "indian institute of technology bhilai": "IIT Bhilai",
    "indian institute of technology goa": "IIT Goa",
    "indian institute of technology jammu": "IIT Jammu",
    "indian institute of technology dharwad": "IIT Dharwad",
    "indian institute of technology tirupati": "IIT Tirupati",
    "indian institute of technology palakkad": "IIT Palakkad",
    "national institute of technology tiruchirappalli": "NIT Trichy",
    "national institute of technology warangal": "NIT Warangal",
    "national institute of technology karnataka surathkal": "NIT Surathkal",
    "national institute of technology rourkela": "NIT Rourkela",
    "national institute of technology calicut": "NIT Calicut",
    "national institute of technology durgapur": "NIT Durgapur",
    "national institute of technology silchar": "NIT Silchar",
    "national institute of technology jamshedpur": "NIT Jamshedpur",
    "national institute of technology kurukshetra": "NIT Kurukshetra",
    "national institute of technology srinagar": "NIT Srinagar",
    "national institute of technology hamirpur": "NIT Hamirpur",
    "national institute of technology jalandhar": "NIT Jalandhar",
    "national institute of technology patna": "NIT Patna",
    "national institute of technology raipur": "NIT Raipur",
    "national institute of technology agartala": "NIT Agartala",
    "national institute of technology arunachal pradesh": "NIT Arunachal Pradesh",
    "national institute of technology delhi": "NIT Delhi",
    "national institute of technology goa": "NIT Goa",
    "national institute of technology manipur": "NIT Manipur",
    "national institute of technology meghalaya": "NIT Meghalaya",
    "national institute of technology mizoram": "NIT Mizoram",
    "national institute of technology nagaland": "NIT Nagaland",
    "national institute of technology puducherry": "NIT Puducherry",
    "national institute of technology sikkim": "NIT Sikkim",
    "national institute of technology uttarakhand": "NIT Uttarakhand",
}

# Branch name canonicalization
BRANCH_MAP = {
    "computer science and engineering": "CSE",
    "computer science & engineering": "CSE",
    "electronics and communication engineering": "ECE",
    "electronics & communication engineering": "ECE",
    "electrical engineering": "EE",
    "electrical and electronics engineering": "EEE",
    "mechanical engineering": "Mech",
    "civil engineering": "Civil",
    "chemical engineering": "Chemical",
    "engineering physics": "EP",
    "mathematics and computing": "MnC",
    "aerospace engineering": "Aerospace",
    "biotechnology": "Biotech",
    "metallurgical and materials engineering": "MME",
    "production and industrial engineering": "PIE",
    "instrumentation engineering": "Instrumentation",
    "information technology": "IT",
}


def canonicalize_institute(raw_name: str) -> str:
    """Canonicalize institute name"""
    key = raw_name.lower().strip()
    return INSTITUTE_MAP.get(key, raw_name.strip().title())


def canonicalize_branch(raw_name: str) -> str:
    """Canonicalize branch name"""
    key = raw_name.lower().strip()
    return BRANCH_MAP.get(key, raw_name.strip().title())


def extract_closing_rank(rank_str) -> int:
    """Extract closing rank from string, handling commas and 'P' prefix"""
    if pd.isna(rank_str):
        return None
    
    rank_str = str(rank_str).strip().upper()
    # Remove 'P' prefix (AIR indicator)
    rank_str = rank_str.replace('P', '').replace(',', '').strip()
    
    try:
        return int(float(rank_str))
    except (ValueError, TypeError):
        return None


def get_college_tier(institute_name: str) -> int:
    """Determine college tier from institute name"""
    name_lower = institute_name.lower()
    if "iit" in name_lower:
        return 1
    elif "nit" in name_lower:
        return 2
    elif "iiit" in name_lower:
        return 3
    elif any(x in name_lower for x in ["gfti", "government", "state"]):
        return 4
    else:
        return 5


def load_josaa_data() -> pd.DataFrame:
    """Load all JoSAA Round 6 (or highest round) data from 2021-2024"""
    print("=" * 80)
    print("STEP 1: Loading JoSAA Data")
    print("=" * 80)
    
    all_data = []
    
    # Define files to load (Round 6 for 2021-2023, Round 5 for 2024)
    files = [
        ("2021Round6.xlsx", 2021, 6),
        ("2022Round6.xlsx", 2022, 6),
        ("2023Round6.xlsx", 2023, 6),
        ("2024Round5.xlsx", 2024, 5),  # 2024 only has Round 5
    ]
    
    for filename, year, expected_round in files:
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"⚠️  Warning: {filename} not found, skipping")
            continue
        
        print(f"\nLoading {filename}...")
        df = pd.read_excel(filepath)
        
        # Normalize column names
        df.columns = df.columns.str.strip()
        
        # Filter for the expected round
        if 'Round' in df.columns:
            df = df[df['Round'] == expected_round]
        
        # Filter for OPEN category
        if 'Seat Type' in df.columns:
            df = df[df['Seat Type'].str.strip().str.upper() == 'OPEN']
        
        # Extract required columns
        required_cols = ['Institute', 'Academic Program Name', 'Seat Type', 'Gender', 'Closing Rank']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"⚠️  Warning: Missing columns {missing_cols} in {filename}, skipping")
            continue
        
        # Process each row
        for _, row in df.iterrows():
            institute_raw = str(row['Institute']).strip()
            branch_raw = str(row['Academic Program Name']).strip()
            category = str(row['Seat Type']).strip()
            gender = str(row['Gender']).strip()
            closing_rank = extract_closing_rank(row['Closing Rank'])
            
            if closing_rank is None or closing_rank <= 0:
                continue
            
            all_data.append({
                'year': year,
                'institute': canonicalize_institute(institute_raw),
                'branch': canonicalize_branch(branch_raw),
                'category': category,
                'gender': gender,
                'closing_rank': closing_rank,
            })
        
        print(f"  ✓ Loaded {len(df)} rows from {filename}")
    
    result_df = pd.DataFrame(all_data)
    print(f"\n✓ Total records loaded: {len(result_df)}")
    print(f"✓ Years: {sorted(result_df['year'].unique())}")
    print(f"✓ Unique institutes: {result_df['institute'].nunique()}")
    print(f"✓ Unique branches: {result_df['branch'].nunique()}")
    
    return result_df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create features for ML model"""
    print("\n" + "=" * 80)
    print("STEP 2: Feature Engineering")
    print("=" * 80)
    
    # Sort by combo and year
    df = df.sort_values(['institute', 'branch', 'category', 'gender', 'year'])
    
    # Create combo key
    df['combo_key'] = (
        df['institute'] + '|' + 
        df['branch'] + '|' + 
        df['category'] + '|' + 
        df['gender']
    )
    
    # Calculate lagged features
    print("\nCalculating lagged features...")
    df['closing_rank_prev1'] = df.groupby('combo_key')['closing_rank'].shift(1)
    df['closing_rank_prev2'] = df.groupby('combo_key')['closing_rank'].shift(2)
    df['rank_trend'] = df['closing_rank_prev1'] - df['closing_rank_prev2']
    
    # College tier
    df['college_tier'] = df['institute'].apply(get_college_tier)
    
    # Branch code (by average tightness)
    print("Encoding branches by historical tightness...")
    branch_tightness = df.groupby('branch')['closing_rank'].mean().sort_values()
    branch_to_code = {branch: idx for idx, branch in enumerate(branch_tightness.index)}
    df['branch_code'] = df['branch'].map(branch_to_code)
    
    # Category code
    category_map = {'OPEN': 0, 'OBC-NCL': 1, 'EWS': 2, 'SC': 3, 'ST': 4}
    df['category_code'] = df['category'].map(category_map).fillna(0)
    
    # Gender code
    gender_map = {'Gender-Neutral': 0, 'Female-Only': 1}
    df['gender_code'] = df['gender'].map(gender_map).fillna(0)
    
    # Year index
    df['year_index'] = df['year'] - 2021
    
    # Log closing rank
    df['log_closing_rank'] = np.log(df['closing_rank'])
    
    # Drop rows without at least 1 prior year
    df_features = df[df['closing_rank_prev1'].notna()].copy()
    
    print(f"\n✓ Feature engineering complete")
    print(f"✓ Records with features: {len(df_features)}")
    print(f"✓ Dropped {len(df) - len(df_features)} records without prior year data")
    
    return df_features


def train_models(df: pd.DataFrame) -> Tuple[Pipeline, XGBRegressor, Dict]:
    """Train Ridge and XGBoost models"""
    print("\n" + "=" * 80)
    print("STEP 3: Model Training")
    print("=" * 80)
    
    # Define features
    feature_cols = [
        'closing_rank_prev1', 'closing_rank_prev2', 'rank_trend',
        'college_tier', 'branch_code', 'category_code', 'gender_code',
        'year_index', 'log_closing_rank'
    ]
    
    # Split: train on 2022-2023, test on 2024
    train_df = df[df['year'].isin([2022, 2023])].copy()
    test_df = df[df['year'] == 2024].copy()
    
    print(f"\nTrain set: {len(train_df)} records (years 2022-2023)")
    print(f"Test set: {len(test_df)} records (year 2024)")
    
    # Prepare data
    X_train = train_df[feature_cols].fillna(0)
    y_train = train_df['closing_rank']
    X_test = test_df[feature_cols].fillna(0)
    y_test = test_df['closing_rank']
    
    # Train Ridge
    print("\nTraining Ridge Regression...")
    ridge_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', Ridge(alpha=10.0))
    ])
    ridge_pipeline.fit(X_train, y_train)
    ridge_pred = ridge_pipeline.predict(X_test)
    ridge_pred = np.clip(ridge_pred, 1, 200000)
    
    # Train XGBoost
    print("Training XGBoost...")
    xgb_model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        objective='reg:squarederror'
    )
    xgb_model.fit(X_train, y_train)
    xgb_pred = xgb_model.predict(X_test)
    xgb_pred = np.clip(xgb_pred, 1, 200000)
    
    # Evaluate
    print("\n" + "-" * 80)
    print("MODEL EVALUATION ON 2024 TEST SET")
    print("-" * 80)
    
    results = {}
    
    for name, predictions in [('Ridge', ridge_pred), ('XGBoost', xgb_pred)]:
        mae = mean_absolute_error(y_test, predictions)
        mape = mean_absolute_percentage_error(y_test, predictions) * 100
        within_500 = (np.abs(predictions - y_test) <= 500).mean() * 100
        within_1000 = (np.abs(predictions - y_test) <= 1000).mean() * 100
        
        results[name.lower()] = {
            'mae': float(mae),
            'mape': float(mape),
            'within_500': float(within_500),
            'within_1000': float(within_1000)
        }
        
        print(f"\n{name}:")
        print(f"  MAE: {mae:.0f} ranks")
        print(f"  MAPE: {mape:.2f}%")
        print(f"  Within 500 ranks: {within_500:.1f}%")
        print(f"  Within 1000 ranks: {within_1000:.1f}%")
    
    # Determine winner
    winner = 'xgboost' if results['xgboost']['mae'] < results['ridge']['mae'] else 'ridge'
    results['winner'] = winner
    results['test_year'] = 2024
    results['train_combos'] = len(train_df)
    results['test_combos'] = len(test_df)
    
    print(f"\n✓ Winner: {winner.upper()} (lower MAE)")
    
    # Store predictions in test_df for analysis
    test_df['ridge_pred'] = ridge_pred
    test_df['xgb_pred'] = xgb_pred
    test_df['error'] = np.abs(xgb_pred - y_test)
    
    # Show best and worst predictions
    print("\n" + "-" * 80)
    print("TOP 20 MOST ACCURATE PREDICTIONS (XGBoost)")
    print("-" * 80)
    best = test_df.nsmallest(20, 'error')[['institute', 'branch', 'closing_rank', 'xgb_pred', 'error']]
    for idx, row in best.iterrows():
        print(f"{row['institute']:30s} {row['branch']:15s} Actual: {row['closing_rank']:6.0f} Pred: {row['xgb_pred']:6.0f} Error: {row['error']:5.0f}")
    
    print("\n" + "-" * 80)
    print("TOP 20 LEAST ACCURATE PREDICTIONS (XGBoost)")
    print("-" * 80)
    worst = test_df.nlargest(20, 'error')[['institute', 'branch', 'closing_rank', 'xgb_pred', 'error']]
    for idx, row in worst.iterrows():
        print(f"{row['institute']:30s} {row['branch']:15s} Actual: {row['closing_rank']:6.0f} Pred: {row['xgb_pred']:6.0f} Error: {row['error']:5.0f}")
    
    return ridge_pipeline, xgb_model, results


def generate_2025_predictions(df: pd.DataFrame, ridge_model: Pipeline, xgb_model: XGBRegressor, winner: str) -> List[Dict]:
    """Generate 2025 predictions"""
    print("\n" + "=" * 80)
    print("STEP 4: Generating 2025 Predictions")
    print("=" * 80)
    
    # Get 2024 and 2023 data for each combo
    df_2024 = df[df['year'] == 2024].set_index('combo_key')
    df_2023 = df[df['year'] == 2023].set_index('combo_key')
    
    predictions = []
    
    feature_cols = [
        'closing_rank_prev1', 'closing_rank_prev2', 'rank_trend',
        'college_tier', 'branch_code', 'category_code', 'gender_code',
        'year_index', 'log_closing_rank'
    ]
    
    print(f"\nGenerating predictions for {len(df_2024)} combos...")
    
    for combo_key, row_2024 in df_2024.iterrows():
        # Get 2023 data if available
        closing_2023 = None
        if combo_key in df_2023.index:
            closing_2023_val = df_2023.loc[combo_key, 'closing_rank']
            # Handle Series vs scalar
            if isinstance(closing_2023_val, pd.Series):
                closing_2023 = closing_2023_val.iloc[0] if len(closing_2023_val) > 0 else None
            else:
                closing_2023 = closing_2023_val
        
        # Build features for 2025 prediction
        features = {
            'closing_rank_prev1': row_2024['closing_rank'],  # 2024 as prev1
            'closing_rank_prev2': closing_2023 if closing_2023 is not None else row_2024['closing_rank'],  # 2023 as prev2
            'rank_trend': row_2024['closing_rank'] - closing_2023 if closing_2023 is not None else 0,
            'college_tier': row_2024['college_tier'],
            'branch_code': row_2024['branch_code'],
            'category_code': row_2024['category_code'],
            'gender_code': row_2024['gender_code'],
            'year_index': 4,  # 2025 = index 4
            'log_closing_rank': np.log(row_2024['closing_rank']),
        }
        
        X_pred = pd.DataFrame([features])[feature_cols].fillna(0)
        
        # Predict with both models
        ridge_pred = ridge_model.predict(X_pred)[0]
        xgb_pred = xgb_model.predict(X_pred)[0]
        
        # Use winner model
        final_pred = xgb_pred if winner == 'xgboost' else ridge_pred
        
        # Calculate uncertainty
        uncertainty = abs(xgb_pred - ridge_pred)
        
        # Apply sanity bounds
        final_pred = np.clip(final_pred, 1, 200000)
        final_pred = int(round(final_pred))
        
        # Flag low confidence
        low_confidence = uncertainty > 0.3 * final_pred
        
        predictions.append({
            'institute': row_2024['institute'],
            'branch': row_2024['branch'],
            'category': row_2024['category'],
            'gender': row_2024['gender'],
            'predicted_closing_rank_2025': final_pred,
            'actual_closing_rank_2024': int(row_2024['closing_rank']),
            'actual_closing_rank_2023': int(closing_2023) if closing_2023 is not None else None,
            'prediction_uncertainty': int(uncertainty),
            'low_confidence': bool(low_confidence),
            'model_used': winner,
        })
    
    print(f"✓ Generated {len(predictions)} predictions for 2025")
    print(f"✓ Low confidence predictions: {sum(p['low_confidence'] for p in predictions)}")
    
    return predictions


def save_outputs(predictions: List[Dict], performance: Dict, ridge_model: Pipeline, xgb_model: XGBRegressor):
    """Save all outputs"""
    print("\n" + "=" * 80)
    print("STEP 5: Saving Outputs")
    print("=" * 80)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save predictions
    pred_file = OUTPUT_DIR / "cutoff_predictions_2025.json"
    with open(pred_file, 'w') as f:
        json.dump(predictions, f, indent=2)
    print(f"✓ Saved predictions: {pred_file}")
    
    # Save performance
    perf_file = OUTPUT_DIR / "model_performance.json"
    with open(perf_file, 'w') as f:
        json.dump(performance, f, indent=2)
    print(f"✓ Saved performance: {perf_file}")
    
    # Save models
    ridge_file = OUTPUT_DIR / "cutoff_model_ridge.pkl"
    joblib.dump(ridge_model, ridge_file)
    print(f"✓ Saved Ridge model: {ridge_file}")
    
    xgb_file = OUTPUT_DIR / "cutoff_model_xgb.pkl"
    joblib.dump(xgb_model, xgb_file)
    print(f"✓ Saved XGBoost model: {xgb_file}")


def main():
    """Main pipeline"""
    print("\n" + "=" * 80)
    print("JoSAA CUTOFF PREDICTION ML PIPELINE")
    print("=" * 80)
    
    # Load data
    df = load_josaa_data()
    
    # Engineer features
    df_features = engineer_features(df)
    
    # Train models
    ridge_model, xgb_model, performance = train_models(df_features)
    
    # Generate 2025 predictions
    predictions = generate_2025_predictions(
        df_features, 
        ridge_model, 
        xgb_model, 
        performance['winner']
    )
    
    # Save outputs
    save_outputs(predictions, performance, ridge_model, xgb_model)
    
    print("\n" + "=" * 80)
    print("✓ PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\nNext steps:")
    print(f"1. Restart FastAPI server to load predictions")
    print(f"2. Test /api/cutoff-prediction endpoint")
    print(f"3. Verify recommendations use ML predictions")


if __name__ == "__main__":
    main()
