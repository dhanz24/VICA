from Backend.VICA.config import QDRANT_URL, QDRANT_API_KEY
from typing import List
import uuid
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
from fastapi import UploadFile
from Backend.VICA.apps.VICA.services.pdf import PDFService

DB_DUMMY_CHAT_COLLECTIONS = {
    "uid_1": {
        "cid_1": "ecc129ed-735c-434f-9f4b-539165de0455",  # str(uuid.uuid4())
        "cid_2": "07019e60-9b7f-4d5f-a043-7acf7d902b69",
        "cid_3": "1cc0acc4-3a3a-4747-a6ba-08dfa5f6e6d1",
    },
    "uid_2": {
        "cid_4": "2e74e48d-6569-4ecd-9c91-a783073f5c00",
        "cid_5": "9b89f306-0ed3-4415-b2f7-763177455fe3",
    },
}


class RAGService:
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

    async def create_knowledge_base(
        self, user_id: str, chat_id: str, file: UploadFile, include_visuals: bool
    ) -> None:
        collection_id = self._get_chat_collection_id(user_id, chat_id)
        if self.qdrant_client.collection_exists(collection_id):
            raise ValueError(
                f"Knowledge base already exists for chat_id '{chat_id}'. Create a new chat."
            )
        else:
            documents = await self._load_and_split_documents(file, include_visuals)

            self.qdrant_client.create_collection(
                collection_name=collection_id,
                vectors_config=VectorParams(
                    size=self.embedding_size, distance="Cosine"
                ),
            )

            vector_store = QdrantVectorStore(
                client=self.qdrant_client, collection_name=collection_id
            )
            storage_context = StorageContext.from_defaults(vector_store=vector_store)

            nodes = Settings.node_parser.get_nodes_from_documents(documents)
            storage_context.docstore.add_documents(nodes)

            VectorStoreIndex(
                nodes=nodes, storage_context=storage_context, show_progress=True
            )

    def execute_query(
        self, user_id: str, chat_id: str, question: str, top_k: int = 3
    ) -> Response:
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
        if user_id not in DB_DUMMY_CHAT_COLLECTIONS:
            raise ValueError(f"User ID '{user_id}' not found in the database.")

        user_chats = DB_DUMMY_CHAT_COLLECTIONS[user_id]
        if chat_id not in user_chats:
            raise ValueError(f"Chat ID '{chat_id}' not found for User ID '{user_id}'.")

        return DB_DUMMY_CHAT_COLLECTIONS.get(user_id, {}).get(chat_id)

    async def _load_and_split_documents(
        self, file: UploadFile, include_visuals: bool = True
    ) -> List[Document]:
        descriptions = (
            await self.pdf_service.describe_pdf(file)
            if include_visuals
            else await self.pdf_service.extract_text_from_pdf(file)
        )

        splitter = SentenceSplitter(chunk_size=1000, chunk_overlap=50)

        return [Document(text=text) for text in splitter.split_text(descriptions)]

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

        return query_engine.query(refined_query)
