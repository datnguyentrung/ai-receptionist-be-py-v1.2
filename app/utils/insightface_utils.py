import numpy as np
from insightface.app import FaceAnalysis

def initialize_cpu_face_app():
    """Khởi tạo model nhận diện khuôn mặt tối ưu cho CPU"""
    try:
        # Sử dụng model siêu nhẹ buffalo_s và chỉ định rõ dùng CPU
        app = FaceAnalysis(
            name="buffalo_s",
            providers=["CPUExecutionProvider"]
        )
        # ctx_id = -1 nghĩa là ép buộc chạy trên CPU
        app.prepare(ctx_id=-1, det_size=(640, 640))
        print("Đã khởi tạo InsightFace trên CPU thành công (Model: buffalo_s).")
        return app
    except Exception as e:
        print(f"Lỗi khởi tạo InsightFace: {e}")
        return None


# KHỞI TẠO GLOBAL:
# Biến này nằm ngoài hàm để model chỉ load vào RAM đúng 1 lần khi server FastAPI khởi động,
# tránh việc mỗi lần có người điểm danh lại phải load lại model 159MB.
face_app = initialize_cpu_face_app()

def get_face_embedding(img_array: np.ndarray) -> list[float] | None:
    """
    Trích xuất vector khuôn mặt to nhất trong ảnh.
    Trả về list 512 phần tử (float) để lưu vào pgvector.
    """
    if face_app is None:
        print("Model InsightFace chưa được khởi tạo.")
        return None

    try:
        faces = face_app.get(img_array)
        if not faces:
            return None  # Không tìm thấy ai

        # Chọn khuôn mặt có diện tích lớn nhất (người đứng gần màn hình lễ tân nhất)
        largest_face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))

        return largest_face.embedding.tolist()

    except Exception as e:
        print(f"Lỗi khi trích xuất vector khuôn mặt: {e}")
        return None
