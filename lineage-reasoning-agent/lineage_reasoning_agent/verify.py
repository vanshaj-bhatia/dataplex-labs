from unittest.mock import MagicMock, patch
from lineage_reasoning_agent.main import LineageReasoningAgent


def run_verification():
    print("Running verification for BigQuery Graph integration...")
    
    # Mock BigQuery Client
    with patch("lineage_reasoning_agent.graph_store.bigquery.Client") as mock_client:
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        # Mock query result
        mock_query_job = MagicMock()
        mock_client_instance.query.return_value = mock_query_job
        
        mock_row = MagicMock()
        mock_row.target_fqn = "derived_table_1"
        mock_query_job.result.return_value = [mock_row]
        
        # Mock insert_rows_json
        mock_client_instance.insert_rows_json.return_value = []

        # Mock Gemini
        with patch("lineage_reasoning_agent.main.GenerativeModel") as mock_model:
            mock_model_instance = MagicMock()
            mock_model.return_value = mock_model_instance
            mock_response = MagicMock()
            mock_response.text = "Mocked impact analysis response for BQ Graph."
            mock_model_instance.generate_content.return_value = mock_response

            # Mock Vertex AI Init
            with patch("lineage_reasoning_agent.main.vertexai.init") as mock_init:
                agent = LineageReasoningAgent()
                
                # Test reasoning
                result = agent.analyze_impact(
                    "bigquery:project.dataset.source_table",
                    "Renaming column 'user_id' to 'customer_id'",
                )

                print(f"Result: {result}")
                assert result == "Mocked impact analysis response for BQ Graph."
                
                # Test update graph
                agent.update_graph([
                    {"source": {"fullyQualifiedName": "a"}, "target": {"fullyQualifiedName": "b"}}
                ])
                
                print("Verification passed!")


if __name__ == "__main__":
    run_verification()
