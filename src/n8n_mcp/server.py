import asyncio
import json
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl
import mcp.server.stdio

from n8n_mcp.n8n_api_client import N8nApiClient
from n8n_mcp.postgres_client import PostgresClient
from n8n_mcp.workflow_parser import process_all_workflows, process_workflow
from n8n_mcp.workflow_validator import validate_workflow
from n8n_mcp.embedding_client import EmbeddingClient
from pathlib import Path

server = Server("n8n-mcp")
n8n_client = N8nApiClient()
postgres_client = PostgresClient()
embedding_client = EmbeddingClient()

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="list_workflows",
            description="List all workflows from n8n.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_workflow",
            description="Get a specific workflow by ID.",
            inputSchema={
                "type": "object",
                "properties": {"workflow_id": {"type": "string"}},
                "required": ["workflow_id"],
            },
        ),
        types.Tool(
            name="create_workflow",
            description="Create a new workflow in n8n.",
            inputSchema={
                "type": "object",
                "properties": {"workflow_data": {"type": "object"}},
                "required": ["workflow_data"],
            },
        ),
        types.Tool(
            name="edit_workflow",
            description="Edit an existing workflow in n8n.",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "workflow_data": {"type": "object"},
                },
                "required": ["workflow_id", "workflow_data"],
            },
        ),
        types.Tool(
            name="validate_workflow",
            description="Validate a workflow against best practices.",
            inputSchema={
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "options": {"type": "object"},
                },
                "required": ["workflow_id"],
            },
        ),
        types.Tool(
            name="vectorize_workflows",
            description="Generate embeddings for all workflows.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="search_similar_workflows",
            description="Search for similar workflows based on a query.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="load_workflows_to_postgres",
            description="Load all processed workflows into the PostgreSQL database.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    args = arguments or {}
    if name == "list_workflows":
        result = n8n_client.get_workflows()
    elif name == "get_workflow":
        result = n8n_client.get_workflow(args.get("workflow_id"))
    elif name == "create_workflow":
        result = n8n_client.create_workflow(args.get("workflow_data"))
    elif name == "edit_workflow":
        result = n8n_client.update_workflow(args.get("workflow_id"), args.get("workflow_data"))
    elif name == "validate_workflow":
        workflow = n8n_client.get_workflow(args.get("workflow_id"))
        if workflow:
            result = validate_workflow(workflow, args.get("options"))
        else:
            result = {"status": "error", "message": f"Workflow with ID {args.get('workflow_id')} not found."}
    elif name == "vectorize_workflows":
        processed_workflows = process_all_workflows()
        embeddings = [embedding_client.get_embedding(wf["description"]) for wf in processed_workflows]
        result = {"status": "success", "count": len(embeddings)}
    elif name == "search_similar_workflows":
        processed_workflows = process_all_workflows()
        embeddings = [embedding_client.get_embedding(wf["description"]) for wf in processed_workflows]
        query_embedding = embedding_client.get_embedding(args.get("query"))
        if query_embedding:
            similar_indices = embedding_client.search_similar(query_embedding, embeddings, args.get("top_k", 5))
            result = [processed_workflows[i] for i, score in similar_indices]
        else:
            result = []
    elif name == "load_workflows_to_postgres":
        postgres_client.connect()
        if not postgres_client.connection:
            result = {"status": "error", "message": "Could not connect to PostgreSQL."}
        else:
            postgres_client.create_workflows_table()
            workflows = process_all_workflows()
            for workflow in workflows:
                postgres_client.insert_workflow(workflow)
            postgres_client.disconnect()
            result = {"status": "success", "message": f"Loaded {len(workflows)} workflows into PostgreSQL."}
    else:
        raise ValueError(f"Unknown tool: {name}")

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

async def main():
    """Run the server using stdin/stdout streams."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="n8n-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
