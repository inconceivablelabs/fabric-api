import json

import httpx
import pytest
import respx

from fabric_client.client import FabricClient


@pytest.fixture
def client(api_key, base_url):
    return FabricClient(api_key=api_key, base_url=base_url)


@respx.mock
async def test_get_upload_url(client, base_url):
    respx.get(f"{base_url}/upload").mock(
        return_value=httpx.Response(
            200,
            json={
                "url": "https://storage.example.com/presigned",
                "headers": {"ETag": None, "Content-Disposition": None},
            },
        )
    )
    upload = await client.get_upload_url(filename="test.pdf", size=1024)
    assert upload.url == "https://storage.example.com/presigned"


@respx.mock
async def test_upload_file_data(client, base_url):
    route = respx.put("https://storage.example.com/presigned").mock(
        return_value=httpx.Response(200)
    )
    await client.upload_file_data(
        url="https://storage.example.com/presigned",
        data=b"file content here",
    )
    assert route.called
    assert route.calls[0].request.content == b"file content here"


@respx.mock
async def test_create_file(client, base_url):
    route = respx.post(f"{base_url}/files").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "file-1",
                "kind": "document",
                "name": "test.pdf",
                "mimeType": "application/pdf",
                "tags": [],
            },
        )
    )
    resource = await client.create_file(
        attachment_path="uploads/abc123",
        attachment_filename="test.pdf",
        parent_id="@alias::inbox",
        mime_type="application/pdf",
    )
    assert resource.id == "file-1"
    assert resource.kind == "document"
    body = json.loads(route.calls[0].request.content)
    assert body["attachment"]["path"] == "uploads/abc123"
    assert body["mimeType"] == "application/pdf"
