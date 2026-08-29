# 💄 Güzellik ve Cilt Bakım Asistanı (Yerel RAG Projesi)

**Geliştirici:** Fidan  Zeyneddin
**Kurum:** İstanbul Nişantaşı Üniversitesi  

## 📌 Projenin Amacı
Bu proje, kullanıcıların cilt bakımı ve makyaj teknikleri hakkındaki sorularını tamamen çevrimdışı ve güvenli bir şekilde yanıtlamak amacıyla geliştirilmiş yerel bir Q&A (Soru-Cevap) asistanıdır. Microsoft Foundry Local altyapısı kullanılarak inşa edilen bu asistan, internet bağlantısına ihtiyaç duymadan cihaz üzerinde çalışan bir dil modeli (LLM) ile RAG (Retrieval-Augmented Generation) mimarisini birleştirir.

## ⚙️ Nasıl Çalışır? (Sistem Mimarisi)
Proje, dışarıdan bilgi uydurmayı (halüsinasyon) önlemek için bilgileri yalnızca sağlanan yerel bir veri tabanından çeker.
1. **Veri Hazırlama (Ingestion):** `makeup.txt` içindeki cilt bakım rehberi, akıllı parçalara bölünerek **SQLite** veri tabanına işlenir.
2. **Bağlam Getirme (Retrieval):** Kullanıcı bir soru sorduğunda, sistem bu soruyu vektörel olarak arar, Numpy ile kosinüs benzerliği hesaplar ve veri tabanından en alakalı 3 paragrafı getirir.
3. **Cevap Üretme (Generation):** Bulunan metinler ve kullanıcının sorusu, Foundry Local üzerinden çalışan **Qwen 1.5B Instruct** modeline iletilir. Model, katı kurallarla belirlenmiş sistem mesajı sayesinde sadece bu bağlamı kullanarak cevap üretir.
4. **Kullanıcı Arayüzü:** Tüm bu süreç, Streamlit kullanılarak geliştirilen modern ve interaktif bir web arayüzünde gerçekleşir.

## 🚀 Kurulum ve Çalıştırma Talimatları
Projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin:

**1. Gerekli Kütüphaneleri Yükleyin:**
Terminalinizde aşağıdaki komutu çalıştırarak gereksinimleri kurun:
`pip install -r requirements.txt`

**2. Veri Tabanını Oluşturun:**
Rehberdeki bilgileri vektör veri tabanına yüklemek için veri yükleme betiğini bir kez çalıştırın:
`python veri_yukle.py`

**3. Asistanı Başlatın:**
Streamlit arayüzünü başlatmak için şu komutu girin:
`streamlit run app.py`

## 🛠️ Tasarım Kararları ve Sınırlamalar (Design Decisions & Limitations)
Sistem testleri ve değerlendirme aşamasında aşağıdaki teknik kararlar alınmıştır:
* **Model Seçimi:** Hızlı yanıt alabilmek için 1.5 milyar parametreli (1.5B) küçük bir model tercih edilmiştir.
* **Katı Bilgi Çıkarımı (Strict Extraction):** Küçük modellerin kendi kendine kelime veya yanlış bilgiler (halüsinasyon) üretmesini engellemek adına, Prompt Engineering (İstem Mühendisliği) uygulanmıştır. Sisteme, cevabı bulamadığında tahminde bulunmak yerine *"Maalesef rehberimde bu konuya dair net bir bilgi bulunmuyor."* demesi için kesin ve mekanik komutlar verilmiştir.
* **Kapsam Sınırı:** Asistan, yalnızca sağlanan metin belgesindeki (makeup.txt) bilgilere sadık kalacak şekilde tasarlanmıştır. Belgede yer almayan konulara yanıt vermez.
