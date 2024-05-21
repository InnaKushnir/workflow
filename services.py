from typing import List
import rule_engine
from fastapi import Depends, HTTPException

import schemas
from db import models
from sqlalchemy.orm import Session
from schemas import WorkflowCreate, NodeCreate, EdgeCreate, NodeType
from dependencies import get_db


class WorkflowService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_all_workflow(
            self,
            skip: int = 0,
            limit: int = 100,
    ) -> List[models.Workflow]:
        return self.db.query(models.Workflow).offset(skip).limit(limit).all()

    def get_workflow(self, workflow_id: int):
        return self.db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()

    def create_workflow(self, workflow: WorkflowCreate):
        db_workflow = models.Workflow(name=workflow.name)
        self.db.add(db_workflow)
        self.db.commit()
        self.db.refresh(db_workflow)
        return db_workflow

    def create_node(self, workflow_id: int, node: NodeCreate) -> models.Node:
        if node.type == NodeType.message and not node.message:
            raise ValueError("Message Node must have a message.")
        if node.type == NodeType.condition and not node.condition_expression:
            raise ValueError("Condition Node must have a condition expression.")

        db_node = models.Node(
            type=node.type,
            status=node.status,
            message=node.message,
            condition_text=node.condition_text,
            condition_expression=node.condition_expression,
            workflow_id=workflow_id
        )
        self.db.add(db_node)
        self.db.commit()
        self.db.refresh(db_node)
        return db_node

    def get_all_nodes(
            self,
            skip: int = 0,
            limit: int = 100,
    ) -> List[models.Node]:
        return self.db.query(models.Node).offset(skip).limit(limit).all()

    def update_node(self, node_id: int, node: NodeCreate) -> models.Node:
        db_node = self.db.query(models.Node).filter(models.Node.id == node_id).first()
        for key, value in node.dict().items():
            setattr(db_node, key, value)
        self.db.commit()
        self.db.refresh(db_node)
        return db_node

    def delete_node(self, node_id: int) -> models.Node:
        db_node = self.db.query(models.Node).filter(models.Node.id == node_id).first()
        self.db.delete(db_node)
        self.db.commit()
        return db_node

    def create_edge(self, workflow_id: int, edge: schemas.EdgeCreate) -> models.Edge:
        start_node = self.db.query(models.Node).get(edge.start_node_id)
        end_node = self.db.query(models.Node).get(edge.end_node_id)

        if not start_node or not end_node:
            raise HTTPException(status_code=404, detail="Node not found")

        if start_node.workflow_id != workflow_id:
            raise HTTPException(status_code=400, detail="Start Node does not belong to the specified workflow.")
        if end_node.workflow_id != workflow_id:
            raise HTTPException(status_code=400, detail="End Node does not belong to the specified workflow.")

        if start_node.type == NodeType.start:
            if start_node.incoming_edges:
                raise HTTPException(status_code=400, detail="Start Node cannot have incoming edges.")
            if len(start_node.outgoing_edges) >= 1:
                raise HTTPException(status_code=400, detail="Start Node can only have one outgoing edge.")

        elif start_node.type == NodeType.message:
            if not start_node.message:
                raise HTTPException(status_code=400, detail="Message Node must have a message.")
            if len(start_node.outgoing_edges) >= 1:
                raise HTTPException(status_code=400, detail="Message Node can only have one outgoing edge.")

        elif start_node.type == NodeType.condition:
            if len(start_node.outgoing_edges) >= 2:
                raise HTTPException(status_code=400,
                                    detail="Condition Node can only have two outgoing edges (Yes and No).")
            if edge.status not in ["Yes", "No"]:
                raise HTTPException(status_code=400, detail="Condition Node outgoing edges must be 'Yes' or 'No'.")

            existing_edges = self.db.query(models.Edge).filter_by(start_node_id=start_node.id).all()
            for existing_edge in existing_edges:
                if existing_edge.status == edge.status:
                    raise HTTPException(status_code=400,
                                        detail=f"Condition Node already has an outgoing edge with status '{edge.status}'.")

        elif start_node.type == NodeType.end:
            raise HTTPException(status_code=400, detail="End Node cannot have outgoing edges.")

        if end_node.type == NodeType.start:
            raise HTTPException(status_code=400, detail="Start Node cannot be an end node.")

        if end_node.type == NodeType.condition:

            if not start_node.type == NodeType.message:
                raise HTTPException(status_code=400, detail="Condition Node must be preceded by a Message Node.")


            condition = end_node.condition_expression
            context = {'message': start_node.message}
            rule = rule_engine.Rule(condition)

            if rule.evaluate(context):
                edge.status = "Yes"
            else:
                edge.status = "No"

        db_edge = models.Edge(
            workflow_id=workflow_id,
            start_node_id=edge.start_node_id,
            end_node_id=edge.end_node_id,
            status=edge.status
        )
        self.db.add(db_edge)
        self.db.commit()
        self.db.refresh(db_edge)
        return db_edge

    def update_edge(self, edge_id: int, edge: EdgeCreate) -> models.Edge:
        db_edge = self.db.query(models.Edge).filter(models.Edge.id == edge_id).first()
        for key, value in edge.dict().items():
            setattr(db_edge, key, value)
        self.db.commit()
        self.db.refresh(db_edge)
        return db_edge

    def delete_edge(self, edge_id: int):
        db_edge = self.db.query(models.Edge).filter(models.Edge.id == edge_id).first()
        if not db_edge:
            raise HTTPException(status_code=404, detail="Edge not found")
        self.db.delete(db_edge)
        self.db.commit()

    def get_all_edges(
            self,
            skip: int = 0,
            limit: int = 100,
    ) -> List[models.Edge]:
        return self.db.query(models.Edge).offset(skip).limit(limit).all()

