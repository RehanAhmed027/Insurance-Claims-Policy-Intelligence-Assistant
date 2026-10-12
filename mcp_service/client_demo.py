import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from config import BASE_DIR


async def main():
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_service.server"],
        cwd=str(BASE_DIR),
    )

    # Launch the local server and connect over standard input/output.
    async with stdio_client(server_parameters) as (
        read_stream,
        write_stream,
    ):
        async with ClientSession(
            read_stream,
            write_stream,
        ) as session:
            await session.initialize()

            available = await session.list_tools()

            print("Available MCP tools:")
            for tool in available.tools:
                print(f"- {tool.name}")

            result = await session.call_tool(
                "lookup_claim",
                arguments={"claim_id": "CLM300500"},
            )

            print("\nClaim lookup result:")
            print(result.model_dump_json(indent=2))

            if result.isError:
                raise RuntimeError("The MCP tool call failed.")


if __name__ == "__main__":
    asyncio.run(main())