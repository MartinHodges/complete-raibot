import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import registerProxyRaibotTool from "./raibotProxyTool.js"

export function registerTools(server: McpServer): void {
    registerProxyRaibotTool(server)
}