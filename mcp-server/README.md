# raibot-mcp-server
This project builds an MCP server that includes tools for controlling a Raibot (an AI controlled robot)

There is a full description in my [Medium article](https://medium.com/@martin.hodges/learning-about-agentic-solutions-using-llms-agents-mcp-servers-and-a-raibot-to-add-to-the-fun-8942edccac07). Note that this version is a modified version described in the article. The article contains links to the original code.

# MCP Server Capabilities
This MCP server provides a single tool:

* `proxy_raibot` - An interface to a physical robot

# Configuration
The application requires a `.env` file at the same level as this `README.md` file.

This should define the following:
* `HTTP_HOST` - domain for this server (not used)
* `HTTP_PORT` - port for this server (default `3001`)
* `NODE_ENV` - environment (default not `production`)
* `LOG_LEVEL` - logging level (default `debug`)
* `ROBOT_URL` - URL for robot (default `http://localhost:8080`)

# Building and running
To build this project it is recommended to use node v22.

It is a standard node / Typescript project, first install the dependencies with:
```
npm install
```

You can build and run the project with:
```
npm run build
node build/index.js
```

However, for development it is better to use:
```
npm run dev
```
This will run the server and monitor the project folder. Any change will trigger a new build and a restart of the server.

# Testing

To test the server, you can run an MCP inspector. Once you run your server, you can then test it with:
```
DANGEROUSLY_OMIT_AUTH=true npx @modelcontextprotocol/inspector
```
This will open a web application on <http://localhost:6274> that allows you to connect to the server using Streamable HTTP at http://localhost:3001/mcp (not the `/sse` default).

When the server restarts due to a change, it is best to reload the web page and reconnect.

# Logs
To overcome the logging problem, I have included a `winston` logging implementation that logs to files under the `./logs` folder. This logs in JSON.
