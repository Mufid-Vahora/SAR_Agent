
import argparse, os, pandas as pd
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

DDL = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Account) REQUIRE a.accountID IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transactionID IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Customer) REQUIRE c.customerID IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Device) REQUIRE d.deviceID IS UNIQUE",
]

def load_csvs(session, root):
    # Nodes
    accounts = pd.read_csv(os.path.join(root, "accounts.csv"))
    customers = pd.read_csv(os.path.join(root, "customers.csv"))
    devices = pd.read_csv(os.path.join(root, "devices.csv"))
    txns = pd.read_csv(os.path.join(root, "transactions.csv"))
    ep = pd.read_csv(os.path.join(root, "edges_performed.csv"))
    es = pd.read_csv(os.path.join(root, "edges_sentto.csv"))
    ei = pd.read_csv(os.path.join(root, "edges_initiated_from.csv"))

    # Create nodes
    for _, r in accounts.iterrows():
        session.run("""MERGE (a:Account {accountID:$id})
        SET a.balance=$balance, a.currency=$currency, a.accountType=$atype,
            a.riskScore=$riskScore, a.isSAR=$isSAR""", 
            id=r.accountID, balance=float(r.balance), currency=r.currency,
            atype=r.accountType, riskScore=float(r.riskScore), isSAR=bool(r.isSAR))
    for _, r in customers.iterrows():
        session.run("MERGE (c:Customer {customerID:$id}) SET c.name=$n, c.address=$addr",
                    id=r.customerID, n=r.name, addr=r.address)
    for _, r in devices.iterrows():
        session.run("MERGE (d:Device {deviceID:$id}) SET d.ipAddress=$ip",
                    id=r.deviceID, ip=r.ipAddress)
    for _, r in txns.iterrows():
        session.run("""MERGE (t:Transaction {transactionID:$id})
        SET t.amount=$amt, t.timestamp=datetime($ts), t.transactionType=$tt""", 
        id=r.transactionID, amt=float(r.amount), ts=str(r.timestamp), tt=r.transactionType)

    # Relationships
    for _, r in ep.iterrows():
        session.run("MATCH (a:Account {accountID:$a}), (t:Transaction {transactionID:$t}) MERGE (a)-[:PERFORMED]->(t)",
                    a=r.srcAccountID, t=r.transactionID)
    for _, r in es.iterrows():
        session.run("MATCH (t:Transaction {transactionID:$t}), (a:Account {accountID:$a}) MERGE (t)-[:SENT_TO]->(a)",
                    a=r.dstAccountID, t=r.transactionID)
    for _, r in ei.iterrows():
        session.run("MATCH (t:Transaction {transactionID:$t}), (d:Device {deviceID:$d}) MERGE (t)-[:INITIATED_FROM]->(d)",
                    t=r.transactionID, d=r.deviceID)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv-root", required=True)
    args = ap.parse_args()
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as s:
        for stmt in DDL:
            s.run(stmt)
        load_csvs(s, args.csv_root)
    print("[OK] Data loaded into Neo4j.")

if __name__ == "__main__":
    main()
