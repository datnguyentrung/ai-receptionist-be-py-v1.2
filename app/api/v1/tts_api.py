from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from app.utils.audio_edge_tts import generate_audio_stream
from app.utils.generate_text import generate_text


class GreetingRequest(BaseModel):
    name: str
    belt: str

router = APIRouter(prefix="/tts", tags=["TTS"])


@router.get("/greeting")
async def stream_greeting_audio(name: str, belt: str):
    # 1. Gọi Gemini lấy text (Mất ~0.8s - 1.2s)
    text = await generate_text(name, belt)

    # 2. Trả về Generator (Mất ~0.2s để byte đầu tiên tới Frontend)
    # Tổng cộng chỉ khoảng 1.5s là loa bắt đầu vang lên!
    return StreamingResponse(
        generate_audio_stream(text),
        media_type="audio/mpeg"
    )