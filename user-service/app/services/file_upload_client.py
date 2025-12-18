import uuid
from functools import lru_cache
from typing import Optional

import httpx

from app.settings import get_settings


class FileUploadClient:
    def __init__(self, base_url: str):
        self.client = httpx.AsyncClient(base_url=base_url)

    async def get_signed_url(
        self,
        file_id: uuid.UUID,
        chat_id: Optional[uuid.UUID] = None,
        thumbnail: bool = False,
    ) -> Optional[str]:
        try:
            endpoint = f"/api/v1/files/{file_id}/download"
            if thumbnail:
                endpoint = f"/api/v1/files/{file_id}/thumbnail"

            params = {}
            if chat_id:
                params["chat_id"] = str(chat_id)

            response = await self.client.get(endpoint, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("signed_url")
        except httpx.HTTPStatusError as e:
            print(
                f"Error getting signed URL for file {file_id}: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            print(f"Request error getting signed URL for file {file_id}: {e}")
            return None

    async def upload_file(
        self, file_content: bytes, filename: str, mime_type: str, token: str
    ) -> Optional[dict]:
        try:
            files = {"file": (filename, file_content, mime_type)}
            headers = {"Authorization": f"Bearer {token}"}
            response = await self.client.post(
                "/api/v1/files/upload", files=files, headers=headers, timeout=30
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(
                f"Error uploading file {filename}: {e.response.status_code} - {e.response.text}"
            )
            return None
        except httpx.RequestError as e:
            print(f"Request error uploading file {filename}: {e}")
            return None


@lru_cache
def get_file_upload_client():
    settings = get_settings()
    return FileUploadClient(settings.file_upload_service_url)
