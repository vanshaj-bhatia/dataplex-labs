"""Tools for interacting with Graph Store and Dataplex."""
from typing import Dict, List
from .graph_store import GraphStore


def get_downstream_lineage(asset_fqn: str) -> List[str]:
    """Fetches downstream lineage for a given asset from BigQuery Graph.

    Args:
        asset_fqn: The fully qualified name of the asset.

    Returns:
        A list of downstream asset FQNs.
    """
    store = GraphStore()
    return store.get_downstream_nodes(asset_fqn)


def ingest_lineage_to_graph(links: List[Dict]):
    """Ingests a list of lineage links into BigQuery Graph tables.

    Args:
        links: A list of dicts, each containing 'source' and 'target' with
          'fullyQualifiedName'.
    """
    store = GraphStore()
    for link in links:
        source = link["source"]["fullyQualifiedName"]
        target = link["target"]["fullyQualifiedName"]
        store.create_lineage_relationship(source, target)
