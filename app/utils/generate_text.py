from google import genai
from google.genai import types
from datetime import date, datetime
from uuid import uuid4
from decimal import Decimal

from app.core.config import settings
from app.enums.operation_enum import AttendanceStatus, EvaluationStatus
from app.schemas.student_attendance import StudentAttendanceResponse
from app.utils.load_instruction_from_file import load_instruction_from_file

# Model hợp lệ
MODEL_ID = "gemini-3.1-flash-lite-preview"


# ==========================================
# 1. KHỞI TẠO SẴN (PRE-LOAD/WARM-UP)
# ==========================================
# Chạy ngay khi file này được import hoặc thực thi
def _init_genai_client() -> genai.Client:
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is empty. Please set it in environment or .env file.")
    return genai.Client(api_key=api_key)


# Biến toàn cục lưu trữ Client (Tái sử dụng kết nối mạng)
GLOBAL_GENAI_CLIENT = _init_genai_client()

# Biến toàn cục lưu trữ Prompt (Đọc từ ổ cứng 1 lần, lưu hẳn lên RAM)
GLOBAL_SYSTEM_INSTRUCTION = load_instruction_from_file("instruction/tts_agent.md")


# ==========================================
# 2. HÀM XỬ LÝ CHÍNH (AGENT EXECUTION)
# ==========================================
async def generate_receptionist_greeting_stream(record: StudentAttendanceResponse):
    """
    Nhận dữ liệu điểm danh và trả về câu chào từ AI Agent.
    Không tốn thời gian đọc file hay tạo Client nữa.
    """
    # 1. Chuyển dữ liệu Pydantic → JSON string
    student_data_json = record.model_dump_json(
        by_alias=True,
        exclude_none=True,
        exclude={
            "attendance_id", "enrollment_id", "student_id",
            "class_schedule_id", "updated_at"
        },
    )

    print("\n[DEBUG] JSON GỬI CHO LLM:", student_data_json, "\n")

    try:
        # 2. Dùng biến toàn cục đã khởi tạo sẵn để gọi API ngay lập tức
        response = await GLOBAL_GENAI_CLIENT.aio.models.generate_content(
            model=MODEL_ID,
            contents=student_data_json,
            config=types.GenerateContentConfig(
                system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
                temperature=0.6,
                max_output_tokens=2048,
            ),
        )
        print("AI lễ tân nói:", response.text)
        return response.text

    except Exception as e:
        print(f"\nLỗi khi gọi LLM: {e}")
        return f"Chào mừng {record.student_name} đã đến lớp!"  # Đã có sẵn return ở nhánh lỗi

# ==========================================
# 3. TEST THỬ VỚI DỮ LIỆU MẪU
# ==========================================
if __name__ == "__main__":
    from app.schemas.student_attendance import StudentAttendanceResponse
    from app.schemas.tuition_payment import ActiveClassStatus, TuitionStatusResponse

    mock_tuition = TuitionStatusResponse(
        studentId="7fc3acfa-9508-435f-9566-05841490cfa2",
        studentCode="VQ_nambb_181008",
        fullName="Bùi Bảo Nam",
        hasPaidCurrentMonth=True,
        currentMonth=4,
        currentYear=2026,
        activeClasses=[
            {
                "enrollmentId": "60eb4e95-1855-4687-adc4-5158f228485b",
                "scheduleId": "P43C1",
                "paid": True,
                "amountAllocated": 450000.00
            },
            {
                "enrollmentId": "1ea5d082-eaf6-4028-a32c-1bcf4f1ced6b",
                "scheduleId": "P45C1",
                "paid": True,
                "amountAllocated": 450000.00
            },
            {
                "enrollmentId": "14de84a1-c3a0-4193-812f-3c4b9938df01",
                "scheduleId": "P21C1",
                "paid": True,
                "amountAllocated": 450000.00
            },
            {
                "enrollmentId": "422d165e-77a8-4bec-aec0-26862907da6c",
                "scheduleId": "P14C1",
                "paid": True,
                "amountAllocated": 450000.00
            },
            {
                "enrollmentId": "2a8ce739-e95f-45a4-b6b1-2d92d345979c",
                "scheduleId": "P14C1",
                "paid": True,
                "amountAllocated": 450000.00
            }
        ]
    )

    mock_attendance = StudentAttendanceResponse(
        attendance_id="ATT123",
        enrollment_id="ENR123",
        student_id=mock_tuition.student_id,
        student_name="Nguyen Van A",
        tuition_status=mock_tuition,
        class_schedule_id="SCH001",
        session_date=date.today(),
        attendance_status=AttendanceStatus.PRESENT,
        check_in_time=datetime.now(),
        evaluation_status=EvaluationStatus.GOOD,
        evaluated_by_coach_name="HLV Đạt",
        updated_at=datetime.now(),
    )

    greeting = generate_receptionist_greeting_stream(mock_attendance)
    print("AI le tan noi:\n", greeting)
