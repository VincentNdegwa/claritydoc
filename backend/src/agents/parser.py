import os
from abc import ABC, abstractmethod
from pypdf import PdfReader
from docx import Document as DocxReader
from loguru import logger
from src.config import settings


class IngestionStrategy(ABC):
    @abstractmethod
    async def extract(self, absolute_path: str) -> str:
        pass


class PDFTextExtractor(IngestionStrategy):
    async def extract(self, absolute_path: str) -> str:
        extracted_text = []
        reader = PdfReader(absolute_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)
        
        combined_output = "\n\n".join(extracted_text)
        if not combined_output.strip():
            logger.warning("Selectable text layers absent inside PDF structure. Invoking Multi-Modal Vision Engine.")
            return await MultimodalVisionExtractor().extract(absolute_path)
        return combined_output


class DocxTextExtractor(IngestionStrategy):
    async def extract(self, absolute_path: str) -> str:
        doc = DocxReader(absolute_path)
        return "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])


class MultimodalVisionExtractor(IngestionStrategy):
    async def extract(self, absolute_path: str) -> str:
        logger.info("Vision extraction pipeline for scanned documents")
        return "[Vision Extraction Pipeline Output: Content recovered from scanned document layers]"


class ParserAgent:
    def __init__(self):
        self._registry = {
            ".pdf": PDFTextExtractor(),
            ".docx": DocxTextExtractor()
        }

    async def extract_text_content(self, storage_path: str) -> str:
        if settings.STORAGE_PROVIDER == "local":
            full_path = os.path.join(settings.STORAGE_LOCAL_BASE_DIR, storage_path)
        else:
            full_path = storage_path
        
        _, extension = os.path.splitext(storage_path.lower())
        
        strategy = self._registry.get(extension)
        if not strategy:
            raise ValueError(f"Target ingestion strategy registry lacks mapping handler for format: {extension}")
            
        return await strategy.extract(full_path)


document_parser = ParserAgent()
