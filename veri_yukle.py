import chromadb

# ChromaDB veritabanına bağlan
chroma_client = chromadb.PersistentClient(path="./rag_veritabani")

# Koleksiyonu sıfırdan oluştur (eski bozuk parçaları temizlemek için)
try:
    chroma_client.delete_collection(name="makyaj_rehberi")
except:
    pass

collection = chroma_client.create_collection(name="makyaj_rehberi")

# makeup.txt dosyasını oku ve başlıklarına/paragraflarına göre akıllıca böl
with open("makeup.txt", "r", encoding="utf-8") as f:
    icerik = f.read()

# Metni ana bölümlere ayırıyoruz ki arama yapıldığında nokta atışı gelsin
paragraflar = [p.strip() for p in icerik.split("\n\n") if p.strip()]

# Her bir paragrafı veritabanına ayrı birer parça (document) olarak kaydediyoruz
for i, paragraf in enumerate(paragraflar):
    collection.add(
        documents=[paragraf],
        ids=[f"paragraf_{i}"]
    )

print(f"🚀 BAŞARILI! {len(paragraflar)} adet detaylı paragraf veritabanına işlendi.")