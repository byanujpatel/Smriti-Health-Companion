from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

MemoryMode = Literal["local", "cloud"]
LLMBackend = Literal["groq", "ollama"]
VisionBackend = Literal["groq", "ollama"]
STTBackend = Literal["groq", "parakeet"]
LOCAL_SUPERMEMORY_HOSTS = ("localhost", "127.0.0.1", "[::1]")


class Settings(BaseSettings):
    smriti_memory_mode: MemoryMode = "local"
    smriti_llm_backend: LLMBackend = "groq"
    smriti_vision_backend: VisionBackend = "groq"
    smriti_stt_backend: STTBackend = "groq"
    supermemory_base_url: str | None = "http://localhost:6767"
    supermemory_api_key: str
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    groq_stt_model: str = "whisper-large-v3-turbo"
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    ollama_base_url: str = "http://localhost:11434"
    ollama_text_model: str = "llama3.2"
    ollama_vision_model: str = "llava"
    parakeet_base_url: str = "http://localhost:8765"
    parakeet_stt_model: str = "parakeet-tdt-0.6b-v2"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def memory_mode(self) -> MemoryMode:
        return self.smriti_memory_mode

    @property
    def llm_backend(self) -> LLMBackend:
        return self.smriti_llm_backend

    @property
    def vision_backend(self) -> VisionBackend:
        return self.smriti_vision_backend

    @property
    def stt_backend(self) -> STTBackend:
        return self.smriti_stt_backend

    @property
    def fully_local(self) -> bool:
        return (
            self.memory_mode == "local"
            and self.llm_backend == "ollama"
            and self.vision_backend == "ollama"
            and self.stt_backend == "parakeet"
        )

    @property
    def effective_supermemory_base_url(self) -> str | None:
        if self.memory_mode == "cloud":
            if not self.supermemory_base_url:
                return None
            normalized = self.supermemory_base_url.rstrip("/")
            if any(host in normalized for host in LOCAL_SUPERMEMORY_HOSTS):
                return None
            return normalized
        return (self.supermemory_base_url or "http://localhost:6767").rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
