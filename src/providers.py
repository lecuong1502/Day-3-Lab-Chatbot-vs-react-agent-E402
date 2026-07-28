"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        import re

        text = prompt.lower()
        is_react_mode = "reAct".lower() in system_prompt.lower() or "thought:" in system_prompt.lower()

        if "thời tiết" in text and "hà nội" in text and is_react_mode:
            return "Thought: Cần tra cứu thời tiết Hà Nội.\nAction: get_weather['Hà Nội']"

        # --- Mô phỏng luồng ReAct của Cupid Agent (bám theo REACT_SYSTEM_PROMPT) ---
        # CHỈ kích hoạt khi được gọi trong ngữ cảnh ReAct (có system_prompt ReAct).
        # Baseline chatbot (không có tool) KHÔNG được phép trả lời theo định dạng
        # Thought/Action -> nếu không phải react mode, luôn trả lời hội thoại thường.
        if is_react_mode:
            user_ids = list(dict.fromkeys(re.findall(r"user_\d{3}", prompt)))
            if len(user_ids) >= 2:
                return self._cupid_react_step(prompt, user_ids[0], user_ids[1])
            if len(user_ids) == 1:
                return (
                    f"Thought: Câu hỏi chỉ có 1 user_id ({user_ids[0]}), thiếu người thứ hai để so sánh.\n"
                    f"Final Answer: Bạn muốn so sánh {user_ids[0]} với ai? Cho mình xin thêm user_id thứ hai nhé."
                )
            return (
                "Thought: Câu hỏi không cung cấp user_id nào để tra cứu.\n"
                "Final Answer: Bạn có thể cho mình biết user_id của (những) người bạn muốn phân tích không?"
            )

        # --- Chế độ Baseline (không có tool) ---
        return (
            "🤖 [Mock Provider - Baseline]: Mình chưa có quyền truy cập cơ sở dữ liệu người dùng thật "
            "nên không thể xác nhận thông tin cụ thể. Dựa trên kiến thức chung, độ hợp giữa hai người "
            "thường phụ thuộc vào tính cách, sở thích và giá trị sống — nếu bạn cho mình biết thêm "
            "chi tiết, mình có thể tư vấn kỹ hơn."
        )

    @staticmethod
    def _cupid_react_step(transcript: str, target_a: str, target_b: str) -> str:
        """
        Sinh ra ĐÚNG 1 bước Thought->Action (hoặc Final Answer) tiếp theo,
        dựa trên các Observation đã có trong transcript. Được gọi lặp lại
        bởi vòng lặp ReAct ở app.py cho tới khi có Final Answer.
        """
        import re

        observations = re.findall(r"Observation:\s*(.*)", transcript)
        combined_obs = " ".join(observations)

        fetched = [uid for uid in (target_a, target_b) if f"Hồ sơ {uid}" in combined_obs]

        if target_a not in fetched:
            return (
                f"Thought: Cần lấy hồ sơ của {target_a} trước khi so sánh.\n"
                f"Action: get_user_profile('{target_a}')"
            )

        if target_b not in fetched:
            return (
                f"Thought: Đã có hồ sơ {target_a}, cần lấy thêm hồ sơ {target_b}.\n"
                f"Action: get_user_profile('{target_b}')"
            )

        def _status_of(uid):
            m = re.search(rf"Hồ sơ {uid}.*?Tình trạng mối quan hệ: ([^\.]+)\.", combined_obs)
            return m.group(1).strip() if m else None

        blocked = {"đang hẹn hò", "đã kết hôn"}
        status_a, status_b = _status_of(target_a), _status_of(target_b)

        if "GUARDRAIL_CHECK_DONE" not in transcript and (status_a in blocked or status_b in blocked):
            blocked_uid = target_a if status_a in blocked else target_b
            blocked_status = status_a if status_a in blocked else status_b
            return (
                f"Thought: {blocked_uid} có tình trạng mối quan hệ là '{blocked_status}'. "
                f"Theo Guardrail #7 (Relationship Status Guardrail), phải DỪNG NGAY và "
                f"KHÔNG được gọi calculate_compatibility_score. [GUARDRAIL_CHECK_DONE]\n"
                f"Final Answer: Xin lỗi, mình không thể thực hiện phân tích ghép đôi cho trường hợp "
                f"này vì {blocked_uid} hiện đang trong một mối quan hệ ({blocked_status}). "
                f"Mình tôn trọng mối quan hệ hiện tại của họ nên sẽ dừng phân tích ở đây."
            )

        if "Điểm tương thích giữa" not in combined_obs:
            return (
                "Thought: Cả hai đều độc thân (hoặc đã xác nhận an toàn), có thể tính điểm tương thích. "
                "[GUARDRAIL_CHECK_DONE]\n"
                f"Action: calculate_compatibility_score('{target_a}', '{target_b}')"
            )

        score_obs = next(o for o in observations if "Điểm tương thích giữa" in o)
        return f"Thought: Tôi đã có đủ thông tin để trả lời.\nFinal Answer: {score_obs}"


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")