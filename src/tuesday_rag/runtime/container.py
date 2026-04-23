from tuesday_rag.config import RuntimeConfig
from tuesday_rag.generation.service import GeneratorService
from tuesday_rag.generation.use_case import GenerationUseCase
from tuesday_rag.infrastructure.chunking import CharacterChunker
from tuesday_rag.infrastructure.file_document_parser import LocalFileDocumentParser
from tuesday_rag.infrastructure.file_vector_store import FileBackedVectorStore
from tuesday_rag.infrastructure.providers import DeterministicLLMProvider, HashEmbeddingProvider
from tuesday_rag.infrastructure.resilience import (
    ResilientEmbeddingProvider,
    ResilientLLMProvider,
    ResilientVectorStore,
)
from tuesday_rag.infrastructure.vector_store import InMemoryVectorStore
from tuesday_rag.ingestion.file_use_case import FileIngestionUseCase
from tuesday_rag.ingestion.service import IndexerService
from tuesday_rag.ingestion.use_case import IngestionUseCase
from tuesday_rag.retrieval.service import RetrieverService
from tuesday_rag.retrieval.use_case import RetrievalUseCase


class Container:
    def __init__(self) -> None:
        self.config = RuntimeConfig.from_env()
        self.vector_store = self._build_vector_store()
        self.embedding_provider = ResilientEmbeddingProvider(
            HashEmbeddingProvider(),
            timeout_ms=self.config.embedding_timeout_ms,
            max_retries=self.config.embedding_max_retries,
        )
        self.llm_provider = ResilientLLMProvider(
            DeterministicLLMProvider(),
            timeout_ms=self.config.generation_timeout_ms,
            max_retries=self.config.generation_max_retries,
        )
        self.chunker = CharacterChunker(
            chunk_size=self.config.ingestion_chunk_size_chars_default,
            chunk_overlap=self.config.ingestion_chunk_overlap_chars_default,
        )
        self.document_parser = LocalFileDocumentParser()
        self.indexer = IndexerService(self.embedding_provider, self.vector_store)
        self.retriever = RetrieverService(self.embedding_provider, self.vector_store)
        self.generator = GeneratorService(
            self.llm_provider,
            insufficient_context_answer=self.config.insufficient_context_answer,
        )
        self.ingestion_use_case = IngestionUseCase(
            config=self.config,
            chunker=self.chunker,
            indexer=self.indexer,
        )
        self.file_ingestion_use_case = FileIngestionUseCase(
            config=self.config,
            parser=self.document_parser,
            ingestion_use_case=self.ingestion_use_case,
        )
        self.retrieval_use_case = RetrievalUseCase(
            config=self.config,
            retriever=self.retriever,
        )
        self.generation_use_case = GenerationUseCase(
            config=self.config,
            retriever=self.retriever,
            generator=self.generator,
        )

    def _build_vector_store(self) -> ResilientVectorStore:
        if self.config.vector_store_backend == "file":
            store = FileBackedVectorStore(self.config.vector_store_file_path)
        else:
            store = InMemoryVectorStore()
        return ResilientVectorStore(
            store,
            timeout_ms=self.config.vector_store_timeout_ms,
            max_retries=self.config.vector_store_max_retries,
        )


container = Container()
