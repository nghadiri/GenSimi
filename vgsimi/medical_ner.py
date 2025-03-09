from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
from typing import List, Dict
import logging
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalNERProcessor:
    def __init__(self, model_name: str = "samrawal/bert-base-clinical-ner"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name).to(self.device)
        
    def _clean_token(self, token: str) -> str:
        """Remove special tokens and ##"""
        if token.startswith('##'):
            return token[2:]
        return token.replace('[CLS]', '').replace('[SEP]', '').strip()

    @lru_cache(maxsize=1000)
    def process_text(self, text: str) -> List[Dict]:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        probabilities = torch.softmax(outputs.logits, dim=2)
        predictions = torch.argmax(outputs.logits, dim=2)
        confidence_scores = torch.max(probabilities, dim=2).values
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        
        entities = []
        current_entity = None
        
        for token, pred, conf in zip(tokens, predictions[0], confidence_scores[0]):
            if pred != 0:  # Not 'O' label
                clean_token = self._clean_token(token)
                if not clean_token:
                    continue
                    
                label = self.model.config.id2label[pred.item()]
                confidence = conf.item()
                
                if current_entity and current_entity["label"] == label:
                    current_entity["text"] += clean_token if token.startswith('##') else f" {clean_token}"
                    current_entity["confidence"] = min(current_entity["confidence"], confidence)
                else:
                    if current_entity:
                        entities.append(current_entity)
                    current_entity = {
                        "text": clean_token,
                        "label": label,
                        "confidence": confidence
                    }
                    
        if current_entity:
            entities.append(current_entity)
            
        # Filter out low confidence predictions and clean up texts
        entities = [
            {**e, "text": e["text"].strip()} 
            for e in entities 
            if e["confidence"] > 0.5
        ]
            
        return entities

    def process_batch(self, texts: List[str], batch_size: int = 8) -> List[List[Dict]]:
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                batch_results = [self.process_text(text) for text in batch]
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size}: {str(e)}")
                results.extend([[] for _ in batch])
        return results

def main():
    print("Loading model...")
    processor = MedicalNERProcessor()
    sample_text = "Patient presents with severe chest pain and shortness of breath. Medical history includes hypertension."
    entities = processor.process_text(sample_text)
    for entity in entities:
        print(f"Entity: {entity['text']}")
        print(f"Label: {entity['label']}")
        print(f"Confidence: {entity['confidence']:.2f}")
        print("---")

if __name__ == "__main__":
    main()
