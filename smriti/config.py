from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

MemoryMode = Literal["local", "cloud"]
LOCAL_SUPERMEMORY_HOSTS = ("localhost", "127.0.0.1", "[::1]")


class Settings(BaseSettings):
    smriti_memory_mode: MemoryMode = "local"
    supermemory_base_url: str | None = "http://localhost:6767"
    supermemory_api_key: str
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"
    groq_stt_model: str = "whisper-large-v3-turbo"
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def memory_mode(self) -> MemoryMode:
        return self.smriti_memory_mode

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
