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

# --- 2. SISTEM DATABASE FAIL (KESELAMATAN) ---
PASSWORD_FILE = "user_config.json"

def load_password():
    if os.path.exists(PASSWORD_FILE):
        try:
            with open(PASSWORD_FILE, "r") as f:
                data = json.load(f)
                return data.get("password", "admin123")
        except:
            return "admin123"
    return "admin123"

def save_password(new_pw):
    with open(PASSWORD_FILE, "w") as f:
        json.dump({"password": new_pw}, f)

if "current_password" not in st.session_state:
    st.session_state.current_password = load_password()

# --- 3. DATABASE PENGGUNA ---
USER_DB = {"1": "OOI SUE ANN", "2": "WONG YUEAN YI", "3": "CHAN BOON YEAH"}

# --- 4. FUNGSI EKSPORT QGIS ---
def convert_to_geojson(df, x, y, stn_labels, area, perimeter, epsg_input):
    transformer = Transformer.from_crs(f"EPSG:{epsg_input}", "EPSG:4326", always_xy=True)
    features = []
    poly_coords = []
    
    for i in range(len(df)):
        lon, lat = transformer.transform(x[i], y[i])
        poly_coords.append([lon, lat])
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"Stesen": str(stn_labels[i]), "E": float(x[i]), "N": float(y[i])}
        })
    
    poly_coords.append(poly_coords[0]) # Tutup poligon
    features.append({
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [poly_coords]},
        "properties": {"Nama": "Lot Survey", "Luas_m2": round(area, 3), "Perimeter_m": round(perimeter, 3)}
    })
    
    return json.dumps({"type": "FeatureCollection", "features": features}, indent=4)

# --- 5. DIALOG & AUTH ---
@st.dialog("🔑 Kemaskini Kata Laluan")
def change_password_dialog(is_forgot=False):
    if is_forgot:
        check_id = st.text_input("Sahkan ID Pengguna:", key="verify_id")
    new_pw = st.text_input("Kata Laluan Baharu:", type="password", key="new_pw")
    conf_pw = st.text_input("Sahkan Kata Laluan Baharu:", type="password", key="conf_pw")
    
    if st.button("Simpan", use_container_width=True):
        if is_forgot and check_id not in USER_DB: st.error("❌ ID tidak sah!")
        elif new_pw == conf_pw and new_pw != "":
            save_password(new_pw)
            st.session_state.current_password = new_pw
            st.success("✅ Berjaya!"); st.rerun()
        else: st.error("❌ Ralat!")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            input_id = st.text_input("👤 ID:", key="l_id")
            pw = st.text_input("🔑 Kata Laluan:", type="password", key="l_pw")
            if st.button("Log Masuk", use_container_width=True):
                if input_id in USER_DB and pw == load_password():
                    st.session_state.password_correct = True
                    st.session_state.user_full_name = USER_DB[input_id]
                    st.rerun()
                else: st.error("❌ Salah!")
            if st.button("❓ Lupa Kata Laluan?", use_container_width=True): change_password_dialog(True)
        return False
    return True

# --- 6. MAIN APP ---
if check_password():
    # Header
    colh1, colh2 = st.columns([1, 4])
    with colh2:
        st.markdown('<div style="background:#f8f9fa; padding:15px; border-radius:10px; border-left:5px solid #007BFF;"><h1>SISTEM SURVEY LOT</h1><p>Politeknik Ungku Omar</p></div>', unsafe_allow_html=True)

    # Input
    c1, c2 = st.columns([1, 2])
    epsg = c1.text_input("🌍 EPSG:", value="4390")
    file = c2.file_uploader("📂 Muat naik CSV", type="csv")

    if file:
        df = pd.read_csv(file)
        x, y, labels = df['E'].values, df['N'].values, df['STN'].values
        num = len(df)
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        perimeter = sum(math.sqrt((x[i]-x[(i+1)%num])**2 + (y[i]-y[(i+1)%num])**2) for i in range(num))
        
        # Sidebar
        st.sidebar.title(f"Hai, {st.session_state.user_full_name.split()[0]}!")
        m_size = st.sidebar.slider("Saiz Marker", 5, 40, 22)
        t_size = st.sidebar.slider("Saiz Teks", 8, 25, 12)
        p_color = st.sidebar.color_picker("Warna", "#FFFF00")
        
        # Export Button
        geojson_data = convert_to_geojson(df, x, y, labels, area, perimeter, epsg)
        st.sidebar.download_button("🚀 Export to QGIS (.geojson)", geojson_data, f"survey_{labels[0]}.geojson", "application/json", use_container_width=True)

        # Map
        try:
            trans = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
            lon_c, lat_c = trans.transform(np.mean(x), np.mean(y))
            m = folium.Map(location=[lat_c, lon_c], zoom_start=19)
            
            # Layers
            folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', attr='Google', name='Satelit (Hybrid)', max_zoom=25).add_to(m)
            folium.TileLayer('openstreetmap', name='Peta Jalan').add_to(m)
            
            fg = folium.FeatureGroup(name="Data Survey").add_to(m)
            poly_coords = []
            
            for i in range(num):
                ln1, lt1 = trans.transform(x[i], y[i])
                ln2, lt2 = trans.transform(x[(i+1)%num], y[(i+1)%num])
                poly_coords.append([lt1, ln1])
                
                # Marker
                folium.Marker([lt1, ln1], icon=folium.DivIcon(html=f'<div style="color:white; background:red; border-radius:50%; width:{m_size}px; height:{m_size}px; line-height:{m_size}px; text-align:center; font-size:10px; font-weight:bold; border:2px solid white; transform:translate(-50%,-50%);">{labels[i]}</div>')).add_to(fg)
                
                # Bearing/Dist
                d = math.sqrt((x[(i+1)%num]-x[i])**2 + (y[(i+1)%num]-y[i])**2)
                b = math.degrees(math.atan2(x[(i+1)%num]-x[i], y[(i+1)%num]-y[i])) % 360
                folium.Marker([(lt1+lt2)/2, (ln1+ln2)/2], icon=folium.DivIcon(html=f'<div style="text-align:center; width:100px; transform:translate(-50%,-50%);"><span style="color:{p_color}; font-weight:bold; font-size:{t_size}px; text-shadow:1px 1px 2px black;">{int(b)}°<br>{d:.2f}m</span></div>')).add_to(fg)

            folium.Polygon(poly_coords, color=p_color, fill=True, fill_opacity=0.2).add_to(fg)
            Fullscreen().add_to(m)
            folium.LayerControl(collapsed=False).add_to(m)
            st_folium(m, width="100%", height=700)
        except Exception as e: st.error(f"Ralat: {e}")

    # Logout
    st.sidebar.divider()
    if st.sidebar.button("🔑 Tukar Password"): change_password_dialog()
    if st.sidebar.button("🚪 Log Keluar"): 
        del st.session_state["password_correct"]
        st.rerun()
