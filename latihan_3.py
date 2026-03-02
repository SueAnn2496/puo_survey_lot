import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import json
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="Sistem Survey Lot Pro", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        password = st.text_input("Sila masukkan kata laluan:", type="password")
        if st.button("Log Masuk"):
            if password == "admin123":
                st.session_state.password_correct = True
                st.success("✅ Log Masuk Berjaya! Sila tunggu sebentar...")
                st.rerun()
            else:
                st.error("❌ Kata laluan salah.")
        return False
    return True

if check_password():
    # --- SIDEBAR ---
    st.sidebar.header("🛠️ Panel Kawalan GIS")
    
    with st.sidebar.expander("🌍 Tetapan Geo & Peta", expanded=True):
        epsg_code = st.text_input("Kod EPSG (Cth: 4390, 3168)", value="4390")
        map_zoom = st.slider("Zoom Peta", 10, 22, 19)

    with st.sidebar.expander("📏 Pelarasan Grafik"):
        poly_color = st.color_picker("Warna Sempadan", "#FFFF00") # Kuning standard ukur
        show_labels = st.checkbox("Papar No. Stesen & Data", value=True)
        show_area_centre = st.checkbox("Papar Luas di Tengah", value=True)

    # --- HEADER ---
    logo_file = "puo logo.png"
    col_h1, col_h2 = st.columns([1, 4])
    with col_h1:
        if os.path.exists(logo_file):
            st.image(logo_file, width=150)
    with col_h2:
        st.markdown("## SISTEM SURVEY LOT\n#### Politeknik Ungku Omar | Jabatan Kejuruteraan Awam")

    st.divider()

    # --- UPLOAD DATA ---
    uploaded_data = st.file_uploader("Muat naik fail CSV (Format: STN, E, N)", type="csv")

    if uploaded_data is not None:
        df = pd.read_csv(uploaded_data)
        
        if 'E' in df.columns and 'N' in df.columns:
            x, y = df['E'].values, df['N'].values
            num_stn = len(df)
            
            # Pengiraan Geometri
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            centroid_x, centroid_y = np.mean(x), np.mean(y)

            # Dashboard Ringkas
            c1, c2, c3 = st.columns(3)
            c1.metric("Bil. Stesen", num_stn)
            c2.metric("Luas (m²)", f"{area:.3f}")
            
            # --- FUNGSI EKSPORT QGIS ---
            # Mencipta GeoJSON untuk QGIS
            def to_geojson(df, epsg):
                features = []
                coords = []
                transformer = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
                for i in range(len(df)):
                    ln, lt = transformer.transform(df['E'].iloc[i], df['N'].iloc[i])
                    coords.append([ln, lt])
                coords.append(coords[0]) # Tutup poligon
                
                feature = {
                    "type": "Feature",
                    "properties": {"name": "Survey Lot", "area_m2": area},
                    "geometry": {"type": "Polygon", "coordinates": [coords]}
                }
                features.append(feature)
                return json.dumps({"type": "FeatureCollection", 
                                   "crs": {"type": "name", "properties": {"name": f"urn:ogc:def:crs:EPSG::{epsg}"}},
                                   "features": features})

            geojson_data = to_geojson(df, epsg_code)
            c3.download_button(label="📥 Eksport ke QGIS (GeoJSON)", 
                               data=geojson_data, 
                               file_name="survey_lot_qgis.geojson", 
                               mime="application/json")

            # --- MAP OVERLAY (GOOGLE SATELITE) ---
            st.write("### 🌍 Paparan Lot di Atas Satelit")
            try:
                transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
                lon_c, lat_c = transformer.transform(centroid_x, centroid_y)
                
                # Cipta Peta Folium
                m = folium.Map(location=[lat_c, lon_c], zoom_start=map_zoom, control_scale=True)
                
                # Layer Google Satelite (Overlay Utama)
                folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                    attr='Google Hybrid', name='Google Hybrid', overlay=False
                ).add_to(m)

                # Tukar semua koordinat untuk plotting
                poly_coords = []
                for k in range(num_stn):
                    ln, lt = transformer.transform(df['E'].iloc[k], df['N'].iloc[k])
                    poly_coords.append([lt, ln])
                    
                    if show_labels:
                        # Label No Stesen
                        folium.Marker(
                            location=[lt, ln],
                            icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; background: red; border-radius: 50%; width: 20px; height: 20px; text-align: center; font-size: 12px; font-weight: bold;">{df['STN'].iloc[k]}</div>""")
                        ).add_to(m)

                # Lukis Poligon
                folium.Polygon(
                    locations=poly_coords,
                    color=poly_color,
                    weight=3,
                    fill=True,
                    fill_opacity=0.2,
                    tooltip=f"Luas: {area:.2f} m²"
                ).add_to(m)

                # Label Luas di Tengah
                if show_area_centre:
                    folium.Marker(
                        location=[lat_c, lon_c],
                        icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: {poly_color}; font-weight: bold; width: 200px; font-size: 14px; text-shadow: 2px 2px black;">LUAS: {area:.3f} m²</div>""")
                    ).add_to(m)

                # Papar Peta
                st_folium(m, width=1300, height=700, returned_objects=[])
                
            except Exception as e:
                st.error(f"Sila semak Kod EPSG: {e}")

    if st.sidebar.button("Log Keluar"):
        del st.session_state.password_correct
        st.rerun()
