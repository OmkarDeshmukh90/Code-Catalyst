import streamlit as st
import pandas as pd
from name import EcoSustainAPI  # Import your existing code

# Initialize the core system
eco_sustain = EcoSustainAPI()

def main():
    st.set_page_config(page_title="Food Waste Management", layout="wide")
    
    # Sidebar for data upload
    with st.sidebar:
        st.header("Upload Data")
        historical_file = st.file_uploader("Historical Sales Data", type="csv")
        temp_file = st.file_uploader("Temperature Data", type="csv")
        holiday_file = st.file_uploader("Holiday Calendar", type="csv")
        
        if st.button("Initialize System"):
            with st.spinner("Loading data..."):
                try:
                    historical_data = pd.read_csv(historical_file, parse_dates=['date'])
                    temperature_data = pd.read_csv(temp_file, parse_dates=['date'])
                    holiday_data = pd.read_csv(holiday_file, parse_dates=['holiday_date'])
                    
                    preprocessed_data = eco_sustain.demand_predictor.preprocess_data(
                        historical_data, 
                        temperature_data,
                        holiday_data
                    )
                    eco_sustain.demand_predictor.train_hybrid_model(preprocessed_data)
                    st.session_state.initialized = True
                    st.success("System initialized successfully!")
                except Exception as e:
                    st.error(f"Initialization failed: {str(e)}")

    # Main interface
    st.title("🍏 EcoSustain Food Waste Management")
    
    if 'initialized' not in st.session_state:
        st.warning("Please upload data and initialize the system using the sidebar")
        return

    # Demand Forecasting Section
    with st.expander("Demand Forecasting", expanded=True):
        if st.button("Generate Forecast"):
            future_dates = pd.date_range(start=pd.Timestamp.today(), periods=7)
            forecast = eco_sustain.demand_predictor.predict_demand(future_dates)
            st.line_chart(forecast, use_container_width=True)

    # Redistribution Planning
    with st.expander("Surplus Redistribution"):
        if st.button("Optimize Routes"):
            results = eco_sustain.process_daily_data()
            if results:
                st.dataframe(results['redistribution_routes'], use_container_width=True)

    # Waste Analytics
    with st.expander("Waste Analysis"):
        if st.button("Detect Anomalies"):
            results = eco_sustain.process_daily_data()
            if results and not results['waste_anomalies'].empty:
                st.dataframe(results['waste_anomalies'], use_container_width=True)
            else:
                st.info("No waste anomalies detected")

if __name__ == "__main__":
    main()