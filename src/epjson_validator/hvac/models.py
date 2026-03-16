"""HVAC graph models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class HVACNode:
    node_id: str
    label: str
    kind: str


@dataclass(slots=True)
class HVACPath:
    label: str
    node_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class HVACDiagram:
    name: str
    kind: str
    nodes: dict[str, HVACNode] = field(default_factory=dict)
    paths: list[HVACPath] = field(default_factory=list)

    def add_node(self, node_id: str, label: str, kind: str) -> None:
        self.nodes.setdefault(node_id, HVACNode(node_id=node_id, label=label, kind=kind))

    def add_path(self, label: str, node_ids: list[str]) -> None:
        self.paths.append(HVACPath(label=label, node_ids=node_ids))
