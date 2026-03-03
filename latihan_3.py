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

# --- DATABASE PENGGUNA ---
USER_DB = {
    "1": "OOI SUE ANN",
    "2": "WONG YUEAN YI",
    "3": "CHAN BOON YEAH"
}

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        with col_p2:
            input_id = st.text_input("👤 Masukkan ID:", key="id_input")
            password = st.text_input("🔑 Masukkan Kata Laluan:", type="password")
            if st.button("Log Masuk", use_container_width=True):
                if input_id in USER_DB:
                    if password == "admin123":
                        st.session_state.password_correct = True
                        st.session_state.user_full_name = USER_DB[input_id]
                        st.rerun()
                    else:
                        st.error("❌ Kata laluan salah!")
                else:
                    st.error("❌ ID Pengguna tidak dijumpai!")
        return False
    return True

if check_password():
    if "login_notified" not in st.session_state:
        st.toast(f"✅ {st.session_state.user_full_name} Berjaya Log Masuk!", icon="🚀")
        st.session_state.login_notified = True

    # --- HEADER ---
    logo_file = "puo logo.png"
    col_h1, col_h2 = st.columns([1, 4])
    with col_h1:
        if os.path.exists(logo_file):
            st.image(logo_file, width=150)
    with col_h2:
        st.markdown(f"<h1 style='margin-bottom:0;'>SISTEM SURVEY LOT</h1><p style='color:gray; font-size:18px;'>Politeknik Ungku Omar | Surveyor: {st.session_state.user_full_name}</p>", unsafe_allow_html=True)

    st.divider()

    # --- 2. INPUT DATA ---
    col_main1, col_main2 = st.columns([1, 2])
    with col_main1:
        epsg_input = st.text_input("🌍 Kod EPSG:", value="4390")
    with col_main2:
        uploaded_data = st.file_uploader("📂 Muat naik fail CSV (STN, E, N)", type="csv")

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
            perimeter = sum(math.sqrt((x[i]-x[(i+1)%num_stn])**2 + (y[i]-y[(i+1)%num_stn])**2) for i in range(num_stn))
            centroid_x, centroid_y = np.mean(x), np.mean(y)

            # --- 3. SIDEBAR ---
            st.sidebar.header(f"⚙️ Kawalan Peta")
            map_zoom = st.sidebar.slider("Tahap Zoom", 10, 25, 19)
            poly_color = st.sidebar.color_picker("Warna Poligon", "#FFFF00")
            stn_marker_size = st.sidebar.slider("Saiz Marker Stesen", 5, 30, 18)

            # --- 4. MAP OVERLAY ---
            try:
                transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
                lon_c, lat_c = transformer.transform(centroid_x, centroid_y)
                
                m = folium.Map(location=[lat_c, lon_c], zoom_start=map_zoom, max_zoom=25)
                folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Hybrid', max_zoom=25).add_to(m)
                
                poly_coords = []
                bearing_dist_list = []

                for i in range(num_stn):
                    p1_e, p1_n = x[i], y[i]
                    p2_e, p2_n = x[(i + 1) % num_stn], y[(i + 1) % num_stn]
                    ln1, lt1 = transformer.transform(p1_e, p1_n)
                    poly_coords.append([lt1, ln1])

                    # Kira Bearing & Jarak untuk diletakkan dalam Popup
                    dist = math.sqrt((p2_e-p1_e)**2 + (p2_n-p1_n)**2)
                    bearing = math.degrees(math.atan2(p2_e-p1_e, p2_n-p1_n)) % 360
                    bearing_dist_list.append(f"<b>{df['STN'].iloc[i]} ke {df['STN'].iloc[(i+1)%num_stn]}:</b> {decimal_to_dms(bearing)} / {dist:.3f}m")

                    # Marker Stesen (Tetap ada)
                    folium.Marker(
                        location=[lt1, ln1],
                        icon=folium.DivIcon(html=f'<div style="color: white; background: red; border-radius: 50%; width: {stn_marker_size}px; height: {stn_marker_size}px; line-height: {stn_marker_size}px; text-align: center; font-size: 10px; font-weight: bold; border: 1px solid white; transform: translate(-50%, -50%);">{df["STN"].iloc[i]}</div>')
                    ).add_to(m)

                # Bina Kandungan Popup (HTML)
                bd_html = "<br>".join(bearing_dist_list)
                popup_content = f"""
                <div style="font-family: Arial; width: 220px;">
                    <h4 style="margin:0; color:#007BFF;">Maklumat Lot</h4>
                    <hr style="margin:5px 0;">
                    <b>Surveyor:</b> {st.session_state.user_full_name}<br>
                    <b>Luas:</b> {area:.3f} m²<br>
                    <b>Perimeter:</b> {perimeter:.3f} m<br>
                    <hr style="margin:5px 0;">
                    <small><b>Bearing & Jarak:</b><br>{bd_html}</small>
                </div>
                """

                # Tambah Poligon dengan Popup
                folium.Polygon(
                    locations=poly_coords,
                    color=poly_color,
                    weight=3,
                    fill=True,
                    fill_opacity=0.3,
                    popup=folium.Popup(popup_content, max_width=300)
                ).add_to(m)

                st_folium(m, width="100%", height=700)
            except Exception as e:
                st.error(f"Ralat: {e}")

            # --- 5. EKSPORT ---
            st.divider()
            st.download_button(label=f"📥 Muat Turun Fail GeoJSON", data="JSON_DATA", file_name=f"survey_{st.session_state.user_full_name}.geojson")

    if st.sidebar.button("Log Keluar"):
        st.session_state.clear()
        st.rerun()
