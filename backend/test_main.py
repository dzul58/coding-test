import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, mock_open, MagicMock
from main import app, load_data, paginate_data, search_data

# Create test client
client = TestClient(app)

# Sample dummy data for testing
DUMMY_DATA = {
    "salesReps": [
        {
            "id": "1",
            "name": "John Doe",
            "role": "Sales Manager",
            "region": "North America",
            "skills": ["Negotiation", "Leadership", "Product Knowledge"],
            "deals": [
                {"client": "ABC Corp", "value": 50000, "status": "Closed Won"},
                {"client": "XYZ Inc", "value": 75000, "status": "In Progress"}
            ],
            "clients": [
                {"name": "ABC Corp", "industry": "Technology", "contact": "contact@abc.com"},
                {"name": "XYZ Inc", "industry": "Healthcare", "contact": "contact@xyz.com"}
            ]
        },
        {
            "id": "2",
            "name": "Jane Smith",
            "role": "Account Executive",
            "region": "Europe",
            "skills": ["Prospecting", "CRM", "B2B Sales"],
            "deals": [
                {"client": "Global Ltd", "value": 30000, "status": "Closed Lost"},
                {"client": "Euro Tech", "value": 45000, "status": "Closed Won"}
            ],
            "clients": [
                {"name": "Global Ltd", "industry": "Finance", "contact": "contact@global.com"},
                {"name": "Euro Tech", "industry": "Technology", "contact": "contact@eurotech.com"}
            ]
        }
    ]
}

# Mock data loading
@pytest.fixture
def mock_load_data():
    with patch('main.load_data', return_value=DUMMY_DATA):
        yield DUMMY_DATA

# Test load_data function with mocked file
def test_load_data():
    # Mock open to return our dummy data
    mock_file_data = json.dumps(DUMMY_DATA)
    with patch("builtins.open", mock_open(read_data=mock_file_data)):
        data = load_data()
        assert data == DUMMY_DATA
        assert "salesReps" in data
        assert len(data["salesReps"]) == 2

# Test search_data function
def test_search_data():
    # Test with name search
    results = search_data(DUMMY_DATA["salesReps"], "john")
    assert len(results) == 1
    assert results[0]["name"] == "John Doe"
    
    # Test with role search
    results = search_data(DUMMY_DATA["salesReps"], "manager")
    assert len(results) == 1
    assert results[0]["role"] == "Sales Manager"
    
    # Test with region search
    results = search_data(DUMMY_DATA["salesReps"], "europe")
    assert len(results) == 1
    assert results[0]["region"] == "Europe"
    
    # Test with skill search
    results = search_data(DUMMY_DATA["salesReps"], "leadership")
    assert len(results) == 1
    assert "Leadership" in results[0]["skills"]
    
    # Test with empty search
    results = search_data(DUMMY_DATA["salesReps"], "")
    assert len(results) == 2
    
    # Test with non-matching search
    results = search_data(DUMMY_DATA["salesReps"], "nonexistent")
    assert len(results) == 0

# Test paginate_data function
def test_paginate_data():
    # Generate list with 15 items
    data = [{"id": str(i), "name": f"Test {i}"} for i in range(1, 16)]
    
    # Test first page with 10 items per page
    result = paginate_data(data, 1, 10)
    assert len(result["data"]) == 10
    assert result["meta"]["page"] == 1
    assert result["meta"]["total_items"] == 15
    assert result["meta"]["total_pages"] == 2
    assert result["meta"]["has_next"] == True
    assert result["meta"]["has_prev"] == False
    
    # Test second page with 10 items per page
    result = paginate_data(data, 2, 10)
    assert len(result["data"]) == 5
    assert result["meta"]["page"] == 2
    assert result["meta"]["has_next"] == False
    assert result["meta"]["has_prev"] == True
    
    # Test with custom page size
    result = paginate_data(data, 1, 5)
    assert len(result["data"]) == 5
    assert result["meta"]["total_pages"] == 3

# Test GET /api/sales-reps endpoint
def test_get_sales_reps(mock_load_data):
    response = client.get("/api/sales-reps")
    assert response.status_code == 200
    data = response.json()
    
    # Check structure and content
    assert "data" in data
    assert "meta" in data
    assert len(data["data"]) == 2
    assert data["meta"]["page"] == 1
    assert data["meta"]["total_items"] == 2

# Test GET /api/sales-reps with search parameters
def test_get_sales_reps_with_search(mock_load_data):
    # Test name search
    response = client.get("/api/sales-reps?name=john")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "John Doe"
    
    # Test role search
    response = client.get("/api/sales-reps?role=executive")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["role"] == "Account Executive"
    
    # Test region search
    response = client.get("/api/sales-reps?region=europe")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["region"] == "Europe"
    
    # Test skills search
    response = client.get("/api/sales-reps?skills=leadership")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert "Leadership" in data["data"][0]["skills"]
    
    # Test no results
    response = client.get("/api/sales-reps?name=nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 0

# Test GET /api/sales-reps with pagination
def test_get_sales_reps_with_pagination(mock_load_data):
    # Test with page=1 and page_size=1
    response = client.get("/api/sales-reps?page=1&page_size=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["meta"]["page"] == 1
    assert data["meta"]["total_items"] == 2
    assert data["meta"]["total_pages"] == 2
    assert data["meta"]["has_next"] == True
    
    # Test with page=2 and page_size=1
    response = client.get("/api/sales-reps?page=2&page_size=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["meta"]["page"] == 2
    assert data["meta"]["has_next"] == False
    assert data["meta"]["has_prev"] == True

# Test POST /api/ai endpoint
@patch('google.generativeai.GenerativeModel')
def test_ai_endpoint(mock_generative_model, mock_load_data):
    # Setup mock for Gemini AI
    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "The top sales rep is John Doe with deals worth $125,000 in total. He has one Closed Won deal with ABC Corp."
    mock_chat.send_message.return_value = mock_response
    mock_model = MagicMock()
    mock_model.start_chat.return_value = mock_chat
    mock_generative_model.return_value = mock_model
    
    # Test with question
    request_data = {
        "question": "Who is the top sales rep?"
    }
    response = client.post("/api/ai", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0
    
    # Check that the model was called with the right parameters
    mock_generative_model.assert_called_once()
    mock_model.start_chat.assert_called_once()
    mock_chat.send_message.assert_called_once()
    
    # Test with both question and data
    mock_chat.send_message.reset_mock()
    mock_model.start_chat.reset_mock()
    mock_generative_model.reset_mock()
    
    request_data = {
        "question": "Who is the top sales rep?",
        "data": DUMMY_DATA
    }
    response = client.post("/api/ai", json=request_data)
    assert response.status_code == 200
    
    # Check that the model was called with the data provided
    mock_generative_model.assert_called_once()
    mock_model.start_chat.assert_called_once()
    mock_chat.send_message.assert_called_once()

# Test error handling for load_data
@patch("builtins.open", side_effect=Exception("File not found"))
def test_load_data_error(mock_open):
    with pytest.raises(Exception):
        load_data()

# Test error handling for GET /api/sales-reps
@patch('main.load_data', side_effect=Exception("Database error"))
def test_get_sales_reps_error(mock_load_data):
    response = client.get("/api/sales-reps")
    assert response.status_code == 500
    assert "detail" in response.json()

# Test error handling for POST /api/ai
@patch('main.load_data', return_value={"salesReps": []})
def test_ai_endpoint_empty_data(mock_load_data):
    request_data = {
        "question": "Who is the top sales rep?"
    }
    response = client.post("/api/ai", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "empty" in data["answer"].lower() or "not in the expected format" in data["answer"].lower()

# Test AI endpoint with invalid model - FIXED TEST
@patch('google.generativeai.GenerativeModel', side_effect=Exception("Model not available"))
@patch('main.load_data', return_value=DUMMY_DATA)
def test_ai_endpoint_model_error(mock_load_data, mock_generative_model):
    request_data = {
        "question": "Who is the top sales rep?"
    }
    response = client.post("/api/ai", json=request_data)
    
    # Update test to expect 200 status code instead of 500
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    # Verify the response indicates service unavailability
    assert "AI service is currently unavailable" in data["answer"]