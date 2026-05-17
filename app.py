import streamlit as st
from openai import OpenAI

# Setup Tampilan
st.set_page_config(page_title="AI IT Support Pro", page_icon="🤖")
st.title("🤖 Enterprise IT Ticket Solver (AI Powered)")

# Sidebar untuk API Key (Cara aman agar kunci tidak tersebar)
with st.sidebar:
    st.header("Pengaturan AI")
    api_key = st.text_input("Masukkan OpenAI API Key Anda:", type="password")
    st.info("AI ini menggunakan model GPT-4o untuk memahami keluhan Anda.")

# Input Tiket
ticket_input = st.text_area("Jelaskan masalah IT Anda secara detail:", 
                            placeholder="Contoh: Saya tidak bisa masuk ke email sejak pagi tadi, muncul error 404.")

if st.button("Proses dengan AI"):
    if not api_key:
        st.warning("Mohon masukkan API Key di sebelah kiri terlebih dahulu.")
    elif not ticket_input:
        st.warning("Silakan ketik keluhan Anda.")
    else:
        try:
            # Menghubungkan ke OpenAI
            client = OpenAI(api_key=api_key)
            
            with st.spinner('AI sedang berpikir cerdas...'):
                # Membuat perintah (Prompt) untuk AI
                response = client.chat.completions.create(
                    model="gpt-4o-mini", # Model yang cepat dan murah
                    messages=[
                        {"role": "system", "content": "Kamu adalah admin IT Support profesional. Klasifikasikan tiket menjadi (Network, Hardware, Software, atau Access). Berikan solusi singkat dan tentukan prioritasnya (Low, Medium, High)."},
                        {"role": "user", "content": ticket_input}
                    ]
                )
                
                # Mengambil jawaban dari AI
                ai_answer = response.choices[0].message.content
                
                st.success("Analisis AI Selesai!")
                st.markdown("### 📋 Hasil Analisis & Solusi:")
                st.write(ai_answer)

        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")