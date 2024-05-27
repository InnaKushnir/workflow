import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import Workflow, Node, Edge
from database import get_session

async def clear_database():
    async with await get_session() as session:
        await session.execute("DELETE FROM edges")
        await session.execute("DELETE FROM nodes")
        await session.execute("DELETE FROM workflows")
        await session.commit()

@pytest.fixture(scope="function", autouse=True)
async def clear_database_fixture():
    await clear_database()

@pytest.fixture
async def create_workflow():
    async with await get_session() as session:
        workflow = Workflow(name="Test Workflow", description="A test workflow")
        session.add(workflow)
        await session.commit()
        await session.refresh(workflow)
        return workflow

@pytest.fixture
async def create_nodes(create_workflow):

    async with await get_session() as session:
        node1 = Node(workflow_id=create_workflow.id, type="Start", message="Start Node")
        node2 = Node(workflow_id=create_workflow.id, type="Message", message="Message Node")
        node3 = Node(workflow_id=create_workflow.id, type="End", message="End Node")
        session.add_all([node1, node2, node3])
        await session.commit()
        await session.refresh(node1)
        await session.refresh(node2)
        await session.refresh(node3)
        return node1, node2, node3

@pytest.fixture
async def create_edge(create_nodes):
    node1, node2, node3 = create_nodes
    async with await get_session() as session:
        edge1 = Edge(start_node_id=node1.id, end_node_id=node2.id, status="active")
        edge2 = Edge(start_node_id=node2.id, end_node_id=node3.id, status="active")
        session.add_all([edge1, edge2])
        await session.commit()
        await session.refresh(edge1)
        await session.refresh(edge2)
        return edge1, edge2

@pytest.mark.asyncio
async def test_create_and_get_all_workflows():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/workflows/", json={"name": "Test Workflow 1", "description": "First test workflow"})
        assert response.status_code == 200

        response = await ac.post("/workflows/", json={"name": "Test Workflow 2", "description": "Second test workflow"})
        assert response.status_code == 200

        response = await ac.get("/workflows/")
        assert response.status_code == 200

        workflows = response.json()
        assert isinstance(workflows, list)
        assert len(workflows) >= 2
        assert any(workflow["name"] == "Test Workflow 1" for workflow in workflows)
        assert any(workflow["name"] == "Test Workflow 2" for workflow in workflows)


@pytest.mark.asyncio
async def test_get_workflow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/workflows/", json={"name": "Test Workflow", "description": "Test workflow"})
        assert response.status_code == 200
    if response.status_code == 404:
        assert response.json() == {"detail": "Author not found"}
    else:
        assert response.status_code == 200
        assert "name" in response.json()


@pytest.mark.asyncio
async def test_create_node():
    workflow_id = 1
    node_data = {
        "type": "Message",
        "message": "Test message"
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(f"/workflows/{workflow_id}/nodes/", json=node_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Test message"




@pytest.mark.asyncio
async def test_get_all_edges(create_edge):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/edges/")
    assert response.status_code == 200
    edges = response.json()
    assert isinstance(edges, list)
    assert len(edges) >= 2



