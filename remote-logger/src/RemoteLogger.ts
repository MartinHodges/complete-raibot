import express from 'express';

export class RemoteLogger {
  private app: express.Application;
  private port: number;

  constructor(port: number = 3002) {
    this.port = port;
    this.app = express();
    this.app.use(express.json());
    this.app.use(express.text());
    // this.app.use(express.urlencoded({ extended: true }));
    // this.app.use(express.raw());
    this.setupRoutes();
  }

  private setupRoutes(): void {
    this.app.post('/log', (req, res) => {
      let logLine: string;

      if (req.headers['content-type'] === 'application/json') {
        // JSON body
        try {
          const jsonBody = req.body;
          logLine = jsonBody.message || JSON.stringify(jsonBody);
        } catch (error) {
          logLine = `${error} ${req}`;
        }
      } else if (req.headers['content-type'] === 'text/plain') {
        // Text body
        logLine = req.body;
      } else {
        logLine = String(req.body || '');
      }
      
      console.log(logLine);
      res.status(200).send('OK');
    });
  }

  start(): void {
    this.app.listen(this.port, () => {
      console.log(`RemoteLogger listening on port ${this.port}`);
    });
  }
}
