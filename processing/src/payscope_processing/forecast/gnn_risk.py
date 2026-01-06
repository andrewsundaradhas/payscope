from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import networkx as nx


@dataclass
class GraphSnapshot:
    graph: nx.Graph
    timestamp: str


class SimpleGNN(nn.Module):
    """
    Minimal GNN for risk propagation. Deterministic initialization.
    """

    def __init__(self, in_dim: int = 4, hidden: int = 8):
        super().__init__()
        torch.manual_seed(42)
        self.lin1 = nn.Linear(in_dim, hidden)
        self.lin2 = nn.Linear(hidden, 1)
        nn.init.xavier_uniform_(self.lin1.weight)
        nn.init.zeros_(self.lin1.bias)
        nn.init.xavier_uniform_(self.lin2.weight)
        nn.init.zeros_(self.lin2.bias)

    def forward(self, x, adj):
        h = torch.relu(self.lin1(torch.matmul(adj, x)))
        out = torch.sigmoid(self.lin2(h)).squeeze(-1)
        return out


def build_snapshot(nodes: List[Dict], edges: List[Tuple[str, str]]) -> GraphSnapshot:
    g = nx.Graph()
    for n in nodes:
        g.add_node(n["id"], **n)
    for u, v in edges:
        g.add_edge(u, v)
    return GraphSnapshot(graph=g, timestamp="")


def infer_risk(snapshot: GraphSnapshot) -> Dict[str, float]:
    g = snapshot.graph
    if g.number_of_nodes() == 0:
        return {}

    node_ids = list(g.nodes())
    n = len(node_ids)
    id_to_idx = {nid: i for i, nid in enumerate(node_ids)}

    # Features: [base_risk, degree, is_merchant, is_bank]
    feats = torch.zeros((n, 4), dtype=torch.float32)
    for nid in node_ids:
        i = id_to_idx[nid]
        data = g.nodes[nid]
        feats[i, 0] = float(data.get("base_risk", 0.1))
        feats[i, 1] = float(g.degree[nid])
        feats[i, 2] = 1.0 if data.get("label") == "merchant" else 0.0
        feats[i, 3] = 1.0 if data.get("label") == "bank" else 0.0

    adj = torch.zeros((n, n), dtype=torch.float32)
    for u, v in g.edges():
        i, j = id_to_idx[u], id_to_idx[v]
        adj[i, j] = 1.0
        adj[j, i] = 1.0
    # Normalize adjacency
    deg = adj.sum(dim=1, keepdim=True) + 1e-6
    adj = adj / deg

    model = SimpleGNN()
    with torch.no_grad():
        scores = model(feats, adj)
    return {nid: float(scores[id_to_idx[nid]]) for nid in node_ids}




