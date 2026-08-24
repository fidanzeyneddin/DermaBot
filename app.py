import streamlit as st
from foundry_local_sdk import FoundryLocalManager, Configuration
import chromadb
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
# 2. SİSTEMİ VE MODELİ HAZIRLAMA (ÖNBELLEKLİ)
# ==========================================
@st.cache_resource(show_spinner="Asistan Hazırlanıyor... Lütfen bekleyin.")
def sistemi_hazirla():
    """Veritabanını ve yerel dil modelini (LLM) bir kere yükleyip önbelleğe alır."""
    # Vektör veritabanına bağlan
    chroma_client = chromadb.PersistentClient(path="./rag_veritabani")
    collection = chroma_client.get_collection(name="makyaj_rehberi")
    
    # Foundry Local Yöneticisini başlat
    try:
        config = Configuration(app_name="GuzellikAsistani")
        manager = FoundryLocalManager(config)
    except Exception:
        manager = FoundryLocalManager._instance
    
    # Qwen 1.5B modelini bul ve belleğe yükle
    model = None
    for m in manager.catalog.list_models():
        if "qwen2.5-1.5b-instruct" in getattr(m, 'id', '').lower() or "qwen2.5-1.5b-instruct" in getattr(m, 'name', '').lower():
            model = m
            break
            
    if model is None:
        raise Exception("Eyvah! 1.5B modeli katalogda bulunamadı.")
        
    if not model.is_loaded:
        try:
            if hasattr(model, 'download'): model.download()
            elif hasattr(manager.catalog, 'download_model'): manager.catalog.download_model(model.id)
        except: pass
        model.load()
        
    try: manager.start_web_service()
    except Exception: pass
        
    return collection, manager, model

# Uygulama başlarken sistemi kur
collection, manager, model = sistemi_hazirla()

# Kapanışta servisi durdurarak kaynak sızıntısını önle
def servisi_kapat():
    try: manager.stop_web_service()
    except: pass
atexit.register(servisi_kapat)

# ==========================================
# 3. SOHBET GEÇMİŞİ (MEMORY)
# ==========================================
if "mesajlar" not in st.session_state:
    st.session_state.mesajlar = []

# Eski mesajları arayüze tekrar bas
for mesaj in st.session_state.mesajlar:
    with st.chat_message(mesaj["role"]):
        st.markdown(mesaj["content"])

# ==========================================
# 4. KULLANICI ETKİLEŞİMİ VE RAG (RETRIEVAL-AUGMENTED GENERATION)
# ==========================================
if soru := st.chat_input("Rehbere bir soru sor (Örn: Yağlı ciltler ne kullanmalı?)..."):
    
    # Kullanıcının sorusunu kaydet ve ekranda göster
    st.session_state.mesajlar.append({"role": "user", "content": soru})
    with st.chat_message("user"):
        st.markdown(soru)

    with st.chat_message("assistant"):
        cevap_alani = st.empty()
        
        with st.spinner("🔍 Rehber taranıyor ve cevap üretiliyor..."):
            try:
                client = model.get_chat_client()
                
                # ADIM 1: GETİRME (RETRIEVAL)
                # Veritabanından soruyla en çok eşleşen 3 paragrafı bul
                sonuclar = collection.query(query_texts=[soru], n_results=3)
                bulunan_metinler = sonuclar['documents'][0]
                baglam_metni = "\n\n---\n\n".join(bulunan_metinler)
                
                # ADIM 2: SİSTEM MESAJI (İngilizce Komut, Türkçe Çıktı)
                sistem_mesaji = f"""You are a strict data extraction assistant.
TASK: Answer the user's question using ONLY the provided TEXT.
RULES:
1. Extract the exact sentences from the TEXT. Do not generate new information.
2. If the TEXT does not explicitly contain the answer, you MUST reply ONLY with this exact Turkish phrase: "Maalesef rehberimde bu konuya dair net bir bilgi bulunmuyor."
3. Always respond in Turkish.

TEXT:
{baglam_metni}"""
                
                # ADIM 3: ÜRETİM (GENERATION)
                # LLM'e soruyu ve bağlamı gönder, cevabı al
                response = client.complete_chat(
                    messages=[
                        {"role": "system", "content": sistem_mesaji},
                        {"role": "user", "content": soru}
                    ]
                )
                
                # Gelen cevabı güvenli bir şekilde formatla
                if hasattr(response, 'choices'): cevap = response.choices[0].message.content
                elif hasattr(response, 'message'): cevap = response.message.content
                elif hasattr(response, 'content'): cevap = response.content
                else: cevap = str(response)
                
                # Cevabı ekrana bas ve geçmişe kaydet
                cevap_alani.markdown(cevap)
                st.session_state.mesajlar.append({"role": "assistant", "content": cevap})
                
            except Exception as e:
                st.warning(f"Bir hata oluştu: {e}")