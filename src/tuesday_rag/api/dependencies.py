from tuesday_rag.application.services.generator import GeneratorService
from tuesday_rag.application.services.indexer import IndexerService
from tuesday_rag.application.services.retriever import RetrieverService
from tuesday_rag.application.use_cases.generation import GenerationUseCase
from tuesday_rag.application.use_cases.ingestion import IngestionUseCase
from tuesday_rag.application.use_cases.retrieval import RetrievalUseCase
from tuesday_rag.config import RuntimeConfig
from tuesday_rag.infrastructure.chunking import CharacterChunker
from tuesday_rag.infrastructure.providers import DeterministicLLMProvider, HashEmbeddingProvider
from tuesday_rag.infrastructure.vector_store import InMemoryVectorStore


class Container:
    def __init__(self) -> None:
        self.config = RuntimeConfig.from_env()
        self.vector_store = InMemoryVectorStore()
        self.embedding_provider = HashEmbeddingProvider()
        self.llm_provider = DeterministicLLMProvider()
        self.chunker = CharacterChunker(
            chunk_size=self.config.ingestion_chunk_size_chars_default,
            chunk_overlap=self.config.ingestion_chunk_overlap_chars_default,
        )
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
        self.retrieval_use_case = RetrievalUseCase(
            config=self.config,
            retriever=self.retriever,
        )
        self.generation_use_case = GenerationUseCase(
            config=self.config,
            retriever=self.retriever,
            generator=self.generator,
        )


container = Container()
