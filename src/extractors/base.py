from abc import ABC, abstractmethod
from src.schema import ExtractionResult

class BaseExtractor(ABC):
    name: str

    @abstractmethod
    def extract(self, image_path: str, bill_id: str) -> ExtractionResult:
        ...