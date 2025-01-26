import streamlit as st
import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key="AIzaSyCMilxFm-Wnwh_bolKdG-tLCLtk0kr2RbU")

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-pro')

# Function to generate insights and solutions using Gemini
def analyze_food_waste(data):
    try:
        # Generate insights and solutions using Gemini
        prompt = f"""
        You are a sustainability expert. Analyze the following food waste data and provide insights and solutions:
        
        Food Waste Data:
        {data}

        Insights:
        - Identify key trends and issues in the data.
        - Highlight areas where waste can be reduced.

        Solutions:
        - Provide actionable recommendations to reduce waste.
        - Suggest ways to improve sustainability.
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {e}"

# Function to extract the quantity of food waste from the input data
def extract_waste_quantity(data):
    # Example: Extract numbers followed by "kg" or "kgs"
    import re
    match = re.search(r"(\d+)\s*(kg|kgs)", data, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0  # Default to 0 if no quantity is found

# Function to display alerts in the bottom-right corner
def display_alerts(alert_message, alert_type="info"):
    # Define alert colors based on type
    alert_colors = {
        "info": "#4CAF50",  # Green for normal
        "warning": "#FFA500",  # Orange for medium
        "error": "#FF0000",  # Red for high
    }
    color = alert_colors.get(alert_type, "#4CAF50")  # Default to green

    # Custom HTML and CSS for the alert
    alert_html = f"""
    <style>
    .alert {{
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: {color};
        color: #fff;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        z-index: 1000;
        animation: slideIn 0.5s ease-in-out;
    }}
    @keyframes slideIn {{
        from {{
            transform: translateX(100%);
        }}
        to {{
            transform: translateX(0);
        }}
    }}
    </style>
    <div class="alert">
        🚨 <strong>Alert:</strong> {alert_message}
    </div>
    """
    # Display the alert using st.markdown
    st.markdown(alert_html, unsafe_allow_html=True)

# Streamlit app
def main():
    st.title("Food Waste Insights and Solutions")
    st.markdown("""
    This application provides insights and alerts on food waste trends and offers solutions to reduce waste while improving sustainability.
    """)

    # Input fields for business data
    st.header("Enter Business Data")
    business_name = st.text_input("Business Name")
    food_waste_data = st.text_area("Enter Food Waste Data (e.g., types of waste, quantities, etc.)")

    if st.button("Analyze Food Waste"):
        if business_name and food_waste_data:
            with st.spinner("Analyzing food waste data..."):
                # Extract waste quantity from the input data
                waste_quantity = extract_waste_quantity(food_waste_data)

                # Generate insights and solutions
                result = analyze_food_waste(food_waste_data)
                st.success("Analysis Complete!")
                
                # Display results
                st.header("Insights and Solutions")
                st.write(result)

                # Display alerts based on waste quantity
                if waste_quantity == 0:
                    display_alerts("No food waste detected. Great job!", "info")
                elif 0 < waste_quantity <= 10:
                    display_alerts("Food waste is within normal limits.", "info")
                elif 10 < waste_quantity <= 50:
                    display_alerts("Medium food waste detected. Consider reducing waste.", "warning")
                else:
                    display_alerts("High food waste detected! Take immediate action.", "error")
        else:
            st.warning("Please enter both business name and food waste data.")

if __name__ == "__main__":
    main()