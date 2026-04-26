from dataclasses import dataclass

@dataclass
class Slot:
    start_time: str
    end_time: str
    capacity: int = 2
