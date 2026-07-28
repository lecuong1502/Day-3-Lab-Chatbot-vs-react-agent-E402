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

## 📝 Ghi chú
Bảng điểm và test case trên dựa trên giả định luồng nghiệp vụ chuẩn của Cupid Agent (tra cứu hồ sơ → tính điểm tương thích → giải thích). Nếu nhóm đã có bộ tool/API cụ thể khác (ví dụ thêm tool phân tích lịch sử trò chuyện, tool gợi ý hoạt động hẹn hò...), nên cập nhật lại phần lý do đánh giá và test case cho khớp với trace log thực tế đã chạy.