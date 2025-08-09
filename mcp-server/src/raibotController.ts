export type Direction = 'forward' | 'reverse'

export type Controls = {
  right: {
      duty: number,
      count: number,
      direction: Direction
  },
  left: {
      duty: number,
      count: number,
      direction: Direction
  }
}

export type Status = {
  right: {
    running: boolean,
    direction: Direction,
    duty: number,
    travelled: number
  },
  left: {
    running: boolean,
    direction: Direction,
    duty: number,
    travelled: number
  },
  force_stopped: boolean,
  adjustment: number,
  bumps: {
    front: number,
    left: number,
    right: number,
    back: number
  }
}

const SEND = true
const DUMMY_RESPONSE: Status = {
  right: {
    running: false,
    direction: 'forward',
    duty: 65000,
    travelled: 0
  },
  left: {
    running: false,
    direction: 'forward',
    duty: 65000,
    travelled: 0
  },
  force_stopped: false,
  adjustment: 0.9,
  bumps: {
    front: 0,
    left: 0,
    right: 0,
    back: 0
  }
}

export class RaibotController {
  private apiUrl: string

  constructor(apiUrl: string) {
    this.apiUrl = apiUrl
  }

  async postInstruction(message: Controls): Promise<Status> {

    console.log("Instruction: ", message)
    if (!SEND) {
      console.log("DUMMY RESPONSE: ", DUMMY_RESPONSE)
      return {
        right: {
          running: false,
          direction: message.right.direction,
          duty: message.right.duty,
          travelled: message.right.count
        },
        left: {
          running: false,
          direction: message.left.direction,
          duty: message.left.duty,
          travelled: message.left.count
        },
        force_stopped: false,
        adjustment: 0.9,
        bumps: {
          front: 0,
          left: 0,
          right: 0,
          back: 0
        }
      }
    }

    const response = await fetch(this.apiUrl + "/motor", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(message),
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`)
    }

    return response.json()
  }

  async postRestart(): Promise<Status> {

    console.log("Restart")
    
    if (!SEND) {
      console.log("DUMMY RESPONSE: ", DUMMY_RESPONSE)
      return DUMMY_RESPONSE
    }

    const response = await fetch(this.apiUrl + "/restart", {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`)
    }

    return response.json()
  }

  async getStatus(): Promise<Status> {

    console.log("Get Status")

    const response = await fetch(this.apiUrl + "/status", {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`)
    }

    return response.json()
  }
}