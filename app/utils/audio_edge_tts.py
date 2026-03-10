import edge_tts


async def generate_audio_stream(text: str):
    """
    True Streaming: Nhận được chunk âm thanh nào từ Microsoft,
    nhả (yield) ngay lập tức về cho Frontend phát.
    """
    communicate = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural")

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            yield chunk["data"]  # Bắn thẳng dữ liệu thô ra ngoài, không gom vào RAM nữa
