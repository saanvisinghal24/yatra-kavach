import httpx
import pytest
from app.services import weather

@pytest.fixture(autouse=True)
def fixture_client_without_environment_proxy(monkeypatch):
    # This suite stubs HTTP responses: runtime proxy support is not under test.
    original = httpx.AsyncClient.__init__
    def init(self, *args, **kwargs):
        kwargs["trust_env"] = False
        original(self, *args, **kwargs)
    monkeypatch.setattr(httpx.AsyncClient, "__init__", init)

@pytest.mark.asyncio
async def test_weather_missing_values_are_unavailable(monkeypatch):
    weather._weather_cache.clear()
    async def get(self, url, **kwargs):
        return httpx.Response(200, json={'hourly': {}}, request=httpx.Request('GET', url))
    monkeypatch.setattr(httpx.AsyncClient, 'get', get)
    result = await weather.get_checkpoint_weather(888, 32, 76, 'Fixture')
    assert result['status'] == 'unavailable'
    assert 'temp_current_c' not in result

@pytest.mark.asyncio
async def test_weather_timestamps_and_stale_cache(monkeypatch):
    weather._weather_cache.clear()
    async def get(self, url, **kwargs):
        return httpx.Response(200, json={'hourly': {'time':['2026-10-08T10:00','2026-10-08T11:00'], 'temperature_2m':[7,8], 'precipitation':[0,1], 'wind_gusts_10m':[10,12], 'weather_code':[0,1]}}, request=httpx.Request('GET', url))
    monkeypatch.setattr(httpx.AsyncClient, 'get', get)
    result = await weather.get_checkpoint_weather(889, 32, 76, 'Fixture')
    assert result['issue_time'] is None
    assert result['valid_until'] == '2026-10-08T12:00:00+00:00'
    assert result['retrieved_at'].endswith('+00:00')
    weather._weather_cache[889]['timestamp'] = 0
    async def fail(*args, **kwargs):
        raise httpx.ConnectError('offline')
    monkeypatch.setattr(httpx.AsyncClient, 'get', fail)
    stale = await weather.get_checkpoint_weather(889, 32, 76, 'Fixture')
    assert stale['status'] == 'stale'
    assert stale['retrieved_at'] == result['retrieved_at']
    assert stale['r5_flag'] is None
