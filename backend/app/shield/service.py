from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import List, Dict

class PIIShieldService:
    def __init__(self):
        # Initialize engines once (heavy model load)
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def analyze_text(self, text: str, entities: List[str] = None):
        """
        Analyze text for PII entities.
        """
        results = self.analyzer.analyze(text=text, entities=entities, language='en')
        return [result.to_dict() for result in results]

    def anonymize_text(self, text: str, entities: List[str] = None):
        """
        Redact PII from text.
        """
        analyzer_results = self.analyzer.analyze(text=text, entities=entities, language='en')
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results
        )
        return {
            "text": anonymized_result.text,
            "items": [
                {
                    "start": item.start,
                    "end": item.end,
                    "entity_type": item.entity_type,
                    "text": item.text if hasattr(item, 'text') else None,
                    "operator": item.operator
                } 
                for item in anonymized_result.items
            ]
        }
