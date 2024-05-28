import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import Workflow, Node, Edge
from database import get_session


async def clear_database():
    async for session in get_session():
        await session.execute("DELETE FROM edges")
        await session.execute("DELETE FROM nodes")
        await session.execute("DELETE FROM workflows")
        await session.commit()


@pytest.fixture(scope="function", autouse=True)
async def clear_database_fixture():
    await clear_database()

@pytest.fixture
async def create_workflow():
    async for session in get_session():
        workflow = Workflow(name="Test Workflow")
        session.add(workflow)
        await session.commit()
        await session.refresh(workflow)
        return workflow

@pytest.fixture
async def create_nodes(create_workflow):
    workflow = await create_workflow
    async for session in get_session():
        node1 = Node(workflow_id=workflow.id, type="Start")
        node2 = Node(workflow_id=workflow.id, type="Message", message="Message Node")
        node3 = Node(workflow_id=workflow.id, type="End")
        node4 = Node(workflow_id=workflow.id, type="Condition", condition_text="Hello", condition_expression="Hello")
        session.add_all([node1, node2, node3])
        await session.commit()
        await session.refresh(node1)
        await session.refresh(node2)
        await session.refresh(node3)
        await session.refresh(node4)
        return node1, node2, node3, node4


@pytest.fixture
async def create_edge(create_nodes):
    node1, node2, node3, node4 = await create_nodes
    async for session in get_session():
        edge1 = Edge(start_node_id=node1.id, end_node_id=node2.id)
        edge2 = Edge(start_node_id=node2.id, end_node_id=node4.id)
        edge3 = Edge(start_node_id=node4.id, end_node_id=node3.id, status="Yes")
        session.add_all([edge1, edge2, edge3])
        await session.commit()
        await session.refresh(edge1)
        await session.refresh(edge2)
        await session.refresh(edge3)
        return edge1, edge2, edge3


@pytest.mark.asyncio
async def test_create_and_get_all_workflows():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/workflows/", json={"name": "Test Workflow 1"})
        assert response.status_code == 200

        response = await ac.post("/workflows/", json={"name": "Test Workflow 2"})
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
        assert response.json() == {"detail": "Workflow not found"}
    else:
        assert response.status_code == 200
        assert "name" in response.json()


@pytest.mark.asyncio
async def test_create_node(create_workflow):
    workflow = await create_workflow
    workflow_id = workflow.id
    node_data = {
        "workflow_id": workflow_id,
        "type": "Message",
        "message": "Test message"
    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(f"/workflows/{workflow_id}/nodes/", json=node_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Test message"


@pytest.mark.asyncio
async def test_create_edge(create_workflow):
    workflow = await create_workflow
    workflow_id = workflow.id

    node1_data = {
        "workflow_id": workflow_id,
        "type": "Message",
        "message": "Test message 1"
    }
    node2_data = {
        "workflow_id": workflow_id,
        "type": "Message",
        "message": "Test message 2"
    }

    async with AsyncClient(app=app, base_url="http://test") as ac:

        response1 = await ac.post(f"/workflows/{workflow_id}/nodes/", json=node1_data)
        assert response1.status_code == 200
        node1 = response1.json()

        response2 = await ac.post(f"/workflows/{workflow_id}/nodes/", json=node2_data)
        assert response2.status_code == 200
        node2 = response2.json()

        edge_data = {
            "start_node_id": node1["id"],
            "end_node_id": node2["id"],
        }
        response = await ac.post(f"/workflows/{workflow_id}/edges/", json=edge_data)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_get_all_edges(create_edge):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/edges/")
    assert response.status_code == 200
    edges = response.json()
    assert isinstance(edges, list)
    assert len(edges) >= 2


@pytest.mark.asyncio
async def test_update_edge(create_edge):
    edge1, edge2, edge3 = await create_edge
    edge_data = {
        "start_node_id": edge1.start_node_id,
        "end_node_id": edge1.end_node_id,

    }
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.put(f"/edges/{edge1.id}/", json=edge_data)
    assert response.status_code == 200





@pytest.mark.asyncio
async def test_delete_edge(create_edge):
    edge1, edge2 = create_edge
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(f"/edges/{edge1.id}/")
    assert response.status_code == 200
    async with await get_session() as session:
        result = await session.execute(select(Edge).filter_by(id=edge1.id))
        edge = result.scalars().first()
        assert edge is None


@pytest.mark.asyncio
async def test_run_workflow(create_nodes, create_edge):
    node1, node2, node3 = create_nodes
    workflow_id = node1.workflow_id
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(f"/workflows/{workflow_id}/run/")
    assert response.status_code == 200
    result = response.json()
    assert "path" in result
    assert isinstance(result["path"], list)
