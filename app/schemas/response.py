from enum import Enum
from pydantic import BaseModel, ConfigDict

from app.schemas.student_attendance import StudentAttendanceResponse
from app.schemas.user import UserResponse


class AudioSignal(str, Enum):
    CHECKIN_SUCCESS = "CHECKIN_SUCCESS"
    ALREADY_CHECKED_IN = "ALREADY_CHECKED_IN"
    NO_VALID_SESSION = "NO_VALID_SESSION"
    FACE_NOT_RECOGNIZED = "FACE_NOT_RECOGNIZED"

class CheckInResponse(BaseModel):
    audio_signal: AudioSignal
    status: bool = True
    user: UserResponse | None = None
    attendance_record: StudentAttendanceResponse | None = None


