from fabric_client.models import (
    PaginatedResponse,
    PresignedUpload,
    Resource,
    ResourceRoot,
    SearchHit,
    Tag,
)


def test_resource_from_camel_case():
    data = {
        "id": "abc-123",
        "kind": "bookmark",
        "name": "Test Bookmark",
        "parentId": "def-456",
        "rootId": "ghi-789",
        "createdAt": "2026-01-01T00:00:00Z",
        "modifiedAt": "2026-01-02T00:00:00Z",
        "url": "https://example.com",
        "tags": [{"id": "tag-1", "name": "important"}],
    }
    r = Resource.model_validate(data)
    assert r.id == "abc-123"
    assert r.kind == "bookmark"
    assert r.parent_id == "def-456"
    assert r.root_id == "ghi-789"
    assert r.url == "https://example.com"
    assert len(r.tags) == 1
    assert r.tags[0].name == "important"


def test_resource_extra_fields_preserved():
    data = {
        "id": "abc-123",
        "kind": "notepad",
        "mimeType": "text/plain",
        "stateProcessing": "completed",
        "unknownFutureField": True,
    }
    r = Resource.model_validate(data)
    assert r.id == "abc-123"
    # Extra fields accessible via model_extra
    assert r.model_extra is not None
    assert r.model_extra.get("unknownFutureField") is True


def test_resource_optional_fields_default_none():
    data = {"id": "abc-123", "kind": "folder"}
    r = Resource.model_validate(data)
    assert r.name is None
    assert r.parent_id is None
    assert r.url is None
    assert r.tags == []


def test_resource_root_from_api():
    data = {
        "id": "root-1",
        "type": "SYSTEM",
        "subtype": "inbox",
        "createdAt": "2026-01-01T00:00:00Z",
        "modifiedAt": "2026-01-01T00:00:00Z",
        "isPrivate": False,
        "folder": {
            "id": "folder-1",
            "name": "Inbox",
            "isReadonly": True,
            "icon": None,
            "childrenCount": 5,
            "memberCount": 1,
        },
    }
    root = ResourceRoot.model_validate(data)
    assert root.id == "root-1"
    assert root.type == "SYSTEM"
    assert root.subtype == "inbox"
    assert root.folder_name == "Inbox"


def test_search_hit_has_score():
    data = {"id": "abc-123", "kind": "notepad", "score": 0.95}
    hit = SearchHit.model_validate(data)
    assert hit.score == 0.95
    assert hit.kind == "notepad"


def test_paginated_response_with_resources():
    data = {
        "total": 42,
        "hasMore": True,
        "nextCursor": "cursor-abc",
        "items": [
            {"id": "1", "kind": "bookmark"},
            {"id": "2", "kind": "notepad"},
        ],
    }
    page = PaginatedResponse[Resource].model_validate(data)
    assert page.total == 42
    assert page.has_more is True
    assert page.next_cursor == "cursor-abc"
    assert len(page.items) == 2
    assert page.items[0].kind == "bookmark"


def test_tag_model():
    data = {"id": "tag-1", "name": "project", "userId": "user-1", "description": None}
    tag = Tag.model_validate(data)
    assert tag.id == "tag-1"
    assert tag.name == "project"


def test_presigned_upload():
    data = {
        "url": "https://storage.example.com/upload",
        "headers": {"ETag": "abc", "Content-Disposition": "attachment"},
    }
    upload = PresignedUpload.model_validate(data)
    assert upload.url == "https://storage.example.com/upload"
    assert upload.headers["ETag"] == "abc"
