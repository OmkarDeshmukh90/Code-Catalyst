import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import json
from datetime import datetime
import pydeck as pdk
import numpy as np

MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "abhi1234",
    "database": "food_demand_db"
}

engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
)

st.markdown("""
<style>
    .stApp { background-color: #f5f5f5; }
    .stButton>button { background-color: #4CAF50; color: white; border-radius: 5px; }
    .card { padding: 20px; margin: 15px 0; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .open-status { color: #2e7d32; font-weight: bold; }
    .closed-status { color: #c62828; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def get_geolocation():
    if 'location' not in st.session_state:
        js_code = """
        <script>
        navigator.geolocation.getCurrentPosition(
            position => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                window.parent.postMessage({type: "geoLocation", lat: lat, lon: lon}, "*");
            },
            error => {
                window.parent.postMessage({type: "geoLocationError", error: error.message}, "*");
            }
        );
        </script>
        """
        st.components.v1.html(js_code, height=0)
        st.session_state.location = (19.0760, 72.8777)

def is_charity_open(operating_hours_str):
    try:
        hours = json.loads(operating_hours_str)
        now = datetime.now().time()
        current_day = datetime.now().weekday()
        
        time_slots = []
        if 'daily' in hours: time_slots.extend(hours['daily'].split(','))
        if current_day <5 and 'weekdays' in hours: time_slots.extend(hours['weekdays'].split(','))
        if current_day >=5 and 'weekends' in hours: time_slots.extend(hours['weekends'].split(','))

        for slot in time_slots:
            start_str, end_str = slot.strip().split('-')
            start = datetime.strptime(start_str.strip(), "%H:%M").time()
            end = datetime.strptime(end_str.strip(), "%H:%M").time()
            if start <= now <= end: return True
        return False
    except:
        return False

def main_app():
    user_lat, user_lon = st.session_state.location
    
    st.title("🍲 Mumbai Food Redistribution Network")
    st.markdown(f"### Your Current Location: {user_lat:.4f}, {user_lon:.4f}")
    
    food_type_mapping = {
        "Cooked Food": "cooked_food",
        "Dry Rations": "dry_rations",
        "Vegetables": "vegetables",
        "Packaged Goods": "packaged_goods"
    }

    with st.expander("⚙️ Filter Options", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_type = st.selectbox("Food Type", list(food_type_mapping.keys()))
            quantity = st.slider("Quantity (kg)", 1, 100, 10)
        with col2:
            max_distance = st.slider("Max Distance (km)", 1, 50, 15)
            show_open = st.checkbox("Show only open now", True)

    with engine.connect() as conn:
        charities = pd.read_sql(
            text("""
            SELECT *, 
                (6371 * acos(cos(radians(:lat)) * cos(radians(latitude)) 
                * cos(radians(longitude) - radians(:lon)) 
                + sin(radians(:lat)) * sin(radians(latitude)))) 
                AS distance_km 
            FROM Charities
            WHERE verification_status = 'verified'
            AND JSON_CONTAINS(accepted_categories, :food_type)
            HAVING distance_km <= :max_dist
            AND capacity_kg >= :quantity
            """),
            conn,
            params={
                'lat': user_lat,
                'lon': user_lon,
                'food_type': json.dumps([food_type_mapping[selected_type]]),
                'max_dist': max_distance,
                'quantity': quantity
            }
        )

    if not charities.empty:
        charities['status'] = charities['operating_hours'].apply(
            lambda x: "Open" if is_charity_open(x) else "Closed"
        )
        charities['capacity_pct'] = (charities['capacity_kg'] / charities['capacity_kg'].max() * 100).round(2)
        
        if show_open: charities = charities[charities['status'] == "Open"]

        user_loc_df = pd.DataFrame({'lat': [user_lat], 'lon': [user_lon], 'name': ['You']})
        
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=user_lat,
                longitude=user_lon,
                zoom=12,
                pitch=50
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=charities,
                    get_position='[longitude, latitude]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=200,
                    pickable=True
                ),
                pdk.Layer(
                    'ScatterplotLayer',
                    data=user_loc_df,
                    get_position='[lon, lat]',
                    get_color='[0, 128, 255, 200]',
                    get_radius=300
                )
            ],
            tooltip={"html": "<b>{name}</b><br>Distance: {distance_km:.2f} km<br>Status: {status}"}
        ))

        st.subheader(f"Found {len(charities)} Matching Charities")
        for _, row in charities.iterrows():
            status_class = "open-status" if row['status'] == "Open" else "closed-status"
            progress = st.progress(int(row['capacity_pct']))
            st.markdown(f"""
            <div class="card">
                <div style="display: flex; justify-content: space-between;">
                    <h3>{row['name']}</h3>
                    <span class="{status_class}">{row['status']}</span>
                </div>
                <p>📍 {row['address']}</p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        📞 {row['contact_phone']}<br>
                        📧 {row['contact_email'] or ''}
                    </div>
                    <div>
                        📏 Distance: {row['distance_km']:.2f} km<br>
                        ⚖️ Capacity: {row['capacity_kg']} kg
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            progress.empty()
    else:
        st.warning("No matching charities found. Try adjusting your filters.")

if __name__ == "__main__":
    get_geolocation()
    if 'location' in st.session_state:
        main_app()
    else:
        st.title("🍲 Mumbai Food Redistribution Network")
        st.error("Please enable location access to use this application")