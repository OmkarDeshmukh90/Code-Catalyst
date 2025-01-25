import streamlit as st
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
from statsmodels.tsa.arima.model import ARIMAResults

class PredictionSystem:
    def __init__(self):
        # Load models with custom objects
        self.arima = joblib.load('arima_model.joblib')
        self.lstm = tf.keras.models.load_model('lstm_model.h5')
        self.scaler = joblib.load('scaler.joblib')
        
    def predict_demand(self, steps):
        # ARIMA prediction
        arima_pred = self.arima.forecast(steps=steps)
        
        # LSTM prediction (using recent data pattern)
        last_seq = self._get_last_sequence()
        scaled_seq = self.scaler.transform(last_seq.reshape(-1, 3)).reshape(1, 7, 3)
        lstm_pred = self.lstm.predict(scaled_seq)
        
        return {
            'arima': arima_pred,
            'lstm': lstm_pred.flatten(),
            'combined': 0.7*arima_pred + 0.3*lstm_pred.flatten()
        }

    def _get_last_sequence(self):
        # Implement your logic to get recent historical data
        return np.random.randn(7, 3)  # Replace with actual data loading

def main():
    st.set_page_config(page_title="Food Waste Analytics", layout="wide")
    st.title("🍱 Food Waste Management System")
    
    system = PredictionSystem()
    
    with st.sidebar:
        st.header("Controls")
        prediction_days = st.slider("Forecast Days", 1, 14, 7)
    
    st.subheader("Demand Forecast")
    if st.button("Generate Predictions"):
        forecast = system.predict_demand(prediction_days)
        st.line_chart(forecast['combined'])
        st.metric("Peak Demand", f"{np.max(forecast['combined']):.0f} units")

if __name__ == "__main__":
    main()