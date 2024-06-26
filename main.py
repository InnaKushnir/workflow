import networkx as nx
import rule_engine
from fastapi import FastAPI, Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse
from typing_extensions import Union


from db import models
from typing import List
import schemas
from db.models import NodeType
from dependencies import get_db
from schemas import WorkflowCreate
from services import WorkflowService

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/workflows/", response_model=List[schemas.Workflow])
def get_all_workflow(workflow_service: WorkflowService = Depends()):
    """
        Retrieve all workflows.
    """
    return workflow_service.get_all_workflow()


@app.get("/workflows/{workflow_id}/", response_model=schemas.Workflow)
def get_workflow(workflow_id: Union[int, None] = None, workflow_service: WorkflowService = Depends()):
    """
        Retrieve a workflow by its ID.
    """
    db_workflow = workflow_service.get_workflow(workflow_id=workflow_id)

    if db_workflow is None:
        raise HTTPException(status_code=404, detail="Author not found")

    return db_workflow


@app.post("/workflows/", response_model=schemas.Workflow)
def create_workflow(workflow: schemas.WorkflowCreate, workflow_service: WorkflowService = Depends()):
    """
        Create a new workflow.
    """

    return workflow_service.create_workflow(workflow=workflow)


@app.post("/workflows/{workflow_id}/nodes/", response_model=schemas.Node)
def create_node(workflow_id: int, node: schemas.NodeCreate, node_service: WorkflowService = Depends()):
    """
        Create a new node within a workflow.
    """
    return node_service.create_node(workflow_id, node)


@app.get("/nodes/", response_model=List[schemas.Node])
def get_all_nodes(nodes_service: WorkflowService = Depends()):
    """
        Retrieve all nodes.
    """
    return nodes_service.get_all_nodes()


@app.get("/nodes/{node_id}/", response_model=schemas.Node)
def get_node(node_id: Union[int, None] = None, node_service: WorkflowService = Depends()):
    """
        Retrieve a node by its ID.
    """
    db_node = node_service.get_node(node_id=node_id)

    if db_node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    return db_node


@app.put("/nodes/{node_id}/", response_model=schemas.Node)
def update_node(node_id: int, node: schemas.NodeCreate, node_service: WorkflowService = Depends()):
    """
        Update an existing node by its ID.
    """
    return node_service.update_node(node_id, node)


@app.delete("/nodes/{node_id}/", response_model=schemas.Node)
def delete_node(node_id: int, node_service: WorkflowService = Depends()):
    """
        Delete a node by its ID.
    """
    node_service.delete_edge(node_id)
    return JSONResponse(content={"message": "Node successfully deleted"})


@app.post("/workflows/{workflow_id}/edges/", response_model=schemas.Edge)
def create_edge(workflow_id: int, edge: schemas.EdgeCreate, edge_service: WorkflowService = Depends()):
    """
        Create a new edge within a workflow.
    """
    return edge_service.create_edge(workflow_id, edge)


@app.get("/edges/", response_model=List[schemas.Edge])
def get_all_edges(edge_service: WorkflowService = Depends()):
    """
        Retrieve all edges.
    """
    return edge_service.get_all_edges()


@app.get("/edges/{edge_id}/", response_model=schemas.Edge)
def get_edge_by_id(edge_id: int, edge_service: WorkflowService = Depends()):
    """
    Retrieve an edge by its ID.
    """
    db_edge = edge_service.get_edge_by_id(edge_id)
    if not db_edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    return db_edge

@app.put("/edges/{edge_id}/", response_model=schemas.Edge)
def update_edge(edge_id: int, edge: schemas.EdgeCreate, edge_service: WorkflowService = Depends()):
    """
        Update an existing edge by its ID.
    """
    return edge_service.update_edge(edge_id, edge)


@app.delete("/edges/{edge_id}/", response_model=schemas.Edge)
def delete_edge(edge_id: int, edge_service: WorkflowService = Depends()):
    """
            Delete an existing edge by its ID.
    """
    edge_service.delete_edge(edge_id)
    return JSONResponse(content={"message": "Edge successfully deleted"})


@app.post("/workflows/{workflow_id}/run/")
def run_workflow(workflow_id: int, workflow_service: WorkflowService = Depends()):
    """
        Execute a workflow and find the shortest path from a start node to an end node.
    """
    workflow = workflow_service.get_workflow(workflow_id)
    G = nx.DiGraph()

    for node in workflow.nodes:
        G.add_node(node.id, type=node.type, status=node.status, message=node.message)

    for edge in workflow.edges:
        G.add_edge(edge.start_node_id, edge.end_node_id, status=edge.status)

    start_nodes = [node.id for node in workflow.nodes if node.type == NodeType.start]
    end_nodes = [node.id for node in workflow.nodes if node.type == NodeType.end]

    if not start_nodes:
        return {"error": "No start node found"}
    if not end_nodes:
        return {"error": "No end node found"}

    try:
        shortest_path = None
        shortest_length = float('inf')

        for start_node in start_nodes:
            for end_node in end_nodes:
                try:
                    path = nx.shortest_path(G, source=start_node, target=end_node)
                    path_length = len(path)
                    if path_length < shortest_length:
                        shortest_length = path_length
                        shortest_path = path
                except nx.NetworkXNoPath:
                    continue

        if not shortest_path:
            return {"error": "No path found from start to end node"}

        detailed_path = []
        for node_id in shortest_path:
            node = workflow_service.get_node(node_id)

            if node.type == NodeType.condition:
                last_message_node = workflow_service.find_last_message_node(node)
                if not last_message_node:
                    raise HTTPException(status_code=400, detail="Condition Node must have a preceding Message Node.")

                condition = node.condition_expression
                context = {'message': last_message_node.message}
                rule = rule_engine.Rule(condition)

                if rule.evaluate(context):
                    edge = workflow_service.db.query(models.Edge).filter(
                        models.Edge.start_node_id == last_message_node.id,
                        models.Edge.end_node_id == node.id
                    ).first()
                    edge.status = "Yes"
                else:
                    edge = workflow_service.db.query(models.Edge).filter(
                        models.Edge.start_node_id == last_message_node.id,
                        models.Edge.end_node_id == node.id
                    ).first()
                    edge.status = "No"

            detailed_path.append({
                "id": node.id,
                "type": node.type,
                "status": node.status,
                "message": node.message
            })

        return {"path": detailed_path}
    except nx.NetworkXNoPath:
        return {"error": "No path found from start to end node"}

