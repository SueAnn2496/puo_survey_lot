import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import math
from PIL import Image

# 1. KONFIGURASI HALAMAN & KATA LALUAN
st.set_page_config(page_title="PUO Surveying Tool", layout="centered")

def check_password():
    """Memulangkan True jika pengguna memasukkan kata laluan yang betul."""
    if "password_correct" not in st.session_state:
        st.subheader("🔑 Sila Log Masuk")
        password = st.text_input("Masukkan Kata Laluan", type="password")
        if st.button("Log Masuk"):
            if password == "admin123":
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Kata laluan salah!")
        return False
    return True

if check_password():
    # --- LOGO KEKAL (Hardcoded) ---
    # Saya gunakan URL logo PUO secara terus supaya ia sentiasa ada
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
    uploaded_data = st.file_uploader("Muat naik fail CSV Koordinat (STN, E, N)", type="csv")

    if uploaded_data is not None:
        df = pd.read_csv(uploaded_data)
        
        if 'E' in df.columns and 'N' in df.columns:
            x = df['E
