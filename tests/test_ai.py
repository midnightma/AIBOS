import pytest
import json
import unittest
from unittest.mock import patch, MagicMock, mock_open

# Import the module explicitly before patching so that the 'ai' namespace is populated
from ai.analyzer import AIAnalyzer

# We mock the Llama model so tests don't require the actual 3GB+ GGUF file to run CI/CD.
@patch('ai.analyzer.Llama')
def test_ai_analyzer_parsing(mock_llama):
    # Setup mock behavior
    mock_instance = MagicMock()
    # Simulate a clean JSON response from the LLM
    mock_instance.return_value = {
        'choices': [{
            'text': '{"clarified_request": "Test request", "security_notes": ["Note 1"], "security_score": 2}'
        }]
    }
    mock_llama.return_value = mock_instance

    # Instantiate with a dummy path and mocked file read for the policy
    with patch("builtins.open", mock_open(read_data="Dummy policy")):
        analyzer = AIAnalyzer(model_path="dummy.gguf")
        
        result = analyzer.analyze_request("Do a test")
        
        assert "clarified_request" in result
        assert result["security_score"] == 2
        assert len(result["security_notes"]) == 1

@patch('ai.analyzer.Llama')
def test_ai_analyzer_failure_fallback(mock_llama):
    # Setup mock behavior
    mock_instance = MagicMock()
    # Simulate a garbled/invalid JSON response to trigger the failsafe
    mock_instance.return_value = {
        'choices': [{
            'text': 'This is not valid JSON and will fail to parse.'
        }]
    }
    mock_llama.return_value = mock_instance

    with patch("builtins.open", mock_open(read_data="Dummy policy")):
        analyzer = AIAnalyzer(model_path="dummy.gguf")
        
        result = analyzer.analyze_request("Malicious request")
        
        # System MUST fallback to max security score on parsing failure
        assert result["security_score"] == 10
        assert "AI Parsing failure" in result["security_notes"][0]