// src/utils/logger.ts
import winston from 'winston'
import * as path from 'path'
import * as fs from 'fs'
import { fileURLToPath } from 'url'

// Determine the environment
const isProduction = (process.env.NODE_ENV === 'production')
const logLevel = process.env.LOG_LEVEL || (isProduction ? 'warning' : 'debug')

// --- ESM-compatible __dirname replacement ---
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// Directory for log files
const logDirectory = path.join(__dirname, '../logs') // Adjust path as needed for your project structure

// Ensure the log directory exists
if (!fs.existsSync(logDirectory)) {
    try {
        fs.mkdirSync(logDirectory, { recursive: true })
    } catch (err: any) { // Explicitly type 'err' as 'any' or 'Error'
        // CRITICAL: If the directory cannot be created, logging to file WILL FAIL.
        // Consider exiting the process or logging a severe error to console only.
        process.exit(1) // Force exit if directory creation fails to prevent further errors
    }
}

// Define common formats
const commonFormats = winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss.SSS' }), // ISO 8601 timestamps
    winston.format.errors({ stack: true }), // Include stack trace for errors
    winston.format.metadata({ fillExcept: ['message', 'level', 'timestamp', 'stack'] }), // Add metadata like application, node_version
    winston.format((info) => {
        // Custom formatter to add base properties to metadata
        info.metadata = {
            ...(typeof info.metadata === 'object' && info.metadata !== null ? info.metadata : {}),
            application: 'my-mcp-server',
            node_version: process.version,
        }
        return info
    })(),
)

// Define transports
const transports: winston.transports.FileTransportInstance[] = [
    // Main file transport for all logs (JSON format, info level and above)
    new winston.transports.File({
        filename: path.join(logDirectory, 'app.log'),
        level: 'info', // Logs 'info' and above to the main file
        format: winston.format.combine(
            commonFormats,
            winston.format.json() // JSON format for file logs
        ),
        maxsize: 5242880, // 5MB
        maxFiles: 5,      // Retain 5 files (e.g., app.log, app.log.1, app.log.2...)
        tailable: true    // Always append to the current file
    }),
    // Separate file transport for error logs (JSON format)
    new winston.transports.File({
        filename: path.join(logDirectory, 'error.log'),
        level: 'error', // Only 'error' and 'fatal' logs go to this file
        format: winston.format.combine(
            commonFormats,
            winston.format.json()
        ),
        maxsize: 5242880, // 5MB
        maxFiles: 5,
        tailable: true
    }),
    // Separate file transport for error logs (JSON format)
    new winston.transports.File({
        filename: path.join(logDirectory, 'debug.log'),
        level: 'debug', // Only 'debug' logs go to this file
        format: winston.format.combine(
            commonFormats,
            winston.format.json()
        ),
        maxsize: 5242880, // 5MB
        maxFiles: 5,
        tailable: true
    })
]

// // Add console transport for development
// if (!isProduction) {
//     transports.push(
//         new winston.transports.File({
//             level: logLevel, // Use the determined log level (e.g., 'debug' in dev)
//             format: winston.format.combine(
//                 winston.format.colorize(), // Add colors for console output
//                 winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }), // Shorter timestamp for console
//                 winston.format.printf(info => {
//                     // Custom printf format for pretty console output
//                     const { timestamp, level, message, stack, metadata, ...rest } = info
//                     const metaString = Object.keys(rest).length > 0 ? ` ${JSON.stringify(rest)}` : ''
//                     return `${timestamp} ${level}: ${message}${metaString}${stack ? `\n${stack}` : ''}`
//                 })
//             )
//         }) as winston.transports.FileTransportInstance // Type assertion to satisfy array type
//     )
// }

// Create the Winston logger instance
const logger = winston.createLogger({
    level: logLevel, // Base log level for the logger instance
    transports: transports,
    exitOnError: false // Do not exit on handled exceptions, we handle them explicitly
})

// Optional: Catch uncaught exceptions and unhandled promise rejections
// Winston has built-in handlers for this directly on the logger
logger.exceptions.handle(
    new winston.transports.File({
        filename: path.join(logDirectory, 'exceptions.log'),
        format: winston.format.json(),
        maxsize: 5242880,
        maxFiles: 1
    }),
    new winston.transports.Console({
        format: winston.format.combine(
            winston.format.colorize(),
            winston.format.printf(info => `${info.timestamp} ${info.level}: ${info.message}${info.stack ? `\n${info.stack}` : ''}`)
        )
    })
)

logger.rejections.handle(
    new winston.transports.File({
        filename: path.join(logDirectory, 'rejections.log'),
        format: winston.format.json(),
        maxsize: 5242880,
        maxFiles: 1
    }),
    new winston.transports.Console({
        format: winston.format.combine(
            winston.format.colorize(),
            winston.format.printf(info => `${info.timestamp} ${info.level}: ${info.message}${info.stack ? `\n${info.stack}` : ''}`)
        )
    })
)

// It's still good practice to have process-level handlers for safety,
// though Winston's handlers cover most cases.
process.on('uncaughtException', (err) => {
    // If Winston's exception handler is already active and writing to a file,
    // this might be redundant or could lead to double logging.
    // However, it acts as a safeguard.
    logger.error('CRITICAL: Uncaught exception caught outside Winston handler. Exiting.')
    logger.error(err)
    process.exit(1)
})

process.on('unhandledRejection', (reason, promise) => {
    // Similar to uncaughtException, this is a safeguard.
    logger.error('CRITICAL: Unhandled promise rejection caught outside Winston handler. Exiting.')
    logger.error('Reason:', reason)
    logger.error('Promise:', promise)
    process.exit(1)
})

export default logger