from dataclasses import dataclass

@dataclass
class Booking:
    date: str
    user_id: int
    full_name: str
    start_time: str
    end_time: str
    status: str = 'active'
