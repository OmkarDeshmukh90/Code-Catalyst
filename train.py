# train_models.py
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.sql.elements import quoted_name
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from joblib import dump
import warnings
warnings.filterwarnings('ignore')

# Database configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "abhi1234",
    "database": "food_demand_db"
}

engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
)

def convert_columns_to_string(df):
    """Convert all column names to strings, handling SQLAlchemy quoted_name"""
    new_columns = []
    for col in df.columns:
        if isinstance(col, quoted_name):
            new_columns.append(str(col))
        else:
            new_columns.append(str(col))
    df.columns = new_columns
    return df

def load_and_preprocess_data():
    """Load data from database and preprocess for ML models"""
    with engine.connect() as conn:
        # Load and convert production data
        production_df = pd.read_sql_table('production_data', conn)
        production_df = convert_columns_to_string(production_df)
        production_df['waste_percentage'] = production_df['waste'] / production_df['yield']
        
        # Load and convert retail data
        retail_df = pd.read_sql_table('retail_data', conn)
        retail_df = convert_columns_to_string(retail_df)
        retail_df['waste_ratio'] = retail_df['waste'] / retail_df['stock_level']
        
        # Load and convert consumption data
        consumption_df = pd.read_sql_table('consumption_data', conn)
        consumption_df = convert_columns_to_string(consumption_df)
        
    return production_df, retail_df, consumption_df

def train_production_model(production_df):
    """Train production waste prediction model"""
    production_df = convert_columns_to_string(production_df)
    
    X = production_df[['yield', 'storage_days', 'temperature']]
    X = convert_columns_to_string(X)
    y = production_df['waste_percentage']
    
    numeric_transformer = Pipeline(steps=[
        ('scaler', StandardScaler())
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, ['yield', 'storage_days', 'temperature'])
        ])

    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=150, random_state=42))
    ])

    model.fit(X, y)
    return model

def train_retail_model(retail_df):
    """Train retail anomaly detection model"""
    retail_df = convert_columns_to_string(retail_df)
    
    features = retail_df[['stock_level', 'sales', 'discounts', 'waste_ratio']]
    features = convert_columns_to_string(features)
    
    # Final verification
    print("Retail feature columns types:", [type(c) for c in features.columns])
    
    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42
    )
    model.fit(features)
    return model

def train_consumption_model(consumption_df):
    """Train consumption clustering model"""
    consumption_df = convert_columns_to_string(consumption_df)
    
    categorical_features = ['meal_type', 'storage_method']
    numeric_features = ['portion_size', 'leftovers']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ])
    
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('cluster', KMeans(n_clusters=4, random_state=42))
    ])
    
    model.fit(consumption_df)
    return model

def save_models(prod_model, retail_model, cons_model):
    """Persist trained models to disk"""
    dump(prod_model, 'production_waste_predictor.joblib')
    dump(retail_model, 'retail_anomaly_detector.joblib')
    dump(cons_model, 'consumption_clusterer.joblib')
    print("Models saved successfully")

def main():
    # Load and preprocess data
    production_df, retail_df, consumption_df = load_and_preprocess_data()
    
    # Train models
    print("Training production model...")
    prod_model = train_production_model(production_df)
    
    print("Training retail model...")
    retail_model = train_retail_model(retail_df)
    
    print("Training consumption model...")
    cons_model = train_consumption_model(consumption_df)
    
    # Save models
    save_models(prod_model, retail_model, cons_model)

if __name__ == "__main__":
    main()