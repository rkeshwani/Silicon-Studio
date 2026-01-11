from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseEngineService(ABC):
    @abstractmethod
    def get_supported_models(self) -> List[Dict[str, Any]]:
        """Return a list of supported models configuration."""
        pass

    @abstractmethod
    def register_model(self, name: str, path: str, url: str = "") -> Dict[str, Any]:
        """Register a custom model."""
        pass

    @abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """List models (internal method, often same as get_supported_models)."""
        pass

    @abstractmethod
    async def get_model_and_tokenizer(self, model_id: str):
        """Load and return the model and tokenizer."""
        pass

    @abstractmethod
    async def generate_response(self, model_id: str, messages: list) -> Dict[str, Any]:
        """Generate a chat response."""
        pass

    @abstractmethod
    async def start_finetuning(self, job_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start a fine-tuning job."""
        pass

    @abstractmethod
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a job."""
        pass

    @abstractmethod
    def get_models_status(self) -> List[Dict[str, Any]]:
        """Return models with download status."""
        pass

    @abstractmethod
    def download_model(self, model_id: str) -> bool:
        """Download a model."""
        pass

    @abstractmethod
    def delete_model(self, model_id: str) -> bool:
        """Delete a model."""
        pass
