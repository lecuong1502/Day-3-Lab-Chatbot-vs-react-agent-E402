"""
🌐 BACKEND API (FastAPI) cho Cupid Agent
Bọc quanh app.py/tools.py để UI Streamlit gọi qua HTTP thay vì import trực tiếp,
mô phỏng kiến trúc client-server thật (UI tách rời khỏi Agent Core).

Chạy: uvicorn api:app --reload --port 8000
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app import run_react_agent, run_baseline_chatbot, parse_llm_response, execute_tool, _validate_final_answer
from prompts import MAX_ITERATIONS, REACT_SYSTEM_PROMPT, CHATBOT_BASELINE_PROMPT
from providers import get_llm_provider
from tools import (
    list_all_users,
    register_user_profile,
    get_user_profile,
    VALID_MBTI,
    VALID_ZODIAC,
    VALID_RELATIONSHIP_STATUS,
)

app_api = FastAPI(title="Cupid Agent API", version="1.0.0")

# Cho phép Streamlit (chạy port khác) gọi API thoải mái trong môi trường demo
app_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_provider = get_llm_provider()

# Alias để chạy chuẩn convention `uvicorn api:app --reload --port 8000`
app = app_api


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class UserProfileIn(BaseModel):
    user_id: str
    name: str
    age: int = Field(ge=18, le=100)
    city: str
    mbti: str
    zodiac: str
    interests: list[str]
    values: list[str]
    relationship_status: str = "độc thân"


class CompatibilityRequest(BaseModel):
    user_id_a: str
    user_id_b: str


class BaselineRequest(BaseModel):
    query: str


class TraceStep(BaseModel):
    step: int
    thought: str
    action: str | None = None
    observation: str | None = None
    is_final: bool = False


class CompatibilityResponse(BaseModel):
    final_answer: str
    trace: list[TraceStep]
    guardrail_triggered: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app_api.get("/health")
def health():
    return {"status": "ok", "provider": _provider.__class__.__name__}


@app_api.get("/meta")
def meta():
    """Trả về danh sách giá trị hợp lệ để UI dựng dropdown đúng theo schema tool."""
    return {
        "mbti_options": sorted(VALID_MBTI),
        "zodiac_options": VALID_ZODIAC,
        "relationship_status_options": VALID_RELATIONSHIP_STATUS,
        "max_iterations": MAX_ITERATIONS,
    }


@app_api.get("/users")
def get_users():
    return {"users": list_all_users()}


@app_api.get("/users/{user_id}")
def get_user(user_id: str):
    result = get_user_profile(user_id)
    if result.startswith("LỖI"):
        raise HTTPException(status_code=404, detail=result)
    return {"user_id": user_id, "profile_text": result}


@app_api.post("/users")
def create_user(payload: UserProfileIn):
    result = register_user_profile(
        user_id=payload.user_id,
        name=payload.name,
        age=payload.age,
        city=payload.city,
        mbti=payload.mbti,
        zodiac=payload.zodiac,
        interests=payload.interests,
        values=payload.values,
        relationship_status=payload.relationship_status,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app_api.post("/baseline", response_model=dict)
def baseline_chat(payload: BaselineRequest):
    """Gọi Chatbot Baseline (không tool) để so sánh với ReAct Agent."""
    response = _provider.generate(payload.query, system_prompt=CHATBOT_BASELINE_PROMPT)
    return {"response": response}


@app_api.post("/compatibility", response_model=CompatibilityResponse)
def analyze_compatibility(payload: CompatibilityRequest):
    """
    Chạy vòng lặp ReAct đầy đủ (Thought -> Action -> Observation) để phân tích
    độ tương thích giữa 2 user_id, trả về cả Final Answer lẫn toàn bộ trace
    để UI hiển thị từng bước suy luận cho người dùng xem trực quan.
    """
    query = f"Tôi ({payload.user_id_a}) và người dùng {payload.user_id_b} có hợp nhau không? Vì sao?"

    transcript = f"Question: {query}\n"
    trace: list[TraceStep] = []
    step = 0
    final_answer = None
    guardrail_triggered = False

    while step < MAX_ITERATIONS:
        step += 1
        llm_output = _provider.generate(transcript, system_prompt=REACT_SYSTEM_PROMPT)
        parsed = parse_llm_response(llm_output)

        thought_text = llm_output.split("Action:")[0].split("Final Answer:")[0].strip()

        if parsed["type"] == "final":
            final_answer = parsed["content"]
            trace.append(TraceStep(step=step, thought=thought_text, is_final=True))
            break

        if parsed["type"] == "invalid":
            observation = f"LỖI ĐỊNH DẠNG: {parsed['reason']}"
            trace.append(TraceStep(step=step, thought=thought_text, observation=observation))
            transcript += f"{llm_output.strip()}\nObservation: {observation}\n"
            continue

        tool_name, args, kwargs = parsed["tool"], parsed["args"], parsed["kwargs"]
        observation = execute_tool(tool_name, args, kwargs)
        action_str = f"{tool_name}({', '.join(repr(a) for a in args)})"

        trace.append(TraceStep(step=step, thought=thought_text, action=action_str, observation=observation))
        transcript += f"{llm_output.strip()}\nObservation: {observation}\n"

    if final_answer is None:
        guardrail_triggered = True
        final_answer = (
            "Xin lỗi, tôi chưa thể xử lý đầy đủ yêu cầu này. Bạn có thể cung cấp "
            "thêm thông tin (vd: user_id chính xác) để tôi hỗ trợ tốt hơn không?"
        )
    else:
        final_answer = _validate_final_answer(final_answer, transcript)

    return CompatibilityResponse(
        final_answer=final_answer,
        trace=trace,
        guardrail_triggered=guardrail_triggered,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_api, host="0.0.0.0", port=8000)