import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
import os
from pyproj import Transformer
import folium
from streamlit_folium import st_folium

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="Sistem Survey Lot Pro", layout="wide")

# Custom CSS untuk UI yang lebih cantik
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Survey Lot PUO</h2>", unsafe_allow_html=True)
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
    # --- SIDEBAR KAWALAN ---
    st.sidebar.header("🛠️ Panel Kawalan GIS")
    
    with st.sidebar.expander("🌍 Tetapan Geo & Peta", expanded=True):
        epsg_code = st.text_input("Kod EPSG (Cth: 3168)", value="3168")
        show_satelite = st.toggle("Buka Peta Satelit", value=False)
        map_zoom = st.slider("Zoom Peta", 10, 20, 18)

    with st.sidebar.expander("👁️ Elemen Paparan", expanded=True):
        show_bearing_dist = st.checkbox("Bearing & Jarak (Rotate)", value=True)
        show_stn_labels = st.checkbox("Nombor Stesen", value=True)
        show_angles = st.checkbox("Sudut Dalaman", value=False)
        show_grid = st.checkbox("Grid Line", value=True)

    with st.sidebar.expander("📏 Pelarasan Grafik"):
        label_offset = st.slider("Jarak Label Stesen", 0.5, 15.0, 3.5)
        text_size = st.slider("Saiz Tulisan", 5, 15, 9)
        point_size = st.slider("Saiz Point", 20, 300, 80)
        poly_color = st.color_picker("Warna Garisan", "#1f77b4")

    # --- HEADER ---
    logo_file = "puo logo.png"
    col_h1, col_h2 = st.columns([1, 4])
    with col_h1:
        if os.path.exists(logo_file):
            st.image(logo_file, width=180)
    with col_h2:
        st.markdown("""
            <h1 style='margin-bottom:0;'>SISTEM SURVEY LOT</h1>
            <p style='color:gray; font-size:18px;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        """, unsafe_allow_html=True)

    st.divider()

    # --- FUNGSI PENGIRAAN ---
    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = (deg - d - m/60) * 3600
        return f"{d}°{m}'{s:.0f}\""

    uploaded_data = st.file_uploader("Muat naik fail CSV (Format: STN, E, N)", type="csv")

    if uploaded_data is not None:
        df = pd.read_csv(uploaded_data)
        
        if 'E' in df.columns and 'N' in df.columns:
            x, y = df['E'].values, df['N'].values
            num_stn = len(df)
            
            # Pengiraan Luas & Perimeter
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            perimeter = sum(math.sqrt((x[i]-x[(i+1)%num_stn])**2 + (y[i]-y[(i+1)%num_stn])**2) for i in range(num_stn))
            centroid_x, centroid_y = np.mean(x), np.mean(y)

            # --- METRICS DASHBOARD ---
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Bil. Stesen", f"{num_stn}")
            m2.metric("Perimeter", f"{perimeter:.3f} m")
            m3.metric("Luas (m²)", f"{area:.3f}")
            m4.metric("Luas (Ekar)", f"{(area/4046.86):.4f}")

            # --- PLOT PELAN TEKNIKAL ---
            tab1, tab2 = st.tabs(["📊 Pelan Grafik", "📋 Jadual Data"])
            
            with tab1:
                fig, ax = plt.subplots(figsize=(12, 10))
                
                # Plot Poligon
                df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
                ax.plot(df_poly['E'], df_poly['N'], color=poly_color, linewidth=2, zorder=2)
                ax.scatter(df['E'], df['N'], color='red', s=point_size, edgecolors='black', zorder=3)
                ax.fill(df_poly['E'], df_poly['N'], alpha=0.1, color='green' if area > 500 else 'orange')

                if show_grid: ax.grid(True, linestyle=':', alpha=0.5)

                # Penunjuk Arah Utara (North Arrow)
                x_n, y_n, arrow_len = 0.05, 0.95, 0.1
                ax.annotate('N', xy=(x_n, y_n), xytext=(x_n, y_n-arrow_len),
                            arrowprops=dict(facecolor='black', width=2, headwidth=8),
                            xycoords='axes fraction', ha='center', va='center', fontsize=15, fontweight='bold')

                for i in range(num_stn):
                    # 1. Label Stesen
                    if show_stn_labels:
                        dx, dy = x[i] - centroid_x, y[i] - centroid_y
                        dist_c = math.sqrt(dx**2 + dy**2) if dist_c != 0 else 1
                        ax.text(x[i] + (dx/dist_c)*label_offset, y[i] + (dy/dist_c)*label_offset, 
                                str(df['STN'].iloc[i]), fontsize=text_size+2, fontweight='bold', color='red', ha='center')

                    # 2. Bearing & Jarak (Rotating Text)
                    if show_bearing_dist:
                        p1_e, p1_n = x[i], y[i]
                        p2_e, p2_n = x[(i + 1) % num_stn], y[(i + 1) % num_stn]
                        dist = math.sqrt((p2_e-p1_e)**2 + (p2_n-p1_n)**2)
                        bearing = math.degrees(math.atan2(p2_e-p1_e, p2_n-p1_n)) % 360
                        
                        angle_rad = math.atan2(p2_n-p1_n, p2_e-p1_e)
                        angle_deg = math.degrees(angle_rad)
                        if angle_deg > 90: angle_deg -= 180
                        elif angle_deg < -90: angle_deg += 180
                        
                        ax.text((p1_e+p2_e)/2, (p1_n+p2_n)/2, f"{decimal_to_dms(bearing)}\n{dist:.3f}m", 
                                fontsize=text_size, color='darkgreen', rotation=angle_deg, 
                                ha='center', va='center', bbox=dict(facecolor='white', alpha=0.6, lw=0))

                ax.set_aspect('equal')
                st.pyplot(fig)

            with tab2:
                st.write("### Data Koordinat & Analisis")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Muat Turun Data CSV", data=csv, file_name='data_survey.csv', mime='text/csv')

            # --- PETA SATELIT ---
            if show_satelite:
                st.write("### 🌍 Lokasi Peta Satelit")
                try:
                    transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
                    lon_c, lat_c = transformer.transform(centroid_x, centroid_y)
                    
                    m = folium.Map(location=[lat_c, lon_c], zoom_start=map_zoom, tiles=None)
                    folium.TileLayer(tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', 
                                     attr='Google', name='Satelite').add_to(m)

                    poly_coords = [[transformer.transform(df['E'].iloc[k], df['N'].iloc[k])[1], 
                                    transformer.transform(df['E'].iloc[k], df['N'].iloc[k])[0]] for k in range(num_stn)]
                    
                    folium.Polygon(locations=poly_coords, color="yellow", fill=True, fill_opacity=0.3).add_to(m)
                    st_folium(m, width=1200, height=500)
                except:
                    st.error("Ralat EPSG. Sila pastikan kod betul.")

    if st.sidebar.button("Log Keluar"):
        del st.session_state.password_correct
        st.rerun()
