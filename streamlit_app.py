import streamlit as st
import pandas as pd
import h3
import requests
from shapely.geometry import Polygon, mapping
import pydeck as pdk
import numpy as np
from datetime import datetime

API_KEY = "fbc1a3e4195587859716ff9cdb486900"

@st.cache_data(ttl=900)
def fetch_firms(bbox, days, sensor):
    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{API_KEY}/{sensor}/{bbox}/{days}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error fetching data from FIRMS API: {e}")
        return pd.DataFrame()

def hex_aggregate(df, resolution=5):
    df["hex_id"] = df.apply(lambda x: h3.geo_to_h3(x.latitude, x.longitude, resolution), axis=1)
    agg = df.groupby("hex_id").agg(
        frequency=("acq_date", "count"),
        mean_brightness=("brightness", "mean"),
        lat=("latitude", "mean"),
        lon=("longitude", "mean")
    ).reset_index()
    return agg

def bivariate_color(row, freq_q, bright_q):
    if row["frequency"] >= freq_q[1]:
        if row["mean_brightness"] >= bright_q[1]:
            return [50, 0, 70]    # deep purple/black (high-high)
        else:
            return [120, 0, 180]  # purple (high freq, low bright)
    else:
        if row["mean_brightness"] >= bright_q[1]:
            return [0, 70, 255]   # blue (low freq, high bright)
        else:
            return [200, 200, 220]  # light-grey (low-low)

def hex_elevation(row, freq_q):
    return 2000 if row["frequency"] >= freq_q[1] else 400

def build_geojson(agg, resolution=5):
    """Directly build a GeoJSON FeatureCollection as dict (no geopandas)."""
    features = []
    for _, row in agg.iterrows():
        hex_boundary = h3.h3_to_geo_boundary(row["hex_id"], geo_json=True)
        poly = Polygon(hex_boundary)
        features.append({
            "type": "Feature",
            "geometry": mapping(poly),
            "properties": {
                "frequency": int(row["frequency"]),
                "mean_brightness": float(row["mean_brightness"]),
                "color": row["color"],
                "elevation": int(row["elevation"])
            }
        })
    return {"type": "FeatureCollection", "features": features}

st.set_page_config(layout="wide")
st.title("🔥 22+ Years of Forest Fire: Interactive Bivariate Hex Map (Live FIRMS, India)")

with st.sidebar:
    st.markdown("### Filters")
    days = st.slider("Past days", 1, 10, 3)
    bbox = st.text_input("Bounding Box (W,S,E,N)", value="68,8,98,37")
    sensor = st.selectbox(
        "Sensor",
        {
            "MODIS_NRT": "MODIS (Terra/Aqua)",
            "VIIRS_SNPP_NRT": "VIIRS SNPP",
            "VIIRS_NOAA20_NRT": "VIIRS NOAA-20"
        }
    )
    confidence = st.slider("Minimum Confidence (%)", 0, 100, 75, step=1)
    year = st.selectbox("Year (filter)", ["All"] + list(range(2001, datetime.now().year + 1))[::-1])
    month = st.selectbox("Month (filter)", ["All"] + [datetime(2000, i, 1).strftime('%B') for i in range(1, 13)])
    resolution = st.slider("Hex Resolution (smaller=larger hex)", 3, 7, 5, help="Lower is coarser (bigger hexes).")

df = fetch_firms(bbox, days, sensor)
if df.empty:
    st.stop()

st.caption(f"Fetched {len(df)} points from NASA FIRMS {sensor}")

# Filter by confidence, year, month
if "confidence" in df.columns and confidence > 0:
    df = df[df["confidence"] >= confidence]
df["acq_date"] = pd.to_datetime(df["acq_date"], errors='coerce')
if year != "All":
    df = df[df["acq_date"].dt.year == int(year)]
if month != "All":
    df = df[df["acq_date"].dt.strftime('%B') == month]

st.write(f"After filtering: {len(df)} points remain.")

# Download filtered data
csv = df.to_csv(index=False)
st.download_button("Download filtered CSV", csv, file_name="filtered_firms.csv", mime='text/csv')

if len(df) == 0:
    st.warning("No data available for the selected filters.")
else:
    agg = hex_aggregate(df, resolution=resolution)
    # Compute quantiles for mapping
    freq_q = np.quantile(agg["frequency"], [0.5, 0.9])
    bright_q = np.quantile(agg["mean_brightness"], [0.5, 0.9])
    agg["color"] = agg.apply(lambda r: bivariate_color(r, freq_q, bright_q), axis=1)
    agg["elevation"] = agg.apply(lambda r: hex_elevation(r, freq_q), axis=1)

    geojson = build_geojson(agg, resolution=resolution)

    layer = pdk.Layer(
        "GeoJsonLayer",
        data=geojson,
        opacity=0.8,
        stroked=False,
        filled=True,
        get_fill_color="properties.color",
        get_elevation="properties.elevation",
        extruded=True,
        pickable=True,
        auto_highlight=True,
    )
    view = pdk.ViewState(longitude=80, latitude=22, zoom=4.1, pitch=30)

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        tooltip={
            "html": "<b>Frequency:</b> {properties.frequency}<br/>"
                    "<b>Mean Intensity:</b> {properties.mean_brightness:.1f}",
            "style": {"color": "white"}
        }
    ))

    st.markdown("""
    <div style='margin-top:16px;margin-bottom:8px;'>
        <b>Bivariate Legend:</b>
    </div>
    <style>
    .legend-grid { display: grid; grid-template-columns: 50px 50px; grid-gap: 2px; }
    .legend-cell { width: 50px; height: 25px; display: flex; align-items: center; justify-content: center; color:white; font-size:12px;}
    </style>
    <div class='legend-grid'>
        <div class='legend-cell' style='background:#c8c8dc;'>Low<br>Low</div>
        <div class='legend-cell' style='background:#0046ff;'>Low<br>High</div>
        <div class='legend-cell' style='background:#7800b4;'>High<br>Low</div>
        <div class='legend-cell' style='background:#320046;'>High<br>High</div>
    </div>
    <div style='margin-top:8px;'>
        <b>X-axis:</b> Frequency → <b>Y-axis:</b> Intensity<br>
        <i>Hex height = frequency, Color = mean intensity</i>
    </div>
    """, unsafe_allow_html=True)

    st.info("""
    **How to read:**  
    - Dark large hexes = frequent, intense fires (high risk)
    - Purple = frequent, moderate intensity
    - Blue = rare, intense
    - Pale = rare, low intensity  
    """)
