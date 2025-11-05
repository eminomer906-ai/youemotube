# 1. Temel imaj olarak Python 3.11 kullan
FROM python:3.11-slim

# 2. Çalışma dizini oluştur
WORKDIR /app

# 3. Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Tüm proje dosyalarını kopyala
COPY . .

# 5. 8080 portunu aç
EXPOSE 8080

# 6. Uygulamayı başlat
CMD ["python", "app.py"]
