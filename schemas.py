from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel


class NodeType(str, Enum):
    start = 'Start'
    message = 'Message'
    condition = 'Condition'
    end = 'End'


class NodeStatus(str, Enum):
    pending = 'pending'
    sent = 'sent'
    opened = 'opened'


class EdgeStatus(str, Enum):
    yes = 'Yes'
    no = 'No'


class NodeBase(BaseModel):
    type: NodeType
    status: Optional[NodeStatus] = None
    message: Optional[str] = None
    condition_text: Optional[str] = None
    condition_expression: Optional[str] = None


class NodeCreate(NodeBase):
    pass


class Node(NodeBase):
    id: int
    workflow_id: int

    class Config:
        orm_mode = True


class EdgeBase(BaseModel):
    start_node_id: int
    end_node_id: int
    status: Optional[EdgeStatus] = None


class EdgeCreate(EdgeBase):
    pass


class Edge(EdgeBase):
    id: int

    class Config:
        orm_mode = True


class WorkflowBase(BaseModel):
    name: str


class WorkflowCreate(WorkflowBase):
    pass


class Workflow(WorkflowBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    nodes: List['Node'] = []
    edges: List['Edge'] = []

    class Config:
        orm_mode = True
