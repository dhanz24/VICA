# VICA - Virtual Intelligence Chatbot Assistant


## Cara Menjalankan Aplikasi

1. Install dependencies yang diperlukan dengan menjalankan perintah berikut:
  ```bash
  pip install -r requirements.txt
  ```
2. To use from pdf2image import convert_from_bytes, install poppler-utils (https://pdf2image.readthedocs.io/en/latest/installation.html)

3. Jalankan aplikasi dengan perintah berikut:
  ```bash
  uvicorn Backend.VICA.main:app --port 8000 --host 0.0.0.0 --reload
  ```

Aplikasi akan berjalan pada `http://0.0.0.0:8000`.

## Kontribusi

Kami menyambut kontribusi dari siapa saja. Silakan buat pull request atau laporkan masalah yang Anda temui.