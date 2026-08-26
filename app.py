import streamlit as st
from foundry_local_sdk import FoundryLocalManager, Configuration
import sqlite3
import json
import numpy as np
import atexit

# ==========================================
# 1. ARAYÜZ VE SAYFA TASARIMI
# ==========================================
st.set_page_config(page_title="Yerel RAG Asistanı", page_icon="💄", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');
    html, body, div, span, p, h1, h2, h3, label, input { font-family: 'Nunito', sans-serif; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("💄 Güzellik ve Cilt Bakım Asistanı")
st.markdown("Cilt bakımı ve makyaj rehberime bağlı olarak çalışır. Tamamen çevrimdışıdır!")

# ==========================================
# YARDIMCI FONKSİYONLAR
# ==========================================
def kosinus_benzerligi(vec1, vec2):
    dot_product = np.dot(vec1, vec2)
    norm_a = np.linalg.norm(vec1)
    norm_b = np.linalg.norm(vec2)
    return dot_product / (norm_a * norm_b)

def get_top_chunks(query, conn, embedding_client, k=3):
    # ÇÖZÜM 1: SDK'nın beklediği güncel ve doğru komut
    response = embedding_client.generate_embedding(query)
    query_embedding = response.data[0].embedding
    
    cursor = conn.cursor()
    cursor.execute("SELECT content, embedding FROM documents")
    kayitlar = cursor.fetchall()
    
    benzerlikler = []
    for icerik, vektor_json in kayitlar:
        vektor = json.loads(vektor_json)
        skor = kosinus_benzerligi(query_embedding, vektor)
        benzerlikler.append((skor, icerik))
        
    benzerlikler.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in benzerlikler[:k]]

# ==========================================
# 2. SİSTEMİ VE MODELLERİ HAZIRLAMA
# ==========================================
@st.cache_resource(show_spinner="Asistan Hazırlanıyor... Lütfen bekleyin.")
def sistemi_hazirla():
    conn = sqlite3.connect("rag_veritabani.sqlite", check_same_thread=False)
    
    # ÇÖZÜM 2: Doğru başlatma metodu (Instance hatasını çözer)
    try:
        config = Configuration(app_name="GuzellikAsistani")
        FoundryLocalManager.initialize(config)
    except Exception:
        pass # Zaten başlatılmışsa devam et
        
    manager = FoundryLocalManager.instance
    
    embedding_model = None
    chat_model = None
    
    for m in manager.catalog.list_models():
        model_id = getattr(m, 'id', '').lower()
        model_name = getattr(m, 'name', '').lower()
        
        if "embedding" in model_id or "embedding" in model_name:
            if embedding_model is None: 
                embedding_model = m
                
        if "qwen2.5-1.5b-instruct" in model_id or "qwen2.5-1.5b-instruct" in model_name:
            chat_model = m

    if embedding_model is None or chat_model is None:
        raise Exception("Gerekli modellerden biri veya her ikisi katalogda bulunamadı!")
        
    for model in [embedding_model, chat_model]:
        if not model.is_loaded:
            try:
                if hasattr(model, 'download'): model.download()
                elif hasattr(manager.catalog, 'download_model'): manager.catalog.download_model(model.id)
            except: pass
            model.load()
        
    try: manager.start_web_service()
    except Exception: pass
    
    emb_client = embedding_model.get_embedding_client()
    ch_client = chat_model.get_chat_client()
        
    return conn, manager, emb_client, ch_client

conn, manager, embedding_client, chat_client = sistemi_hazirla()

def servisi_kapat():
    try: 
        conn.close()
        manager.stop_web_service()
    except: pass
atexit.register(servisi_kapat)

# ==========================================
# 3. SOHBET GEÇMİŞİ
# ==========================================
if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

for mesaj in st.session_state.mesajlar:
    with st.chat_message(mesaj["role"]):
        st.markdown(mesaj["content"])

# ==========================================
# 4. KULLANICI ETKİLEŞİMİ VE RAG
# ==========================================
if soru := st.chat_input("Rehbere bir soru sor (Örn: Yağlı ciltler ne kullanmalı?)..."):
    
    st.session_state.mesajlar.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        
        with st.spinner("🔍 Rehber taranıyor ve cevap üretiliyor..."):
            try:
                bulunan_metinler = get_top_chunks(query=soru, conn=conn, embedding_client=embedding_client, k=3)
                baglam_metni = "\n\n---\n\n".join(bulunan_metinler)
                
                sistem_mesaji = f"""Aşağıdaki BAĞLAM metninde yazan bilgileri kullanarak soruyu yanıtla. Sadece BAĞLAM'daki cümleleri kullan.

BAĞLAM:
{baglam_metni}"""

                # Arka planda veritabanından hangi metinlerin geldiğini terminalde görmek için:
                print("\n\n=== LLM'E GİDEN BAĞLAM METNİ ===")
                print(baglam_metni)
                print("==================================\n\n")
                
                response = chat_client.complete_chat(
                    messages=[
                        {"role": "system", "content": sistem_mesaji},
                        {"role": "user", "content": soru}
                    ]
                )
                
                if hasattr(response, 'choices'): cevap = response.choices[0].message.content
                elif hasattr(response, 'message'): cevap = response.message.content
                elif hasattr(response, 'content'): cevap = response.content
                else: cevap = str(response)
                
                cevap_alani.markdown(cevap)
                st.session_state.mesajlar.append({"role": "assistant", "content": cevap})
                
            except Exception as e:
                st.warning(f"Bir hata oluştu: {e}")