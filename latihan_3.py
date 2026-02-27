import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import os
from pyproj import Transformer # Sila tambah 'pyproj' dalam requirements.txt
import folium
from streamlit_folium import st_folium

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PUO Geomatik Pro", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Geomatik Pro PUO</h2>", unsafe_allow_html=True)
        password = st.text_input("Sila masukkan kata laluan:", type="password")
        if st.button("Log Masuk"):
            if password == "admin123":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Kata laluan salah.")
        return False
    return True

if check_password():
    # --- SIDEBAR KAWALAN (PROFESIONAL PANEL) ---
    st.sidebar.header("🛠️ Panel Kawalan")
    
    # Input EPSG
    epsg_code = st.sidebar.text_input("Kod EPSG (Cth: 3168, 4390, 3386)", value="3168")
    
    # On/Off Layers
    st.sidebar.subheader("👁️ Paparan Layer")
    show_bearing_dist = st.sidebar.checkbox("Paparan Bearing & Jarak", value=True)
    show_stn_labels = st.sidebar.checkbox("Paparan No. Stesen", value=True)
    show_area_label = st.sidebar.checkbox("Paparan Label Luas", value=True)
    show_grid = st.sidebar.checkbox("Paparan Grid Line", value=True)
    show_satelite = st.sidebar.checkbox("Buka Layer Satelit (Peta)", value=False)

    # Edit Sizes
    st.sidebar.subheader("📏 Saiz Elemen")
    poly_size = st.sidebar.slider("Ketebalan Garisan Poligon", 0.5, 5.0, 1.5)
    point_size = st.sidebar.slider("Saiz Point Stesen", 1, 100, 30)
    text_size = st.sidebar.slider("Saiz Tulisan Data", 5, 15, 8)
    label_offset = st.sidebar.slider("Jarak Label Koordinat", 0.1, 2.0, 0.8)

    # --- LOGO & HEADER ---
    logo_file = "puo logo.png"
    col_h1, col_h2 = st.columns([1, 4])
    with col_h1:
        if os.path.exists(logo_file):
            st.image(logo_file, width=200)
    with col_h2:
        st.markdown("## POLITEKNIK UNGKU OMAR\n#### Jabatan Kejuruteraan Awam - Unit Geomatik")

    st.divider()

    # --- UPLOAD & PROCESSING ---
    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = (deg - d - m/60) * 3600
        return f"{d}°{m}'{s:.0f}\""

    uploaded_data = st.file_uploader("Muat naik fail CSV Koordinat (STN, E, N)", type="csv")

    if uploaded_data is not None:
        df = pd.read_csv(uploaded_data)
        
        if 'E' in df.columns and 'N' in df.columns:
            x, y = df['E'].values, df['N'].values
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            num_stn = len(df)
            perimeter = sum(math.sqrt((x[i]-x[(i+1)%num_stn])**2 + (y[i]-y[(i+1)%num_stn])**2) for i in range(num_stn))

            # Metric Cards
            m1, m2, m3 = st.columns(3)
            m1.metric("Bil. Stesen", num_stn)
            m2.metric("Perimeter", f"{perimeter:.3f} m")
            m3.metric("Luas", f"{area:.3f} m²")

            # --- PLOT MATPLOTLIB (PROFESIONAL) ---
            st.write("### 📊 Pelan Poligon")
            fig, ax = plt.subplots(figsize=(10, 8))
            
            df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
            ax.plot(df_poly['E'], df_poly['N'], color='blue', linewidth=poly_size, zorder=2)
            ax.scatter(df['E'], df['N'], color='red', s=point_size, zorder=3)
            ax.fill(df_poly['E'], df_poly['N'], alpha=0.1, color='cyan')

            if show_grid:
                ax.grid(True, linestyle='--', alpha=0.6)

            centroid_x, centroid_y = np.mean(x), np.mean(y)

            for i in range(num_stn):
                # Stesen Labels
                if show_stn_labels:
                    dx, dy = x[i] - centroid_x, y[i] - centroid_y
                    mag = math.sqrt(dx**2 + dy**2)
                    ax.text(x[i] + (dx/mag)*label_offset, y[i] + (dy/mag)*label_offset, 
                            str(df['STN'].iloc[i]), fontsize=text_size+2, fontweight='bold', color='red')

                # Bearing & Jarak
                if show_bearing_dist:
                    p1, p2 = df.iloc[i], df.iloc[(i + 1) % num_stn]
                    dist = math.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
                    angle = math.degrees(math.atan2(p2['E']-p1['E'], p2['N']-p1['N'])) % 360
                    ax.text((p1['E']+p2['E'])/2, (p1['N']+p2['N'])/2, f"{decimal_to_dms(angle)}\n{dist:.3f}m", 
                            fontsize=text_size, ha='center', bbox=dict(facecolor='white', alpha=0.6, lw=0))

            if show_area_label:
                ax.text(centroid_x, centroid_y, f"LUAS:\n{area:.3f} m²", ha='center', fontweight='bold',
                        bbox=dict(facecolor='yellow', alpha=0.8, boxstyle='round'))

            ax.set_aspect('equal')
            st.pyplot(fig)

            # --- LAYER SATELIT (FOLIUM) ---
            if show_satelite:
                st.write("### 🌍 Paparan Peta Satelit")
                try:
                    # Tukar koordinat ke WGS84
                    transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326")
                    lat, lon = transformer.transform(centroid_y, centroid_x)
                    
                    m = folium.Map(location=[lat, lon], zoom_start=18, tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Google Satelite')
                    
                    # Tambah Poligon ke Peta
                    poly_coords = []
                    for i in range(len(df)):
                        plat, plon = transformer.transform(df['N'].iloc[i], df['E'].iloc[i])
                        poly_coords.append([plat, plon])
                    
                    folium.Polygon(locations=poly_coords, color="yellow", weight=2, fill=True, fill_opacity=0.2).add_to(m)
                    st_folium(m, width=1000, height=500)
                except Exception as e:
                    st.error(f"Gagal menukar koordinat. Sila pastikan Kod EPSG ({epsg_code}) betul.")

    if st.sidebar.button("Log Keluar"):
        del st.session_state.password_correct
        st.rerun()
