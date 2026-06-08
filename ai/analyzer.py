import json
import os
from llama_cpp import Llama
from config import MODEL_PATH, POLICY_PATH

class AIAnalyzer:
    def __init__(self, model_path=MODEL_PATH, policy_path=POLICY_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"\n[!] AI Model not found at:\n{model_path}\n")
        self.llm = Llama(model_path=model_path, n_ctx=4096, n_gpu_layers=0)
        with open(policy_path, "r", encoding="utf-8") as f:
            self.policy = f.read()

    def analyze_request(self, request_text: str) -> dict:
        prompt = f"""<|turn>system You are AI BOS, a strict security analyzer. Follow these policies exactly:
{self.policy}<turn|>
<|turn>user User Request: {request_text}

Respond ONLY in valid JSON format:
{{"clarified_request": "string", "security_notes": ["string"], "security_score": integer (0-10)}}<turn|>
<|turn>model"""
        response = self.llm(prompt, max_tokens=1024, temperature=0.1, stop=["<turn|>"], echo=False)
        try:
            output_text = response['choices'][0]['text'].strip()
            if output_text.startswith("{") == False:
                output_text = output_text[output_text.find("{"):output_text.rfind("}")+1]
            return json.loads(output_text)
        except Exception as e:
            return {"clarified_request": "Failed to parse AI output.", "security_notes": [f"Failure: {str(e)}"], "security_score": 10}

    # NEW: Assistant Selection Intelligence
    def select_assistant(self, request_text: str, assistants: list) -> dict:
        assistants_json = json.dumps(assistants, ensure_ascii=False)
        prompt = f"""<|turn>system You are the AI BOS Operations Router.
Here is the list of available external execution assistants:
{assistants_json}

Task: Choose the best assistant to fulfill the user's request. If none match, set assistant_id to 0. Extract or translate the core request into a highly optimized search query string.
<turn|>
<|turn>user User Request: {request_text}

Respond ONLY in valid JSON format:
{{"assistant_id": integer, "query_text": "string"}}<turn|>
<|turn>model"""
        
        response = self.llm(prompt, max_tokens=256, temperature=0.1, stop=["<turn|>"], echo=False)
        try:
            output_text = response['choices'][0]['text'].strip()
            if output_text.startswith("{") == False:
                output_text = output_text[output_text.find("{"):output_text.rfind("}")+1]
            return json.loads(output_text)
        except Exception:
            return {"assistant_id": 0, "query_text": request_text}