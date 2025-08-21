"""Script to check if database tables are properly initialized."""

from app.infra.supabase_client import SupabaseClient

async def check_tables():
    """Check if required tables exist."""
    client = SupabaseClient.get_client()
    
    # Check workflows table
    result = client.table("workflows").select("*").limit(1).execute()
    print("Workflows table exists:", bool(result.data is not None))
    
    # Check runs table
    result = client.table("runs").select("*").limit(1).execute()
    print("Runs table exists:", bool(result.data is not None))
    
    # Check run_steps table
    result = client.table("run_steps").select("*").limit(1).execute()
    print("Run steps table exists:", bool(result.data is not None))
    
    # Check audit_logs table
    result = client.table("audit_logs").select("*").limit(1).execute()
    print("Audit logs table exists:", bool(result.data is not None))

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_tables())

