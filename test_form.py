import httpx

async def upload_file(file_path: str, user_id: str, chat_id: str, token: str):
    url = "http://localhost:8000/rag/knowledge/create"
    
    # Membaca file untuk dikirimkan
    with open(file_path, 'rb') as file:
        files = {
            'file': (file.name, file, 'image/png')
        }
        data = {
            'user_id': user_id,
            'chat_id': chat_id
        }

        headers = {
            'Authorization': f'Bearer {token}'
        }

        # Kirim POST request dengan data dan file
        async with httpx.AsyncClient() as client:
            print("Mengunggah file...")
            print("URL:", url)
            print("Data:", data)
            print("Headers:", headers)
            print("Files:", files)
            response = await client.post(url, files=files, data=data, headers=headers)

            # Menampilkan respons dari server
            if response.status_code == 200:
                print("File berhasil diunggah!")
                print("Response:", response.json())
            else:
                print(f"Upload gagal. Status Code: {response.status_code}")
                print("Response:", response.text)

# Memanggil fungsi di atas dengan parameter yang sesuai
if __name__ == "__main__":
    import asyncio
    # Ganti dengan path file yang sesuai
    file_path = 'public/logo_dark.png'  # Contoh path file
    user_id = '9eda4fa6-5e8c-4efc-b620-c12da9466143'
    chat_id = '0e724f1e-26fc-4e85-a5f7-f93fb963cb62'
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjllZGE0ZmE2LTVlOGMtNGVmYy1iNjIwLWMxMmRhOTQ2NjE0MyIsIm5hbWUiOiJhZG1pbiIsImV4cCI6MTczNDg3OTkyN30.o3A7zPX39WQ6dG7h_8PqmlGbbhrNnfYcwYZoeOFJMfw'

    # Jalankan fungsi secara asinkron
    asyncio.run(upload_file(file_path, user_id, chat_id, token))
