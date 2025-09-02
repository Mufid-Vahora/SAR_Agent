
import argparse, json, os, requests, pandas as pd
import torch
from neo4j import GraphDatabase
from torch_geometric.data import Data
from torch_geometric.nn import GATConv
import torch.nn.functional as F
import numpy as np

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma:2b"  # uses local Ollama

class TinyGAT(torch.nn.Module):
    def __init__(self, in_dim=2, hidden=16, out_dim=2, heads=2):
        super().__init__()
        self.g1 = GATConv(in_dim, hidden, heads=heads)
        self.g2 = GATConv(hidden*heads, out_dim, heads=1, concat=False)
    def forward(self, x, edge_index):
        x = self.g1(x, edge_index)
        x = F.elu(x)
        x = F.dropout(x, p=0.2, training=self.training)
        x = self.g2(x, edge_index)
        return x

def fetch_data():
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as s:
        res = s.run("MATCH (a:Account) RETURN a.accountID AS id ORDER BY id")
        nodes = [r['id'] for r in res]
        idx = {n:i for i,n in enumerate(nodes)}
        res = s.run("""MATCH (a:Account)-[:PERFORMED]->(t:Transaction)-[:SENT_TO]->(b:Account)
                       RETURN a.accountID as src, b.accountID as dst""")
        edges = [(idx[r['src']], idx[r['dst']]) for r in res]
    # features
    import networkx as nx
    g = nx.DiGraph()
    g.add_nodes_from(range(len(nodes)))
    g.add_edges_from(edges)
    indeg = np.array([g.in_degree(i) for i in range(len(nodes))], dtype=np.float32)
    outdeg = np.array([g.out_degree(i) for i in range(len(nodes))], dtype=np.float32)
    x = np.stack([indeg, outdeg], axis=1)
    edge_index = torch.tensor(np.array(edges).T, dtype=torch.long) if edges else torch.empty((2,0), dtype=torch.long)
    data = Data(x=torch.tensor(x, dtype=torch.float32), edge_index=edge_index)
    data.node_ids = nodes
    return data

def top_k_accounts(scores, node_ids, k):
    arr = scores[:,1]  # probability of class=1 (cycle)
    top_idx = np.argsort(-arr)[:k]
    return [(node_ids[i], float(arr[i])) for i in top_idx]

def fetch_subgraph_for_account(account_id, radius=2, limit=60):
    q = f"""
    MATCH (a:Account {{accountID: $aid}})
    CALL {
      WITH a
      MATCH path = (a)-[:PERFORMED|SENT_TO*1..{radius}]-(b)
      RETURN path LIMIT {limit}
    }
    WITH collect(path) AS paths
    CALL apoc.convert.toTree(paths) YIELD value
    RETURN value AS tree
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as s:
        res = s.run(q, aid=account_id)
        rec = res.single()
        return rec['tree'] if rec else None

def narrative_from_ollama(facts):
    prompt = f"""You are a financial crime analyst. Using only these facts, explain why this activity may indicate a circular money movement scheme. Be concise and cite the key accounts and transactions.

Facts:
{facts}
"""
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "(no response)")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--topk', type=int, default=5)
    args = ap.parse_args()

    # Inference
    data = fetch_data()
    model = TinyGAT()
    model.load_state_dict(torch.load('artifacts/model.pth', map_location='cpu'))
    model.eval()
    with torch.no_grad():
        logits = model(data.x, data.edge_index)
        probs = torch.softmax(logits, dim=1).cpu().numpy()
    candidates = top_k_accounts(probs, data.node_ids, args.topk)

    os.makedirs('artifacts', exist_ok=True)
    out_path = 'artifacts/explanations.jsonl'
    with open(out_path, 'w') as f:
        for aid, score in candidates:
            sub = fetch_subgraph_for_account(aid)
            # Turn subgraph dict into facts text
            facts = json.dumps(sub)[:8000]  # keep prompt small
            narrative = narrative_from_ollama(facts)
            rec = {"accountID": aid, "risk": score, "narrative": narrative}
            f.write(json.dumps(rec) + "\n")
            print(f"[EXPLAINED] {aid} score={score:.3f}")
    print(f"[OK] Wrote {out_path}")

if __name__ == '__main__':
    main()
