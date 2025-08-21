"""Test script for API endpoints.

This script tests all the workflow and run API endpoints, including:
- Workflow CRUD operations
- Run operations
- LLM integration

Make sure to have the backend server running before executing this script.
Also ensure you have the OPENAI_API_KEY environment variable set.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, TextIO

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "test_results"

# Test data
TEST_WORKFLOW = {
    "id": f"test-workflow-{uuid.uuid4()}",
    "name": "Test Workflow",
    "version": 1,
    "variables": {},
    "nodes": [
        {
            "id": "start",
            "type": "Prompt",
            "config": {
                "text": "What would you like me to help you with?"
            },
            "next": "llm"
        },
        {
            "id": "llm",
            "type": "LLM",
            "config": {
                "prompt": "User request: {{user_input}}\nAnalyze the request and provide a JSON response with the following fields:\n- response: A helpful response to the user\n- topic: The main topic or category of the request\n- complexity: The complexity level (simple/medium/complex)",
                "extract": ["response", "topic", "complexity"]
            },
            "next": "output"
        },
        {
            "id": "output",
            "type": "Output",
            "config": {
                "text": "Response: {{response}}\nTopic: {{topic}}\nComplexity: {{complexity}}"
            }
        }
    ],
    "edges": [
        {
            "id": "edge1",
            "source": "start",
            "target": "llm"
        },
        {
            "id": "edge2",
            "source": "llm",
            "target": "output"
        }
    ]
}

class MarkdownWriter:
    """Helper class to write test results in markdown format."""

    def __init__(self) -> None:
        """Initialize markdown writer."""
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = OUTPUT_DIR / f"api_test_results_{self.timestamp}.md"
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.file: TextIO

    def __enter__(self) -> 'MarkdownWriter':
        """Open file for writing."""
        self.file = open(self.output_file, 'w', encoding='utf-8')
        self.write_header()
        return self

    def __exit__(self, *args: Any) -> None:
        """Close file."""
        self.file.close()

    def write_header(self) -> None:
        """Write markdown header."""
        self.file.write(f"# API Test Results\n\n")
        self.file.write(f"Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        self.file.write(f"Server URL: {BASE_URL}\n\n")

    def write_section(self, title: str) -> None:
        """Write section header."""
        self.file.write(f"\n## {title}\n\n")

    def write_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write request details."""
        self.file.write(f"### {method} {path}\n\n")
        if data:
            self.file.write("Request body:\n```json\n")
            self.file.write(json.dumps(data, indent=2))
            self.file.write("\n```\n\n")

    def write_response(
        self,
        status_code: int,
        headers: Dict[str, str],
        body: str
    ) -> None:
        """Write response details."""
        self.file.write(f"Response status: {status_code}\n\n")
        self.file.write("Response headers:\n```json\n")
        self.file.write(json.dumps(headers, indent=2))
        self.file.write("\n```\n\n")
        self.file.write("Response body:\n```json\n")
        try:
            # Try to format as JSON
            self.file.write(json.dumps(json.loads(body), indent=2))
        except:
            # Fallback to raw text
            self.file.write(body)
        self.file.write("\n```\n\n")

    def write_error(self, error: str) -> None:
        """Write error message."""
        self.file.write(f"❌ Error: {error}\n\n")

    def write_success(self, message: str) -> None:
        """Write success message."""
        self.file.write(f"✅ {message}\n\n")

async def make_request(
    writer: MarkdownWriter,
    method: str,
    path: str,
    json_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an HTTP request to the API."""
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}{path}"
        writer.write_request(method, path, json_data)
        
        try:
            response = await client.request(
                method,
                url,
                json=json_data,
                headers=HEADERS
            )
            
            writer.write_response(
                response.status_code,
                dict(response.headers),
                response.text
            )
            
            if not response.is_success:
                raise Exception(f"Request failed with status {response.status_code}: {response.text}")
            
            return response.json() if response.text else {}
            
        except httpx.RequestError as e:
            writer.write_error(f"Request error: {str(e)}")
            raise

async def test_workflow_crud(writer: MarkdownWriter) -> str:
    """Test workflow CRUD operations."""
    writer.write_section("Workflow CRUD Operations")
    
    # Create workflow
    writer.write_success("Creating workflow...")
    workflow = await make_request(writer, "POST", "/workflows/", TEST_WORKFLOW)
    writer.write_success(f"Created workflow: {workflow['id']}")
    
    # Get workflow
    writer.write_success("Getting workflow...")
    retrieved = await make_request(writer, "GET", f"/workflows/{workflow['id']}")
    writer.write_success(f"Retrieved workflow: {retrieved['id']}")
    
    # List workflows
    writer.write_success("Listing workflows...")
    workflows = await make_request(writer, "GET", "/workflows/")
    writer.write_success(f"Found {len(workflows)} workflows")
    
    # Update workflow
    writer.write_success("Updating workflow...")
    workflow["name"] = "Updated Test Workflow"
    updated = await make_request(
        writer,
        "PUT",
        f"/workflows/{workflow['id']}",
        workflow
    )
    writer.write_success(f"Updated workflow name: {updated['name']}")
    
    return workflow["id"]

async def test_run_operations(writer: MarkdownWriter, workflow_id: str) -> None:
    """Test run operations."""
    writer.write_section("Run Operations")
    
    # Start run
    writer.write_success("Starting run...")
    run = await make_request(
        writer,
        "POST",
        "/runs/",
        {"workflow_id": workflow_id}
    )
    writer.write_success(f"Started run: {run['id']}")
    
    # Get run
    writer.write_success("Getting run...")
    retrieved_run = await make_request(writer, "GET", f"/runs/{run['id']}")
    writer.write_success(f"Retrieved run: {retrieved_run['id']}")
    
    # Step run multiple times to test conversation flow
    test_messages = [
        "Help me write a Python script",
        "I want to create a web scraper",
        "Make it handle pagination"
    ]
    
    for msg in test_messages:
        writer.write_success(f"Stepping run with message: {msg}")
        stepped_run = await make_request(
            writer,
            "POST",
            f"/runs/{run['id']}/step",
            {"user_text": msg}
        )
        
        # Get run steps
        steps = await make_request(writer, "GET", f"/runs/{run['id']}/steps")
        
        # Verify run state
        writer.write_success(f"Run status: {stepped_run['status']}")
        writer.write_success(f"Run variables: {json.dumps(stepped_run.get('variables', {}), indent=2)}")
        writer.write_success(f"Total steps: {len(steps)}")
        
        # Verify latest step
        if steps:
            latest_step = steps[-1]
            writer.write_success(f"Latest step node: {latest_step['node_id']}")
            writer.write_success(f"Step latency: {latest_step['latency_ms']}ms")
            writer.write_success(f"Input messages: {json.dumps(latest_step['input_messages'], indent=2)}")
            writer.write_success(f"Output messages: {json.dumps(latest_step['output_messages'], indent=2)}")
            writer.write_success(f"Variables snapshot: {json.dumps(latest_step['variables_snapshot'], indent=2)}")
        
        # Add delay between steps
        await asyncio.sleep(1)

async def cleanup(writer: MarkdownWriter, workflow_id: str) -> None:
    """Clean up test data."""
    writer.write_section("Cleanup")
    
    # Delete workflow
    writer.write_success("Deleting workflow...")
    await make_request(writer, "DELETE", f"/workflows/{workflow_id}")
    writer.write_success("Workflow deleted")

async def main() -> None:
    """Run all tests."""
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    with MarkdownWriter() as writer:
        try:
            # Test workflow CRUD
            workflow_id = await test_workflow_crud(writer)
            
            # Test run operations
            await test_run_operations(writer, workflow_id)
            
            # Clean up
            await cleanup(writer, workflow_id)
            
            writer.write_success("All tests completed successfully!")
            print(f"\n✅ Test results saved to: {writer.output_file}")
            
        except Exception as e:
            writer.write_error(f"Tests failed: {str(e)}")
            print(f"\n❌ Tests failed: {str(e)}")
            print(f"See details in: {writer.output_file}")

if __name__ == "__main__":
    asyncio.run(main())