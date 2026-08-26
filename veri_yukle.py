import sqlite3
import json
from foundry_local_sdk import FoundryLocalManager, Configuration

def veritabani_olustur():
    conn = sqlite3.connect("rag_veritabani.sqlite")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            embedding TEXT
        )
    ''')
    cursor.execute('DELETE FROM documents') # Kodu tekrar çalıştırırsan veriler çiftlenmesin diye
    conn.commit()
    return conn, cursor

def metni_parcala(dosya_yolu):
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        metin = f.read()
    
    # Paragraflara ayır
    parcalar = metin.split("\n\n")
    return [p.strip() for p in parcalar if len(p.strip()) > 10]

def main():
    print("Veritabanı tablosu oluşturuluyor...")
    conn, cursor = veritabani_olustur()
    
    print("Foundry Local başlatılıyor...")
    try:
        config = Configuration(app_name="DermabotIngestion")
        FoundryLocalManager.initialize(config)
    except Exception:
        pass
        
    manager = FoundryLocalManager.instance
    
    # Sadece Embedding modelini bul ve yükle
    embedding_model = None
    for m in manager.catalog.list_models():
        if "embedding" in getattr(m, 'id', '').lower():
            embedding_model = m
            break
            
    if not embedding_model.is_loaded:
        try: embedding_model.download()
        except: pass
        embedding_model.load()
    
    try: manager.start_web_service()
    except Exception: pass
    
    embedding_client = embedding_model.get_embedding_client()
    
    print("Rehber okunuyor ve vektörlere dönüştürülüyor...")
    metin_parcalari = metni_parcala("makeup.txt")
    
    for i, paragraf in enumerate(metin_parcalari):
        print(f"Parça {i+1}/{len(metin_parcalari)} işleniyor...")
        # Metni vektöre çevir
        response = embedding_client.generate_embedding(paragraf)
        vektor = response.data[0].embedding
        
        # Vektörü SQLite'a kaydet
        vektor_json = json.dumps(vektor)
        cursor.execute('INSERT INTO documents (content, embedding) VALUES (?, ?)', (paragraf, vektor_json))
        
    conn.commit()
    conn.close()
    
    try: manager.stop_web_service()
    except: pass
    
    print("Harika! Veritabanı başarıyla oluşturuldu ve veriler kaydedildi.")

if __name__ == "__main__":
    main()