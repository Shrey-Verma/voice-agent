#!/bin/bash

# Base URL
API_URL="http://localhost:8000"

echo "Testing Workflow API..."
echo

# List workflows (should be empty initially)
echo "1. Listing workflows..."
curl -s -X GET "$API_URL/workflows/"
echo -e "\n"

# Create a workflow
echo "2. Creating workflow..."
WORKFLOW_RESPONSE=$(curl -s -X POST "$API_URL/workflows/" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "",
    "name": "Test Workflow",
    "version": 1,
    "variables": {},
    "nodes": [
      {
        "id": "prompt1",
        "type": "Prompt",
        "config": {
          "text": "What is your name?"
        },
        "position": {"x": 100, "y": 100}
      },
      {
        "id": "llm1",
        "type": "LLM",
        "config": {
          "fields": ["name"],
          "model": "gpt-4-turbo-preview"
        },
        "position": {"x": 100, "y": 200}
      }
    ],
    "edges": [
      {
        "id": "e1",
        "source": "prompt1",
        "target": "llm1"
      }
    ]
  }')
echo "$WORKFLOW_RESPONSE"
echo

# Extract workflow ID
WORKFLOW_ID=$(echo "$WORKFLOW_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created workflow ID: $WORKFLOW_ID"
echo

# Get the workflow
echo "3. Getting workflow..."
curl -s -X GET "$API_URL/workflows/$WORKFLOW_ID"
echo -e "\n"

# Start a run
echo "4. Starting workflow run..."
RUN_RESPONSE=$(curl -s -X POST "$API_URL/runs/" \
  -H "Content-Type: application/json" \
  -d "{
    \"workflow_id\": \"$WORKFLOW_ID\",
    \"input_text\": \"Hello\"
  }")
echo "$RUN_RESPONSE"
echo

# Extract run ID
RUN_ID=$(echo "$RUN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Created run ID: $RUN_ID"
echo

# Step through the run
echo "5. Stepping through run..."
curl -s -X POST "$API_URL/runs/$RUN_ID/step" \
  -H "Content-Type: application/json" \
  -d '{
    "user_text": "John"
  }'
echo -e "\n"

