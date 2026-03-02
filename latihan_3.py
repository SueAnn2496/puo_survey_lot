import streamlit as st
import pandas as pd
import numpy as np
import math
import os
import json
from pyproj import Transformer
import folium
from streamlit_folium import st_folium
from folium.plugins import MiniMap, Fullscreen

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Survey Lot Pro", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        password = st.text_input("Sila masukkan kata laluan:", type="password")
        if st.button("Log Masuk"):
            if password == "admin123":
                st.session_state.password_correct = True
                st.success("✅ Login Successful!")
                st.rerun()
            else:
                st.error("❌ Wrong Password!")
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

    # --- 2. INPUT EPSG & FAIL ---
    st.markdown("### 🗺️ Konfigurasi Data")
    col_main1, col_main2 = st.columns([1, 2])
    
    with col_main1:
        epsg_input = st.text_input("🌍 Masukkan Kod EPSG:", value="4390", help="Contoh: 4390 (Perak), 3167 (Selangor)")
        
    with col_main2:
        uploaded_data = st.file_uploader("📂 Muat naik fail CSV Koordinat (STN, E, N)", type="csv")

    if uploaded_data is not None:
        df = pd.read_csv(uploaded_data)
        
        if 'E' in df.columns and 'N' in df.columns:
            # Data Processing
            x, y = df['E'].values, df['N'].values
            num_stn = len(df)
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            centroid_x, centroid_y = np.mean(x), np.mean(y)

            # --- 3. PANEL PELARASAN (SIDEBAR) ---
            st.sidebar.header("🎨 Pelarasan Visual")
            poly_color = st.sidebar.color_picker("Warna Sempadan", "#FFFF00")
            
            st.sidebar.subheader("👁️ Kawalan Paparan")
            show_stn = st.sidebar.checkbox("Papar No. Stesen", value=True)
            show_bearing = st.sidebar.checkbox("Papar Bearing & Jarak", value=True)
            show_area_label = st.sidebar.checkbox("Papar Luas (Tengah)", value=True)
            
            st.sidebar.subheader("📐 Saiz & Zoom")
            line_weight = st.sidebar.slider("Ketebalan Garisan", 1, 10, 3)
            fill_opacity = st.sidebar.slider("Ketelusan (Fill)", 0.0, 1.0, 0.3)
            text_size = st.sidebar.slider("Saiz Tulisan Data", 10, 40, 14)
            map_zoom = st.sidebar.slider("Tahap Zoom Peta", 1, 30, 19)
            
            # --- 4. MAP OVERLAY ---
            st.subheader("🌍 Paparan Lot di Atas Satelit")
            
            try:
                transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
                lon_c, lat_c = transformer.transform(centroid_x, centroid_y)
                
                m = folium.Map(location=[lat_c, lon_c], zoom_start=map_zoom, control_scale=True, max_zoom=30)
                
                # Google Hybrid
                folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                    attr='Google Hybrid', name='Google Hybrid', overlay=False, max_zoom=30
                ).add_to(m)

                # Add Plugins
                MiniMap(toggle_display=True).add_to(m)
                Fullscreen().add_to(m)

                poly_coords = []
                for i in range(num_stn):
                    # Koordinat Point Sekarang
                    ln1, lt1 = transformer.transform(x[i], y[i])
                    # Koordinat Point Seterusnya
                    next_i = (i + 1) % num_stn
                    ln2, lt2 = transformer.transform(x[next_i], y[next_i])
                    
                    poly_coords.append([lt1, ln1])
                    
                    # 1. Label No Stesen
                    if show_stn:
                        folium.Marker(
                            location=[lt1, ln1],
                            icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; font-weight: bold; background-color: red; padding: 2px 5px; border-radius: 50%; font-size: 10px; border: 1px solid white;">{df['STN'].iloc[i]}</div>""")
                        ).add_to(m)

                    # 2. Pengiraan Bearing & Jarak
                    if show_bearing:
                        # Jarak Ground
                        dist = math.sqrt((x[next_i]-x[i])**2 + (y[next_i]-y[i])**2)
                        
                        # Bearing (Azimuth)
                        angle_rad = math.atan2(x[next_i]-x[i], y[next_i]-y[i])
                        bearing_deg = math.degrees(angle_rad) % 360
                        
                        # Convert to DMS for display
                        d = int(bearing_deg)
                        m_dms = int((bearing_deg - d) * 60)
                        s_dms = (bearing_deg - d - m_dms/60) * 3600
                        bearing_text = f"{d}°{m_dms}'{s_dms:.0f}\""

                        # Rotation Angle for text (Matplotlib style rotation)
                        rot_angle = 90 - math.degrees(math.atan2(lt2-lt1, ln2-ln1))
                        if rot_angle > 90: rot_angle -= 180
                        if rot_angle < -90: rot_angle += 180

                        # Posisi Tengah Garisan
                        mid_lat, mid_lon = (lt1 + lt2) / 2, (ln1 + ln2) / 2
                        
                        folium.Marker(
                            location=[mid_lat, mid_lon],
                            icon=folium.DivIcon(html=f"""
                                <div style="transform: rotate({rot_angle}deg); font-family: sans-serif; color: {poly_color}; font-weight: bold; font-size: {text_size}px; white-space: nowrap; text-shadow: 1px 1px 2px black; text-align: center;">
                                    {bearing_text}<br>{dist:.3f}m
                                </div>""")
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

                # Label Luas
                if show_area_label:
                    folium.Marker(
                        location=[lat_c, lon_c],
                        icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; font-weight: bold; width: 300px; font-size: {text_size+4}px; text-shadow: 2px 2px 4px #000; text-align: center; border: 1px dashed {poly_color}; padding: 5px;">LUAS: {area:.3f} m²</div>""")
                    ).add_to(m)

                st_folium(m, width="100%", height=650, returned_objects=[])

            except Exception as e:
                st.error(f"Ralat: {e}")

            # --- 5. FOOTER ---
            st.divider()
            f1, f2, f3 = st.columns(3)
            f1.metric("Luas (m²)", f"{area:.3f}")
            f2.metric("Luas (Ekar)", f"{(area/4046.86):.4f}")
            
            geojson_data = json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"area": area}, "geometry": {"type": "Polygon", "coordinates": [[ [transformer.transform(df['E'].iloc[i], df['N'].iloc[i])[0], transformer.transform(df['E'].iloc[i], df['N'].iloc[i])[1]] for i in range(num_stn) ] + [[transformer.transform(df['E'].iloc[0], df['N'].iloc[0])[0], transformer.transform(df['E'].iloc[0], df['N'].iloc[0])[1]]]]}}]})
            f3.download_button("📥 Eksport GeoJSON", data=geojson_data, file_name="survey.geojson")

    if st.sidebar.button("Log Keluar"):
        del st.session_state.password_correct
        st.rerun()
