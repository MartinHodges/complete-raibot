import dotenv from 'dotenv';
dotenv.config();

import express from "express"
import { randomUUID } from "node:crypto"
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js"
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js"
import { registerTools } from "./tools/toolRegistration.js"

const app = express()
app.use(express.json())

// Define host and port, preferably from environment variables
const HTTP_HOST = process.env.MCP_SERVER_HOST || 'localhost'
const HTTP_PORT = parseInt(process.env.MCP_SERVER_PORT || '3001', 10)

// Map to store transports by session ID
const transports: { [sessionId: string]: StreamableHTTPServerTransport } = {}

const server = new McpServer({
    name: "raibot", // Unique name for this server
    version: "0.0.1", // Server version
    // Declare the types of capabilities the server will offer
    capabilities: {
        prompts: {},  // Will be populated by registerPrompts
        resources: {},// Will be populated by registerResources
        tools: {},    // Will be populated by registerTools
    }
})

// Load and register all tools
registerTools(server)

console.log("Configuring end points for MCP server at " + HTTP_PORT)

// Handle POST requests for client-to-server communication
app.post('/mcp', async (req: any, res: any) => {
  // Check for existing session ID
  const sessionId = req.headers['mcp-session-id'] as string | undefined
  let transport: StreamableHTTPServerTransport

  if (sessionId && transports[sessionId]) {
    // Reuse existing transport
    transport = transports[sessionId]
  } else if (!sessionId && isInitializeRequest(req.body)) {
    // New initialization request
    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (sessionId) => {
        // Store the transport by session ID
        transports[sessionId] = transport
      },
      // DNS rebinding protection is disabled by default for backwards compatibility. If you are running this server
      // locally, make sure to set:
      // enableDnsRebindingProtection: true,
      // allowedHosts: ['127.0.0.1'],
    })

    // Clean up transport when closed
    transport.onclose = () => {
      if (transport.sessionId) {
        delete transports[transport.sessionId]
      }
    }

    console.log('Agent connecting to MCP server...')

    // Connect to the MCP server
    await server.connect(transport)
  } else {
    // Invalid request
    res.status(400).json({
      jsonrpc: '2.0',
      error: {
        code: -32000,
        message: 'Bad Request: No valid session ID provided',
      },
      id: null,
    })
    return
  }

  // Handle the request
  await transport.handleRequest(req, res, req.body)
})

// Reusable handler for GET and DELETE requests
const handleSessionRequest = async (req: express.Request, res: express.Response) => {
  const sessionId = req.headers['mcp-session-id'] as string | undefined
  if (!sessionId || !transports[sessionId]) {
    res.status(400).send('Invalid or missing session ID')
    return
  }
  
  const transport = transports[sessionId]
  await transport.handleRequest(req, res)
}

// Handle GET requests
app.get('/mcp', handleSessionRequest)

// Handle DELETE requests for session termination
app.delete('/mcp', handleSessionRequest)

app.listen(HTTP_PORT)

console.log("MCP server configured")
