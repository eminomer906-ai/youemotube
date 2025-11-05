# Temel imaj
FROM python:3.11-slim

# Çalışma dizini
WORKDIR /app

# Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm proje dosyalarını kopyala
COPY . .

# Port ayarı
EXPOSE 8080

# Flask çalıştırma
CMD ["python", "app.py"]
