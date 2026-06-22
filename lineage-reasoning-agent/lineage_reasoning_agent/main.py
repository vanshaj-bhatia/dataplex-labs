"""Main agent logic for Lineage Reasoning with Neo4j."""
import os
from vertexai.generative_models import GenerativeModel
import vertexai
from .tools import get_downstream_lineage, ingest_lineage_to_graph


class LineageReasoningAgent:
    def __init__(self, model_name: str = "gemini-2.5-pro"):
        """Initializes the agent."""
        vertexai.init()
        self.model = GenerativeModel(model_name)

    def analyze_impact(self, asset_fqn: str, change_description: str) -> str:
        """Analyzes the impact of a change on an asset using the graph store.

        Args:
            asset_fqn: The fully qualified name of the asset.
            change_description: Description of the proposed change.

        Returns:
            A natural language explanation of the impact.
        """
        # 1. Fetch lineage from Neo4j
        downstream_assets = get_downstream_lineage(asset_fqn)

        if not downstream_assets:
            return f"No downstream assets found for {asset_fqn} in the graph store. The change appears to be isolated."

        # 2. Construct prompt
        prompt = f"""
You are a data engineering assistant. Your task is to analyze the impact of a proposed change to a data asset.

I have queried the enterprise knowledge graph and found the following downstream assets that depend on '{asset_fqn}':
{downstream_assets}

Proposed Change to '{asset_fqn}':
{change_description}

Analyze the impact of this change on the listed downstream assets. Explain what might break or what needs to be updated. Be specific.
"""

        # 3. Call Gemini
        response = self.model.generate_content(prompt)

        return response.text

    def update_graph(self, metadata_links: list):
        """Updates the knowledge graph with new lineage metadata.

        This fulfills the 'construct or update' part of the use case.
        """
        print(f"Updating graph with {len(metadata_links)} links...")
        ingest_lineage_to_graph(metadata_links)
        print("Graph update complete.")


if __name__ == "__main__":
    # This will fail if Neo4j is not running or env vars are not set.
    # But it shows the usage.
    agent = LineageReasoningAgent()
    
    # Example of updating the graph (Construction)
    sample_links = [
        {
            "source": {"fullyQualifiedName": "bigquery:project.dataset.table_a"},
            "target": {"fullyQualifiedName": "bigquery:project.dataset.table_b"},
        },
        {
            "source": {"fullyQualifiedName": "bigquery:project.dataset.table_b"},
            "target": {"fullyQualifiedName": "bigquery:project.dataset.dashboard_c"},
        },
    ]
    agent.update_graph(sample_links)
    
    # Example of reasoning
    result = agent.analyze_impact(
        "bigquery:project.dataset.table_a",
        "Changing column 'id' from INT to STRING",
    )
    print(result)
