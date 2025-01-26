import streamlit as st
import requests
import pandas as pd

# API configuration
API_BASE_URL = "http://localhost:8000"

def main():
    st.title("🍏 Food Waste Reduction Dashboard")
    
    # Analysis Control
    with st.container():
        st.header("📊 Run Analysis")
        if st.button("🚀 Start New Analysis"):
            try:
                response = requests.post(f"{API_BASE_URL}/run-analysis")
                if response.status_code == 200:
                    st.success("✅ Analysis completed successfully!")
                else:
                    st.error(f"❌ Error: {response.json().get('detail', 'Unknown error')}")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Could not connect to analysis engine")

    # Display Results
    try:
        # Forecast Display
        forecast_response = requests.get(f"{API_BASE_URL}/forecast")
        if forecast_response.status_code == 200:
            with st.expander("📈 Sales Predictions", expanded=True):
                forecast_df = pd.DataFrame(forecast_response.json()).rename(columns={
                    "ds": "Date",
                    "yhat": "Predicted Sales",
                    "yhat_lower": "Minimum Expected",
                    "yhat_upper": "Maximum Expected"
                })
                
                # Convert Date column to datetime
                forecast_df['Date'] = pd.to_datetime(forecast_df['Date'])
                
                # Prepare chart data
                chart_data = forecast_df.set_index("Date")[
                    ["Predicted Sales", "Minimum Expected", "Maximum Expected"]
                ].apply(pd.to_numeric, errors='coerce').fillna(0)
                
                # Use numerical indices for the slider
                min_index = 0
                max_index = len(chart_data) - 1
                selected_indices = st.slider(
                    "Select Date Range",
                    min_value=min_index,
                    max_value=max_index,
                    value=(min_index, max_index)
                )
                
                # Filter data based on selected indices
                filtered_data = chart_data.iloc[selected_indices[0]:selected_indices[1] + 1]
                
                # Display chart and data
                st.line_chart(filtered_data)
                st.markdown("### 📊 Detailed Forecast Data")
                st.dataframe(forecast_df.style.format({"Predicted Sales": "{:.2f}", "Minimum Expected": "{:.2f}", "Maximum Expected": "{:.2f}"}))

        # Inventory Status Display
        status_response = requests.get(f"{API_BASE_URL}/inventory-status")
        if status_response.status_code == 200:
            with st.expander("📦 Inventory Health Check", expanded=True):
                status_df = pd.DataFrame(status_response.json()).rename(columns={
                    "item_id": "Product ID",
                    "days": "Forecast Days",
                    "status": "Status",
                    "current_stock": "Current Stock",
                    "required_stock": "Required Stock"
                })
                st.markdown("### 📦 Inventory Status")
                st.dataframe(status_df.style.applymap(lambda x: "color: green" if x == "Adequate" else "color: red", subset=["Status"]))

        # Recommendations Display
        rec_response = requests.get(f"{API_BASE_URL}/recommendations")
        if rec_response.status_code == 200:
            with st.expander("🚨 Action Required", expanded=True):
                rec_df = pd.DataFrame(rec_response.json()).rename(columns={
                    "item_id": "Product ID",
                    "days": "Days Ahead",
                    "type": "Issue Type",
                    "recommendation": "Recommended Action"
                })
                
                critical = rec_df[rec_df["Issue Type"] != "Adequate"]
                if not critical.empty:
                    st.markdown("### ⚠️ Urgent Actions Needed")
                    for _, row in critical.iterrows():
                        st.warning(f"""
                        **Product**: {row['Product ID']}  
                        **Timeframe**: {row['Days Ahead']} days  
                        **Action**: {row['Recommended Action']}
                        """)
                else:
                    st.success("🎉 All inventory levels are within safe limits")

        # Item Search
        with st.expander("🔍 Product Lookup", expanded=True):
            item_id = st.text_input("Enter Product ID:")
            if item_id:
                item_response = requests.get(f"{API_BASE_URL}/item-details/{item_id}")
                if item_response.status_code == 200:
                    item_data = item_response.json()
                    if any(item_data.values()):
                        st.markdown(f"### 🛒 Product Analysis: {item_id}")
                        
                        st.markdown("#### 📈 Sales Forecast")
                        sales_forecast_df = pd.DataFrame(item_data["forecast"]).rename(columns={
                            "ds": "Date",
                            "yhat": "Predicted Sales"
                        })
                        st.dataframe(sales_forecast_df.style.format({"Predicted Sales": "{:.2f}"}))
                        
                        st.markdown("#### 📦 Stock Status")
                        stock_status_df = pd.DataFrame(item_data["status"]).rename(columns={
                            "days": "Days Ahead",
                            "status": "Status"
                        })
                        st.dataframe(stock_status_df.style.applymap(lambda x: "color: green" if x == "Adequate" else "color: red", subset=["Status"]))
                    else:
                        st.info("ℹ️ No data available for this product")
                
    except requests.exceptions.ConnectionError:
        st.error("🔌 Connection to analysis engine lost")

if __name__ == "__main__":
    main()