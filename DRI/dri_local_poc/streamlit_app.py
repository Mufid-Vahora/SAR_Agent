
import streamlit as st, json, os
import plotly.graph_objects as go
from neo4j import GraphDatabase

st.set_page_config(page_title="DRI PoC", layout="wide")

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

@st.cache_data(ttl=30)
def list_top_accounts(limit=30):
    # Read last explanations file if present
    path = 'artifacts/explanations.jsonl'
    items = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                items.append(json.loads(line))
    items = sorted(items, key=lambda x: -x.get('risk', 0.0))
    return items[:limit]

def fetch_edges_for_account(aid, radius=2, limit=80):
    q = f"""
    MATCH (a:Account {{accountID:$aid}})
    MATCH p=(a)-[:PERFORMED|SENT_TO*1..{radius}]-(b:Account)
    WITH nodes(p) AS ns, relationships(p) AS rs
    UNWIND ns AS n
    WITH collect(DISTINCT n) AS nodes, rs
    UNWIND rs AS r
    RETURN [n IN nodes | n.accountID] AS node_ids, collect({{
      src: startNode(r).accountID,
      dst: endNode(r).accountID
    }})[0..{limit}] AS edges
    """
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as s:
        rec = s.run(q, aid=aid).single()
        if not rec:
            return [], []
        return rec['node_ids'], rec['edges']

def draw_graph(node_ids, edges):
    if not node_ids:
        st.info("No subgraph found.")
        return
    # simple circular layout
    import math
    N = len(node_ids)
    pos = {node_ids[i]:(math.cos(2*math.pi*i/N), math.sin(2*math.pi*i/N)) for i in range(N)}
    edge_x, edge_y = [], []
    for e in edges:
        if e['src'] in pos and e['dst'] in pos:
            x0,y0 = pos[e['src']]
            x1,y1 = pos[e['dst']]
            edge_x += [x0,x1,None]
            edge_y += [y0,y1,None]
    node_x = [pos[n][0] for n in node_ids]
    node_y = [pos[n][1] for n in node_ids]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', hoverinfo='none'))
    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text',
                             text=node_ids, textposition='top center'))
    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=520)
    st.plotly_chart(fig, use_container_width=True)

st.title("Dynamic Risk Intelligence — Local PoC (Ollama gemma:2b)")
items = list_top_accounts()
if not items:
    st.warning("Run detection first: `python detect_and_explain.py --topk 5`.")
else:
    labels = [f"{it['accountID']} (risk={it['risk']:.2f})" for it in items]
    choice = st.selectbox("Select an alert:", labels)
    sel = items[labels.index(choice)]
    st.subheader(f"Alert: {sel['accountID']}")
    c1, c2 = st.columns([2,1])
    with c1:
        nodes, edges = fetch_edges_for_account(sel['accountID'])
        draw_graph(nodes, edges)
    with c2:
        st.markdown("### Narrative (LLM)")
        st.write(sel.get('narrative','(no narrative)'))
