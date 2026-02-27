import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math

# --- 1. KONFIGURASI HALAMAN & KATA LALUAN ---
st.set_page_config(page_title="PUO Surveying Tool", layout="centered")

def check_password():
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Geomatik PUO</h2>", unsafe_allow_html=True)
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
    # --- LOGO SEKOLAH (Menggunakan fail yang anda beri) ---
    logo_url = "https://raw.githubusercontent.com/SueAnn2496/puo_survey_lot/main/puo%20logo.png"

    # --- HEADER ---
    col_logo1, col_logo2 = st.columns([1, 2])
    with col_logo1:
        # Menggunakan logo yang anda muat naik ke GitHub
        st.image(logo_url, width=250) 

    with col_logo2:
        st.markdown("""
            <div style='padding-top: 20px;'>
                <h2 style='margin-bottom: 0px; font-size: 22px;'>POLITEKNIK UNGKU OMAR</h2>
                <p style='font-size: 15px; color: gray;'>Jabatan Kejuruteraan Awam - Unit Geomatik</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # --- PENJANA POLIGON ---
    st.write("### 🗺️ Penjana Poligon & Analisis Luas")
    
    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = (deg - d - m/60) * 3600
        return f"{d}°{m}'{s:.0f}\""

    uploaded_data = st.file_uploader("Muat naik fail CSV Koordinat (STN, E, N)", type="csv")

    if uploaded_data is not None:
        df = pd.read_csv(uploaded_data)
        
        if 'E' in df.columns and 'N' in df.columns:
            x = df['E'].values
            y = df['N'].values
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            centroid_x = np.mean(x)
            centroid_y = np.mean(y)

            if st.button('🚀 Proses & Jana Grafik'):
                st.session_state.processed = True
                
            if st.session_state.get('processed', False):
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Plot Poligon
                df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
                ax.plot(df_poly['E'], df_poly['N'], marker='o', linestyle='-', color='b', zorder=2)
                ax.fill(df_poly['E'], df_poly['N'], alpha=0.15, color='skyblue', zorder=1)

                # Label & Data
                for i in range(len(df)):
                    curr_x, curr_y = df['E'].iloc[i], df['N'].iloc[i]
                    dx, dy = curr_x - centroid_x, curr_y - centroid_y
                    mag = math.sqrt(dx**2 + dy**2) if math.sqrt(dx**2 + dy**2) != 0 else 1
                    ax.text(curr_x + (dx/mag)*0.7, curr_y + (dy/mag)*0.7, 
                            str(df['STN'].iloc[i]), fontsize=10, fontweight='bold', color='red', ha='center')

                    # Kira Bearing/Jarak
                    p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                    de, dn = p2['E']-p1['E'], p2['N']-p1['N']
                    dist = math.sqrt(de**2 + dn**2)
                    angle = math.degrees(math.atan2(de, dn)) % 360
                    
                    mid_e, mid_n = (p1['E']+p2['E'])/2, (p1['N']+p2['N'])/2
                    ax.text(mid_e, mid_n, f"{decimal_to_dms(angle)}\n{dist:.3f}m", 
                            color='darkgreen', fontsize=7, fontweight='bold', ha='center',
                            bbox=dict(facecolor='white', alpha=0.7, lw=0))

                ax.text(centroid_x, centroid_y, f"LUAS:\n{area:.3f} m²", 
                        ha='center', va='center', fontsize=12, fontweight='bold',
                        bbox=dict(facecolor='yellow', alpha=0.7, boxstyle='round'))

                ax.set_aspect('equal')
                st.pyplot(fig)
                st.success(f"Analisis Selesai. Luas: {area:.3f} m²")

    if st.sidebar.button("Log Keluar"):
        del st.session_state.password_correct
        st.rerun()
