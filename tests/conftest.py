import pytest
from app.models import ChartRequest


@pytest.fixture
def request_data():
    return {
        "birth": {
            "date": "1988-08-14",
            "time": "19:05:00",
            "latitude": 26.8467,
            "longitude": 80.9462,
            "timezone": "Asia/Kolkata",
            "confidence": "certificate",
        },
        "as_of": "2026-10-22T00:00:00Z",
    }


@pytest.fixture
def chart_request(request_data):
    return ChartRequest.model_validate(request_data)
