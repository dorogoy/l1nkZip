from mcp.server import Server
from mcp.server.sse import SseServerTransport

from l1nkzip.logging import get_logger


logger = get_logger(__name__)

mcp_server = Server("l1nkzip-mcp-server")

sse_transport = SseServerTransport("/mcp/messages")
