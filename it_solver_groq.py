import os
import io
import time
import json
import string
import random
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv

# Konfigurasi Firebase NoSQL
import firebase_admin
from firebase_admin import credentials, firestore

# Konfigurasi AI & RAG
from groq import Groq
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not firebase_admin._apps:
    try:
        if "firebase_json" in st.secrets:
            firebase_secrets = json.loads(st.secrets["firebase_json"])
            cred = credentials.Certificate(firebase_secrets)
        else:
            cred = credentials.Certificate("credentials-firebase.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Gagal memuat kunci Firebase. Error: {e}")

db = firestore.client()

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

st.set_page_config(page_title="Optima Resolve", page_icon="🛡️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0a0e14;
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
    }
 
    [data-testid="stHeader"], .stAppHeader, [data-testid="stStatusWidget"], footer {
        visibility: hidden !important; display: none !important;
    }
    
    .block-container {padding-top: 1rem !important; padding-bottom: 120px !important;}
    
    div[data-testid="InputInstructions"] { visibility: hidden !important; display: none !important; }
    
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

def generate_sequential_id():
    prefix = "OPT-"
    try:
        tickets_ref = db.collection('rekap_tiket')
        query = tickets_ref.order_by('Waktu', direction=firestore.Query.DESCENDING).limit(1).stream()
        
        last_id_string = None
        for doc in query:
            last_id_string = doc.to_dict().get('ID Tiket')
            
        if last_id_string:
            last_number = int(last_id_string.replace(prefix, ""))
            next_number = last_number + 1
        else:
            next_number = 1
    except Exception as e:
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
    "123456": {"pass": "testing123", "nama": "Public", "divisi": "Finance", "telepon": "0856-777-888"},
    "11223": {"pass": "honda123", "nama": "Andi Pratama", "divisi": "IT", "telepon": "0811-222-333"}
}

if st.session_state.page == "LOGIN":
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form", border=True):
            st.markdown("<h2 style='text-align: center; color: white;'>🛡️ Optima Resolve</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #8b949e; margin-bottom: 30px;'>Enterprise SSO Login Gateway</p>", unsafe_allow_html=True)
            
            nip_input = st.text_input("NIP / Employee ID")
            pass_input = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Masuk / Sign In", use_container_width=True, type="primary")
            st.markdown("<p style='text-align: center; color: #8b949e; margin-top: 15px; font-size: 13px;'>💡 Silahkan Login: NIP 123456 | Password testing123</p>", unsafe_allow_html=True)
            
            if submitted:
                if nip_input == "Admin" and pass_input == "william123":
                    st.session_state.page = "ADMIN"
                    st.rerun()
                elif nip_input in DATABASE_KARYAWAN and DATABASE_KARYAWAN[nip_input]["pass"] == pass_input:
                    st.session_state.user_data = DATABASE_KARYAWAN[nip_input]
                    st.session_state.user_data['nip'] = nip_input
                    st.session_state.page = "FORM_TIKET"
                    st.rerun()
                else:
                    st.error("❌ Login Gagal. NIP atau Password tidak terdaftar di sistem HRD.")

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
        
        st.markdown("#### 📸 Lampirkan Foto Error / Bukti Kendala")
        foto_awal = st.file_uploader("Pilih foto agar langsung terbaca admin bersama keluhan", type=['png', 'jpg', 'jpeg'])
        
        submitted = st.form_submit_button("🚀 Submit & Hubungkan ke Optima AI", type="primary")
        
        if submitted:
            if kendala == "":
                st.warning("⚠️ Deskripsi Kendala wajib diisi!")
            else:
                nama_file_foto = "Tidak ada lampiran"
                if foto_awal:
                    os.makedirs("attachments", exist_ok=True)
                    nama_file_foto = f"{st.session_state.ticket_id}_{foto_awal.name}"
                    filepath = f"attachments/{nama_file_foto}"
                    with open(filepath, "wb") as f: 
                        f.write(foto_awal.getbuffer())
                
                st.session_state.user_data['kendala_awal'] = kendala
                st.session_state.user_data['lampiran_awal'] = nama_file_foto
                st.session_state.first_prompt_pending = True
                st.session_state.page = "CHAT_CONSOLE"
                st.rerun()
    
    if st.button("⬅️ Kembali ke Login"): logout()

elif st.session_state.page == "CHAT_CONSOLE":
    st.markdown("## 🛡️ RAG-Powered Intelligent IT Service Desk")
    st.markdown(f'<p style="color: #8b949e; margin-top: -10px;">Hi, {st.session_state.user_data["nama"]} ({st.session_state.user_data["divisi"]}) | Optima Console v4.0</p>', unsafe_allow_html=True)
    
    col_chat, col_info = st.columns([2.5, 1])

    with col_info:
        with st.container(border=True):
            st.markdown("### ⚙️ Optima Engine Status")
            st.markdown('<p class="watermark">Powered by Optima Resolve Core</p>', unsafe_allow_html=True)
            
            info_placeholder = st.empty()
            def render_info():
                info_placeholder.empty()
                waktu_wib = datetime.utcnow() + timedelta(hours=7)
                teks_info = f"""
                **ID TIKET:** `{st.session_state.ticket_id}`  
                **STATUS:** {st.session_state.ticket_status}  
                **PRIORITAS:** {st.session_state.ticket_priority}  
                **TANGGAL:** {waktu_wib.strftime('%d %B %Y')}
                """
                info_placeholder.info(teks_info)
            render_info()
            if st.button("Tutup Tiket & Keluar", type="secondary", use_container_width=True):
                logout()

    with col_chat:
        with st.container(height=550, border=True):
            with st.expander("📸 Upload Foto Tambahan"):
                st.caption("Gunakan ini jika AI meminta screenshot tambahan saat obrolan berlangsung.")
                foto_kendala = st.file_uploader("Pilih Foto Tambahan", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed", key=f"upload_{st.session_state.uploader_key}")
                if foto_kendala:
                    st.image(foto_kendala, width=200)
                    st.info("💡 Foto tambahan siap dikirim.")
            st.markdown("---")
            
            if st.session_state.first_prompt_pending:
                keluhan_awal = st.session_state.user_data['kendala_awal']
                lampiran_awal = st.session_state.user_data.get('lampiran_awal', 'Tidak ada lampiran')
                
                img_path = None
                if lampiran_awal != "Tidak ada lampiran":
                    img_path = f"attachments/{lampiran_awal}"
                    
                st.session_state.messages.append({"role": "user", "content": keluhan_awal, "image_path": img_path})
                
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
                
                # SET WAKTU AWAL & KIRIM KE FIREBASE DENGAN .SET() AGAR HANYA 1 BARIS
                ud = st.session_state.user_data
                st.session_state.waktu_awal = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
                
                db.collection('rekap_tiket').document(st.session_state.ticket_id).set({
                    'Waktu': st.session_state.waktu_awal,
                    'ID Tiket': st.session_state.ticket_id,
                    'NIP': ud['nip'],
                    'Nama': ud['nama'],
                    'Divisi': ud['divisi'],
                    'Telepon': ud['telepon'],
                    'Kendala': f"USER:\n{keluhan_awal}",
                    'Solusi': f"AI:\n{full_response}",
                    'Lampiran': lampiran_awal
                })
                    
                st.session_state.ticket_status = "Selesai (AI) ✅"
                render_info()
                st.rerun()

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if message.get("image_path"): st.image(message["image_path"], width=300)
                    st.markdown(message["content"])

        if prompt_input := st.chat_input("Ketik pesan balasan di sini... (Shift + Enter untuk baris baru)"):
            filepath = None
            nama_file_foto = "Tidak ada lampiran"
            
            if foto_kendala:
                os.makedirs("attachments", exist_ok=True)
                nama_file_foto = f"{st.session_state.ticket_id}_{foto_kendala.name}"
                filepath = f"attachments/{nama_file_foto}"
                with open(filepath, "wb") as f: f.write(foto_kendala.getbuffer())
                st.session_state.uploader_key += 1
                teks_untuk_db = f"[📸 FOTO TAMBAHAN] {prompt_input}"
            else:
                teks_untuk_db = prompt_input
                
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
                    
                    # GABUNGKAN SELURUH CHAT UNTUK DITIMPA KE BARIS FIREBASE YANG SAMA
                    ud = st.session_state.user_data
                    wkt_simpan = st.session_state.get('waktu_awal', (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S"))
                    
                    semua_kendala = "\n\n---\n\n".join([f"USER:\n{m['content']}" for m in st.session_state.messages if m["role"] == "user"])
                    semua_solusi = "\n\n---\n\n".join([f"AI:\n{m['content']}" for m in st.session_state.messages if m["role"] == "assistant"])
                    foto_final = nama_file_foto if nama_file_foto != "Tidak ada lampiran" else st.session_state.user_data.get('lampiran_awal', 'Tidak ada lampiran')

                    db.collection('rekap_tiket').document(st.session_state.ticket_id).set({
                        'Waktu': wkt_simpan,
                        'ID Tiket': st.session_state.ticket_id,
                        'NIP': ud['nip'],
                        'Nama': ud['nama'],
                        'Divisi': ud['divisi'],
                        'Telepon': ud['telepon'],
                        'Kendala': semua_kendala,
                        'Solusi': semua_solusi,
                        'Lampiran': foto_final
                    })

                    st.session_state.ticket_status = "Selesai (AI) ✅"
                    render_info()
                    if filepath: st.rerun()
                except Exception as e:
                    st.error("Koneksi Error. Silakan coba lagi.")

elif st.session_state.page == "ADMIN":
    st.markdown("## 🛠️ OPTIMA ANALYTICS")
    if st.button("Keluar dari Dashboard", type="primary"):
        logout()
    
    with st.container(border=True):
        try:
            tickets_ref = db.collection('rekap_tiket')
            docs = tickets_ref.stream()
            
            data_list = []
            for doc in docs:
                data_list.append(doc.to_dict())
                
            if len(data_list) > 0:
                df = pd.DataFrame(data_list)
                df = df[['Waktu', 'ID Tiket', 'NIP', 'Nama', 'Divisi', 'Telepon', 'Kendala', 'Solusi', 'Lampiran']]
                df = df.sort_values(by='Waktu', ascending=True)
            else:
                df = pd.DataFrame(columns=['Waktu', 'ID Tiket', 'NIP', 'Nama', 'Divisi', 'Telepon', 'Kendala', 'Solusi', 'Lampiran'])

            if not df.empty:
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
                    div_count = df['Divisi'].value_counts().reset_index()
                    div_count.columns = ['Divisi', 'Jumlah']
                    fig_pie = px.pie(div_count, values='Jumlah', names='Divisi', hole=0.4, template='plotly_dark')
                    fig_pie.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", font_color="#e0e0e0")
                    st.plotly_chart(fig_pie, use_container_width=True)

                st.markdown("#### 📋 Database Log Enterprise")
                df_bersih = df.drop(columns=['Tanggal'], errors='ignore')
                html_table = df_bersih.to_html(index=False, escape=False)

                st.markdown(f"""
                <div style="overflow-x: auto;">
                    <style>
                        .custom-table {{ width: 100%; border-collapse: collapse; color: #e0e0e0; font-size: 13px; }}
                        .custom-table th {{ background-color: #21262d; padding: 12px; text-align: left; border: 1px solid #30363d; color: #58a6ff; }}
                        .custom-table td {{ padding: 12px; border: 1px solid #30363d; white-space: normal !important; word-break: break-word !important; vertical-align: top; }}
                        .custom-table tr:nth-child(even) {{ background-color: rgba(255, 255, 255, 0.02); }}
                    </style>
                    <div class="custom-table">
                        {html_table}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("#### 🔍 Inspektur Detail & Bukti Foto Tiket")
                
                list_tiket = df['ID Tiket'].dropna().unique()
                selected_ticket = st.selectbox("Pilih ID Tiket untuk verifikasi bukti foto laporan:", list_tiket)
                
                if selected_ticket:
                    tiket_rows = df[df['ID Tiket'] == selected_ticket]
                    tiket_row_awal = tiket_rows.iloc[0]
                    
                    foto_rows = tiket_rows[tiket_rows['Lampiran'] != "Tidak ada lampiran"]
                    if not foto_rows.empty:
                        nama_foto = foto_rows.iloc[-1]['Lampiran']
                    else:
                        nama_foto = "Tidak ada lampiran"
                        
                    col_det1, col_det2 = st.columns([1.8, 1.2])
                    
                    with col_det1:
                        st.write(f"👤 **Pelapor:** {tiket_row_awal['Nama']} ({tiket_row_awal['Divisi']}) — Ext: {tiket_row_awal['Telepon']}")
                        st.write(f"📅 **Waktu Pengajuan:** {tiket_row_awal['Waktu']}")
                        st.info(f"📌 **Deskripsi Kendala:**\n\n{tiket_row_awal['Kendala']}")
                        st.success(f"🤖 **Solusi AI Terkirim:**\n\n{tiket_row_awal['Solusi']}")
                        
                    with col_det2:
                        st.write("🖼️ **Bukti Screenshot Lampiran:**")
                        path_foto = f"attachments/{nama_foto}"
                        
                        if nama_foto != "Tidak ada lampiran" and os.path.exists(path_foto):
                            st.image(path_foto, caption=f"Bukti Lampiran Tiket {selected_ticket}", use_container_width=True)
                        else:
                            st.warning("⚠️ Tiket ini diselesaikan tanpa ada lampiran foto.")
                
                st.markdown("---")
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
                    for col_num, value in enumerate(df.drop(columns=['Tanggal'], errors='ignore').columns):
                        worksheet.write(0, col_num, value, header_format)

                st.download_button(
                    label="📥 Download Laporan Optima Full (.xlsx)",
                    data=output.getvalue(),
                    file_name="Laporan_Optima_Resolve.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("📊 Database Firebase Anda saat ini masih kosong. Silakan masuk sebagai user dan buat tiket pertama Anda untuk mengujinya!")
                
        except Exception as e:
            st.error(f"Gagal mengambil data dari Firebase. Pastikan koneksi internet stabil. Detail: {e}")

st.markdown("""
<div class="custom-footer">
    © 2026 IT Division | Optima Resolve Enterprise Identity Management
</div>
""", unsafe_allow_html=True)