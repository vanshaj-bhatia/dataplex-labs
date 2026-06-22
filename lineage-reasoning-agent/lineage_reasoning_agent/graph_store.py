"""Graph store operations using BigQuery Graph."""
import os
from typing import Dict, List
from google.cloud import bigquery


class GraphStore:
    def __init__(self):
        """Initializes the BigQuery client."""
        self.client = bigquery.Client()
        self.dataset_id = os.getenv("BQ_LINEAGE_DATASET", "lineage_graph")
        self.graph_name = os.getenv("BQ_LINEAGE_GRAPH", "lineage_graph")

    def create_lineage_relationship(self, source_fqn: str, target_fqn: str):
        """Inserts a lineage relationship into the edges table.

        This assumes a table `edges` exists in the dataset.
        """
        table_ref = self.client.dataset(self.dataset_id).table("edges")
        
        rows_to_insert = [
            {"source_fqn": source_fqn, "target_fqn": target_fqn}
        ]
        
        errors = self.client.insert_rows_json(table_ref, rows_to_insert)
        if errors:
            print(f"Errors occurred while inserting rows: {errors}")
            raise Exception(f"Failed to insert rows into BQ: {errors}")

    def get_downstream_nodes(self, fqn: str) -> List[str]:
        """Fetches all downstream nodes for a given asset FQN using BigQuery
        Graph.

        This assumes a Property Graph named `lineage_graph` is defined.
        """
        # Construct the query using BigQuery Graph syntax (openCypher)
        # Note: The exact syntax may depend on how the graph was created.
        # We assume a standard GRAPH_TABLE usage.
        query = f"""
        SELECT target_fqn
        FROM GRAPH_TABLE(
          `{self.client.project}.{self.dataset_id}.{self.graph_name}`
          MATCH (source:Dataset {{fqn: @fqn}})-[:LEADS_TO*]->(target:Dataset)
          COLUMNS(target.fqn AS target_fqn)
        )
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("fqn", "STRING", fqn)
            ]
        )
        
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        
        return [row.target_fqn for row in results]
