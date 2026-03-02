import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import json
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Survey Lot Pro", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        password = st.text_input("Sila masukkan kata laluan:", type="password")
        if st.button("Log Masuk") or (password == "admin123" and password != ""):
            if password == "admin123":
                st.session_state.password_correct = True
                st.success("✅ Log Masuk Berjaya!")
                st.rerun()
            else:
                st.error("❌ Kata laluan salah.")
        return False
    return True

if check_password():
    # --- HEADER ---
    logo_file = "puo logo.png"
    col_h1, col_h2 = st.columns([1, 5])
    with col_h1:
        if os.path.exists(logo_file):
            st.image(logo_file, width=120)
    with col_h2:
        st.markdown("<h2 style='margin-bottom:0;'>SISTEM SURVEY LOT</h2><p style='color:gray;'>Politeknik Ungku Omar | Unit Geomatik</p>", unsafe_allow_html=True)

    st.divider()

    # --- 2. UPLOAD FAIL ---
    epsg_input = st.text_input("🌍 Masukkan Kod EPSG (Cth: 4390 untuk Cassini Perak):", value="4390")
    uploaded_data = st.file_uploader("📂 Muat naik fail CSV Koordinat (STN, E, N)", type="csv")

    if uploaded_data is not None:
        df = pd.read_csv(uploaded_data)
        
        if 'E' in df.columns and 'N' in df.columns:
            x, y = df['E'].values, df['N'].values
            num_stn = len(df)
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            centroid_x, centroid_y = np.mean(x), np.mean(y)

            # --- 3. PANEL PELARASAN (Hanya muncul selepas upload) ---
            st.sidebar.header("🎨 Pelarasan Pelan")
            poly_color = st.sidebar.color_picker("Warna Sempadan Poligon", "#FFFF00")
            line_weight = st.sidebar.slider("Ketebalan Garisan", 1, 10, 3)
            fill_opacity = st.sidebar.slider("Ketelusan Warna (Fill)", 0.0, 1.0, 0.3)
            text_size = st.sidebar.slider("Saiz Tulisan Luas", 10, 30, 16)
            map_zoom = st.sidebar.slider("Tahap Zoom Peta", 10, 22, 19)
            
            # --- 4. MAP OVERLAY (GOOGLE SATELITE SEBAGAI BASE) ---
            st.subheader("🌍 Paparan Lot di Atas Satelit")
            
            try:
                transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
                lon_c, lat_c = transformer.transform(centroid_x, centroid_y)
                
                # Cipta Peta
                m = folium.Map(location=[lat_c, lon_c], zoom_start=map_zoom, control_scale=True)
                
                # Layer Google Satelite sebagai Base
                folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                    attr='Google Hybrid', name='Google Hybrid', overlay=False
                ).add_to(m)

                # Convert koordinat poligon
                poly_coords = []
                for k in range(num_stn):
                    ln, lt = transformer.transform(df['E'].iloc[k], df['N'].iloc[k])
                    poly_coords.append([lt, ln])
                    
                    # Marker Stesen
                    folium.CircleMarker(
                        location=[lt, ln], radius=4, color="red", fill=True, fill_color="red"
                    ).add_to(m)
                    
                    # Nombor Stesen
                    folium.Marker(
                        location=[lt, ln],
                        icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; font-weight: bold; background-color: rgba(0,0,0,0.5); padding: 2px; border-radius: 3px; font-size: 10px;">{df['STN'].iloc[k]}</div>""")
                    ).add_to(m)

                # Lukis Poligon
                folium.Polygon(
                    locations=poly_coords,
                    color=poly_color,
                    weight=line_weight,
                    fill=True,
                    fill_color=poly_color,
                    fill_opacity=fill_opacity,
                ).add_to(m)

                # Label Luas di Tengah
                folium.Marker(
                    location=[lat_c, lon_c],
                    icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: {poly_color}; font-weight: bold; width: 300px; font-size: {text_size}px; text-shadow: 2px 2px 4px #000;">LUAS: {area:.3f} m²</div>""")
                ).add_to(m)

                # Papar Peta Folium
                st_folium(m, width="100%", height=600, returned_objects=[])

            except Exception as e:
                st.error(f"Ralat: Pastikan Kod EPSG betul. ({e})")

            # --- 5. EKSPORT & METRICS ---
            st.divider()
            col1, col2, col3 = st.columns([1,1,2])
            with col1:
                st.metric("Luas (m²)", f"{area:.3f}")
            with col2:
                st.metric("Bil. Stesen", num_stn)
            with col3:
                # Fungsi Eksport GeoJSON untuk QGIS
                def to_geojson(df, epsg):
                    coords = []
                    transformer_geo = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
                    for i in range(len(df)):
                        ln, lt = transformer_geo.transform(df['E'].iloc[i], df['N'].iloc[i])
                        coords.append([ln, lt])
                    coords.append(coords[0])
                    feature = {"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"area": area}, "geometry": {"type": "Polygon", "coordinates": [coords]}}]}
                    return json.dumps(feature)

                st.write("📥 **Eksport Data**")
                st.download_button("Download GeoJSON untuk QGIS", data=to_geojson(df, epsg_input), file_name="survey_qgis.geojson")

    if st.sidebar.button("Log Keluar"):
        del st.session_state.password_correct
        st.rerun()
