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

# Inisialisasi Kata Laluan dalam Session State (Default: admin123)
if "current_password" not in st.session_state:
    st.session_state.current_password = "admin123"

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        with col_p2:
            input_id = st.text_input("👤 Masukkan ID:", key="id_input")
            password = st.text_input("🔑 Masukkan Kata Laluan:", type="password")
            if st.button("Log Masuk", use_container_width=True):
                if input_id in USER_DB:
                    # Semak kata laluan dari session state
                    if password == st.session_state.current_password:
                        st.session_state.password_correct = True
                        st.session_state.user_full_name = USER_DB[input_id]
                        st.rerun()
                    else:
                        st.error("❌ Kata laluan salah!")
                else:
                    st.error("❌ ID Pengguna tidak dijumpai!")
        return False
    return True

# Fungsi untuk dialog tukar password
@st.dialog("🔑 Tukar Kata Laluan")
def change_password_dialog():
    new_pw = st.text_input("Kata Laluan Baharu:", type="password")
    conf_pw = st.text_input("Sahkan Kata Laluan Baharu:", type="password")
    if st.button("Simpan Kata Laluan", use_container_width=True):
        if new_pw == "" or conf_pw == "":
            st.warning("Sila isi semua ruangan!")
        elif new_pw == conf_pw:
            st.session_state.current_password = new_pw
            st.success("✅ Kata laluan berjaya ditukar!")
            st.rerun()
        else:
            st.error("❌ Kata laluan tidak sepadan!")

if check_password():
    if "login_notified" not in st.session_state:
        st.toast(f"✅ {st.session_state.user_full_name} Berjaya Log Masuk!", icon="🚀")
        st.session_state.login_notified = True

    # --- HEADER ---
    col_h1, col_h2 = st.columns([1, 4])
    with col_h1:
        if os.path.exists("puo logo.png"):
            st.image("puo logo.png", width=150)
    with col_h2:
        st.markdown(f"""
            <div style="background-color:#f8f9fa; padding:10px; border-radius:10px; border-left: 5px solid #007BFF;">
                <h1 style='margin-bottom:0; color:#1f1f1f;'>SISTEM SURVEY LOT</h1>
                <p style='color:gray; font-size:16px; margin-top:0;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
            </div>
        """, unsafe_allow_html=True)

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
            stn_labels = df['STN'].values
            num_stn = len(df)
            
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            perimeter = sum(math.sqrt((x[i]-x[(i+1)%num_stn])**2 + (y[i]-y[(i+1)%num_stn])**2) for i in range(num_stn))
            centroid_x, centroid_y = np.mean(x), np.mean(y)

            # --- 3. SIDEBAR ---
            st.sidebar.markdown(f"""
                <div style="background: linear-gradient(135deg, #007BFF, #00d4ff); padding: 20px; border-radius: 15px; color: white; margin-bottom: 20px; text-align: center;">
                    <span style="font-size: 40px;">👤</span>
                    <h3 style="margin: 10px 0 0 0;">Hai, {st.session_state.user_full_name.split()[0]}!</h3>
                    <p style="font-size: 14px; opacity: 0.9;">{st.session_state.user_full_name}</p>
                </div>
            """, unsafe_allow_html=True)

            st.sidebar.header(f"⚙️ Kawalan Paparan")
            stn_marker_size = st.sidebar.slider("Saiz Marker Stesen", 5, 40, 22)
            bd_text_size = st.sidebar.slider("Saiz Bearing/Jarak", 8, 25, 12)
            map_zoom = st.sidebar.slider("Tahap Zoom", 10, 25, 19)
            poly_color = st.sidebar.color_picker("Warna Poligon", "#FFFF00")

            # --- 4. MAP OVERLAY ---
            try:
                transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
                lon_c, lat_c = transformer.transform(centroid_x, centroid_y)
                
                m = folium.Map(location=[lat_c, lon_c], zoom_start=map_zoom, max_zoom=25)
                folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Hybrid', max_zoom=25).add_to(m)
                
                Fullscreen().add_to(m)
                MiniMap(toggle_display=True).add_to(m)
                
                poly_coords = []
                for i in range(num_stn):
                    p1_e, p1_n = x[i], y[i]
                    p2_e, p2_n = x[(i + 1) % num_stn], y[(i + 1) % num_stn]
                    ln1, lt1 = transformer.transform(p1_e, p1_n)
                    ln2, lt2 = transformer.transform(p2_e, p2_n)
                    poly_coords.append([lt1, ln1])

                    # Popup Stesen
                    stn_popup_html = f"<div style='font-family:Arial;'><b>STESEN {stn_labels[i]}</b><br>E: {p1_e:.3f}<br>N: {p1_n:.3f}</div>"
                    folium.Marker(
                        location=[lt1, ln1],
                        popup=folium.Popup(stn_popup_html, max_width=200),
                        icon=folium.DivIcon(html=f'<div style="color:white; background:red; border-radius:50%; width:{stn_marker_size}px; height:{stn_marker_size}px; line-height:{stn_marker_size}px; text-align:center; font-size:11px; font-weight:bold; border:2px solid white; transform:translate(-50%,-50%);">{stn_labels[i]}</div>')
                    ).add_to(m)

                    # Bearing & Jarak
                    dist = math.sqrt((p2_e-p1_e)**2 + (p2_n-p1_n)**2)
                    bearing = math.degrees(math.atan2(p2_e-p1_e, p2_n-p1_n)) % 360
                    angle_deg = -math.degrees(math.atan2(p2_n-p1_n, p2_e-p1_e))
                    if angle_deg > 90: angle_deg -= 180
                    elif angle_deg < -90: angle_deg += 180
                    mid_lat, mid_lon = (lt1 + lt2) / 2, (ln1 + ln2) / 2
                    folium.Marker(
                        location=[mid_lat, mid_lon],
                        icon=folium.DivIcon(html=f'<div style="transform: translate(-50%, -50%) rotate({angle_deg}deg); text-align: center; width: 150px;"><span style="color:{poly_color}; font-weight:bold; font-size:{bd_text_size}px; text-shadow:1px 1px 2px black;">{decimal_to_dms(bearing)}<br>{dist:.3f}m</span></div>')
                    ).add_to(m)

                # Popup Poligon
                lot_info_html = f"""
                <div style="font-family: sans-serif; width: 200px;">
                    <h4 style="color:#007BFF; margin-top:0;">📍 Info Lot</h4>
                    <b>Surveyor:</b> {st.session_state.user_full_name}<br>
                    <b>Luas:</b> {area:.3f} m²<br>
                    <b>Perimeter:</b> {perimeter:.3f} m
                </div>
                """
                folium.Polygon(locations=poly_coords, color=poly_color, weight=3, fill=True, fill_opacity=0.2, popup=folium.Popup(lot_info_html, max_width=250)).add_to(m)
                
                st_folium(m, width="100%", height=700)
            except Exception as e:
                st.error(f"Ralat: {e}")

    # --- BUTTONS AT SIDEBAR BOTTOM ---
    st.sidebar.divider()
    if st.sidebar.button("🔑 Tukar Kata Laluan", use_container_width=True):
        change_password_dialog()
        
    if st.sidebar.button("🚪 Log Keluar", use_container_width=True):
        st.session_state.clear()
        st.rerun()
