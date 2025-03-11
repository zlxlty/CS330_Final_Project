import networkx as nx
import matplotlib.pyplot as plt

# Create a directed graph
G = nx.DiGraph()

# Add nodes
G.add_node("source")
G.add_nodes_from([1, 2, 3])
G.add_nodes_from(["a", "b"])
G.add_node("sink")

# Add edges with flow and capacity attributes:
# From source to nodes 1, 2, 3
G.add_edge("source", 1, flow=3, capacity=5)
G.add_edge("source", 2, flow=2, capacity=4)
G.add_edge("source", 3, flow=4, capacity=6)

# From nodes 1,2,3 to a and b
G.add_edge(1, "a", flow=3, capacity=5)
G.add_edge(2, "a", flow=1, capacity=4)
G.add_edge(2, "b", flow=1, capacity=3)
G.add_edge(3, "b", flow=4, capacity=6)

# From a and b to sink
G.add_edge("a", "sink", flow=4, capacity=5)
G.add_edge("b", "sink", flow=5, capacity=7)

# Manually define positions for a four-column layout:
# Column 0: source, Column 1: 1,2,3, Column 2: a,b, Column 3: sink
pos = {
    "source": (0, 0),  # Column 0 (x=0)
    1: (1, 1),  # Column 1 (x=1), spaced vertically
    2: (1, 0),
    3: (1, -1),
    "a": (2, 0.5),  # Column 2 (x=2)
    "b": (2, -0.5),
    "sink": (3, 0),  # Column 3 (x=3)
}

# Create an edge label dictionary in the format "f/c"
edge_labels = {
    (u, v): f"{data['flow']}/{data['capacity']}" for u, v, data in G.edges(data=True)
}

# Draw the graph
plt.figure(figsize=(10, 6))
nx.draw_networkx(
    G,
    pos,
    with_labels=True,
    node_color="lightblue",
    node_size=1500,
    arrows=True,
    arrowstyle="->",
    arrowsize=20,
)
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

plt.title("Directed Graph with Flow/Capacity Edge Labels")
plt.axis("off")
plt.show()
