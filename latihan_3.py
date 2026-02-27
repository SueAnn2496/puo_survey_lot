import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
from PIL import Image

st.set_page_config(page_title="PUO Surveying Tool", layout="centered")

# --- BAHAGIAN UPLOAD LOGO ---
st.sidebar.header("⚙️ Konfigurasi Logo")
logo_file = st.sidebar.file_uploader("Upload Logo Sekolah (PNG/JPG)", type=["png", "jpg", "jpeg"])

default_logo_url = "https://upload.wikimedia.org/wikipedia/ms/thumb/b/b3/Logo_Politeknik_Ungku_Omar.png/200px-Logo_Politeknik_Ungku_Omar.png"

if logo_file is not None:
    display_logo = Image.open(logo_file)
else:
    display_logo = default_logo_url

# --- HEADER ---
col_logo1, col_logo2 = st.columns([1, 2])
with col_logo1:
    st.image(display_logo, width=180) 

with col_logo2:
    st.markdown("""
        <div style='padding-top: 20px;'>
            <h2 style='margin-bottom: 0px; font-size: 24px;'>POLITEKNIK UNGKU OMAR</h2>
            <p style='font-size: 16px; color: gray;'>Jabatan Kejuruteraan Awam - Unit Geomatik</p>
        </div>
    """, unsafe_allow_html=True)

st.divider()

def decimal_to_dms(deg):
    d = int(deg)
    m = int((deg - d) * 60)
    s = (deg - d - m/60) * 3600
    return f"{d}°{m}'{s:.0f}\""

st.write("### 🗺️ Penjana Poligon & Analisis Luas")
uploaded_data = st.file_uploader("Muat naik fail CSV Koordinat (STN, E, N)", type="csv")

if uploaded_data is not None:
    df = pd.read_csv(uploaded_data)
    
    if 'E' in df.columns and 'N' in df.columns:
        x = df['E'].values
        y = df['N'].values
        # Shoelace formula untuk luas
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        centroid_x = np.mean(x)
        centroid_y = np.mean(y)

        if st.button('🚀 Proses & Jana Grafik'):
            st.session_state.processed = True
            
        if st.session_state.get('processed', False):
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Watermark
            ax.text(0.5, 0.5, 'POLITEKNIK UNGKU OMAR', transform=ax.transAxes, 
                    fontsize=40, color='gray', alpha=0.05, ha='center', va='center', rotation=30)

            # Plot Poligon
            df_poly = pd.concat([df, df.iloc[[0]]], ignore_index=True)
            ax.plot(df_poly['E'], df_poly['N'], marker='o', linestyle='-', color='b', zorder=2)
            ax.fill(df_poly['E'], df_poly['N'], alpha=0.15, color='skyblue', zorder=1)

            # Label Stesen
            for i in range(len(df)):
                curr_x, curr_y = df['E'].iloc[i], df['N'].iloc[i]
                dx, dy = curr_x - centroid_x, curr_y - centroid_y
                mag = math.sqrt(dx**2 + dy**2)
                offset = 0.6
                ax.text(curr_x + (dx/mag)*offset, curr_y + (dy/mag)*offset, 
                        str(df['STN'].iloc[i] if 'STN' in df.columns else i+1), 
                        fontsize=12, fontweight='bold', color='red', ha='center', va='center')

                # Kira Bearing & Jarak
                p1, p2 = df.iloc[i], df.iloc[(i + 1) % len(df)]
                de, dn = p2['E']-p1['E'], p2['N']-p1['N']
                dist = math.sqrt(de**2 + dn**2)
                angle = math.degrees(math.atan2(de, dn))
                if angle < 0: angle += 360
                
                # Laraskan sudut teks supaya mudah dibaca
                text_angle = math.degrees(math.atan2(dn, de))
                if text_angle > 90: text_angle -= 180
                elif text_angle < -90: text_angle += 180
                
                mid_e, mid_n = (p1['E']+p2['E'])/2, (p1['N']+p2['N'])/2
                ax.text(mid_e, mid_n, f"{decimal_to_dms(angle)}\n{dist:.3f}m", 
                        color='darkgreen', fontsize=8, fontweight='bold',
                        ha='center', va='center', rotation=text_angle,
                        bbox=dict(facecolor='white', alpha=0.8, lw=0))

            # Papar Luas di Tengah
            ax.text(centroid_x, centroid_y, f"LUAS:\n{area:.3f} m²", 
                    ha='center', va='center', fontsize=12, fontweight='bold',
                    bbox=dict(facecolor='yellow', alpha=0.7, edgecolor='black', boxstyle='round'))

            ax.set_aspect('equal')
            ax.grid(True, linestyle=':', alpha=0.4)
            st.pyplot(fig)
            st.success(f"Analisis Selesai. Luas: {area:.3f} m²")
            
    else:
        st.error("Format CSV salah! Pastikan ada kolom 'E' dan 'N'.")
