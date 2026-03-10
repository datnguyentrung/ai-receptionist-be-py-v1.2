ai-receptionist-backend/
├── app/
│   ├── api/                # Nơi chứa các API Routers (Endpoints)
│   │   ├── v1/             # Phiên bản API (VD: /api/v1/chat, /api/v1/voice)
│   │   └── dependencies.py # Các dependency injection (VD: xác thực, kết nối DB)
│   ├── core/               # Cấu hình cốt lõi của hệ thống
│   │   ├── config.py       # Load biến môi trường từ .env
│   │   └── security.py     # Xử lý JWT, hashing password (nếu có auth)
│   ├── models/             # Chứa các model Database (SQLAlchemy)
│   │   └── user.py         # VD: Lưu thông tin khách hàng, lịch sử cuộc gọi
│   ├── schemas/            # Pydantic models để validate dữ liệu in/out
│   │   ├── chat.py         # Validate payload gửi lên cho AI
│   │   └── response.py     # Format dữ liệu trả về chuẩn
│   ├── services/           # Nơi chứa TOÀN BỘ logic nghiệp vụ và AI
│   │   ├── ai_agent.py     # Logic gọi LLM (LangChain, Gemini, OpenAI...)
│   │   ├── audio.py        # Xử lý Speech-to-Text và Text-to-Speech
│   │   └── booking.py      # Logic đặt lịch/lễ tân (nếu có)
│   ├── db/                 # Thiết lập kết nối Database
│   │   └── session.py
│   ├── utils/              # Các hàm tiện ích dùng chung (format thời gian, log...)
│   └── main.py             # File khởi chạy ứng dụng FastAPI
├── tests/                  # Thư mục chứa Unit Test (Pytest)
├── .env                    # Chứa API keys (LLM, DB URL) - KHÔNG push lên Git
├── .gitignore              
├── requirements.txt        # Danh sách thư viện (hoặc dùng poetry/pyproject.toml)
└── README.md               # Tài liệu hướng dẫn setup dự án