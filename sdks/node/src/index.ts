import { Request, Response, NextFunction, ErrorRequestHandler } from 'express';
import axios, { AxiosError } from 'axios';

const INGESTED = Symbol.for('error_ingested');

/**
 * Sanitizes path by replacing IDs with placeholders to reduce cardinality and avoid leaking IDs
 * Examples:
 *   /users/123 -> /users/:id
 *   /users/123/orders/456 -> /users/:id/orders/:id
 *   /users/550e8400-e29b-41d4-a716-446655440000 -> /users/:id
 */
function sanitizePath(path: string): string {
  let sanitized = path;
  
  // Replace UUIDs FIRST (e.g., /550e8400-e29b-41d4-a716-446655440000)
  // Must check UUIDs before numeric IDs since UUIDs can start with digits
  sanitized = sanitized.replace(/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, '/:id');
  
  // Replace numeric IDs (e.g., /123, /456)
  sanitized = sanitized.replace(/\/\d+/g, '/:id');
  
  return sanitized;
}

export interface ErrorIngestionOptions {
  apiUrl: string;
  projectKey: string;
  timeout?: number;
}

export interface ErrorEvent {
  message: string;
  stack?: string;
  method: string;
  path: string;
  status_code?: number;
  timestamp: string;
}

/**
 * Express error-handling middleware that captures errors and sends them to the backend
 * Non-blocking: errors in sending are silently caught to not interrupt request handling
 */
export function errorIngestionMiddleware(
  options: ErrorIngestionOptions
): ErrorRequestHandler {
  const { apiUrl, projectKey, timeout = 5000 } = options;

  return (
    err: Error,
    req: Request,
    res: Response,
    next: NextFunction
  ) => {
    // Skip if error was already ingested by another middleware layer
    if ((err as any)[INGESTED]) {
      return next(err);
    }

    // Mark error as ingested to prevent duplicate ingestion
    (err as any)[INGESTED] = true;

    // Capture error data
    // Get status code from error object or default to 500
    // Note: res.statusCode defaults to 200, so if it's 200 we ignore it (errors shouldn't be 200)
    let statusCode = (err as any).statusCode || (err as any).status;
    if (!statusCode) {
      // Only use res.statusCode if it's been set to an error code (not default 200)
      statusCode = (res.statusCode && res.statusCode !== 200) ? res.statusCode : 500;
    }
    
    // Sanitize path to avoid leaking IDs and reduce cardinality
    // Use originalUrl to preserve original path (before middleware modifications)
    // Remove query string to avoid cardinality from query params
    const pathToSanitize = req.originalUrl 
      ? req.originalUrl.split('?')[0]  // Remove query string
      : req.path;
    const sanitizedPath = sanitizePath(pathToSanitize);
    
    const errorEvent: ErrorEvent = {
      message: err.message || 'Unknown error',
      stack: err.stack,
      method: req.method,
      path: sanitizedPath,
      status_code: statusCode,
      timestamp: new Date().toISOString(),
    };

    // Send to backend asynchronously (non-blocking)
    sendErrorEvent(apiUrl, projectKey, errorEvent, timeout).catch(() => {
      // Silently fail - don't block request handling
    });

    // Continue with default error handling
    next(err);
  };
}

/**
 * Sends error event to backend endpoint
 * Errors are handled internally and not propagated
 */
async function sendErrorEvent(
  apiUrl: string,
  projectKey: string,
  event: ErrorEvent,
  timeout: number
): Promise<void> {
  try {
    await axios.post(
      `${apiUrl}/api/v1/events`,
      {
        project_key: projectKey,
        ...event,
      },
      {
        timeout,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  } catch (error) {
    // Log to console in development, but don't throw
    if (process.env.NODE_ENV === 'development') {
      const axiosError = error as AxiosError;
      console.warn(
        `[Error Ingestion SDK] Failed to send error event: ${axiosError.message}`
      );
    }
    // Swallow error - don't propagate
    return;
  }
}

