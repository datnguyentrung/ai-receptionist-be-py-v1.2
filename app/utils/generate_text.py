import json
import logging
import base64
from typing import Any
from google import genai
from google.genai import types
from google.genai.types import ThinkingLevel

from app.core.config import settings
from app.enums.operation_enum import AttendanceStatus, EvaluationStatus
from app.schemas.student_attendance import StudentAttendanceResponse
from app.utils.load_instruction_from_file import load_instruction_from_file

# Danh sách model để fallback - Sắp xếp từ ưu tiên nhất đến dự phòng
MODELS_TO_TRY = [
    "gemini-3-flash-preview",  # Sáng tạo nhất, hỗ trợ Thinking High
    "gemini-3.1-flash-lite-preview",  # Nhanh, nhẹ
    "gemini-3.1-pro-preview",
    "gemini-2.0-flash",  # Ổn định
    "gemini-1.5-flash-latest",  # Dự phòng cuối cùng
]


# ==========================================
# 1. KHỞI TẠO VÀ HELPER
# ==========================================
def _init_genai_client() -> genai.Client:
    api_key = (settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is empty.")
    return genai.Client(api_key=api_key)


GLOBAL_GENAI_CLIENT = _init_genai_client()
GLOBAL_SYSTEM_INSTRUCTION = load_instruction_from_file("instruction/tts_agent.md")


def _safe_json_loads(text: str, default: dict) -> dict:
    """Parse JSON an toàn, tránh crash backend nếu AI trả về chuỗi lạ"""
    try:
        clean_text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception:
        return default


# ==========================================
# 2. CORE FALLBACK LOGIC
# ==========================================
async def generate_with_fallback_async(
        contents: list[types.Content],
        config: types.GenerateContentConfig
) -> str:
    """
    Hàm gọi API bất đồng bộ với cơ chế đổi model khi gặp lỗi
    """
    for model_id in MODELS_TO_TRY:
        try:
            # SỬ DỤNG generate_content THAY VÌ generate_content_stream
            # Đảm bảo nhận cục JSON hoàn chỉnh, không bị gãy chunk
            response = await GLOBAL_GENAI_CLIENT.aio.models.generate_content(
                model=model_id,
                contents=contents,
                config=config,
            )

            if response.text:
                return response.text

        except Exception as e:
            print(f"⚠️ Model '{model_id}' thất bại: {e}")
            continue

    raise RuntimeError("Tất cả các model Gemini đều không phản hồi.")


# ==========================================
# 3. HÀM XỬ LÝ CHÍNH (AI RECEPTIONIST)
# ==========================================
async def generate_receptionist_greeting_stream(record: StudentAttendanceResponse) -> str:
    """
    Hàm sinh câu chào AI với đầy đủ tính năng:
    Fallback + Thinking + Structured Output (JSON)
    """

    # 1. Chuẩn bị data
    student_data = record.model_dump_json(
        by_alias=True,
        exclude_none=True,
        exclude={"attendance_id", "updated_at"}
    )

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"Dữ liệu học viên: {student_data}")]
        )
    ]

    # 2. Cấu hình (Áp dụng đúng cấu trúc của Google AI Studio)
    generate_content_config = types.GenerateContentConfig(
        system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
        response_mime_type="application/json",
        response_schema=genai.types.Schema(
            type=genai.types.Type.OBJECT,
            required=["text"],
            properties={
                "text": genai.types.Schema(type=genai.types.Type.STRING),
            },
        ),
        temperature=0.9,
    )

    try:
        # 3. Gọi xử lý với cơ chế Fallback
        raw_response = await generate_with_fallback_async(
            contents=contents,
            config=generate_content_config
        )

        # 4. Parse kết quả JSON
        result_dict = _safe_json_loads(raw_response, {"text": ""})
        final_greeting = result_dict.get("text", "")

        if not final_greeting:
            raise ValueError("AI trả về chuỗi JSON rỗng")

        print(f"🤖 AI Lễ tân: {final_greeting}")
        return final_greeting

    except Exception as e:
        print(f"🚨 Lỗi nghiêm trọng AI Agent: {e}")
        # Phương án dự phòng cuối cùng
        student_name = getattr(record, 'student_name', 'Học viên')
        return f"Xin chào {student_name}, chúc con có một buổi tập luyện hiệu quả!"