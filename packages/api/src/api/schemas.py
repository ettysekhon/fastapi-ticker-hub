from typing import TypedDict


class OHLCVPoint(TypedDict):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
