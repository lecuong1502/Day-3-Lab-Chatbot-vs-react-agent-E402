"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import ast
import inspect
import json
import os
import re
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data["test_cases"]


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


# ---------------------------------------------------------------------------
# ReAct Loop internals: parser (Thought/Action/Final Answer) + tool executor
# ---------------------------------------------------------------------------

_ACTION_PAREN_RE = re.compile(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^\n]*)\)", re.IGNORECASE)
_ACTION_BRACKET_RE = re.compile(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[([^\n]*)\]", re.IGNORECASE)
_FINAL_ANSWER_RE = re.compile(r"Final Answer:\s*(.+)", re.IGNORECASE | re.DOTALL)
_OBSERVATION_RE = re.compile(r"Observation\s*:", re.IGNORECASE)


def _strip_fabricated_observation(text: str) -> str:
    """
    Anti-Hallucination Guardrail: Observation CHỈ được hệ thống điền từ tool
    thật. Nếu LLM tự bịa luôn cả Observation (và có thể cả Final Answer dựa
    trên Observation giả đó), cắt bỏ từ Observation trở đi để ép Agent phải
    đợi kết quả tool thật ở vòng lặp kế tiếp.
    """
    match = _OBSERVATION_RE.search(text)
    if match:
        return text[: match.start()].rstrip()
    return text


def _parse_call_args(raw_args: str):
    """Parse chuỗi tham số dạng lệnh gọi hàm Python bằng ast.literal_eval
    (chỉ nhận literal, không eval code tùy ý) -> (args, kwargs)."""
    call_node = ast.parse(f"f({raw_args})", mode="eval").body
    args = [ast.literal_eval(a) for a in call_node.args]
    kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in call_node.keywords}
    return args, kwargs


def parse_llm_response(raw_text: str) -> dict:
    """
    Phân tích 1 lượt phản hồi của LLM trong vòng lặp ReAct.

    Trả về dict:
      {"type": "final", "content": str}
      {"type": "action", "tool": str, "args": list, "kwargs": dict}
      {"type": "invalid", "reason": str}
    """
    text = raw_text.replace("**", "")  # bỏ markdown bold gây lệch regex
    text = _strip_fabricated_observation(text)

    final_match = _FINAL_ANSWER_RE.search(text)
    if final_match:
        return {"type": "final", "content": final_match.group(1).strip()}

    is_bracket = False
    match = _ACTION_PAREN_RE.search(text)
    if not match:
        match = _ACTION_BRACKET_RE.search(text)
        is_bracket = True

    if not match:
        return {
            "type": "invalid",
            "reason": "Không tìm thấy 'Action: tool(...)' hay 'Final Answer:' hợp lệ trong phản hồi.",
        }

    tool_name, raw_args = match.group(1), match.group(2).strip()
    try:
        if is_bracket:
            args = ast.literal_eval(f"[{raw_args}]") if raw_args else []
            kwargs = {}
        else:
            args, kwargs = _parse_call_args(raw_args)
    except Exception as e:
        return {
            "type": "invalid",
            "reason": f"Cú pháp tham số không hợp lệ trong '{tool_name}({raw_args})' ({e}).",
        }

    return {"type": "action", "tool": tool_name, "args": args, "kwargs": kwargs}


def execute_tool(tool_name: str, args: list, kwargs: dict) -> str:
    """Thực thi tool thật trong AVAILABLE_TOOLS. Luôn trả về string quan sát
    được (Observation), KHÔNG BAO GIỜ để Exception làm crash vòng lặp."""
    tool_func = AVAILABLE_TOOLS.get(tool_name)
    if tool_func is None:
        valid_tools = ", ".join(AVAILABLE_TOOLS.keys())
        return f"LỖI: Tool '{tool_name}' không tồn tại. Các tool hợp lệ gồm: [{valid_tools}]"
    try:
        bound = inspect.signature(tool_func).bind(*args, **kwargs)
        bound.apply_defaults()
    except TypeError as e:
        return f"LỖI: Tham số truyền cho tool '{tool_name}' không hợp lệ ({e})."
    try:
        return str(tool_func(*bound.args, **bound.kwargs))
    except Exception as e:
        return f"LỖI: Tool '{tool_name}' gặp sự cố khi thực thi: {e}"


def _format_action_call(tool_name: str, args: list, kwargs: dict) -> str:
    parts = [repr(a) for a in args] + [f"{k}={v!r}" for k, v in kwargs.items()]
    return f"{tool_name}({', '.join(parts)})"


_SCORE_OBS_RE = re.compile(r"Điểm tương thích giữa .*?: (\d{1,3})/100")


def _validate_final_answer(final_answer: str, transcript: str) -> str:
    """
    Guardrail code-level (bổ sung cho Guardrail #2 trong REACT_SYSTEM_PROMPT):
    Nếu transcript có Observation chứa điểm tương thích thật (từ tool
    calculate_compatibility_score), nhưng Final Answer của LLM lại nêu một
    con số KHÁC (hallucination), thì override bằng Observation thật thay vì
    tin tưởng LLM. Ngăn trường hợp LLM tự "làm tròn cho đẹp" hoặc bịa số.
    """
    real_scores = _SCORE_OBS_RE.findall(transcript)
    if not real_scores:
        return final_answer  # Không có điểm số nào để đối chiếu, giữ nguyên

    real_score = real_scores[-1]  # Lấy Observation điểm số gần nhất/cuối cùng
    claimed_scores = re.findall(r"(\d{1,3})\s*/\s*100", final_answer)

    if claimed_scores and real_score not in claimed_scores:
        last_score_obs_match = None
        for m in re.finditer(r"Observation:\s*(Điểm tương thích giữa.*?/100\.[^\n]*)", transcript):
            last_score_obs_match = m
        safe_text = last_score_obs_match.group(1) if last_score_obs_match else f"Điểm tương thích: {real_score}/100."
        print(
            f"🛡️ ANTI-HALLUCINATION GUARDRAIL TRIGGERED: LLM nêu điểm {claimed_scores} "
            f"nhưng Observation thật là {real_score}/100. Đã override Final Answer."
        )
        return (
            f"{safe_text} "
            f"(Lưu ý: câu trả lời đã được hệ thống hiệu chỉnh lại theo đúng dữ liệu thật từ tool, "
            f"tránh sai lệch so với kết quả tính toán gốc.)"
        )

    return final_answer


def run_react_agent(user_query: str, provider):
    """
    Vòng lặp ReAct Agent thật (Thought -> Action -> Observation) có Guardrails:
      - Mỗi vòng gọi LLM sinh Thought+Action dựa trên toàn bộ transcript.
      - Ứng dụng tự parse Action, tự gọi tool thật, tự chèn Observation thật
        (LLM không được tự bịa Observation).
      - Dừng khi có Final Answer hợp lệ, hoặc chạm MAX_ITERATIONS (Guardrail).
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    transcript = f"Question: {user_query}\n"
    step = 0
    final_answer = None

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        llm_output = provider.generate(transcript, system_prompt=REACT_SYSTEM_PROMPT)
        parsed = parse_llm_response(llm_output)

        if parsed["type"] == "final":
            final_answer = parsed["content"]
            print(f"🧠 {llm_output.strip()}")
            print(f"🏁 Final Answer: {final_answer}")
            break

        if parsed["type"] == "invalid":
            observation = (
                f"LỖI ĐỊNH DẠNG: {parsed['reason']} "
                "Hãy trả lời đúng định dạng 'Thought: ...\\nAction: tool_name(...)' "
                "hoặc 'Thought: ...\\nFinal Answer: ...'."
            )
            print(f"🧠 {llm_output.strip()}")
            print(f"👁️ Observation: {observation}")
            transcript += f"{llm_output.strip()}\nObservation: {observation}\n"
            continue

        tool_name, args, kwargs = parsed["tool"], parsed["args"], parsed["kwargs"]
        print(f"🧠 {llm_output.strip()}")
        print(f"🛠️ Action: {_format_action_call(tool_name, args, kwargs)}")

        observation = execute_tool(tool_name, args, kwargs)
        print(f"👁️ Observation: {observation}")

        transcript += f"{llm_output.strip()}\nObservation: {observation}\n"

    if final_answer is None:
        final_answer = (
            "Xin lỗi, tôi chưa thể xử lý đầy đủ yêu cầu này. Bạn có thể cung cấp "
            "thêm thông tin (vd: user_id chính xác) để tôi hỗ trợ tốt hơn không?"
        )
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
        print(f"🏁 Final Answer (Safe Fallback): {final_answer}")
    else:
        final_answer = _validate_final_answer(final_answer, transcript)

    return final_answer


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử câu test số 3
    sample_query = tests[2]["query"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)

    # DEMO 3: Câu bẫy (Edge Case) kiểm tra Guardrail #7 - Relationship Status
    edge_case = next((t for t in tests if t["id"] == "TC11"), None)
    if edge_case:
        print("\n--- DEMO 3: CHẠY TRÊN REACT AGENT (Edge Case - Guardrail #7) ---")
        run_react_agent(edge_case["query"], provider)