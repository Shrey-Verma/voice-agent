"""Script to list all workflows in the database."""

from app.infra.supabase_client import SupabaseClient

def list_workflows():
    """List all workflows."""
    client = SupabaseClient.get_client()
    result = client.table("workflows").select("*").execute()
    print("\nWorkflows in database:")
    for workflow in result.data:
        print(f"\nID: {workflow['id']}")
        print(f"Name: {workflow['name']}")
        print(f"Version: {workflow['version']}")
        print(f"Created at: {workflow['created_at']}")
        print("-" * 50)

if __name__ == "__main__":
    list_workflows()

