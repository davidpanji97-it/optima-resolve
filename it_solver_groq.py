import os
import io
import csv
import time
import string
import random
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# Konfigurasi AI & RAG
from groq import Groq
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter

# ==========================================
# 1. INIT & CONFIGURATION
# ==========================================
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

@st.cache_resource
def prepare_knowledge_base():
    """Mempersiapkan RAG (Retrieval-Augmented Generation) Database"""
    loader = TextLoader("manual_it.txt")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return FAISS.from_documents(docs, embeddings)

vector_db = prepare_knowledge_base()

# ==========================================
# 2. UI/UX & STYLING (WHITE-LABEL)
# ==========================================
st.set_page_config(page_title="Optima Resolve", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0a0e14;
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Menghilangkan Jejak Streamlit */
    [data-testid="stHeader"], .stAppHeader, [data-testid="stStatusWidget"], footer {
        visibility: hidden !important; display: none !important;
    }
    
    /* Ruang aman di bawah layar */
    .block-container {padding-top: 1rem !important; padding-bottom: 120px !important;}
    
    /* Menghilangkan teks "Press Enter to apply" */
    div[data-testid="InputInstructions"] { visibility: hidden !important; display: none !important; }
    
    /* MENGHILANGKAN KOTAK NYASAR: Desain langsung ditempel ke kontainer bawaan Streamlit */
    div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(23, 28, 36, 0.8) !important;
        border: 1px solid #30363d !important;
        border-radius: 15px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8) !important;
    }
    
    .stChatMessage { 
        background-color: rgba(255, 255, 255, 0.03) !important; 
        border-radius: 10px; border: 1px solid #30363d;
    }
    
    /* Posisi kotak input melayang di bawah */
    div[data-testid="stChatInput"] { bottom: 45px !important; z-index: 1000 !important; }
    
    .custom-footer {
        position: fixed; bottom: 0; left: 0; right: 0; width: 100%;
        text-align: center; color: #58a6ff; font-size: 13px; font-family: 'JetBrains Mono', monospace;
        padding-bottom: 10px; background-color: #0a0e14; z-index: 999;
        border-top: 1px solid #30363d; padding-top: 10px;
    }
    .watermark { font-size: 10px; color: #58a6ff; opacity: 0.6; margin-top: -10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 3. SESSION STATE MANAGEMENT
# ==========================================
def generate_sequential_id():
    file_path = 'rekap_tiket_it.csv'
    prefix = "OPT-"
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        try:
            df_temp = pd.read_csv(file_path, names=['Waktu', 'ID Tiket', 'NIP', 'Nama', 'Divisi', 'Telepon', 'Kendala', 'Solusi', 'Lampiran'], engine='python')
            last_id_string = df_temp['ID Tiket'].dropna().iloc[-1]
            last_number = int(last_id_string.replace(prefix, ""))
            next_number = last_number + 1
        except:
            next_number = 1
    else:
        next_number = 1
    return f"{prefix}{next_number:05d}"

def logout():
    st.session_state.clear()
    st.rerun()

if "page" not in st.session_state: st.session_state.page = "LOGIN"
if "user_data" not in st.session_state: st.session_state.user_data = {}
if "ticket_id" not in st.session_state: st.session_state.ticket_id = generate_sequential_id()
if "messages" not in st.session_state: st.session_state.messages = []
if "ticket_status" not in st.session_state: st.session_state.ticket_status = "Menunggu Input ⏳"
if "ticket_priority" not in st.session_state: st.session_state.ticket_priority = "Belum Terdeteksi"
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "first_prompt_pending" not in st.session_state: st.session_state.first_prompt_pending = False

DATABASE_KARYAWAN = {
    "12345": {"pass": "yola123", "nama": "Yola Suryani", "divisi": "HR-Division", "telepon": "0812-333-444"},
    "123456": {"pass": "honda123", "nama": "Public", "divisi": "Finance", "telepon": "0856-777-888"},
    "11223": {"pass": "honda123", "nama": "Andi Pratama", "divisi": "IT", "telepon": "0811-222-333"}
}

# ==========================================
# 4. ROUTER: HALAMAN LOGIN
# ==========================================
if st.session_state.page == "LOGIN":
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form", border=True):
            st.markdown("<h2 style='text-align: center; color: white;'>🛡️ Optima Resolve</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #8b949e; margin-bottom: 30px;'>Enterprise SSO Login Gateway</p>", unsafe_allow_html=True)
            
            nip_input = st.text_input("NIP / Employee ID", placeholder="Masukkan NIP (Contoh: 12345)")
            pass_input = st.text_input("Password", type="password", placeholder="•••••••• (Contoh: honda123)")
            
            submitted = st.form_submit_button("Masuk / Sign In", use_container_width=True, type="primary")
            
            if submitted:
                if nip_input == "admin" and pass_input == "admin123":
                    st.session_state.page = "ADMIN"
                    st.rerun()
                elif nip_input in DATABASE_KARYAWAN and DATABASE_KARYAWAN[nip_input]["pass"] == pass_input:
                    st.session_state.user_data = DATABASE_KARYAWAN[nip_input]
                    st.session_state.user_data['nip'] = nip_input
                    st.session_state.page = "FORM_TIKET"
                    st.rerun()
                else:
                    st.error("❌ Login Gagal. NIP atau Password tidak terdaftar di sistem HRD.")

# ==========================================
# 5. ROUTER: FORMULIR TIKET
# ==========================================
elif st.session_state.page == "FORM_TIKET":
    st.markdown("## 📝 Buat Tiket Kendala Baru")
    st.caption(f"Logged in as: NIP {st.session_state.user_data.get('nip', '')}")
    
    with st.form("form_keluhan", border=True):
        st.markdown("#### Detail Pelapor (Terhubung dengan HRD)")
        colA, colB = st.columns(2)
        with colA:
            nama = st.text_input("Nama Lengkap", value=st.session_state.user_data.get('nama', ''), disabled=True)
            divisi = st.text_input("Divisi", value=st.session_state.user_data.get('divisi', ''), disabled=True)
        with colB:
            telepon = st.text_input("Nomor Telepon", value=st.session_state.user_data.get('telepon', ''), disabled=True)
        
        st.markdown("#### Deskripsi Masalah")
        kendala = st.text_area("Ceritakan kendala IT yang Anda alami secara detail...", height=100)
        
        submitted = st.form_submit_button("🚀 Submit & Hubungkan ke Optima AI", type="primary")
        
        if submitted:
            if kendala == "":
                st.warning("⚠️ Deskripsi Kendala wajib diisi!")
            else:
                st.session_state.user_data['kendala_awal'] = kendala
                st.session_state.first_prompt_pending = True
                st.session_state.page = "CHAT_CONSOLE"
                st.rerun()
    
    if st.button("⬅️ Kembali ke Login"): logout()

# ==========================================
# 6. ROUTER: AI CHAT CONSOLE
# ==========================================
elif st.session_state.page == "CHAT_CONSOLE":
    st.markdown("## 🛡️ RAG-Powered Intelligent IT Service Desk")
    st.markdown(f'<p style="color: #8b949e; margin-top: -10px;">Hi, {st.session_state.user_data["nama"]} ({st.session_state.user_data["divisi"]}) | Optima Console v3.0</p>', unsafe_allow_html=True)
    
    col_chat, col_info = st.columns([2.5, 1])

    # PANEL KANAN (INFO STATUS)
    with col_info:
        with st.container(border=True):
            st.markdown("### ⚙️ Optima Engine Status")
            st.markdown('<p class="watermark">Powered by Optima Resolve Core</p>', unsafe_allow_html=True)
            
            info_placeholder = st.empty()
            def render_info():
                info_placeholder.empty()
                teks_info = f"""
                **ID TIKET:** `{st.session_state.ticket_id}`  
                **STATUS:** {st.session_state.ticket_status}  
                **PRIORITAS:** {st.session_state.ticket_priority}  
                **TANGGAL:** {datetime.now().strftime('%d %B %Y')}
                """
                info_placeholder.info(teks_info)
            render_info()
            if st.button("Tutup Tiket & Keluar", type="secondary", use_container_width=True):
                logout()

    # PANEL KIRI (AREA CHAT AUTOFIT)
    with col_chat:
        # KUNCI AUTOFIT: height=550 akan membuat kotak chat memiliki scroll sendiri di dalam!
        with st.container(height=550, border=True):
            with st.expander("📸 Lampirkan Foto Error / Bukti Kendala (Opsional)"):
                st.caption("Screenshot kendala Anda akan dikirim bersama chat berikutnya.")
                foto_kendala = st.file_uploader("Pilih Foto", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed", key=f"upload_{st.session_state.uploader_key}")
                if foto_kendala:
                    st.image(foto_kendala, width=200)
                    st.info("💡 Foto siap dikirim.")
            st.markdown("---")
            
            if st.session_state.first_prompt_pending:
                keluhan_awal = st.session_state.user_data['kendala_awal']
                st.session_state.messages.append({"role": "user", "content": keluhan_awal, "image_path": None})
                
                if any(k in keluhan_awal.lower() for k in ['mati', 'rusak', 'terbakar', 'server', 'jaringan']):
                    st.session_state.ticket_priority = "High 🔴"
                elif any(k in keluhan_awal.lower() for k in ['lupa', 'password', 'lambat', 'lemot', 'printer']):
                    st.session_state.ticket_priority = "Medium 🟡"
                else:
                    st.session_state.ticket_priority = "Low 🟢"
                    
                st.session_state.ticket_status = "Scanning System ⚙️"
                render_info()
                
                relevant_docs = vector_db.similarity_search(keluhan_awal, k=1)
                client = Groq(api_key=api_key)
                system_prompt = f"Kamu adalah AI Service Desk Optima Resolve. Jawab LANGSUNG, RINGKAS, dan BENTUK POIN. KONTEKS INTERNAL: {relevant_docs[0].page_content}"
                
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": keluhan_awal}]
                )
                full_response = response.choices[0].message.content
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.first_prompt_pending = False
                
                with open('rekap_tiket_it.csv', mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    wkt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ud = st.session_state.user_data
                    writer.writerow([wkt, st.session_state.ticket_id, ud['nip'], ud['nama'], ud['divisi'], ud['telepon'], keluhan_awal, full_response, "Tidak ada lampiran"])
                    
                st.session_state.ticket_status = "Selesai (AI) ✅"
                render_info()
                st.rerun()

            # Menampilkan isi chat
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if message.get("image_path"): st.image(message["image_path"], width=300) 
                    st.markdown(message["content"])

        # Kotak input di luar area Autofit (tetap melayang dengan aman)
        if prompt_input := st.chat_input("Ketik pesan balasan di sini..."):
            filepath = None
            nama_file_foto = "Tidak ada lampiran"
            
            if foto_kendala:
                os.makedirs("attachments", exist_ok=True)
                nama_file_foto = f"{st.session_state.ticket_id}_{foto_kendala.name}"
                filepath = f"attachments/{nama_file_foto}"
                with open(filepath, "wb") as f: f.write(foto_kendala.getbuffer())
                st.session_state.uploader_key += 1
                teks_untuk_csv = f"[📸 FOTO TERLAMPIR] {prompt_input}"
            else:
                teks_untuk_csv = prompt_input
                
            st.session_state.ticket_status = "Scanning System ⚙️"
            render_info()
            
            st.session_state.messages.append({"role": "user", "content": prompt_input, "image_path": filepath})
            with st.chat_message("user"):
                if filepath: st.image(filepath, width=300)
                st.markdown(prompt_input)

            with st.chat_message("assistant"):
                try:
                    with st.spinner("Optima AI merespons..."):
                        relevant_docs = vector_db.similarity_search(prompt_input, k=1)
                        client = Groq(api_key=api_key)
                        hist = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-3:-1]])
                        sys_prompt = f"Kamu AI IT Support Optima Resolve. KONTEKS: {relevant_docs[0].page_content}. HISTORY: {hist}"
                        
                        response = client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": prompt_input}]
                        )
                        full_response = response.choices[0].message.content
                    
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

                    with open('rekap_tiket_it.csv', mode='a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        wkt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ud = st.session_state.user_data
                        writer.writerow([wkt, st.session_state.ticket_id, ud['nip'], ud['nama'], ud['divisi'], ud['telepon'], teks_untuk_csv, full_response, nama_file_foto])

                    st.session_state.ticket_status = "Selesai (AI) ✅"
                    render_info()
                    if filepath: st.rerun()
                except Exception as e:
                    st.error("Koneksi Error. Silakan coba lagi.")

# ==========================================
# 7. ROUTER: DASHBOARD ADMIN
# ==========================================
elif st.session_state.page == "ADMIN":
    st.markdown("## 🛠️ OPTIMA CENTRAL ANALYTICS")
    if st.button("Keluar dari Dashboard (Logout)", type="primary"):
        logout()
    
    with st.container(border=True):
        try:
            df = pd.read_csv('rekap_tiket_it.csv', names=['Waktu', 'ID Tiket', 'NIP', 'Nama', 'Divisi', 'Telepon', 'Kendala', 'Solusi', 'Lampiran'])
            
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.markdown("**📈 Tren Volume Tiket**")
                df['Tanggal'] = pd.to_datetime(df['Waktu'], errors='coerce').dt.date
                tiket_per_hari = df.groupby('Tanggal').size().reset_index(name='Jumlah')
                if not tiket_per_hari.empty:
                    fig_line = px.line(tiket_per_hari, x='Tanggal', y='Jumlah', markers=True, template='plotly_dark')
                    fig_line.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#e0e0e0")
                    st.plotly_chart(fig_line, use_container_width=True)
                
            with col_chart2:
                st.markdown("**📊 Masalah per Divisi**")
                if not df.empty:
                    div_count = df['Divisi'].value_counts().reset_index()
                    div_count.columns = ['Divisi', 'Jumlah']
                    fig_pie = px.pie(div_count, values='Jumlah', names='Divisi', hole=0.4, template='plotly_dark')
                    fig_pie.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e0e0e0")
                    st.plotly_chart(fig_pie, use_container_width=True)

            st.markdown("#### 📋 Database Log Enterprise")
            st.dataframe(df.drop(columns=['Tanggal'], errors='ignore'), use_container_width=True, hide_index=True, height=300)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.drop(columns=['Tanggal'], errors='ignore').to_excel(writer, index=False, sheet_name='Data_Optima')
                workbook = writer.book
                worksheet = writer.sheets['Data_Optima']
                wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'vcenter'})
                header_format = workbook.add_format({'bold': True, 'bg_color': '#30363d', 'font_color': 'white', 'border': 1})
                
                worksheet.set_column('A:B', 15, wrap_format) 
                worksheet.set_column('C:F', 15, wrap_format) 
                worksheet.set_column('G:H', 40, wrap_format) 
                worksheet.set_column('I:I', 20, wrap_format) 
                for col_num, value in enumerate(df.columns):
                    if value != 'Tanggal': worksheet.write(0, col_num, value, header_format)

            st.download_button(
                label="📥 Download Laporan Optima Full (.xlsx)",
                data=output.getvalue(),
                file_name="Laporan_Optima_Resolve.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except FileNotFoundError:
            st.warning("Database masih kosong.")

# ==========================================
# 8. FOOTER
# ==========================================
st.markdown("""
<div class="custom-footer">
    © 2026 IT Division | Optima Resolve Enterprise Identity Management
</div>
""", unsafe_allow_html=True)