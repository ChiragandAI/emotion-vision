from __future__ import annotations

from typing import Any


class ProviderInferenceClient:
    def __init__(self, provider_name: str, api_url: str, api_key: str) -> None:
        self.provider_name = provider_name
        self.api_url = api_url
        self.api_key = api_key

    def infer_image_bytes(self, content: bytes, filename: str) -> dict[str, Any]:
        raise NotImplementedError(
            "Provider client integration is a project extension point. Add the company's inference API here."
        )

