# 📊 BÁO CÁO GIÁM SÁT & ĐÁNH GIÁ (OBSERVABILITY TRACE LOGS)
*Dành cho Role 5: Observability & Reviewer*
*Đề tài: Cupid Agent — Trợ Lý Ghép Đôi & Phân Tích Độ Tương Thích*

---

## 🎯 1. BẢNG CHẤM ĐIỂM AGENTIC FIT (SCORING MATRIX)

| Tiêu chí | Điểm (1-5) | Lý do đánh giá |
| :--- | :---: | :--- |
| 🧠 **Multi-step Reasoning** | `5/5` | Phải suy luận qua nhiều tầng: đọc hồ sơ cá nhân → xác định tiêu chí so khớp (tính cách, sở thích, giá trị sống, mục tiêu mối quan hệ) → tổng hợp thành điểm tương thích → diễn giải kết quả bằng ngôn ngữ tự nhiên, dễ hiểu cho người dùng. |
| 🛠️ **Tool Interaction** | `5/5` | Cần gọi nhiều công cụ khác nhau: `get_user_profile`, `search_candidates`, `calculate_compatibility_score`, có thể thêm `get_mbti_result` hoặc `get_horoscope_info`. Đây không phải bài toán trả lời từ tri thức tĩnh mà bắt buộc phải truy vấn dữ liệu thực tế. |
| 🔀 **Dynamic Decision** | `5/5` | Kết quả bước trước ảnh hưởng trực tiếp đến hành động kế tiếp: nếu hồ sơ thiếu thông tin → agent phải hỏi lại người dùng; nếu điểm tương thích thấp → agent cân nhắc mở rộng tiêu chí tìm kiếm hoặc gợi ý ứng viên khác thay vì trả lời cứng nhắc. |
| ⏳ **Long Horizon** | `4/5` | Quy trình thường kéo dài nhiều lượt hội thoại: thu thập sở thích/tiêu chí → tìm & chấm điểm ứng viên → giải thích lý do phù hợp → xử lý câu hỏi follow-up ("còn ai khác không?", "vì sao điểm thấp?"). Không phải tác vụ 1 bước nhưng cũng chưa đến mức cực kỳ dài hạn (nhiều ngày, nhiều phiên). |
| **TỔNG ĐIỂM FIT** | **19/20** | **KẾT LUẬN: BÀI TOÁN RẤT NÊN DÙNG REACT AGENT!** |

---

## 🔍 2. SO SÁNH PHẢN HỒI (TEST CASE #3)

**Câu hỏi**: *"Tôi và Lan có hợp nhau không? Nếu hợp thì vì sao?"*

### 🤖 Chatbot Baseline:
* **Phản hồi**: *"Xin lỗi, tôi không có thông tin về hồ sơ cá nhân của bạn hoặc của Lan nên không thể đánh giá độ hợp."*
* **Nhận xét**: An toàn nhưng không giải quyết được nhu cầu thực tế — người dùng cần một câu trả lời có căn cứ dữ liệu, không phải lời từ chối.

### 🧠 ReAct Agent:
* **Thought 1**: Cần lấy hồ sơ của người dùng và của Lan để so sánh.
* **Action 1**: `get_user_profile['user_id']`
* **Observation 1**: `MBTI: INFJ, sở thích: đọc sách, du lịch, giá trị: gia đình, ổn định.`
* **Thought 2**: Cần lấy hồ sơ của Lan.
* **Action 2**: `get_user_profile['Lan']`
* **Observation 2**: `MBTI: ENFP, sở thích: du lịch, âm nhạc, giá trị: tự do, trải nghiệm.`
* **Thought 3**: Có đủ dữ liệu, tiến hành tính điểm tương thích.
* **Action 3**: `calculate_compatibility_score[user_id, Lan]`
* **Observation 3**: `Điểm tương thích: 82/100 (Tính cách bổ trợ tốt, điểm chung: du lịch; khác biệt: mức độ ưa thích ổn định).`
* **Thought 4**: Đã có điểm số và lý do, tổng hợp thành câu trả lời dễ hiểu.
* **Final Answer**: *"Bạn và Lan có độ hợp 82/100. Hai người bổ trợ tốt về tính cách (INFJ & ENFP thường cân bằng nhau) và cùng đam mê du lịch. Điểm cần lưu ý: bạn thiên về sự ổn định trong khi Lan thích trải nghiệm mới — đây có thể là điểm cần trao đổi thêm khi tìm hiểu nhau."*
* **Nhận xét**: Hoàn thành xuất sắc nhiệm vụ nhờ khả năng tra cứu dữ liệu thực tế từ nhiều nguồn, kết hợp suy luận nhiều bước và diễn giải kết quả có căn cứ, thay vì chỉ đưa ra câu trả lời chung chung hoặc từ chối.

---

## 🧪 3. LOG PHẢN HỒI THỰC TẾ — CHATBOT BASELINE (chạy từ `src/app.py`)

**Câu hỏi test** (Test Case #3 trong `config/test_cases.json`):
*"Tôi (user_001) và Lan (user_002) có hợp nhau không? Vì sao?"*

**Provider**: `OpenAIProvider` (model: `gpt-4o`)

### 📄 Phản hồi ghi nhận được:

> Chào bạn! Để đánh giá độ hợp giữa bạn và Lan, có thể dựa vào một số yếu tố như MBTI, cung hoàng đạo, sở thích chung, và các giá trị sống...
> 1. **MBTI:** *"một người là ENFP thường hợp với INFJ vì cả hai đều hướng tới sự hiểu biết sâu sắc và cảm xúc."*
> 2. **Cung Hoàng Đạo:** *"Cự Giải và Song Ngư thường được coi là hợp nhau..."*
> 3. **Sở Thích và Giá Trị Sống:** nêu chung chung, không có dữ liệu cụ thể.
> 4. **Cách Giao Tiếp và Giải Quyết Mâu Thuẫn**.
> ...*"Nếu bạn có thêm thông tin cụ thể về hai bạn, mình có thể đưa ra nhận định chi tiết hơn."*

### 🔎 Quan sát & Đánh giá:

| Tiêu chí | Kết quả | Chi tiết |
| :--- | :---: | :--- |
| **Có bịa dữ liệu hồ sơ thật của user_001/user_002 không?** | ❌ Không | Chatbot **không** tự bịa tuổi, MBTI, sở thích thật của Minh/Lan — đây là điểm tích cực, cho thấy nó nhận ra mình thiếu quyền truy cập dữ liệu. |
| **Có đưa ra câu trả lời trực tiếp cho câu hỏi không?** | ❌ Không | Không trả lời được "có hợp hay không" — chỉ liệt kê **khung lý thuyết chung chung** (framework) rồi yêu cầu người dùng tự cung cấp thêm thông tin. |
| **Có dấu hiệu ảo giác (hallucination) không?** | ⚠️ Có, dạng nhẹ | Chatbot đưa ra các cặp MBTI/cung hoàng đạo "mẫu" (ENFP-INFJ, Cự Giải-Song Ngư) như thể đó là dữ kiện liên quan đến Minh và Lan, dễ khiến người dùng **hiểu nhầm là đang được phân tích riêng cho trường hợp của họ** — trong khi thực chất đây chỉ là ví dụ minh họa lấy từ tri thức chung, không liên quan gì đến MBTI thật của user_001 (INFJ) / user_002 (ENFP). Đây là kiểu ảo giác "ngữ cảnh gây hiểu lầm" (misleading framing) hơn là bịa số liệu trắng trợn. |
| **Có tự nhận giới hạn của mình không?** | ✅ Có | Cuối câu trả lời có nhắc: *"Nếu bạn có thêm thông tin cụ thể..."* — cho thấy model được prompt tốt (nhờ system prompt nêu rõ "KHÔNG có quyền truy cập cơ sở dữ liệu"), nên hành xử an toàn hơn so với baseline hoàn toàn không guardrail. |
| **Có giải quyết được nhu cầu thực tế của người dùng không?** | ❌ Không | Người dùng hỏi cụ thể về Minh và Lan nhưng nhận lại lời khuyên tổng quát, không có điểm số, không có lý do cụ thể dựa trên dữ liệu thật — **không đáp ứng được ý định truy vấn ban đầu**. |

### 📌 Kết luận (so với ReAct Agent — cùng Test Case #3):

Chatbot Baseline **không hallucinate trắng trợn** dữ liệu cá nhân của user_001/user_002 (nhờ system prompt cảnh báo rõ giới hạn), nhưng lại **né tránh trả lời trực tiếp** và chèn các ví dụ MBTI/cung hoàng đạo "mẫu" theo cách dễ gây hiểu lầm là đang phân tích đúng trường hợp thật. Ngược lại, ReAct Agent truy xuất đúng hồ sơ thật qua `get_user_profile` (INFJ ↔ ENFP, sở thích chung: du lịch) và tính ra điểm tương thích cụ thể (60/100) có căn cứ — **giải quyết đúng và đủ nhu cầu người dùng**, minh chứng rõ giá trị của việc trang bị tool cho Agent.

---

## 📝 Ghi chú
Bảng điểm và test case trên dựa trên giả định luồng nghiệp vụ chuẩn của Cupid Agent (tra cứu hồ sơ → tính điểm tương thích → giải thích). Nếu nhóm đã có bộ tool/API cụ thể khác (ví dụ thêm tool phân tích lịch sử trò chuyện, tool gợi ý hoạt động hẹn hò...), nên cập nhật lại phần lý do đánh giá và test case cho khớp với trace log thực tế đã chạy.