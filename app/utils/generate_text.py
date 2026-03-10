from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyBjbkn9Pi_jIln8djkuamBXHdXiX2UukA0")


async def generate_text(user_name: str, belt: str) -> str:
    prompt = f"Lễ tân AI võ đường. Chào võ sinh '{user_name}', đai '{belt}'. Dưới 15 từ, không ngoặc kép."

    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=30
            )
        )

        # --- LỚP PHÒNG THỦ: Kiểm tra xem Gemini có thực sự trả lời không ---
        if response and response.text:
            return response.text.strip()
        else:
            # Nếu Gemini bị block hoặc trả về rỗng, lập tức dùng câu mặc định
            print(f"Cảnh báo: Gemini trả về rỗng cho {user_name}. Dùng fallback.")
            return f"Chào mừng {user_name} đã đến lớp."

    except Exception as e:
        # Nếu rớt mạng hoặc Gemini sập, cũng dùng câu mặc định
        print(f"Lỗi gọi Gemini: {e}")
        return f"Xin chào {user_name}. Mời vào thảm tập."