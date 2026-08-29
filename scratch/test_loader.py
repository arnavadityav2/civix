import torch
from torch_geometric.data import Data
from torch_geometric.loader import NeighborLoader

print("Testing NeighborLoader...")
try:
    x = torch.randn(100, 16)
    edge_index = torch.randint(0, 100, (2, 500))
    data = Data(x=x, edge_index=edge_index)
    loader = NeighborLoader(data, num_neighbors=[5, 5], batch_size=10, num_workers=0)
    for batch in loader:
        print("Success! Batch nodes:", batch.num_nodes)
        break
except Exception as e:
    print("Error:", e)
