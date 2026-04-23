import logging

from tuesday_rag.config import RuntimeConfig
from tuesday_rag.generation.service import GeneratorService
from tuesday_rag.generation.use_case import GenerationUseCase
from tuesday_rag.infrastructure.chunking import CharacterChunker
from tuesday_rag.infrastructure.file_document_parser import LocalFileDocumentParser
from tuesday_rag.infrastructure.file_vector_store import FileBackedVectorStore
from tuesday_rag.infrastructure.providers import DeterministicLLMProvider, HashEmbeddingProvider
from tuesday_rag.infrastructure.providers_vendor import (
    AzureOpenAIEmbeddingProvider,
    AzureOpenAILLMProvider,
    GeminiEmbeddingProvider,
    GeminiLLMProvider,
    OpenAIEmbeddingProvider,
    OpenAILLMProvider,
)
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

logger = logging.getLogger("tuesday_rag.runtime")


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

    def _build_embedding_provider(self):
        if self.config.embedding_provider_backend == "demo":
            return HashEmbeddingProvider()
        if self.config.embedding_provider_backend == "openai":
            return OpenAIEmbeddingProvider(
                api_key=self.config.openai_api_key or "",
                base_url=self.config.openai_base_url,
                model=self.config.openai_embedding_model or "",
            )
        if self.config.embedding_provider_backend == "gemini":
            return GeminiEmbeddingProvider(
                api_key=self.config.gemini_api_key or "",
                base_url=self.config.gemini_base_url,
                model=self.config.gemini_embedding_model or "",
            )
        return AzureOpenAIEmbeddingProvider(
            api_key=self.config.azure_openai_api_key or "",
            endpoint=self.config.azure_openai_endpoint or "",
            api_version=self.config.azure_openai_api_version,
            deployment=self.config.azure_openai_embedding_deployment or "",
        )

    def _build_llm_provider(self):
        if self.config.generation_provider_backend == "demo":
            return DeterministicLLMProvider()
        if self.config.generation_provider_backend == "openai":
            return OpenAILLMProvider(
                api_key=self.config.openai_api_key or "",
                base_url=self.config.openai_base_url,
                model=self.config.openai_generation_model or "",
            )
        if self.config.generation_provider_backend == "gemini":
            return GeminiLLMProvider(
                api_key=self.config.gemini_api_key or "",
                base_url=self.config.gemini_base_url,
                model=self.config.gemini_generation_model or "",
            )
        return AzureOpenAILLMProvider(
            api_key=self.config.azure_openai_api_key or "",
            endpoint=self.config.azure_openai_endpoint or "",
            api_version=self.config.azure_openai_api_version,
            deployment=self.config.azure_openai_generation_deployment or "",
        )

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
