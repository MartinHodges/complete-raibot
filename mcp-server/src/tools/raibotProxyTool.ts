import dotenv from 'dotenv'
dotenv.config()

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js"
import logger from "../logger.js"
import { z } from "zod"
import { RaibotController, Status } from "../raibotController.js"

// Define the expected input structure for this tool using Zod
const instructionInputShape = {
    instruction: z.enum(['status', 'left', 'right', 'forward', 'reverse']).describe("The instructions the robot is to carry out"),
    speed: z.number().int().min(0).max(100).optional().describe("The duty cycle for the motors, between 0 and 100"),
    distance: z.number().int().min(1).optional().describe("The distance the robot should move in the specified direction"),
    rotation: z.number().int().min(1).max(360).optional().describe("The rotation the robot should make"),
}

const instructionInputShapeSchema = z.object(instructionInputShape)  
type InstructionInput = z.infer<typeof instructionInputShapeSchema>
logger.debug(">>> URL: " + process.env.ROBOT_URL)
const raibotController = new RaibotController(process.env.ROBOT_URL || "http://localhost:8080")

export default function registerRaibotProxyTool(server: McpServer) {
  logger.debug("Registering Raibot proxy tool...")
  server.tool(
    "raibot_proxy",
    "A tool that drives a real Raibot.",
    instructionInputShape,
    async (args: InstructionInput) => {
      logger.debug("Raibot triggered...with instruction: " + JSON.stringify(args))

      let body: any
      let response: Status

      // There are approximately 6.39 clicks per degree of rotation
      const degrees = Math.trunc((args.rotation || 0) * 1150 / 180.0)
      // There are approximately 69 clicks per cm of travel
      const distance = Math.trunc((args.distance || 0) * 2000 / 29.0)
      // The PWM has 16 bit resolution
      const speed = Math.trunc((args.speed || 0) * 65535 / 100.0)

      try {
        switch (args.instruction) {
          case 'status':
            logger.debug("Raibot status")
            response = await raibotController.getStatus()
            break
          case 'left':
            logger.debug("Raibot moving left")
            body = {
              right: { duty: speed, count: degrees, direction: 'forward' },
              left: { duty: speed, count: degrees, direction: 'reverse' }
            }
            response = await raibotController.postInstruction(body)
            break
          case 'right':
            logger.debug("Raibot moving right")
            body = {
              right: { duty: speed, count: degrees, direction: 'reverse' },
              left: { duty: speed, count: degrees, direction: 'forward' }
            }
            response = await raibotController.postInstruction(body)
            break
          case 'forward':
            logger.debug("Raibot moving forward")
            body = {
              right: { duty: speed, count: distance, direction: 'forward' },
              left: { duty: speed, count: distance, direction: 'forward' }
            }
            response = await raibotController.postInstruction(body)
            break
          case 'reverse':
            logger.debug("Raibot moving reverse")
            body = {
              right: { duty: speed, count: distance, direction: 'reverse' },
              left: { duty: speed, count: distance, direction: 'reverse' }
            }
            response = await raibotController.postInstruction(body)
            break
          default:
            logger.error("Unknown instruction:", args.instruction)
            throw new Error(`Unknown instruction: ${args.instruction}`)
        }
        logger.debug("Raibot body: " + JSON.stringify(body))
        logger.debug("Raibot response: " + JSON.stringify(response))
      } catch (error) {
        logger.error("Error moving Raibot:", error)
        throw new Error(`Error moving Raibot: ${error instanceof Error ? error.message : String(error)}`)
      }

      response.left.duty = response.left.duty * 100 / 65535
      response.right.duty = response.right.duty * 100 / 65535

      response.left.travelled = response.left.travelled * 29.0 / 2000
      response.right.travelled = response.right.travelled * 29.0 / 2000

      return {
        content: [{
            type: "text",
            text: `Raibot status: ${JSON.stringify(response)}`
        }]
      }
    }
  )
}