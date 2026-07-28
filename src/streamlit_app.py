"""
💘 CUPID AGENT — STREAMLIT DEMO UI
Giao diện demo gọi qua API backend (api.py) thay vì import trực tiếp tools/app,
mô phỏng kiến trúc client-server thật.

Chạy:
    1) Terminal 1: uvicorn api:app --reload --port 8000
    2) Terminal 2: streamlit run streamlit_app.py
"""

import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("CUPID_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Cupid Agent Demo", page_icon="💘", layout="wide")


# ---------------------------------------------------------------------------
# Helpers gọi API
# ---------------------------------------------------------------------------
def api_get(path: str):
    try:
        resp = requests.get(f"{API_BASE_URL}{path}", timeout=15)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Không kết nối được tới backend tại {API_BASE_URL}. Hãy chạy `uvicorn api:app --port 8000` trước."
    except requests.exceptions.HTTPError as e:
        return None, f"Lỗi API ({resp.status_code}): {resp.json().get('detail', str(e))}"
    except Exception as e:
        return None, f"Lỗi không xác định: {e}"


def api_post(path: str, payload: dict):
    try:
        resp = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Không kết nối được tới backend tại {API_BASE_URL}. Hãy chạy `uvicorn api:app --port 8000` trước."
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, f"Lỗi API ({resp.status_code}): {detail}"
    except Exception as e:
        return None, f"Lỗi không xác định: {e}"


# ---------------------------------------------------------------------------
# Header + trạng thái backend
# ---------------------------------------------------------------------------
st.title("💘 Cupid Agent — Demo")
st.caption("Trợ lý ghép đôi & phân tích độ tương thích, chạy trên kiến trúc ReAct Agent.")

health, health_err = api_get("/health")
if health_err:
    st.error(health_err)
    st.stop()
st.success(f"🔌 Backend đang chạy — LLM Provider: **{health['provider']}**")

meta, meta_err = api_get("/meta")
if meta_err:
    st.error(meta_err)
    st.stop()

tab_input, tab_analyze, tab_users = st.tabs(["📝 Nhập hồ sơ", "💞 Phân tích ghép đôi", "👥 Danh sách người dùng"])


# ---------------------------------------------------------------------------
# TAB 1: Nhập hồ sơ mới (đúng theo schema register_user_profile trong tools.py)
# ---------------------------------------------------------------------------
with tab_input:
    st.subheader("Nhập hồ sơ người dùng mới")
    st.caption("Các trường bám sát đúng schema mà `get_user_profile` / `calculate_compatibility_score` sử dụng trong `tools.py`.")

    with st.form("register_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            user_id = st.text_input("User ID *", placeholder="vd: user_005")
            name = st.text_input("Tên *", placeholder="vd: Hà")
            age = st.number_input("Tuổi *", min_value=18, max_value=100, value=25)
            city = st.text_input("Thành phố *", placeholder="vd: Hà Nội")
        with col2:
            mbti = st.selectbox("MBTI *", options=meta["mbti_options"])
            zodiac = st.selectbox("Cung hoàng đạo *", options=meta["zodiac_options"])
            relationship_status = st.selectbox(
                "Tình trạng mối quan hệ *", options=meta["relationship_status_options"]
            )

        interests_raw = st.text_input("Sở thích * (phân tách bởi dấu phẩy)", placeholder="vd: du lịch, đọc sách, cà phê")
        values_raw = st.text_input("Giá trị sống * (phân tách bởi dấu phẩy)", placeholder="vd: gia đình, ổn định")

        submitted = st.form_submit_button("✅ Lưu hồ sơ", type="primary")

        if submitted:
            interests = [i.strip() for i in interests_raw.split(",") if i.strip()]
            values = [v.strip() for v in values_raw.split(",") if v.strip()]

            if not user_id or not name or not city or not interests or not values:
                st.warning("Vui lòng điền đầy đủ các trường bắt buộc (*).")
            else:
                result, err = api_post("/users", {
                    "user_id": user_id,
                    "name": name,
                    "age": int(age),
                    "city": city,
                    "mbti": mbti,
                    "zodiac": zodiac,
                    "interests": interests,
                    "values": values,
                    "relationship_status": relationship_status,
                })
                if err:
                    st.error(err)
                else:
                    st.success(f"Đã lưu hồ sơ **{result['user_id']}** thành công! Chuyển sang tab 'Phân tích ghép đôi' để thử ngay.")
                    st.cache_data.clear()


# ---------------------------------------------------------------------------
# TAB 2: Phân tích ghép đôi — gọi /compatibility, hiển thị trace ReAct trực quan
# ---------------------------------------------------------------------------
with tab_analyze:
    st.subheader("Phân tích độ tương thích giữa 2 người")

    users_data, users_err = api_get("/users")
    if users_err:
        st.error(users_err)
    else:
        users = users_data["users"]
        options = {f"{u['user_id']} — {u['name']} ({u['city']}, {u['age']} tuổi)": u["user_id"] for u in users}

        col_a, col_b = st.columns(2)
        with col_a:
            label_a = st.selectbox("Người thứ nhất", options=list(options.keys()), key="user_a")
        with col_b:
            remaining = [k for k in options.keys() if k != label_a]
            label_b = st.selectbox("Người thứ hai", options=remaining, key="user_b")

        if st.button("🔍 Phân tích ngay", type="primary"):
            user_id_a, user_id_b = options[label_a], options[label_b]

            with st.spinner("Agent đang suy luận (Thought → Action → Observation)..."):
                result, err = api_post("/compatibility", {"user_id_a": user_id_a, "user_id_b": user_id_b})

            if err:
                st.error(err)
            else:
                if result["guardrail_triggered"]:
                    st.warning("🛡️ Guardrail giới hạn vòng lặp đã được kích hoạt (Agent không kết luận được trong số bước cho phép).")

                st.markdown("### 🏁 Kết quả")
                st.info(result["final_answer"])

                st.markdown("### 🧠 Trace suy luận (ReAct Loop)")
                for step in result["trace"]:
                    icon = "🏁" if step["is_final"] else "🔄"
                    with st.expander(f"{icon} Bước {step['step']}", expanded=True):
                        st.markdown(f"**Thought:** {step['thought']}")
                        if step.get("action"):
                            st.code(f"Action: {step['action']}", language="text")
                        if step.get("observation"):
                            st.markdown(f"**Observation:** {step['observation']}")


# ---------------------------------------------------------------------------
# TAB 3: Danh sách người dùng hiện có (để biết user_id nào đang tồn tại)
# ---------------------------------------------------------------------------
with tab_users:
    st.subheader("Danh sách người dùng trong hệ thống")
    users_data, users_err = api_get("/users")
    if users_err:
        st.error(users_err)
    else:
        st.dataframe(users_data["users"], use_container_width=True, hide_index=True)
        st.caption("Danh sách này gồm cả dữ liệu mock có sẵn và các hồ sơ vừa nhập ở tab 'Nhập hồ sơ'.")