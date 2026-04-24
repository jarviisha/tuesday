import logging

from llama_index.core import Settings

from tuesday.rag.generation.service import GeneratorService
from tuesday.rag.generation.use_case import GenerationUseCase
from tuesday.rag.infrastructure.chunking import LlamaIndexNodeParser
from tuesday.rag.infrastructure.file_document_parser import LocalFileDocumentParser
from tuesday.rag.infrastructure.file_vector_store import FileBackedVectorStore
from tuesday.rag.infrastructure.providers import (
    DeterministicDenseEmbeddingProvider,
    DeterministicLLMProvider,
    HashEmbeddingProvider,
)
from tuesday.rag.infrastructure.resilience import (
    ResilientEmbeddingProvider,
    ResilientLLMProvider,
    ResilientVectorStore,
)
from tuesday.rag.infrastructure.vector_store import InMemoryVectorStore
from tuesday.rag.ingestion.file_use_case import FileIngestionUseCase
from tuesday.rag.ingestion.service import IndexerService
from tuesday.rag.ingestion.use_case import IngestionUseCase
from tuesday.rag.retrieval.service import RetrieverService
from tuesday.rag.retrieval.use_case import RetrievalUseCase
from tuesday.runtime.config import RuntimeConfig

logger = logging.getLogger("tuesday.runtime")


class Container:
    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config
        self.vector_store = self._build_vector_store()
        self.embedding_provider = ResilientEmbeddingProvider(
            self._build_embedding_provider(),
            timeout_ms=self.config.embedding_timeout_ms,
            max_retries=self.config.embedding_max_retries,
        )
        self.llm_provider = ResilientLLMProvider(
            self._build_llm_provider(),
            timeout_ms=self.config.generation_timeout_ms,
            max_retries=self.config.generation_max_retries,
        )
        self.chunker = LlamaIndexNodeParser(
            chunk_size=self.config.ingestion_chunk_size_tokens_default,
            chunk_overlap=self.config.ingestion_chunk_overlap_tokens_default,
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
        elif self.config.vector_store_backend == "qdrant":
            from tuesday.rag.infrastructure.qdrant_vector_store import LlamaIndexQdrantAdapter

            store = LlamaIndexQdrantAdapter(
                url=self.config.qdrant_url,
                api_key=self.config.qdrant_api_key,
                location=self.config.qdrant_location,
                collection_prefix=self.config.qdrant_collection_prefix_v2,
                dense_vector_size=self.config.qdrant_dense_vector_size,
            )
        else:
            store = InMemoryVectorStore()
        return ResilientVectorStore(
            store,
            timeout_ms=self.config.vector_store_timeout_ms,
            max_retries=self.config.vector_store_max_retries,
        )

    def _build_embedding_provider(self):
        if self.config.embedding_provider_backend == "demo":
            if self.config.vector_store_backend == "qdrant":
                provider = DeterministicDenseEmbeddingProvider(
                    dimension=self.config.qdrant_dense_vector_size
                )
            else:
                provider = HashEmbeddingProvider()
            if isinstance(provider, DeterministicDenseEmbeddingProvider):
                Settings.embed_model = provider
            return provider

        provider = _build_vendor_embedding(self.config)
        Settings.embed_model = provider.llama_model
        return provider

    def _build_llm_provider(self):
        if self.config.generation_provider_backend == "demo":
            provider = DeterministicLLMProvider()
            Settings.llm = provider
            return provider

        provider = _build_vendor_llm(self.config)
        Settings.llm = provider.llama_llm
        return provider


def _build_vendor_embedding(config: RuntimeConfig):
    from tuesday.rag.infrastructure.providers_vendor import (
        build_azure_openai_embedding,
        build_gemini_embedding,
        build_openai_embedding,
    )

    if config.embedding_provider_backend == "openai":
        return build_openai_embedding(config)
    if config.embedding_provider_backend == "gemini":
        return build_gemini_embedding(config)
    return build_azure_openai_embedding(config)


def _build_vendor_llm(config: RuntimeConfig):
    from tuesday.rag.infrastructure.providers_vendor import (
        build_azure_openai_llm,
        build_gemini_llm,
        build_openai_llm,
    )

    if config.generation_provider_backend == "openai":
        return build_openai_llm(config)
    if config.generation_provider_backend == "gemini":
        return build_gemini_llm(config)
    return build_azure_openai_llm(config)


def build_config_from_env() -> RuntimeConfig:
    return RuntimeConfig.from_env()


def build_container(config: RuntimeConfig | None = None) -> Container:
    resolved_config = config or build_config_from_env()
    resolved_config.validate()
    _run_startup_checks(resolved_config)
    return Container(resolved_config)


def build_runtime_from_env() -> Container:
    return build_container(build_config_from_env())


def _run_startup_checks(config: RuntimeConfig) -> None:
    if config.pdf_startup_check_mode == "off":
        return
    if LocalFileDocumentParser.has_pdftotext():
        return
    message = "pdftotext is not available on PATH; PDF ingestion will not work"
    if config.pdf_startup_check_mode == "warn":
        logger.warning("runtime.startup_check_failed", extra={"check": "pdftotext"})
        logger.warning(message)
        return
    raise RuntimeError(message)
