# mlmodel.py (Enhanced Version)
import streamlit as st
import plotly.express as px
from core import WasteAnalyzer

def main():
    st.set_page_config(page_title="Food Waste Analytics", layout="wide")
    analyzer = WasteAnalyzer()

    # App Header
    st.title("🍏 Food Waste Intelligence Platform")
    st.markdown("""
    *Transform your food supply chain operations* with AI-powered waste reduction insights.
    Visualize patterns, identify opportunities, and take actionable steps to minimize waste.
    """)
    st.divider()

    # Analysis Section
    st.header("📊 Supply Chain Analytics Dashboard")
    analysis_stage = st.selectbox("*Select Analysis Stage*", 
                                ["Production", "Retail", "Consumption"],
                                help="Choose which part of the supply chain to analyze")

    if analysis_stage == "Production":
        st.subheader("🌱 Agricultural Production Analysis")
        with st.expander("How to interpret this analysis", expanded=True):
            st.markdown("""
            - *Waste Percentage*: Shows how much of your total yield becomes waste
            - *Predictions*: Forecasts future waste based on current patterns
            - *3D Visualization*: Explore relationships between yield, storage, and temperature
            """)
        
        prod_df = analyzer.predict_production_waste()
        
        # Key Metrics Row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Recorded Waste", 
                     f"{prod_df['waste'].sum():.0f} kg",
                     help="Actual waste measured in production")
        with col2:
            st.metric("Average Waste Percentage", 
                     f"{prod_df['waste_percentage'].mean()*100:.1f}%",
                     help="Percentage of yield lost as waste")
        with col3:
            st.metric("Predicted Monthly Waste", 
                     f"{prod_df['predicted_waste'].sum()/12:.0f} kg",
                     help="Forecast based on current patterns")
        
        # Visualizations
        tab1, tab2 = st.tabs(["3D Analysis", "Time Trends"])
        with tab1:
            fig = px.scatter_3d(prod_df, x='yield', y='storage_days', z='temperature',
                              color='waste_percentage', hover_data=['crop_type'],
                              title="Crop Waste Relationships")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            fig = px.line(prod_df.groupby('date')['waste'].sum().reset_index(),
                        x='date', y='waste',
                        title="Monthly Waste Trends",
                        labels={'waste': 'Total Waste (kg)', 'date': 'Month'})
            st.plotly_chart(fig, use_container_width=True)

        # Recommendations
        st.subheader("🚀 Optimization Strategies")
        rec_col1, rec_col2, rec_col3 = st.columns(3)
        with rec_col1:
            st.markdown("""
            *🌦 Smart Harvest Scheduling*
            - Predict optimal harvest times
            - Weather pattern integration
            - Yield-quality balancing
            """)
        with rec_col2:
            st.markdown("""
            *❄ Storage Optimization*
            - Dynamic temperature control
            - Humidity monitoring
            - Energy-efficient cooling
            """)
        with rec_col3:
            st.markdown("""
            *🚚 Distribution Planning*
            - Route optimization
            - Demand forecasting
            - Supplier coordination
            """)

    elif analysis_stage == "Retail":
        st.subheader("🛒 Retail Operations Analysis")
        with st.expander("Understanding Anomalies", expanded=True):
            st.markdown("""
            - *Normal Operations*: Expected waste patterns (green markers)
            - *Anomalies*: Unexpected waste spikes (red markers)
            - *Size Indicator*: Current stock levels
            """)
        
        retail_df = analyzer.detect_retail_anomalies()
        
        # Date Range Filter
        min_date = retail_df['record_date'].min().date()
        max_date = retail_df['record_date'].max().date()
        selected_dates = st.date_input("Select Date Range", 
                                      [min_date, max_date],
                                      min_value=min_date,
                                      max_value=max_date)
        
        filtered_df = retail_df[
            (retail_df['record_date'].dt.date >= selected_dates[0]) &
            (retail_df['record_date'].dt.date <= selected_dates[1])
        ]
        
        # Key Metrics
        anomalies = filtered_df[filtered_df['anomaly'] == -1]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Anomalies", len(anomalies),
                     help="Unexpected waste occurrences")
        with col2:
            st.metric("Potential Monthly Savings", 
                     f"₹{(anomalies['waste'].sum() * 50):,.0f}",
                     help="Estimated value of preventable waste")
        with col3:
            st.metric("Anomaly Rate", 
                     f"{(len(anomalies)/len(filtered_df))*100:.1f}%",
                     help="Percentage of abnormal transactions")
        
        # Visualizations
        tab1, tab2 = st.tabs(["Waste Patterns", "Top Products"])
        with tab1:
            fig = px.scatter(filtered_df, x='record_date', y='waste', 
                           color='anomaly', size='stock_level',
                           hover_data=['product', 'store_id'],
                           color_discrete_map={-1: 'red', 1: 'green'},
                           title="Daily Waste Patterns")
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            top_products = filtered_df.groupby('product')['anomaly']\
                                    .apply(lambda x: (x == -1).sum())\
                                    .sort_values(ascending=False)\
                                    .head(5).reset_index()
            fig = px.bar(top_products, x='product', y='anomaly',
                        title="Top Products with Anomalies",
                        labels={'anomaly': 'Anomaly Count'})
            st.plotly_chart(fig, use_container_width=True)

    elif analysis_stage == "Consumption":
        st.subheader("🏠 Consumer Behavior Analysis")
        with st.expander("Cluster Interpretation", expanded=True):
            st.markdown("""
            - *Cluster 0*: Small portions, minimal leftovers
            - *Cluster 1*: Large portions, frequent leftovers
            - *Cluster 2*: Balanced meals, proper storage
            - *Cluster 3*: Irregular patterns, high waste
            """)
        
        cons_df = analyzer.analyze_consumption_patterns()
        
        # Cluster Distribution
        cluster_dist = cons_df['cluster'].value_counts().reset_index()
        cluster_dist.columns = ['Cluster', 'Households']
        
        col1, col2 = st.columns([2, 3])
        with col1:
            st.markdown("### 🎯 Cluster Distribution")
            st.dataframe(cluster_dist,
                        column_config={
                            "Cluster": "Behavior Group",
                            "Households": st.column_config.NumberColumn(
                                "Families",
                                help="Number of households in each group"
                            )
                        },
                        hide_index=True)
        
        with col2:
            fig = px.pie(cluster_dist, names='Cluster', values='Households',
                        title="Household Distribution Across Clusters")
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Analysis
        st.subheader("📈 Cluster Characteristics")
        cluster_stats = cons_df.groupby('cluster').agg({
            'portion_size': 'mean',
            'leftovers': 'mean',
            'storage_method': lambda x: x.mode()[0]
        }).reset_index()
        
        st.dataframe(cluster_stats.style.format({
            'portion_size': '{:.1f} persons',
            'leftovers': '{:.2f} kg/meal'
        }), use_container_width=True)
        
        # Recommendations
        st.subheader("💡 Behavioral Interventions")
        tab1, tab2, tab3 = st.tabs(["Meal Planning", "Storage Tips", "Education"])
        with tab1:
            st.markdown("""
            *🍽 Smart Portioning*
            - AI-generated shopping lists
            - Recipe scaling suggestions
            - Leftover recipe ideas
            """)
        with tab2:
            st.markdown("""
            *🧊 Storage Optimization*
            - Smart container recommendations
            - Expiry tracking alerts
            - Preservation technique guides
            """)
        with tab3:
            st.markdown("""
            *📚 Educational Resources*
            - Interactive cooking workshops
            - Food waste tracking app
            - Community sharing programs
            """)

    # Footer
    st.divider()
    st.markdown("""
    Data updated daily • Predictions refresh hourly  
    For support contact: analytics@foodwaste.ai  
    v2.1 | © 2024 Food Waste Intelligence Platform
    """)

if __name__ == "__main__":
    main()