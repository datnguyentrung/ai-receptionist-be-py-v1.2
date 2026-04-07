from typing import AsyncGenerator
import edge_tts


VOICE = "vi-VN-HoaiMyNeural"


async def generate_audio_stream(
    text: str,
    voice: str = VOICE,
) -> AsyncGenerator[bytes, None]:
    """
    True Streaming: nhận chunk âm thanh từ Microsoft và yield ngay
    về cho caller mà không gom vào RAM.

    Args:
        text:  Văn bản cần đọc.
        voice: Giọng đọc edge-tts (mặc định: tiếng Việt nữ).

    Yields:
        bytes: Chunk dữ liệu MP3 thô.

    Raises:
        edge_tts.exceptions.NoAudioReceived: Nếu TTS không trả về âm thanh.
        Exception: Các lỗi kết nối khác từ edge-tts.
    """
    if not text or not text.strip():
        return  # Tránh gọi TTS với chuỗi rỗng

    communicate = edge_tts.Communicate(text.strip(), voice)

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]  # Bắn thẳng bytes ra ngoài, không buffer