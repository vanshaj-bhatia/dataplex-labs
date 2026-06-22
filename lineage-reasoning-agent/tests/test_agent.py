"""Tests for LineageReasoningAgent."""
from unittest.mock import MagicMock, patch
import pytest
from lineage_reasoning_agent.main import LineageReasoningAgent


@pytest.fixture
def mock_generative_model():
    with patch("lineage_reasoning_agent.main.GenerativeModel") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        # Mock the response of generate_content
        mock_response = MagicMock()
        mock_response.text = "Mocked impact analysis response."
        mock_instance.generate_content.return_value = mock_response
        yield mock_instance


@pytest.fixture
def mock_vertexai_init():
    with patch("lineage_reasoning_agent.main.vertexai.init") as mock:
        yield mock


def test_analyze_impact_with_lineage(mock_generative_model, mock_vertexai_init):
    # We don't mock get_downstream_lineage because we want to test it with the dummy data
    # for the specific test table.
    
    agent = LineageReasoningAgent()
    
    # Call with the table that has dummy data in tools.py
    result = agent.analyze_impact(
        "bigquery:project.dataset.source_table",
        "Renaming column 'user_id' to 'customer_id'",
    )
    
    # Verify vertexai.init was called
    mock_vertexai_init.assert_called_once()
    
    # Verify generate_content was called
    mock_generative_model.generate_content.assert_called_once()
    
    # Verify response matches mock
    assert result == "Mocked impact analysis response."


def test_analyze_impact_no_lineage(mock_generative_model, mock_vertexai_init):
    agent = LineageReasoningAgent()
    
    # Call with a table that has NO dummy data
    result = agent.analyze_impact(
        "bigquery:project.dataset.unknown_table",
        "Renaming column 'user_id' to 'customer_id'",
    )
    
    # Verify generate_content was NOT called
    mock_generative_model.generate_content.assert_not_called()
    
    # Verify response indicates no lineage
    assert "No downstream lineage found" in result
