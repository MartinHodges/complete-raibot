import { RemoteLogger } from './RemoteLogger';

const port = process.env.LOGGER_PORT ? parseInt(process.env.LOGGER_PORT) : 3002;
const logger = new RemoteLogger(port);
logger.start();
