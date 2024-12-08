import os
import sys
import uuid
import base64
import tempfile
import shutil
from typing import List, Any, Dict

import asyncio
from fastapi import UploadFile, HTTPException, status
from pydantic import BaseModel
from unstructured.partition.pdf import partition_pdf

import nltk
nltk.download("punkt_tab")
nltk.download('averaged_perceptron_tagger_eng')

from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams
from llama_index.core import (
    VectorStoreIndex,
    Settings,
    StorageContext,
    get_response_synthesizer,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.schema import Document
from llama_index.core.base.response.schema import Response

from Backend.VICA.apps.RAG.pdf import PDFService
from Backend.VICA.config import QDRANT_URL, QDRANT_API_KEY

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from VICA.apps.VICA.models.user import Users
from VICA.apps.VICA.models.chat import Chats

####################
# MultiModalRAGService
####################

import logging

class MultiModalRAGService:
    def __init__(
        self,
        llm,
        embed_model,
        rerank_service,
        pdf_service: PDFService,
    ) -> None:
        self.llm = llm
        self.embed_model = embed_model
        self.rerank_service = rerank_service
        self.pdf_service = pdf_service
        self.embedding_size = self._get_embedding_size()
        self.qdrant_client = self._get_qdrant_client()

        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def create_knowledge_base(self, user_id: str, chat_id: str, file: UploadFile) -> None:
        """
        Buat knowledge base baru, tambahkan node baru, atau tolak file yang sudah ada berdasarkan nama file.
        """
        self.logger.info(f"Starting knowledge base creation or update for chat_id '{chat_id}'.")
        collection_id = self._get_chat_collection_id(user_id, chat_id)

        # Validasi format file
        if not file.filename.endswith(('.pdf')):
            raise ValueError("Unsupported file type. Please upload a PDF file.")
        
        # Periksa apakah collection sudah ada
        if self.qdrant_client.collection_exists(collection_id):
            self.logger.info(f"File '{file.filename}' is new. Adding to existing collection '{collection_id}'.")
        else:
            # Buat collection baru jika belum ada
            self.logger.info(f"Collection '{collection_id}' does not exist. Creating a new collection.")
            self.qdrant_client.create_collection(
                collection_name=collection_id,
                vectors_config=VectorParams(
                    size=self.embedding_size, distance="Cosine"
                ),
            )
            self.logger.info(f"Collection '{collection_id}' created.")

        # Proses dokumen
        documents = await self._load_and_split_documents(file)
        vector_store = QdrantVectorStore(
            client=self.qdrant_client, collection_name=collection_id
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Tambahkan metadata unik
        file_id = str(uuid.uuid4())  # ID unik untuk file baru
        for document in documents:
            document.metadata = {
                "collection_id": collection_id,
                "file_id": file_id,
                "filename": file.filename,
                "user_id": user_id,
                "chat_id": chat_id,
            }

        # Tambahkan dokumen sebagai node baru
        storage_context.docstore.add_documents(documents)
        VectorStoreIndex(
            nodes=documents, storage_context=storage_context, show_progress=True
        )

        self.logger.info(
            f"Knowledge base updated for chat_id '{chat_id}' in collection '{collection_id}'."
        )


    def execute_query(
        self, user_id: str, chat_id: str, question: str, top_k: int = 3
    ) -> Response:
        self.logger.info(f"Executing query for chat_id '{chat_id}': {question}")
        collection_id = self._get_chat_collection_id(user_id, chat_id)

        if self.qdrant_client.collection_exists(collection_id):
            vector_index = self._get_vector_index(collection_id)

            top_reranked_texts = self._retrieve_top_texts(vector_index, question)
            return self._synthesize_answer(
                vector_index, top_reranked_texts, question, top_k
            )
        else:
            raise ValueError(f"No knowledge base found for chat_id '{chat_id}'.")

    def _get_embedding_size(self) -> int:
        return len(self.embed_model.get_query_embedding("sample"))

    def _get_qdrant_client(self) -> QdrantClient:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    def _get_chat_collection_id(self, user_id: str, chat_id: str) -> str:
        user = Users.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=401,
                detail=f"User ID '{user_id}' not found in the database.",
            )

        user_chats = Chats.get_chat_by_id_and_user_id(chat_id, user_id)
        if user_chats is None:
            raise ValueError(f"No chat '{chat_id}' found for User ID '{user_id}'.")

        return f"{user_id}_{chat_id}"

    async def _load_and_split_documents(self, file: UploadFile) -> List[Document]:
        temp_dir = None
        try:
            # Buat direktori sementara untuk menyimpan file
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, f"temp_{file.filename}")
            image_dir = os.path.join(temp_dir, "images")

            # Simpan file ke direktori sementara
            with open(file_path, "wb") as tmp_file:
                tmp_file.write(await file.read())
            
            self.logger.info(f"File saved temporarily at {file_path}")

            # Gunakan partition_pdf untuk memproses file
            raw_pdf_elements = partition_pdf(
                filename=file_path,
                extract_images_in_pdf=True,
                infer_table_structure=True,
                chunking_strategy="by_title",
                max_characters=4000,
                new_after_n_chars=3800,
                combine_text_under_n_chars=2000,
                extract_image_block_output_dir = f"{image_dir}",
            )
            
            self.logger.info("PDF successfully partitioned.")

            # Log the number of images found
            image_count = len([img for img in os.listdir(image_dir) if img.endswith(('.jpg', '.jpeg', '.png'))])
            self.logger.info(f"Number of images found: {image_count}")

            # Proses deskripsi gambar
            image_descriptions = []

            if os.path.exists(image_dir):
                for image_number, image_file in enumerate(sorted(os.listdir(image_dir)), start=1):
                    if image_file.endswith(('.jpg', '.jpeg', '.png')):
                        image_path = os.path.join(image_dir, image_file)
                        
                        # Convert gambar ke base64 untuk proses lebih lanjut
                        with open(image_path, "rb") as img_file:
                            base64_image = base64.b64encode(img_file.read()).decode("utf-8")
                        
                        # Buat deskripsi gambar
                        description = await self.pdf_service._describe_image(base64_image, image_number)
                        image_descriptions.append(f"Image {image_file}: {description}")
            
            # Gabungkan teks dan deskripsi gambar
            splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=50)
            text_descriptions = " ".join([str(element) for element in raw_pdf_elements])
            combined_content = text_descriptions + "\n" + "\n".join(image_descriptions)

            return [Document(text=text) for text in splitter.split_text(combined_content)]

        except Exception as e:
            self.logger.error(f"Error while loading and splitting documents: {e}")
            raise

        finally:
            # Hapus file sementara setelah selesai
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(image_dir):
                shutil.rmtree(image_dir)
            self.logger.info(f"Temporary file {file_path} and images removed.")

    def _get_vector_index(self, collection_id: uuid) -> VectorStoreIndex:
        vector_store = QdrantVectorStore(
            client=self.qdrant_client, collection_name=collection_id
        )
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        return VectorStoreIndex.from_vector_store(
            vector_store=vector_store, storage_context=storage_context
        )

    def _retrieve_top_texts(
        self, vector_index: VectorStoreIndex, question: str
    ) -> List[str]:
        retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=10)
        relevant_texts = [doc.text for doc in retriever.retrieve(question)]

        if not relevant_texts:
            self.logger.warning("No relevant texts found.")
            return []

        reranked_results = self.rerank_service.rerank(
            model="rerank-english-v3.0", query=question, documents=relevant_texts
        )

        return [relevant_texts[result.index] for result in reranked_results.results[:3]]

    def _synthesize_answer(
        self,
        vector_index: VectorStoreIndex,
        top_reranked_texts: List[str],
        question: str,
        top_k: int,
    ) -> Response:
        query_engine = RetrieverQueryEngine(
            retriever=VectorIndexRetriever(index=vector_index, similarity_top_k=top_k),
            response_synthesizer=get_response_synthesizer(llm=self.llm),
        )
        refined_query = (
            "Based on these documents: "
            f"{top_reranked_texts}, please refine the search for the question: {question}."
        )
        self.logger.info("Generating response.")
        return query_engine.query(refined_query)