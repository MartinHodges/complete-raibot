import logging
import os
from flags import DEBUG
from dotenv import load_dotenv
from pydantic import BaseModel
from strands import Agent
from strands.models.openai import OpenAIModel
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient

load_dotenv()

# Quieten agent actions by setting higher log levels
logging.getLogger("strands").setLevel(logging.CRITICAL)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Sets the logging format and streams logs to stderr with minimal output
logging.basicConfig(
    level=logging.CRITICAL if not DEBUG else logging.DEBUG,
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

class RaibotResponse(BaseModel):
  last_location: str
  target_location: str
  status: str
  map:list[list[str]]

model = OpenAIModel(
    model_id="gpt-4o",
    params={
        "max_tokens": 1000,
        "temperature": 0.7,
    }
)


prompt = """
    You are controlling a robot called Raibot. You will assume the identity of Raibot.
    You can control its left and right motors independently to move it using the raibot_proxy tool.
    When you control the motors you can independently set the speed (0 to 100 percent), 
    the distance (in cm) and the direction (forward, reverse) for each motor.
    The default speed should be set to 100.
    After each movement, the Raibot will report its status, including how far it travelled. 
    It may have hit an obstacle and may not have travelled as far as you wanted it to.
    You can use directional instruction of 'right' and 'left' to turn the robot in place, providing the rotation amount in degrees and the speed.
    Given a command from your human operator, you will get the status of the Raibot using the raibot_proxy tool and then
    provide instructions, distance and speed for each motor.
    You will only issue one instruction at a time and wait for the response, even if this is a turn.
    You will always get the status of the Raibot before each operation and use the adjustment reported in the operation.
    This status includes bump sensors for front, back, left and right.
    You will not go forwards if the front bump sensor is pressed.
    You will not go backwards if the back bump sensor is pressed.
    You can also get this status by issuing a 'status' instruction to the raibot_proxy tool and you can do this before each operation.
"""

streamable_http_mcp_client = MCPClient(lambda: streamablehttp_client(os.environ.get('MCP_HOST_URL')))

# Create an agent with MCP tools
with streamable_http_mcp_client:
    # Get the tools from the MCP server
    tools = streamable_http_mcp_client.list_tools_sync()
    
    agent = Agent(model=model, tools=tools, system_prompt=prompt)

    continue_trip = True

    while continue_trip:
        command = input("\n\nEnter command for Raibot: ")

        if not command:
            print("No command entered.")
            continue
        if command == "exit" or command == 'q':
            print("Exiting...")
            break
        response = agent(command)
        # if DEBUG or True: print("\n\nResponse:", response)

        # result = agent.structured_output(RaibotResponse, "Extract status of last robot movement")
        # if DEBUG or True: print("\n\nResult:", result)

        # continue_trip = result.last_location != result.target_location