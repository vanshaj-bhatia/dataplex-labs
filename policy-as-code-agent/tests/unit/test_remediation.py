from unittest.mock import MagicMock, patch
import json
import pytest

from policy_as_code_agent.agent import suggest_remediation, apply_remediation


@pytest.fixture
def mock_gemini():
    with patch("policy_as_code_agent.agent.GenerativeModel") as mock_model, \
         patch("policy_as_code_agent.agent.vertexai.init") as mock_init:
        
        mock_model_instance = MagicMock()
        
        def dynamic_generate_content(prompt, **kwargs):
            import re
            import json
            # Extract violations JSON block from the prompt
            match = re.search(r"Violations:\n(.*)", prompt, re.DOTALL)
            if match:
                try:
                    violations = json.loads(match.group(1).strip())
                    suggestions = [
                        {"violation": v, "suggestion": "Mocked suggestion text"}
                        for v in violations
                    ]
                    mock_res = MagicMock()
                    mock_res.text = json.dumps(suggestions)
                    return mock_res
                except Exception:
                    pass
            # Fallback
            mock_res = MagicMock()
            mock_res.text = "[]"
            return mock_res
            
        mock_model_instance.generate_content.side_effect = dynamic_generate_content
        mock_model.return_value = mock_model_instance
        
        yield mock_model_instance


def test_suggest_remediation_standard_list(mock_gemini):
    violations = [
        {
            "resource_name": "projects/p/datasets/d/tables/t1",
            "policy": "P1",
            "violation": "V1"
        },
        {
            "resource_name": "projects/p/datasets/d/tables/t2",
            "policy": "P2",
            "violation": "V2"
        }
    ]

    res = suggest_remediation(violations)
    assert res["status"] == "success"
    suggestions = res["remediation_suggestions"]
    assert len(suggestions) == 2
    
    # Verify order is preserved
    assert suggestions[0]["violation"]["resource_name"] == "projects/p/datasets/d/tables/t1"
    assert suggestions[1]["violation"]["resource_name"] == "projects/p/datasets/d/tables/t2"
    assert suggestions[0]["suggestion"] == "Mocked suggestion text"


def test_suggest_remediation_json_string(mock_gemini):
    violations = [
        {
            "resource_name": "projects/p/datasets/d/tables/t1",
            "policy": "P1",
            "violation": "V1"
        }
    ]
    json_str = json.dumps(violations)

    res = suggest_remediation(json_str)
    assert res["status"] == "success"
    suggestions = res["remediation_suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["violation"]["resource_name"] == "projects/p/datasets/d/tables/t1"


def test_suggest_remediation_single_dict(mock_gemini):
    violation = {
        "resource_name": "projects/p/datasets/d/tables/t1",
        "policy": "P1",
        "violation": "V1"
    }

    res = suggest_remediation(violation)
    assert res["status"] == "success"
    suggestions = res["remediation_suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["violation"]["resource_name"] == "projects/p/datasets/d/tables/t1"


def test_suggest_remediation_list_of_strings(mock_gemini):
    violations = ["Simple string violation description"]

    res = suggest_remediation(violations)
    assert res["status"] == "success"
    suggestions = res["remediation_suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["violation"] == {"violation": "Simple string violation description"}


def test_suggest_remediation_filters_system_errors(mock_gemini):
    violations = [
        {
            "policy": "Security Violation",
            "violation": "Restricted import"
        },
        {
            "policy": "Execution Error",
            "violation": "Syntax error"
        },
        {
            "resource_name": "projects/p/datasets/d/tables/t1",
            "policy": "P1",
            "violation": "V1"
        }
    ]

    res = suggest_remediation(violations)
    assert res["status"] == "success"
    suggestions = res["remediation_suggestions"]
    assert len(suggestions) == 1
    assert suggestions[0]["violation"]["resource_name"] == "projects/p/datasets/d/tables/t1"


# --- apply_remediation Tests ---

@patch("policy_as_code_agent.agent.subprocess.run")
def test_apply_remediation_success(mock_run):
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "Updated successfully."
    mock_res.stderr = ""
    mock_run.return_value = mock_res

    res = apply_remediation("bq query --use_legacy_sql=false 'SELECT 1'")
    assert res["status"] == "success"
    assert res["output"] == "Updated successfully."
    
    # Check that subprocess.run was called safely with list of args
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert args[0] == ["bq", "query", "--use_legacy_sql=false", "SELECT 1"]


@patch("policy_as_code_agent.agent.subprocess.run")
def test_apply_remediation_failure(mock_run):
    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stdout = ""
    mock_res.stderr = "Access denied."
    mock_run.return_value = mock_res

    res = apply_remediation("bq query 'SELECT 1'")
    assert res["status"] == "error"
    assert "Access denied." in res["error_message"]


def test_apply_remediation_unallowed_command():
    res = apply_remediation("rm -rf /")
    assert res["status"] == "error"
    assert "Security violation" in res["error_message"]
    
    res2 = apply_remediation("apt-get install curl")
    assert res2["status"] == "error"
    assert "Security violation" in res2["error_message"]


def test_apply_remediation_empty_or_none():
    res = apply_remediation("")
    assert res["status"] == "error"
    assert "Command is required." in res["error_message"]
