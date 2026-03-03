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

# --- SISTEM DATABASE FAIL ---
PASSWORD_FILE = "user_config.json"

def load_password():
    """Membaca kata laluan dari fail. Jika tiada, guna default."""
    if os.path.exists(PASSWORD_FILE):
        with open(PASSWORD_FILE, "r") as f:
            data = json.load(f)
            return data.get("password", "admin123")
    return "admin123"

def save_password(new_pw):
    """Menyimpan kata laluan baharu ke dalam fail .json"""
    with open(PASSWORD_FILE, "w") as f:
        json.dump({"password": new_pw}, f)

# Muat kata laluan ke dalam session state pada permulaan
if "current_password" not in st.session_state:
    st.session_state.current_password = load_password()

# --- DATABASE PENGGUNA ---
USER_DB = {
    "1": "OOI SUE ANN",
    "2": "WONG YUEAN YI",
    "3": "CHAN BOON YEAH"
}

# --- FUNGSI DIALOG ---

@st.dialog("🔑 Tukar / Reset Kata Laluan")
def change_password_dialog(is_forgot=False):
    if is_forgot:
        st.info("Sila masukkan maklumat di bawah untuk menetapkan semula kata laluan anda.")
        check_id = st.text_input("Sahkan ID Pengguna:", key="verify_id")
    
    new_pw = st.text_input("Kata Laluan Baharu:", type="password", key="new_pw_input")
    conf_pw = st.text_input("Sahkan Kata Laluan Baharu:", type="password", key="conf_pw_input")
    
    if st.button("Simpan Kata Laluan", use_container_width=True):
        if is_forgot and check_id not in USER_DB:
            st.error("❌ ID Pengguna tidak sah!")
        elif new_pw == "" or conf_pw == "":
            st.warning("Sila isi semua ruangan!")
        elif new_pw == conf_pw:
            # SIMPAN KE FAIL DAN SESSION
            save_password(new_pw)
            st.session_state.current_password = new_pw
            st.success("✅ Kata laluan berjaya disimpan secara kekal!")
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
            
            if st.button("Log Masuk", use_container_width=True):
                # Sentiasa ambil password terkini dari fail untuk keselamatan
                stored_password = load_password()
                if input_id in USER_DB:
                    if password == stored_password:
                        st.session_state.password_correct = True
                        st.session_state.user_full_name = USER_DB[input_id]
                        st.rerun()
                    else:
                        st.error("❌ Kata laluan salah!")
                else:
                    st.error("❌ ID Pengguna tidak dijumpai!")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("❓ Lupa Kata Laluan?", use_container_width=True):
                change_password_dialog(is_forgot=True)
                
        return False
    return True

# --- MAIN APP FLOW ---

if check_password():
    # (Bahagian ini kekal sama seperti kod anda sebelum ini)
    if "login_notified" not in st.session_state:
        st.toast(f"✅ {st.session_state.user_full_name} Berjaya Log Masuk!", icon="🚀")
        st.session_state.login_notified = True

    # --- HEADER ---
    st.markdown(f"""
        <div style="background-color:#f8f9fa; padding:10px; border-radius:10px; border-left: 5px solid #007BFF;">
            <h1 style='margin-bottom:0; color:#1f1f1f;'>SISTEM SURVEY LOT</h1>
            <p style='color:gray; font-size:16px; margin-top:0;'>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        </div>
    """, unsafe_allow_html=True)

    # --- SIDEBAR & CONTENT ---
    st.sidebar.markdown(f"### Hai, {st.session_state.user_full_name}!")
    
    # ... (Tambahkan kod mapping anda di sini) ...

    # --- SIDEBAR BOTTOM ---
    st.sidebar.divider()
    if st.sidebar.button("🔑 Tukar Kata Laluan", use_container_width=True):
        change_password_dialog(is_forgot=False)
    
    if st.sidebar.button("🚪 Log Keluar", use_container_width=True):
        # Jangan gunakan clear() untuk semua jika anda mahu simpan data tertentu
        del st.session_state["password_correct"]
        st.rerun()
