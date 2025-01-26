import streamlit as st
import pandas as pd
from datetime import datetime

# Function to preprocess the uploaded data
def preprocess_data(df):
    # Convert Expiry_Date to datetime format
    if 'Expiry_Date' in df.columns:
        df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date'], format='%Y-%m-%d')
    
    # Handle missing values (if any)
    df.fillna({'Quantity': 0, 'Cost': 0}, inplace=True)
    
    # Calculate shelf life (days until expiry)
    if 'Expiry_Date' in df.columns:
        today = datetime.today()
        df['Shelf_Life'] = (df['Expiry_Date'] - today).dt.days
    
    # Categorize items (optional)
    if 'Category' in df.columns:
        df['Category'] = df['Category'].str.lower().str.strip()
    
    return df

# Function to generate meal recommendations
def generate_meal_recommendations(df):
    recommendations = []
    # Example: Suggest meals based on available ingredients
    for index, row in df.iterrows():
        if row['Quantity'] > 0:  # Only suggest for available items
            recommendations.append(f"Use {row['Item']} to make a delicious {row['Category']} dish.")
    return recommendations[:10]  # Limit to 10 recommendations

# Function to generate inventory optimization tips
def generate_inventory_tips(df):
    tips = []
    # Example: Suggest actions for items nearing expiry or excess stock
    for index, row in df.iterrows():
        if row['Shelf_Life'] <= 7:  # Items expiring soon
            tips.append(f"Use {row['Item']} (expires in {row['Shelf_Life']} days) in a recipe.")
        if row['Quantity'] > 50:  # Excess inventory
            tips.append(f"Consider reducing stock of {row['Item']} (current quantity: {row['Quantity']}).")
    return tips[:10]  # Limit to 10 tips

# Function to suggest meal plans
def suggest_meal_plans(df):
    meal_plans = []
    # Example: Combine multiple ingredients into a meal plan
    available_items = df[df['Quantity'] > 0]['Item'].tolist()
    if available_items:
        meal_plans.append(f"Meal Plan: Combine {', '.join(available_items[:3])} to make a hearty stew.")
        meal_plans.append(f"Meal Plan: Use {', '.join(available_items[3:5])} to prepare a fresh salad.")
    return meal_plans[:2]  # Limit to 2 meal plans

# Page title
st.title("🍽️ AI-Powered  Recommendation System For Restaurants")

# Sidebar for restaurant input
st.sidebar.header("Restaurant Details")
restaurant_name = st.sidebar.text_input("Restaurant Name")

# File upload for food-related data
st.sidebar.header("Upload Food Data")
uploaded_file = st.sidebar.file_uploader(
    "Upload your food data (CSV file)",
    type=["csv"],
    help="Upload a CSV file containing menu items, inventory, or sales data."
)

# Main content
st.header("Meal Planning and Inventory Optimization")

if uploaded_file is not None:
    # Read the uploaded file
    try:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully!")
        
        # Display the uploaded data
        st.subheader("Uploaded Data Preview")
        st.write(df.head())

        # Preprocess the data
        st.subheader("Preprocessed Data")
        df_processed = preprocess_data(df)
        st.write(df_processed.head())

        # Generate and display meal recommendations
        st.subheader("Meal Recommendations")
        meal_recommendations = generate_meal_recommendations(df_processed)
        if meal_recommendations:
            for recommendation in meal_recommendations:
                st.write(f"- {recommendation}")
        else:
            st.write("No meal recommendations at this time.")

        # Generate and display inventory optimization tips
        st.subheader("Inventory Optimization Tips ")
        inventory_tips = generate_inventory_tips(df_processed)
        if inventory_tips:
            for tip in inventory_tips:
                st.write(f"- {tip}")
        else:
            st.write("No inventory optimization tips at this time.")

        # Suggest meal plans
        st.subheader("Meal Planning Suggestions")
        meal_plans = suggest_meal_plans(df_processed)
        if meal_plans:
            for plan in meal_plans:
                st.write(f"- {plan}")
        else:
            st.write("No meal plans suggested at this time.")

    except Exception as e:
        st.error(f"Error reading or processing the file: {e}")
else:
    st.info("Please upload a CSV file to get started.")