# Optima Resolve — Enterprise IT Support Automation & Solver Platform

An advanced, AI-powered Enterprise IT Helpdesk solution utilizing **Retrieval-Augmented Generation (RAG)** architecture to automate Level-1 support, streamline ticket classification, and deliver instant, context-aware technical resolutions.

## 📌 Executive Summary

Dalam lingkungan korporat skala besar, efisiensi operasional divisi IT dipengaruhi oleh tingginya volume tiket berulang (Level-1 Issues) seperti kendala login, konfigurasi printer, hingga kegagalan sistem lokal. **Optima Resolve** hadir sebagai solusi berbasis kecerdasan buatan (AI) yang menjembatani kesenjangan antara kebutuhan pengguna atas resolusi cepat dan ketersediaan kapasitas tim IT Helpdesk. 

Sistem ini mentransformasi operasional IT konvensional dari yang bersifat reaktif menjadi proaktif melalui gerbang *Self-Service* cerdas yang terintegrasi.

---

## 🚀 Fitur Utama & Kapabilitas Sistem

### 1. Enterprise SSO Login Gateway (Mocked Identity Management)
* **Secure Access:** Menjamin bahwa portal hanya dapat diakses oleh personel internal perusahaan menggunakan NIP (Employee ID) dan kredensial yang tervalidasi.
* **Audit Trail Integration:** Mempersiapkan landasan sistem untuk integrasi manajemen identitas (*Identity Provider*) guna melacak riwayat pelaporan secara akurat.

### 2. AI-Powered Technical Self-Service
* **Natural Language Processing (NLP):** Karyawan dapat melaporkan kendala teknis menggunakan bahasa sehari-hari tanpa perlu memahami terminologi IT yang kaku.
* **Instant Expert Resolution:** AI bertindak sebagai teknisi virtual 24/7, memberikan panduan pemecahan masalah (*step-by-step troubleshooting*) secara instan tanpa perlu menunggu antrean manual tim IT.

### 3. Automated Ticket Classification
* **Smart Triaging:** Sistem secara otomatis mengklasifikasikan urgensi, kategori, dan divisi terkait dari setiap keluhan yang masuk.

---

## 🛡️ Arsitektur RAG & Keamanan Data (Data Security)

Optima Resolve dibangun dengan memprioritaskan keamanan informasi korporat (*Corporate Data Governance*) melalui implementasi **Retrieval-Augmented Generation (RAG)**:

* **Context Isolation (Data Terisolasi):** AI tidak memberikan jawaban generik dari internet. Jawaban bersumber langsung dari dokumen regulasi internal perusahaan (`manual_it.txt`) yang diunggah secara terisolasi.
* **Privacy-First Architecture:** Kunci API eksternal disimpan dengan aman menggunakan enkripsi tingkat server (*Streamlit Cloud Secrets Environment*). File rahasia korporat `.env` dikonfigurasi dalam `.gitignore` untuk mencegah kebocoran kode ke publik.
* **No Data Leakage:** Dokumen internal perusahaan diproses secara *real-time* hanya sebagai konteks referensi prompt dan tidak digunakan untuk melatih (*training*) model LLM publik.

---

## 📈 Business Value & ROI untuk Perusahaan

Implementasi Optima Resolve memberikan dampak bisnis yang terukur pada metrik efisiensi perusahaan:

| Metrik Operasional | Sistem Konvensional | Dengan Optima Resolve | Dampak Bisnis (Business Impact) |
| :--- | :--- | :--- | :--- |
| **MTTR (Mean Time to Resolution)** | Jam hingga Hari (tergantung antrean) | **< 30 Detik** (Instan) | Kepuasan karyawan meningkat, produktivitas kerja kembali pulih lebih cepat. |
| **Beban Kerja IT Helpdesk (L1)** | 70% - 80% waktu habis untuk isu berulang | **Terselesaikan otomatis** | Mengurangi kejenuhan kerja teknisi, mengalihkan fokus tim IT ke proyek strategis (Infrastruktur/Keamanan). |
| **Ketersediaan Layanan Support** | Terbatas pada jam kerja kantor | **24/7/365 Non-stop** | Mendukung operasional *multi-shift* dan cabang perusahaan di berbagai zona waktu secara efisien. |
| **Efisiensi Biaya Operasional** | Meningkat linier seiring bertambahnya karyawan | **Skalabilitas Tinggi tanpa Biaya Tambahan** | Menekan biaya operasional operasional *helpdesk* secara signifikan. |

---

## 🛠️ Tech Stack & Arsitektur Sistem

* **Core Language:** Python 3.10+
* **Framework UI:** Streamlit (Enterprise Web Interface)
* **AI Orchestration:** Retrieval-Augmented Generation (RAG) System
* **Large Language Model Inference:** Groq API (Llama Architecture) untuk pemrosesan super cepat berlatensi rendah.
* **Version Control:** Git & GitHub (Clean Portfolio Management)
