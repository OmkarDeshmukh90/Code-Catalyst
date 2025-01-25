import streamlit as st
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX

# Title of the Streamlit App
st.title("AI-Driven Demand Forecasting and Food Waste Management")

# File uploader for the user to upload a CSV file
uploaded_file = st.file_uploader("Upload your dataset", type=["csv"])

if uploaded_file is not None:
    # Read the uploaded CSV file
    df = pd.read_csv(uploaded_file)

    # Display the column names to help with debugging
    st.subheader("Dataset Columns")
    st.write(df.columns)

    # Check for required columns for forecasting (like 'Food Item' and 'Quantity of Food')
    if 'Food Item' in df.columns and 'Quantity of Food' in df.columns:
        # Preview the data
        st.subheader("Dataset Preview")
        st.write(df.head())

        # Check if a Date column exists for time-based forecasting
        if 'Date' not in df.columns:
            st.error("Missing 'Date' column. Please provide a time-related column for forecasting.")
        else:
            # Group data by 'Food Item' and calculate the total quantity of food
            grouped_data = df.groupby('Food Item').agg({
                'Quantity of Food': 'sum',  # Total quantity of food
                'Wastage Food Amount': 'sum',  # Total wasted food
                'Current Supply': 'sum',  # Total current supply of food
            }).reset_index()

            # Display the aggregated data
            st.subheader("Aggregated Data by Food Item")
            st.write(grouped_data)

            # Forecasting for each food item
            forecasts = []

            for food_item in grouped_data['Food Item'].unique():
                # Filter data for each food item
                item_data = df[df['Food Item'] == food_item]

                # Placeholder for now (assuming a 'Quantity of Food' column exists)
                item_data['Quantity of Food'] = item_data['Quantity of Food'].fillna(0)

                # Convert 'Date' to datetime
                item_data['Date'] = pd.to_datetime(item_data['Date'])
                item_data.set_index('Date', inplace=True)

                # Apply SARIMA model (Seasonal ARIMA)
                try:
                    model = SARIMAX(item_data['Quantity of Food'], 
                                    order=(1, 1, 1),   # ARIMA parameters
                                    seasonal_order=(1, 1, 1, 12))  # Seasonal parameters (12 for monthly data)
                    model_fit = model.fit(disp=False)

                    # Forecast for the next period (e.g., next month)
                    forecast = model_fit.forecast(steps=1)

                    # Ensure to access the forecasted value correctly, whether it's a numpy array or pandas Series
                    forecast_value = forecast[0] if isinstance(forecast, np.ndarray) else forecast.values[0]

                    # Store forecast data
                    forecasts.append({
                        'Food Item': food_item,
                        'Forecasted Demand': forecast_value,
                        'Current Supply': grouped_data[grouped_data['Food Item'] == food_item]['Current Supply'].values[0],
                        'Wastage': grouped_data[grouped_data['Food Item'] == food_item]['Wastage Food Amount'].values[0],
                    })

                except Exception as e:
                    st.warning(f"Failed to generate forecast for {food_item}: {e}")

            # Check if forecasts were generated
            if forecasts:
                forecast_df = pd.DataFrame(forecasts)

                # Decision Logic to recommend products to order or surplus
                forecast_df['Order or Surplus'] = np.where(
                    forecast_df['Forecasted Demand'] > forecast_df['Current Supply'],
                    'Order',
                    'Surplus'
                )

                # Display the results with recommendations
                st.subheader("Food Item Recommendations (Order or Surplus)")
                st.write(forecast_df[['Food Item', 'Forecasted Demand', 'Current Supply', 'Order or Surplus']])

                # Bar chart for visual representation
                st.subheader("Demand vs Supply for Each Food Item")
                
                # Plot the bar chart for Forecasted Demand vs Current Supply
                chart_data = forecast_df[['Food Item', 'Forecasted Demand', 'Current Supply']].set_index('Food Item')
                st.bar_chart(chart_data)
            else:
                st.warning("No forecasts were generated due to errors in the data.")
    else:
        st.error("The dataset must contain 'Food Item' and 'Quantity of Food' columns.")
