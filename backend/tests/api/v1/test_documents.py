import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select

from src.database.models import Document, DocumentVersion


@pytest.mark.asyncio
async def test_upload_document_success(client, monkeypatch):
    async def mock_upload(*args, **kwargs):
        return None
    
    async def mock_trigger(*args, **kwargs):
        return None
    
    from src.api.v1 import documents
    monkeypatch.setattr(documents.storage_service, "upload_file", mock_upload)
    monkeypatch.setattr(documents.agent_orchestrator, "trigger_analysis_pipeline", mock_trigger)
    
    files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    data = {"document_type": "contract"}
    
    response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == "test.pdf"
    assert data["document_type"] == "contract"
    assert data["status"] == "processing"


@pytest.mark.asyncio
async def test_upload_document_unsupported_extension(client):
    files = {"file": ("test.txt", b"fake content", "text/plain")}
    data = {"document_type": "contract"}
    
    response = await client.post(
        "/api/v1/documents/upload",
        files=files,
        data=data
    )
    
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_documents(client, test_user, test_session):
    doc1 = Document(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Document 1",
        document_type="contract",
        status="analyzed",
        current_version_id=None,
    )
    doc2 = Document(
        id=uuid.uuid4(),
        user_id=test_user.id,
        title="Document 2",
        document_type="agreement",
        status="processing",
        current_version_id=None,
    )
    test_session.add(doc1)
    test_session.add(doc2)
    await test_session.commit()
    
    response = await client.get("/api/v1/documents")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = [d["title"] for d in data]
    assert "Document 1" in titles
    assert "Document 2" in titles


@pytest.mark.asyncio
async def test_get_document_details(client, test_user, test_session):
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=test_user.id,
        title="Test Document",
        document_type="contract",
        status="analyzed",
        current_version_id=None,
    )
    test_session.add(doc)
    await test_session.commit()
    
    response = await client.get(f"/api/v1/documents/{doc_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(doc_id)
    assert data["title"] == "Test Document"


@pytest.mark.asyncio
async def test_get_document_not_found(client):
    doc_id = uuid.uuid4()
    response = await client.get(f"/api/v1/documents/{doc_id}")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_success(client, test_user, test_session, monkeypatch):
    async def mock_delete(*args, **kwargs):
        return None
    
    from src.api.v1 import documents
    monkeypatch.setattr(documents.storage_service, "delete_file", mock_delete)
    
    doc_id = uuid.uuid4()
    version_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        user_id=test_user.id,
        title="Test Document",
        document_type="contract",
        status="analyzed",
        current_version_id=None,
    )
    version = DocumentVersion(
        id=version_id,
        document_id=doc_id,
        version_number=1,
        storage_path="uploads/test.pdf",
        file_type="pdf",
        is_signed=False,
    )
    test_session.add(doc)
    test_session.add(version)
    await test_session.commit()
    
    response = await client.delete(f"/api/v1/documents/{doc_id}")
    
    assert response.status_code == 204
    
    result = await test_session.execute(select(Document).where(Document.id == doc_id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_document_not_found(client):
    doc_id = uuid.uuid4()
    response = await client.delete(f"/api/v1/documents/{doc_id}")
    
    assert response.status_code == 404
