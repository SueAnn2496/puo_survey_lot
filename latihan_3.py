import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import os
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Survey Lot - PUO", layout="wide")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
        password = st.text_input("Sila masukkan kata laluan untuk akses:", type="password")
        if st.button("Log Masuk"):
            if password == "admin123":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Kata laluan salah.")
        return False
    return True

if check_password():
    # --- SIDEBAR KAWALAN ---
    st.sidebar.header("🛠️ Panel Kawalan Visual")
    
    st.sidebar.subheader("🌍 Tetapan Geo")
    epsg_code = st.sidebar.text_input("Kod EPSG (Cth: 3168, 3386)", value="3168")
    show_satelite = st.sidebar.toggle("Buka Layer Satelit", value=False)

    st.sidebar.subheader("👁️ Paparan Elemen")
    show_bearing_dist = st.sidebar.checkbox("Paparan Bearing & Jarak", value=True)
    show_stn_labels = st.sidebar.checkbox("Paparan No. Stesen", value=True)
    show_area_label = st.sidebar.checkbox("Paparan Label Luas", value=True)
    show_grid = st.sidebar.checkbox("Paparan Grid Line", value=True)

    st.sidebar.subheader("📏 Pelarasan Saiz")
    poly_weight = st.sidebar.slider("Ketebalan Garisan Poligon", 0.5, 5.0, 1.5)
    point_size = st.sidebar.slider("Saiz Point Stesen", 10, 200, 50)
    text_size = st.sidebar.slider("Saiz Tulisan Data", 5, 15, 8)
    label_offset = st.sidebar.slider("Jarak Nombor Stesen (Offset)", 0.2, 5.0, 1.2)

    # --- HEADER ---
    logo_file = "puo logo.png"
    col_h1, col_h2 = st.columns([1, 4])
    with col_h1:
        if os.path.exists(logo_file):
            st.image(logo_file, width=200)
    with col_h2:
        st.markdown("""
            <h2 style='margin-bottom:0;'>SISTEM SURVEY LOT</h2>
            <h4 style='color:gray;'>Politeknik Ungku Omar - Unit Geomatik</h4>
        """, unsafe_allow_html=True)

    st.divider()

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
            num_stn = len(df)
            
            # Pengiraan
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            perimeter = sum(math.sqrt((x[i]-x[(i+1)%num_stn])**2 + (y[i]-y[(i+1)%num_stn])**2) for i in range(num_stn))
            centroid_x, centroid_y = np.mean(x), np.mean(y)

            # Dashboard Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Bil. Stesen", num_stn)
            m2.metric("Perimeter (m)", f"{perimeter:.3f}")
            m3.metric("Luas (m²)", f"{area:.3f}")

            # --- PLOT MATPLOTLIB ---
            st.write("### 📊 Pelan Teknikal Poligon")
            fig, ax = plt.subplots(figsize=(10, 8))
            
            df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
            ax.plot(df_poly['E'], df_poly['N'], color='#1f77b4', linewidth=poly_weight, zorder=2)
            ax.scatter(df['E'], df['N'], color='red', s=point_size, edgecolors='black', zorder=3)
            ax.fill(df_poly['E'], df_poly['N'], alpha=0.1, color='#7fcdbb')

            if show_grid:
                ax.grid(True, linestyle=':', alpha=0.5)

            for i in range(num_stn):
                if show_stn_labels:
                    dx, dy = x[i] - centroid_x, y[i] - centroid_y
                    dist_c = math.sqrt(dx**2 + dy**2) if math.sqrt(dx**2 + dy**2) != 0 else 1
                    ax.text(x[i] + (dx/dist_c)*label_offset, y[i] + (dy/dist_c)*label_offset, 
                            str(df['STN'].iloc[i]), fontsize=text_size+2, fontweight='bold', color='red', ha='center')

                if show_bearing_dist:
                    p1, p2 = df.iloc[i], df.iloc[(i + 1) % num_stn]
                    dist = math.sqrt((p2['E']-p1['E'])**2 + (p2['N']-p1['N'])**2)
                    angle = math.degrees(math.atan2(p2['E']-p1['E'], p2['N']-p1['N'])) % 360
                    ax.text((p1['E']+p2['E'])/2, (p1['N']+p2['N'])/2, f"{decimal_to_dms(angle)}\n{dist:.3f}m", 
                            fontsize=text_size, color='darkgreen', fontweight='bold', ha='center',
                            bbox=dict(facecolor='white', alpha=0.7, lw=0))

            if show_area_label:
                ax.text(centroid_x, centroid_y, f"LUAS:\n{area:.3f} m²", ha='center', fontweight='bold',
                        bbox=dict(facecolor='#ffffcc', alpha=0.9, edgecolor='black', boxstyle='round'))

            ax.set_aspect('equal')
            ax.set_xlabel("Easting (m)")
            ax.set_ylabel("Northing (m)")
            st.pyplot(fig)

            # --- LAYER SATELIT ---
            if show_satelite:
                st.divider()
                st.write("### 🌍 Integrasi Peta Satelit Google")
                try:
                    transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
                    lon_c, lat_c = transformer.transform(centroid_x, centroid_y)
                    
                    m = folium.Map(location=[lat_c, lon_c], zoom_start=19, tiles=None)
                    folium.TileLayer(
                        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                        attr='Google Satelite', name='Google Satelite'
                    ).add_to(m)

                    poly_coords = []
                    for i in range(len(df)):
                        ln, lt = transformer.transform(df['E'].iloc[i], df['N'].iloc[i])
                        poly_coords.append([lt, ln])
                    
                    folium.Polygon(locations=poly_coords, color="yellow", weight=3, fill=True, fill_opacity=0.3).add_to(m)
                    st_folium(m, width=1100, height=500)
                except Exception as e:
                    st.error(f"Sila pastikan Kod EPSG {epsg_code} betul.")

    if st.sidebar.button("Log Keluar"):
        del st.session_state.password_correct
        st.rerun()
