"""Tests for GraphStore with BigQuery."""
from unittest.mock import MagicMock, patch
import pytest
from lineage_reasoning_agent.graph_store import GraphStore


@pytest.fixture
def mock_bq_client():
    with patch("lineage_reasoning_agent.graph_store.bigquery.Client") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


def test_create_lineage_relationship(mock_bq_client):
    store = GraphStore()
    
    # Mock insert_rows_json to return no errors
    mock_bq_client.insert_rows_json.return_value = []
    
    store.create_lineage_relationship("source", "target")
    
    # Verify insert_rows_json was called
    mock_bq_client.insert_rows_json.assert_called_once()


def test_get_downstream_nodes(mock_bq_client):
    store = GraphStore()
    
    # Mock query and result
    mock_query_job = MagicMock()
    mock_bq_client.query.return_value = mock_query_job
    
    mock_row = MagicMock()
    mock_row.target_fqn = "downstream_1"
    mock_query_job.result.return_value = [mock_row]
    
    nodes = store.get_downstream_nodes("source")
    
    assert nodes == ["downstream_1"]
    mock_bq_client.query.assert_called_once()
