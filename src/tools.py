"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà Cupid Agent (ReAct Agent) có thể gọi.

Chủ đề: Cupid Agent - Trợ Lý Ghép Đôi & Phân Tích Độ Tương Thích
"""

# ---------------------------------------------------------------------------
# Mock database (giả lập dữ liệu người dùng để demo, không kết nối DB thật)
# ---------------------------------------------------------------------------
_MOCK_USERS = {
    "user_001": {
        "name": "Minh",
        "age": 27,
        "city": "Hà Nội",
        "mbti": "INFJ",
        "zodiac": "Bọ Cạp",
        "interests": ["đọc sách", "du lịch", "cà phê"],
        "values": ["gia đình", "ổn định"],
    },
    "user_002": {
        "name": "Lan",
        "age": 26,
        "city": "Hà Nội",
        "mbti": "ENFP",
        "zodiac": "Sư Tử",
        "interests": ["du lịch", "âm nhạc", "nhiếp ảnh"],
        "values": ["tự do", "trải nghiệm"],
    },
    "user_003": {
        "name": "Huy",
        "age": 29,
        "city": "TP.HCM",
        "mbti": "ISTJ",
        "zodiac": "Kim Ngưu",
        "interests": ["thể thao", "nấu ăn"],
        "values": ["ổn định", "sự nghiệp"],
    },
}


def get_user_profile(user_id: str) -> str:
    """
    Tra cứu hồ sơ cá nhân của một người dùng trong hệ thống Cupid Agent.

    Dùng khi cần biết thông tin cơ bản (tuổi, thành phố, MBTI, cung hoàng đạo,
    sở thích, giá trị sống) để phục vụ các bước phân tích tương thích tiếp theo.

    Args:
        user_id (str): Mã định danh người dùng (Ví dụ: 'user_001').

    Returns:
        str: Thông tin hồ sơ dạng văn bản mô tả, hoặc thông báo lỗi nếu
            không tìm thấy user_id trong hệ thống.
    """
    user = _MOCK_USERS.get(user_id)
    if not user:
        return f"LỖI: Không tìm thấy hồ sơ cho user_id '{user_id}'."
    return (
        f"Hồ sơ {user_id} ({user['name']}): {user['age']} tuổi, sống tại {user['city']}. "
        f"MBTI: {user['mbti']}, Cung: {user['zodiac']}. "
        f"Sở thích: {', '.join(user['interests'])}. "
        f"Giá trị sống: {', '.join(user['values'])}."
    )


def search_candidates(city: str = "", min_age: int = 18, max_age: int = 99) -> str:
    """
    Tìm kiếm danh sách ứng viên tiềm năng trong hệ thống theo tiêu chí lọc.

    Dùng khi người dùng muốn tìm người phù hợp nhưng chưa chỉ định một
    người cụ thể (ví dụ: "tìm giúp tôi ai đó ở Hà Nội, 25-30 tuổi").

    Args:
        city (str, optional): Thành phố cần lọc (Ví dụ: 'Hà Nội'). Để trống
            nếu không giới hạn khu vực.
        min_age (int, optional): Độ tuổi tối thiểu. Mặc định là 18.
        max_age (int, optional): Độ tuổi tối đa. Mặc định là 99.

    Returns:
        str: Danh sách user_id thỏa điều kiện kèm thông tin tóm tắt, hoặc
            thông báo nếu không tìm thấy ứng viên nào.
    """
    results = []
    for uid, user in _MOCK_USERS.items():
        if city and city.lower() not in user["city"].lower():
            continue
        if not (min_age <= user["age"] <= max_age):
            continue
        results.append(f"{uid} ({user['name']}, {user['age']} tuổi, {user['city']})")

    if not results:
        return f"Không tìm thấy ứng viên nào phù hợp với tiêu chí (city={city}, {min_age}-{max_age} tuổi)."
    return "Danh sách ứng viên phù hợp:\n" + "\n".join(f"- {r}" for r in results)


def calculate_compatibility_score(user_id_a: str, user_id_b: str) -> str:
    """
    Tính điểm tương thích giữa hai người dùng dựa trên MBTI, sở thích chung
    và giá trị sống.

    Đây là tool trung tâm của Cupid Agent, thường được gọi sau khi đã có
    đủ hồ sơ của cả hai người (qua get_user_profile).

    Args:
        user_id_a (str): Mã định danh người thứ nhất.
        user_id_b (str): Mã định danh người thứ hai.

    Returns:
        str: Điểm tương thích (0-100) kèm lý do ngắn gọn, hoặc thông báo lỗi
            nếu một trong hai user_id không tồn tại.
    """
    user_a = _MOCK_USERS.get(user_id_a)
    user_b = _MOCK_USERS.get(user_id_b)
    if not user_a or not user_b:
        missing = user_id_a if not user_a else user_id_b
        return f"LỖI: Không thể tính điểm tương thích vì không tìm thấy hồ sơ '{missing}'."

    shared_interests = set(user_a["interests"]) & set(user_b["interests"])
    shared_values = set(user_a["values"]) & set(user_b["values"])

    score = 50
    score += len(shared_interests) * 10
    score += len(shared_values) * 15
    score = min(score, 100)

    return (
        f"Điểm tương thích giữa {user_id_a} và {user_id_b}: {score}/100. "
        f"Sở thích chung: {', '.join(shared_interests) or 'không có'}. "
        f"Giá trị chung: {', '.join(shared_values) or 'không có'}."
    )


def get_mbti_analysis(mbti_type_a: str, mbti_type_b: str) -> str:
    """
    Phân tích mức độ hợp giữa hai nhóm tính cách MBTI.

    Dùng để giải thích sâu hơn lý do đằng sau điểm tương thích tổng, khi
    người dùng muốn hiểu rõ khía cạnh tính cách thay vì chỉ nhận một con số.

    Args:
        mbti_type_a (str): Loại MBTI thứ nhất (Ví dụ: 'INFJ').
        mbti_type_b (str): Loại MBTI thứ hai (Ví dụ: 'ENFP').

    Returns:
        str: Mô tả ngắn gọn về mức độ hợp giữa hai loại MBTI, hoặc thông báo
            lỗi nếu định dạng MBTI không hợp lệ (không đủ 4 ký tự chuẩn).
    """
    valid_letters = {
        0: {"I", "E"}, 1: {"N", "S"}, 2: {"F", "T"}, 3: {"J", "P"},
    }
    a, b = mbti_type_a.strip().upper(), mbti_type_b.strip().upper()

    def _is_valid(mbti: str) -> bool:
        return len(mbti) == 4 and all(mbti[i] in valid_letters[i] for i in range(4))

    if not _is_valid(a) or not _is_valid(b):
        return f"LỖI: Định dạng MBTI không hợp lệ ('{mbti_type_a}' hoặc '{mbti_type_b}')."

    shared_letters = sum(1 for i in range(4) if a[i] == b[i])
    if shared_letters >= 3:
        return f"{a} và {b} rất tương đồng ({shared_letters}/4 chữ cái trùng), dễ thấu hiểu nhau nhưng có thể thiếu sự mới mẻ."
    if shared_letters <= 1:
        return f"{a} và {b} khá trái ngược ({shared_letters}/4 chữ cái trùng): có thể bổ trợ tốt cho nhau nhưng dễ xảy ra bất đồng nếu không thấu hiểu."
    return f"{a} và {b} có sự cân bằng vừa phải ({shared_letters}/4 chữ cái trùng): vừa có điểm chung để kết nối, vừa có khác biệt để bổ trợ nhau."


def get_shared_interests(user_id_a: str, user_id_b: str) -> str:
    """
    Tìm danh sách sở thích/hoạt động chung giữa hai người dùng.

    Thường dùng làm bước trung gian trước khi gọi suggest_date_activity,
    để đưa ra gợi ý hẹn hò sát với sở thích thực tế của cả hai.

    Args:
        user_id_a (str): Mã định danh người thứ nhất.
        user_id_b (str): Mã định danh người thứ hai.

    Returns:
        str: Danh sách sở thích chung, hoặc thông báo nếu không có điểm chung
            nào hoặc không tìm thấy hồ sơ.
    """
    user_a = _MOCK_USERS.get(user_id_a)
    user_b = _MOCK_USERS.get(user_id_b)
    if not user_a or not user_b:
        missing = user_id_a if not user_a else user_id_b
        return f"LỖI: Không tìm thấy hồ sơ '{missing}'."

    shared = set(user_a["interests"]) & set(user_b["interests"])
    if not shared:
        return f"{user_id_a} và {user_id_b} không có sở thích chung nào được ghi nhận."
    return f"Sở thích chung giữa {user_id_a} và {user_id_b}: {', '.join(shared)}."


def get_zodiac_compatibility(sign_a: str, sign_b: str) -> str:
    """
    Tra cứu độ hợp giữa hai cung hoàng đạo theo quan niệm chiêm tinh phổ biến.

    Đây là tool mang tính tham khảo/giải trí, hỗ trợ thêm góc nhìn bên cạnh
    điểm tương thích tính từ MBTI và sở thích thực tế.

    Args:
        sign_a (str): Cung hoàng đạo thứ nhất (Ví dụ: 'Sư Tử').
        sign_b (str): Cung hoàng đạo thứ hai (Ví dụ: 'Bạch Dương').

    Returns:
        str: Mô tả ngắn gọn về độ hợp giữa hai cung, hoặc thông báo lỗi nếu
            không nhận diện được tên cung.
    """
    known_signs = {
        "bạch dương", "kim ngưu", "song tử", "cự giải", "sư tử", "xử nữ",
        "thiên bình", "bọ cạp", "nhân mã", "ma kết", "bảo bình", "song ngư",
    }
    a, b = sign_a.strip().lower(), sign_b.strip().lower()
    if a not in known_signs or b not in known_signs:
        return f"LỖI: Không nhận diện được cung hoàng đạo '{sign_a}' hoặc '{sign_b}'."

    fire_signs = {"bạch dương", "sư tử", "nhân mã"}
    if a in fire_signs and b in fire_signs:
        return f"{sign_a} và {sign_b} đều thuộc nhóm Hỏa Cung: năng lượng cao, dễ đồng điệu nhưng cũng dễ va chạm cái tôi."
    return f"{sign_a} và {sign_b} thuộc hai nhóm cung khác nhau: có thể bổ trợ tốt nếu biết dung hòa khác biệt tính cách."


def suggest_date_activity(shared_interests: str) -> str:
    """
    Gợi ý hoạt động hẹn hò phù hợp dựa trên danh sách sở thích chung.

    Thường được gọi ở cuối chuỗi suy luận, sau khi đã xác nhận hai người có
    độ tương thích đủ cao và có sở thích chung cụ thể.

    Args:
        shared_interests (str): Chuỗi mô tả sở thích chung, phân tách bởi dấu
            phẩy (Ví dụ: 'du lịch, âm nhạc').

    Returns:
        str: Gợi ý hoạt động hẹn hò cụ thể tương ứng với sở thích được cung cấp.
    """
    interests = [i.strip().lower() for i in shared_interests.split(",") if i.strip()]
    if not interests:
        return "Không có sở thích chung cụ thể để gợi ý hoạt động; nên bắt đầu bằng một buổi cà phê để tìm hiểu nhau."

    suggestions = []
    activity_map = {
        "du lịch": "cùng lên kế hoạch một chuyến đi ngắn ngày gần thành phố",
        "âm nhạc": "đi xem một buổi biểu diễn nhạc sống hoặc acoustic",
        "đọc sách": "ghé một quán cà phê sách để cùng đọc và trò chuyện",
        "cà phê": "hẹn nhau tại một quán cà phê mới mở để khám phá cùng nhau",
        "nhiếp ảnh": "đi dạo phố cổ và cùng chụp ảnh street photography",
        "thể thao": "cùng tham gia một buổi tập gym hoặc chơi cầu lông",
        "nấu ăn": "cùng vào bếp nấu một món ăn mới tại nhà",
    }
    for interest in interests:
        if interest in activity_map:
            suggestions.append(activity_map[interest])

    if not suggestions:
        return f"Chưa có gợi ý sẵn cho sở thích '{shared_interests}'; gợi ý chung: một buổi hẹn cà phê nhẹ nhàng để tìm hiểu nhau."
    return "Gợi ý hoạt động hẹn hò: " + "; ".join(suggestions) + "."


def get_chat_history_summary(user_id_a: str, user_id_b: str) -> str:
    """
    Tóm tắt lịch sử trò chuyện giữa hai người dùng để đánh giá mức độ
    tương tác và sự quan tâm thực tế, bổ sung cho điểm tương thích tính
    thuần túy từ hồ sơ tĩnh.

    Dùng khi người dùng muốn biết liệu độ "hợp trên giấy" có phản ánh đúng
    tương tác thực tế hay không (Ví dụ: "chúng tôi nhắn tin có ổn không?").

    Args:
        user_id_a (str): Mã định danh người thứ nhất.
        user_id_b (str): Mã định danh người thứ hai.

    Returns:
        str: Tóm tắt mức độ tương tác (tần suất nhắn tin, mức độ phản hồi),
            hoặc thông báo nếu chưa có lịch sử trò chuyện hoặc không tìm
            thấy hồ sơ.
    """
    user_a = _MOCK_USERS.get(user_id_a)
    user_b = _MOCK_USERS.get(user_id_b)
    if not user_a or not user_b:
        missing = user_id_a if not user_a else user_id_b
        return f"LỖI: Không tìm thấy hồ sơ '{missing}'."

    # Dữ liệu giả lập vì đây là bản mock chưa kết nối hệ thống chat thật.
    return (
        f"Chưa có dữ liệu lịch sử trò chuyện thực tế giữa {user_id_a} và {user_id_b} "
        f"trong hệ thống demo này. Trong bản triển khai thật, tool này sẽ trả về "
        f"tần suất nhắn tin, thời gian phản hồi trung bình và sắc thái cảm xúc (tích cực/trung lập/tiêu cực)."
    )


def flag_red_flags(user_id: str) -> str:
    """
    Kiểm tra hồ sơ người dùng để phát hiện các dấu hiệu cảnh báo (red flag)
    tiềm ẩn dựa trên thông tin đã khai báo (ví dụ mâu thuẫn giá trị sống rõ rệt
    với các tiêu chí an toàn của nền tảng).

    Dùng như một bước kiểm duyệt bổ sung trước khi Agent đưa ra gợi ý ghép đôi
    chính thức, không thay thế cho quy trình kiểm duyệt/an toàn thực tế của
    nền tảng.

    Args:
        user_id (str): Mã định danh người dùng cần kiểm tra.

    Returns:
        str: Thông báo không phát hiện red flag, hoặc danh sách cảnh báo nếu
            có; trả về lỗi nếu không tìm thấy hồ sơ.
    """
    user = _MOCK_USERS.get(user_id)
    if not user:
        return f"LỖI: Không tìm thấy hồ sơ cho user_id '{user_id}'."
    # Đây là bản mock đơn giản, luôn trả về "an toàn" cho dữ liệu demo.
    return f"Không phát hiện dấu hiệu cảnh báo nào trong hồ sơ {user_id}."


# ---------------------------------------------------------------------------
# Danh sách các tool được đăng ký để Agent sử dụng
# ---------------------------------------------------------------------------
AVAILABLE_TOOLS = {
    "get_user_profile": get_user_profile,
    "search_candidates": search_candidates,
    "calculate_compatibility_score": calculate_compatibility_score,
    "get_shared_interests": get_shared_interests,
    "get_zodiac_compatibility": get_zodiac_compatibility,
    "get_mbti_analysis": get_mbti_analysis,
    "get_chat_history_summary": get_chat_history_summary,
    "suggest_date_activity": suggest_date_activity,
    "flag_red_flags": flag_red_flags,
}