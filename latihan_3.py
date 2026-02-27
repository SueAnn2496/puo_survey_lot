import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
from PIL import Image

# --- 1. CONFIG & PASSWORD ---
st.set_page_config(page_title="PUO Surveying Tool", layout="centered")

def check_password():
    """Memulangkan True jika pengguna memasukkan kata laluan yang betul."""
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>🔐 Sistem Geomatik PUO</h2>", unsafe_allow_html=True)
        password = st.text_input("Sila masukkan kata laluan untuk akses:", type="password")
        if st.button("Log Masuk"):
            if password == "admin123":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Kata laluan salah. Sila cuba lagi.")
        return False
    return True

# --- RUN APLIKASI JIKA PASSWORD BETUL ---
if check_password():
    # URL Logo PUO yang tetap
    logo_url = "https://upload.wikimedia.org/wikipedia/ms/thumb/b/b3/Logo_Politeknik_Ungku_Omar.png/200px-Logo_Politeknik_Ungku_Omar.png"

    # --- HEADER ---
    col_logo1, col_logo2 = st.columns([1, 2])
    with col_logo1:
        st.image(logo_url, width=150) 

    with col_logo2:
        st.markdown("""
            <div style='padding-top: 10px;'>
                <h2 style='margin-bottom: 0px; font-size: 22px;'>POLITEKNIK UNGKU OMAR</h2>
                <p style='font-size: 15px; color: gray;'>Jabatan Kejuruteraan Awam - Unit Geomatik</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    def decimal_to_dms(deg):
        d = int(deg)
        m = int((deg - d) * 60)
        s = (deg - d - m/60) * 3600
        return f"{d}°{m}'{s:.0f}\""

    st.write("### 🗺️ Penjana Poligon & Analisis Luas")
    
    # Panduan CSV
    with st.expander("ℹ️ Format Fail CSV"):
        st.write("Fail CSV mestilah mempunyai header: **STN, E, N**")
        st.code("STN,E,N\n1,100,100\n2,120,100\n3,120,120\n4,100,120")

    uploaded_data = st.file_uploader("Muat naik fail CSV Koordinat", type="csv")

    if uploaded_data is not None:
        df = pd.read_csv(uploaded_data)
        
        if 'E' in df.columns and 'N' in df.columns:
            x = df['E'].values
            y = df['N'].values
            # Shoelace Formula
            area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
            centroid_x = np.mean(x)
            centroid_y = np.mean(y)

            if st.button('🚀 Proses & Jana Grafik'):
                st.session_state.processed = True
                
            if st.session_state.get('processed', False):
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Watermark
                ax.text(0.5, 0.5, 'POLITEKNIK UNGKU OMAR', transform=ax.transAxes, 
                        fontsize=35, color='gray', alpha=0.05, ha='center', va='center', rotation=30)
