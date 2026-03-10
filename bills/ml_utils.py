import pickle
import numpy as np
import os
from django.conf import settings
import math

# Get the path to ml_models folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ML_MODELS_DIR = os.path.join(BASE_DIR, 'ml_models')

# Load models (do this once when server starts)
def load_models():
    models = {}
    try:
        # Electricity models
        with open(os.path.join(ML_MODELS_DIR, 'electricity_rf_model.pkl'), 'rb') as f:
            models['electricity_predictor'] = pickle.load(f)
        
        with open(os.path.join(ML_MODELS_DIR, 'electricity_scaler.pkl'), 'rb') as f:
            models['electricity_scaler'] = pickle.load(f)
        
        with open(os.path.join(ML_MODELS_DIR, 'electricity_anomaly_model.pkl'), 'rb') as f:
            models['electricity_anomaly'] = pickle.load(f)
        
        with open(os.path.join(ML_MODELS_DIR, 'electricity_payment_model.pkl'), 'rb') as f:
            models['electricity_payment'] = pickle.load(f)
        
        # Water models
        with open(os.path.join(ML_MODELS_DIR, 'water_best_model.pkl'), 'rb') as f:
            models['water_predictor'] = pickle.load(f)
        
        with open(os.path.join(ML_MODELS_DIR, 'water_scaler.pkl'), 'rb') as f:
            models['water_scaler'] = pickle.load(f)
        
        # Mobile models
        with open(os.path.join(ML_MODELS_DIR, 'mobile_best_model.pkl'), 'rb') as f:
            models['mobile_predictor'] = pickle.load(f)
        
        with open(os.path.join(ML_MODELS_DIR, 'mobile_scaler.pkl'), 'rb') as f:
            models['mobile_scaler'] = pickle.load(f)
        
        with open(os.path.join(ML_MODELS_DIR, 'mobile_label_encoder.pkl'), 'rb') as f:
            models['mobile_encoder'] = pickle.load(f)
        
        print("✅ All models loaded successfully!")
        return models
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return None

# Initialize models
MODELS = load_models()

def predict_electricity_bill(units_consumed, month, year):
    """Predict electricity bill"""
    if MODELS is None:
        return None
    
    try:
        # Create features
        quarter = (month - 1) // 3 + 1
        is_peak = 1 if month in [12, 1, 2, 7, 8] else 0
        month_sin = math.sin(2 * math.pi * month / 12)
        month_cos = math.cos(2 * math.pi * month / 12)
        
        features = np.array([[month, year, units_consumed, quarter, is_peak, month_sin, month_cos]])
        
        # Predict
        prediction = MODELS['electricity_predictor'].predict(features)[0]
        return round(prediction, 2)
    except Exception as e:
        print(f"Error predicting electricity: {e}")
        return None

def predict_water_bill(units_consumed, month, year):
    """Predict water bill"""
    if MODELS is None:
        return None
    
    try:
        quarter = (month - 1) // 3 + 1
        is_peak = 1 if month in [12, 1, 2, 7, 8] else 0
        month_sin = math.sin(2 * math.pi * month / 12)
        month_cos = math.cos(2 * math.pi * month / 12)
        
        features = np.array([[month, year, units_consumed, quarter, is_peak, month_sin, month_cos]])
        prediction = MODELS['water_predictor'].predict(features)[0]
        return round(prediction, 2)
    except Exception as e:
        print(f"Error predicting water: {e}")
        return None

def predict_mobile_bill(provider, month, year):
    """Predict mobile bill"""
    if MODELS is None:
        return None
    
    try:
        # Encode provider
        provider_encoded = MODELS['mobile_encoder'].transform([provider])[0]
        
        quarter = (month - 1) // 3 + 1
        is_peak = 1 if month in [12, 1, 2, 7, 8] else 0
        month_sin = math.sin(2 * math.pi * month / 12)
        month_cos = math.cos(2 * math.pi * month / 12)
        
        features = np.array([[month, year, quarter, is_peak, month_sin, month_cos, provider_encoded]])
        prediction = MODELS['mobile_predictor'].predict(features)[0]
        return round(prediction, 2)
    except Exception as e:
        print(f"Error predicting mobile: {e}")
        return None

def detect_anomaly(bill_amount, units_consumed, month):
    """Detect if bill is anomaly"""
    if MODELS is None:
        return False
    
    try:
        features = np.array([[bill_amount, units_consumed, month]])
        prediction = MODELS['electricity_anomaly'].predict(features)[0]
        return prediction == -1  # -1 means anomaly
    except Exception as e:
        print(f"Error detecting anomaly: {e}")
        return False

def predict_payment_risk(bill_amount, units_consumed, month):
    """Predict late payment risk"""
    if MODELS is None:
        return "Unknown"
    
    try:
        features = np.array([[bill_amount, units_consumed, month]])
        prediction = MODELS['electricity_payment'].predict(features)[0]
        return "High Risk" if prediction == 1 else "Low Risk"
    except Exception as e:
        print(f"Error predicting payment risk: {e}")
        return "Unknown"