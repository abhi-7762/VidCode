from typing import Optional
from app.services.video_providers.base import BaseVideoProvider
from app.services.video_providers.mock_provider import MockVideoProvider
from app.services.video_providers.runway_provider import RunwayVideoProvider
from app.services.video_providers.luma_provider import LumaVideoProvider
from app.models.video import VideoProviderType


def get_video_provider(provider_type: Optional[VideoProviderType] = None) -> BaseVideoProvider:
    """Factory to instantiate the appropriate video generation provider."""
    p_type = provider_type or VideoProviderType.MOCK
    if p_type == VideoProviderType.RUNWAY:
        return RunwayVideoProvider()
    elif p_type == VideoProviderType.LUMA:
        return LumaVideoProvider()
    elif p_type == VideoProviderType.MOCK or p_type == VideoProviderType.PIKA:
        return MockVideoProvider()
    return MockVideoProvider()

