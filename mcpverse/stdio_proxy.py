from typing import Any, Iterable
from pydantic.networks import AnyUrl
from mcp.server.lowlevel.helper_types import ReadResourceContents
from mcp.server.stdio import stdio_server
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp import types, server
import base64

async def make_local_server(remote_session: ClientSession) -> server.Server:
    """Create a server instance from a remote app."""
    remote_initialization = await remote_session.initialize()
    capabilities = remote_initialization.capabilities

    local_server: server.Server = server.Server(name=remote_initialization.serverInfo.name)

    if capabilities.prompts:
        @local_server.list_prompts()
        async def _list_prompts() -> list[types.Prompt]:
            result = await remote_session.list_prompts()
            return result.prompts

        @local_server.get_prompt()
        async def _get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult:
            result = await remote_session.get_prompt(name, arguments)
            return result

    if capabilities.resources:
        @local_server.list_resources()
        async def _list_resources() -> list[types.Resource]:
            result = await remote_session.list_resources()
            return result.resources

        @local_server.list_resource_templates()
        async def _list_resource_templates() -> list[types.ResourceTemplate]:
            result = await remote_session.list_resource_templates()
            return result.resourceTemplates

        @local_server.read_resource()
        async def _read_resource(uri: AnyUrl) -> Iterable[ReadResourceContents]:
            result = await remote_session.read_resource(uri)
            contents = []
            for content in result.contents:
                if isinstance(content, types.TextResourceContents):
                    contents.append(ReadResourceContents(content=content.text, mime_type=content.mimeType))
                elif isinstance(content, types.BlobResourceContents):
                    contents.append(ReadResourceContents(
                        content=base64.urlsafe_b64decode(content.blob), 
                        mime_type=content.mimeType
                    ))
            return contents

        @local_server.subscribe_resource()
        async def _subscribe_resource(uri: AnyUrl) -> None:
            await remote_session.subscribe_resource(uri)

        @local_server.unsubscribe_resource()
        async def _unsubscribe_resource(uri: AnyUrl) -> None:
            await remote_session.unsubscribe_resource(uri)

    if capabilities.logging:
        @local_server.set_logging_level()
        async def _set_logging_level(level: types.LoggingLevel) -> None:
            await remote_session.set_logging_level(level)

    if capabilities.tools:
        @local_server.list_tools()
        async def _list_tools() -> list[types.Tool]:
            tools = await remote_session.list_tools()
            return tools.tools

        @local_server.call_tool()
        async def _call_tool(name: str, arguments: dict[str, Any]) -> Iterable[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            result = await remote_session.call_tool(name, arguments)
            return result.content

    @local_server.progress_notification()
    async def _send_progress_notification(progress_token: str | int, progress: float, total: float | None) -> None:
        await remote_session.send_progress_notification(progress_token, progress, total)

    @local_server.completion()
    async def _complete(
        ref: types.PromptReference | types.ResourceReference, 
        argument: types.CompletionArgument
    ) -> types.Completion | None:
        result = await remote_session.complete(ref, argument.model_dump())
        return result.completion

    return local_server

async def run_proxy_stdio_server(url: str, access_token: str) -> None:
    async with sse_client(url, headers={"Authorization": f"Bearer {access_token}"}) as remote_streams:
        async with ClientSession(*remote_streams) as remote_session:
            local_server = await make_local_server(remote_session)
            async with stdio_server() as (local_read_stream, local_write_stream):
                await local_server.run(local_read_stream, local_write_stream, local_server.create_initialization_options())
