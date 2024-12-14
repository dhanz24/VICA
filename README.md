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

Aplikasi Backend akan berjalan pada `http://0.0.0.0:8000`.

4. Masuk ke direktori Frontend:
'''bash
cd frontend/VICA
'''

5. Install dependencies frontend yang dibutuhkan
'''bash
npm install
'''

6. Jalankan Frontend dengan perintah
'''bash
npm run dev
'''

Aplikasi Frontend akan berjalan pada http://localhost:5173/