import pandas as pd
import numpy as np
import tensorflow as tf
from statsmodels.tsa.arima.model import ARIMA
import joblib
from sklearn.preprocessing import StandardScaler

class ModelTrainer:
    def __init__(self):
        self.arima_model = None
        self.lstm_model = None
        self.scaler = StandardScaler()
        self.seq_length = 7

    def load_data(self):
        historical = pd.read_csv('historical_sales_large.csv', parse_dates=['date'])
        temperature = pd.read_csv('temperature_large.csv', parse_dates=['date'])
        holidays = pd.read_csv('holidays_large.csv', parse_dates=['holiday_date'])
        return historical, temperature, holidays

    def preprocess(self, historical, temperature, holidays):
        df = historical.merge(temperature, on='date', how='left')
        df['is_holiday'] = df['date'].isin(holidays['holiday_date']).astype(int)
        df['temperature'] = df['temperature'].interpolate(method='time')
        df = df.dropna(subset=['demand'])
        return df

    def train_arima(self, series):
        self.arima_model = ARIMA(series, order=(5,1,0)).fit()
        joblib.dump(self.arima_model, 'arima_model.joblib')

    def train_lstm(self, X_train, y_train):
        # Use explicit loss function
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(64, input_shape=(self.seq_length, 3)),
            tf.keras.layers.Dense(1)
        ])
        model.compile(
            optimizer='adam',
            loss=tf.keras.losses.MeanSquaredError()  # Use object instead of string
        )
        model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0)
        model.save('lstm_model.h5')
        return model

    def create_sequences(self, data):
        X, y = [], []
        for i in range(len(data)-self.seq_length):
            seq = data[['demand', 'temperature', 'is_holiday']].iloc[i:i+self.seq_length]
            X.append(seq.values)
            y.append(data['demand'].iloc[i+self.seq_length])
        return np.array(X), np.array(y)

    def run_training(self):
        historical, temperature, holidays = self.load_data()
        clean_data = self.preprocess(historical, temperature, holidays)
        
        # Train ARIMA
        self.train_arima(clean_data['demand'])
        
        # Prepare LSTM data
        X_train, y_train = self.create_sequences(clean_data)
        
        # Scale features
        X_train = self.scaler.fit_transform(
            X_train.reshape(-1, 3)
        ).reshape(X_train.shape)
        
        # Train LSTM
        self.train_lstm(X_train, y_train)
        joblib.dump(self.scaler, 'scaler.joblib')

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.run_training()
    print("Models trained and saved successfully!")