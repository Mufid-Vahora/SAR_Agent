
import argparse, torch, pandas as pd
from neo4j import GraphDatabase
from torch_geometric.data import Data
from torch_geometric.nn import GATConv
import torch.nn.functional as F
import numpy as np
import os, json

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

# Pull a simple directed graph from Neo4j (Accounts only; edges from PERFORMED->SENT_TO chain)
# Also load labels from labels.csv (transaction-level), and project to account labels if any cycle tx touches the account.
def fetch_graph(label_csv_path):
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as s:
        # Accounts
        res = s.run("MATCH (a:Account) RETURN a.accountID as id ORDER BY id")
        nodes = [r["id"] for r in res]
        idx = {n:i for i,n in enumerate(nodes)}
        # Edges account->account through transactions
        res = s.run("""
        MATCH (a:Account)-[:PERFORMED]->(t:Transaction)-[:SENT_TO]->(b:Account)
        RETURN a.accountID as src, b.accountID as dst
        """)
        edges = [(idx[r['src']], idx[r['dst']]) for r in res if r['src'] in idx and r['dst'] in idx]
    # Labels
    labels_df = pd.read_csv(label_csv_path)
    cycle_tx = set(labels_df[labels_df['label']=='cycle']['transactionID'].tolist())
    # map txn to accounts using CSV edges
    ep = pd.read_csv(os.path.join(os.path.dirname(label_csv_path), 'edges_performed.csv'))
    es = pd.read_csv(os.path.join(os.path.dirname(label_csv_path), 'edges_sentto.csv'))
    tx_to_accounts = {}
    for _, r in ep.iterrows():
        tx_to_accounts.setdefault(r['transactionID'], set()).add(r['srcAccountID'])
    for _, r in es.iterrows():
        tx_to_accounts.setdefault(r['transactionID'], set()).add(r['dstAccountID'])
    y = np.zeros(len(nodes), dtype=np.int64)
    for tx in cycle_tx:
        for a in tx_to_accounts.get(tx, []):
            if a in idx:
                y[idx[a]] = 1
    # features: degree in/out
    import networkx as nx
    g = nx.DiGraph()
    g.add_nodes_from(range(len(nodes)))
    g.add_edges_from(edges)
    indeg = np.array([g.in_degree(i) for i in range(len(nodes))], dtype=np.float32)
    outdeg = np.array([g.out_degree(i) for i in range(len(nodes))], dtype=np.float32)
    x = np.stack([indeg, outdeg], axis=1)
    edge_index = torch.tensor(np.array(edges).T, dtype=torch.long) if edges else torch.empty((2,0), dtype=torch.long)
    data = Data(x=torch.tensor(x, dtype=torch.float32),
                edge_index=edge_index,
                y=torch.tensor(y, dtype=torch.long))
    data.node_ids = nodes
    return data

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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--epochs', type=int, default=5)
    args = ap.parse_args()
    data = fetch_graph(os.path.join(os.path.dirname(__file__), '..', 'dri_synthetic_data', 'labels.csv'))
    model = TinyGAT()
    opt = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    for epoch in range(1, args.epochs+1):
        model.train()
        opt.zero_grad()
        out = model(data.x, data.edge_index)
        loss = F.cross_entropy(out, data.y)
        loss.backward()
        opt.step()
        with torch.no_grad():
            pred = out.argmax(dim=1)
            acc = (pred == data.y).float().mean().item()
        print(f"epoch {epoch} loss={loss.item():.4f} acc={acc:.3f}")
    os.makedirs('artifacts', exist_ok=True)
    torch.save(model.state_dict(), 'artifacts/model.pth')
    # write node ids for later
    with open('artifacts/node_ids.json','w') as f:
        json.dump(list(data.node_ids), f)
    print('[OK] Saved artifacts/model.pth')

if __name__ == '__main__':
    main()
