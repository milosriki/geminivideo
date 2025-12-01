import os
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MetaAdsMCPClient:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="python3",
            args=["backend/run_mcp_server.py"],
            env={
                **os.environ,
                "META_APP_ID": os.getenv("META_APP_ID", ""),
                "META_APP_SECRET": os.getenv("META_APP_SECRET", ""),
                "META_ACCESS_TOKEN": os.getenv("META_ACCESS_TOKEN", ""),
                "META_AD_ACCOUNT_ID": os.getenv("META_AD_ACCOUNT_ID", "")
            }
        )
        self.session = None
        self.exit_stack = None

    async def connect(self):
        """Establishes the connection to the MCP server."""
        try:
            # We use the context manager manually to keep the session open
            from contextlib import AsyncExitStack
            self.exit_stack = AsyncExitStack()
            
            read, write = await self.exit_stack.enter_async_context(
                stdio_client(self.server_params)
            )
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await self.session.initialize()
            print("✅ MCP Client: Connected to Meta Ads Server")
            return True
        except Exception as e:
            print(f"❌ MCP Client Connection Error: {e}")
            return False

    async def list_tools(self):
        """Lists available tools from the MCP server."""
        if not self.session:
            return []
        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, name: str, arguments: dict):
        """Calls a specific tool on the MCP server."""
        if not self.session:
            raise Exception("MCP Session not connected")
        
        result = await self.session.call_tool(name, arguments)
        return result.content

    async def close(self):
        """Closes the connection."""
        if self.exit_stack:
            await self.exit_stack.aclose()
            print("🔌 MCP Client: Disconnected")

# Singleton instance
meta_ads_client = MetaAdsMCPClient()
