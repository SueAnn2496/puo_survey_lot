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

# --- FUNGSI DIALOG ---

@st.dialog("🔑 Tukar / Reset Kata Laluan")
def change_password_dialog(is_forgot=False):
    if is_forgot:
        st.info("Sila masukkan maklumat di bawah untuk menetapkan semula kata laluan anda.")
        check_id = st.text_input("Sahkan ID Pengguna:")
    
    new_pw = st.text_input("Kata Laluan Baharu:", type="password")
    conf_pw = st.text_input("Sahkan Kata Laluan Baharu:", type="password")
    
    if st.button("Simpan Kata Laluan", use_container_width=True):
        if is_forgot and check_id not in USER_DB:
            st.error("❌ ID Pengguna tidak sah!")
        elif new_pw == "" or conf_pw == "":
            st.warning("Sila isi semua ruangan!")
        elif new_pw == conf_pw:
            st.session_state.current_password = new_pw
            st.success("✅ Kata laluan berjaya dikemaskini!")
            st.rerun()
        else:
            st.error("❌ Kata laluan tidak sepadan!")

# --- SISTEM LOG MASUK ---

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        col_p1, col_p2, col_p3 = st.columns([1, 2, 1])
        
        with col_p2:
            input_id = st.text_input("👤 Masukkan ID:", key="id_login")
            password = st.text_input("🔑 Masukkan Kata Laluan:", type="password", key="pw_login")
            
            # Butang Log Masuk
            if st.button("Log Masuk", use_container_width=True):
                if input_id in USER_DB:
                    if password == st.session_state.current_password:
                        st.session_state.password_correct = True
                        st.session_state.user_full_name = USER_DB[input_id]
                        st.rerun()
                    else:
                        st.error("❌ Kata laluan salah!")
                else:
                    st.error("❌ ID Pengguna tidak dijumpai!")
            
            # Butang Lupa Kata Laluan
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("❓ Lupa Kata Laluan?", use_container_width=True):
                change_password_dialog(is_forgot=True)
                
        return False
    return True

# --- MAIN APP FLOW ---

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

    # --- INPUT DATA & MAP (Sama seperti kod anda sebelumnya) ---
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

            # --- SIDEBAR ---
            st.sidebar.markdown(f"""
                <div style="background: linear-gradient(135deg, #007BFF, #00d4ff); padding: 20px; border-radius: 15px; color: white; margin-bottom: 20px; text-align: center;">
                    <span style="font-size: 40px;">👤</span>
                    <h3 style="margin: 10px 0 0 0;">Hai, {st.session_state.user_full_name.split()[0]}!</h3>
                </div>
            """, unsafe_allow_html=True)

            st.sidebar.header(f"⚙️ Kawalan")
            stn_marker_size = st.sidebar.slider("Saiz Marker", 5, 40, 22)
            bd_text_size = st.sidebar.slider("Saiz Teks", 8, 25, 12)
            poly_color = st.sidebar.color_picker("Warna", "#FFFF00")

            # --- MAP ---
            try:
                transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
                lon_c, lat_c = transformer.transform(centroid_x, centroid_y)
                m = folium.Map(location=[lat_c, lon_c], zoom_start=19, max_zoom=25)
                folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Google Hybrid', max_zoom=25).add_to(m)
                
                # Plotting markers, lines, polygon (Logik sama seperti sebelum ini)
                # ... (Kod Map Anda) ...
                poly_coords = []
                for i in range(num_stn):
                    p1_e, p1_n = x[i], y[i]
                    p2_e, p2_n = x[(i + 1) % num_stn], y[(i + 1) % num_stn]
                    ln1, lt1 = transformer.transform(p1_e, p1_n)
                    ln2, lt2 = transformer.transform(p2_e, p2_n)
                    poly_coords.append([lt1, ln1])
                    
                    folium.Marker(
                        location=[lt1, ln1],
                        icon=folium.DivIcon(html=f'<div style="color:white; background:red; border-radius:50%; width:{stn_marker_size}px; height:{stn_marker_size}px; line-height:{stn_marker_size}px; text-align:center; font-size:11px; font-weight:bold; border:2px solid white; transform:translate(-50%,-50%);">{stn_labels[i]}</div>')
                    ).add_to(m)

                    dist = math.sqrt((p2_e-p1_e)**2 + (p2_n-p1_n)**2)
                    bearing = math.degrees(math.atan2(p2_e-p1_e, p2_n-p1_n)) % 360
                    mid_lat, mid_lon = (lt1 + lt2) / 2, (ln1 + ln2) / 2
                    folium.Marker(
                        location=[mid_lat, mid_lon],
                        icon=folium.DivIcon(html=f'<div style="text-align:center; width:150px; transform:translate(-50%,-50%);"><span style="color:{poly_color}; font-size:{bd_text_size}px; font-weight:bold; text-shadow:1px 1px 2px black;">{decimal_to_dms(bearing)}<br>{dist:.3f}m</span></div>')
                    ).add_to(m)

                lot_info = f"<b>Surveyor:</b> {st.session_state.user_full_name}<br><b>Luas:</b> {area:.3f} m²<br><b>Perimeter:</b> {perimeter:.3f} m"
                folium.Polygon(locations=poly_coords, color=poly_color, weight=3, fill=True, fill_opacity=0.2, popup=folium.Popup(lot_info, max_width=250)).add_to(m)
                
                st_folium(m, width="100%", height=700)
            except Exception as e:
                st.error(f"Ralat: {e}")

    # --- SIDEBAR BOTTOM ---
    st.sidebar.divider()
    if st.sidebar.button("🔑 Tukar Kata Laluan", use_container_width=True):
        change_password_dialog(is_forgot=False)
    if st.sidebar.button("🚪 Log Keluar", use_container_width=True):
        st.session_state.clear()
        st.rerun()
