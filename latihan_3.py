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

# --- 1. SETTING HALAMAN ---
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
    col_h1, col_h2 = st.columns([1, 4])
    with col_h1:
        if os.path.exists(logo_file):
            st.image(logo_file, width=180)
    with col_h2:
        st.markdown("<h1 style='margin-bottom:0;'>SISTEM SURVEY LOT</h1><p style='color:gray; font-size:18px;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>", unsafe_allow_html=True)

    st.divider()

    # --- 2. INPUT DATA (EPSG DI LUAR UPLOAD) ---
    st.markdown("### 🗺️ Konfigurasi Geospasial")
    col_main1, col_main2 = st.columns([1, 2])
    with col_main1:
        epsg_input = st.text_input("🌍 Kod EPSG (Edit di sini):", value="4390")
    with col_main2:
        uploaded_data = st.file_uploader("📂 Muat naik fail CSV (Format: STN, E, N)", type="csv")

    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = (deg - d - m/60) * 3600
        return f"{d}°{m}'{s:.0f}\""

    if uploaded_data is not None:
        df = pd.read_csv(uploaded_data)
        
        if 'E' in df.columns and 'N' in df.columns:
            x, y = df['E'].values, df['N'].values
            num_stn = len(df)
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            centroid_x, centroid_y = np.mean(x), np.mean(y)

            # --- 3. PANEL KAWALAN (SIDEBAR) ---
            st.sidebar.header("🛠️ Panel Kawalan")
            
            with st.sidebar.expander("👁️ On/Off Elemen", expanded=True):
                show_stn = st.checkbox("Papar No. Stesen", value=True)
                show_bd = st.checkbox("Papar Bearing & Jarak", value=True)
                show_area = st.checkbox("Papar Luas di Tengah", value=True)

            with st.sidebar.expander("🎨 Pelarasan Grafik"):
                poly_color = st.color_picker("Warna Poligon", "#FFFF00")
                text_size = st.slider("Saiz Tulisan", 8, 25, 12)
                map_zoom = st.slider("Tahap Zoom", 10, 30, 19)

            # --- 4. MAP OVERLAY (GOOGLE SATELITE) ---
            st.subheader("🌍 Paparan Lot di Atas Satelit")
            
            try:
                transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
                lon_c, lat_c = transformer.transform(centroid_x, centroid_y)
                
                m = folium.Map(location=[lat_c, lon_c], zoom_start=map_zoom, max_zoom=30)
                folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                    attr='Google', name='Google Hybrid', max_zoom=30
                ).add_to(m)

                # Tambah Alat Navigasi
                MiniMap(toggle_display=True).add_to(m)
                Fullscreen().add_to(m)

                poly_coords = []
                for i in range(num_stn):
                    # Koordinat Point
                    p1_e, p1_n = x[i], y[i]
                    p2_e, p2_n = x[(i + 1) % num_stn], y[(i + 1) % num_stn]
                    
                    ln1, lt1 = transformer.transform(p1_e, p1_n)
                    ln2, lt2 = transformer.transform(p2_e, p2_n)
                    poly_coords.append([lt1, ln1])

                    # 1. Label Stesen
                    if show_stn:
                        folium.Marker(
                            location=[lt1, ln1],
                            icon=folium.DivIcon(html=f'<div style="color: white; background: red; border-radius: 50%; width: 18px; height: 18px; text-align: center; font-size: 10px; font-weight: bold; border: 1px solid white;">{df["STN"].iloc[i]}</div>')
                        ).add_to(m)

                    # 2. Pengiraan Bearing & Jarak (Rotating Text)
                    if show_bd:
                        dist = math.sqrt((p2_e-p1_e)**2 + (p2_n-p1_n)**2)
                        bearing = math.degrees(math.atan2(p2_e-p1_e, p2_n-p1_n)) % 360
                        
                        # Pengiraan Sudut Putaran (Logic dari kod asal anda)
                        angle_rad = math.atan2(p2_n-p1_n, p2_e-p1_e)
                        angle_deg = -math.degrees(angle_rad) # Negatif untuk Folium CSS rotation
                        
                        # Normalkan sudut supaya tulisan tidak terbalik
                        if angle_deg > 90: angle_deg -= 180
                        elif angle_deg < -90: angle_deg += 180

                        mid_lat, mid_lon = (lt1 + lt2) / 2, (ln1 + ln2) / 2
                        
                        folium.Marker(
                            location=[mid_lat, mid_lon],
                            icon=folium.DivIcon(html=f"""
                                <div style="transform: rotate({angle_deg}deg); text-align: center; width: 120px; margin-left: -60px;">
                                    <span style="font-family: sans-serif; color: {poly_color}; font-weight: bold; font-size: {text_size}px; text-shadow: 1px 1px 2px black;">
                                        {decimal_to_dms(bearing)}<br>{dist:.3f}m
                                    </span>
                                </div>""")
                        ).add_to(m)

                # Lukis Poligon
                folium.Polygon(
                    locations=poly_coords,
                    color=poly_color,
                    weight=3,
                    fill=True,
                    fill_opacity=0.2
                ).add_to(m)

                # 3. Label Luas di Tengah
                if show_area:
                    folium.Marker(
                        location=[lat_c, lon_c],
                        icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; font-weight: bold; width: 200px; margin-left: -100px; text-align: center; font-size: {text_size+4}px; text-shadow: 2px 2px 4px black; border: 1px dashed {poly_color}; padding: 5px;">LUAS: {area:.3f} m²</div>""")
                    ).add_to(m)

                st_folium(m, width="100%", height=600, returned_objects=[])

            except Exception as e:
                st.error(f"Sila semak Kod EPSG: {e}")

            # --- 5. FOOTER & METRICS ---
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("Luas (m²)", f"{area:.3f}")
            c2.metric("Luas (Ekar)", f"{(area/4046.86):.4f}")
            
            # Export Function
            def to_geojson(df, epsg):
                coords = []
                t = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
                for i in range(len(df)):
                    ln, lt = t.transform(df['E'].iloc[i], df['N'].iloc[i])
                    coords.append([ln, lt])
                coords.append(coords[0])
                return json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "properties": {"area": area}, "geometry": {"type": "Polygon", "coordinates": [coords]}}]})

            c3.download_button("📥 Eksport ke QGIS (GeoJSON)", data=to_geojson(df, epsg_input), file_name="survey_lot.geojson")

    if st.sidebar.button("Log Keluar"):
        del st.session_state.password_correct
        st.rerun()
