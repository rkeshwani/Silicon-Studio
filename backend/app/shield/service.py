from presidio_analyzer import AnalyzerEngine, Registry
from presidio_anonymizer import AnonymizerEngine
from typing import List, Dict
import spacy

class PIIShieldService:
    def __init__(self):
        # Initialize engines once (heavy model load)
        print("DEBUG: Initializing PIIShieldService...", flush=True)
        try:
            # PROD FIX: Explicitly load the bundled spacy model
            # This works better with PyInstaller than relying on string names
            nlp = None
            try:
                import en_core_web_sm
                print("DEBUG: Found en_core_web_sm module, loading...", flush=True)
                nlp = en_core_web_sm.load()
            except ImportError:
                 print("DEBUG: en_core_web_sm module not found, trying spacy.load('en_core_web_sm')", flush=True)
                 try:
                    nlp = spacy.load("en_core_web_sm")
                 except Exception as e:
                    print(f"DEBUG: Failed to load en_core_web_sm: {e}. Trying 'en'...", flush=True)
            
            if nlp:
                 print("DEBUG: Spacy NLP model loaded successfully.", flush=True)
                 # Create a registry with this specific NLP engine
                 from presidio_analyzer.nlp_engine import NlpEngineProvider
                 
                 # Configure Presidio to use this nlp object? 
                 # Actually Presidio expects a config to create the engine.
                 # But we can inject the nlp object if we subclass or use internal APIs.
                 # EASIER: register it?
                 
                 # Official Presidio way with custom model:
                 conf_file = {
                    "nlp_engine_name": "spacy",
                    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]
                 }
                 # But we need to ensure 'en_core_web_sm' is linkable.
                 # If 'en_core_web_sm' is imported as a module, spacy.load('en_core_web_sm') works IF listed in metadata.
                 
                 # Force the loaded nlp into spacy's util cache if needed?
                 # No, AnalyzerEngine defaults to NlpEngineProvider(conf_file).create_engine()
                 
                 provider = NlpEngineProvider(nlp_configuration=conf_file)
                 nlp_engine = provider.create_engine()
                 
                 self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
                 print("DEBUG: AnalyzerEngine initialized with custom config.", flush=True)
                 
            else:
                 # Fallback to default (might crash if model missing)
                 print("WARNING: No NLP model loaded. PIIShield will likely fail.", flush=True)
                 self.analyzer = AnalyzerEngine() 
                 
            self.anonymizer = AnonymizerEngine()
            print("DEBUG: PIIShieldService fully initialized.", flush=True)
            
        except Exception as e:
            print(f"CRITICAL: Failed to init PIIShieldService: {e}", flush=True)
            import traceback
            traceback.print_exc()
            # Don't crash the whole app, but PII will fail
            self.analyzer = None
            self.anonymizer = None

    def analyze_text(self, text: str, entities: List[str] = None):
        """
        Analyze text for PII entities.
        """
        if not self.analyzer: raise ValueError("PII Shield not initialized")
        results = self.analyzer.analyze(text=text, entities=entities, language='en')
        return [result.to_dict() for result in results]

    def anonymize_text(self, text: str, entities: List[str] = None):
        """
        Redact PII from text.
        """
        if not self.analyzer or not self.anonymizer: return {"text": text, "items": []}
        
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
