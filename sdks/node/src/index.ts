import { Request, Response, NextFunction, ErrorRequestHandler } from 'express';
import axios, { AxiosError } from 'axios';

const INGESTED = Symbol.for('error_ingested');

function sanitizePath(path: string): string {
  let sanitized = path;
  
  sanitized = sanitized.replace(/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, '/:id');
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
    if ((err as any)[INGESTED]) {
      return next(err);
    }

    (err as any)[INGESTED] = true;

    let statusCode = (err as any).statusCode || (err as any).status;
    if (!statusCode) {
      statusCode = (res.statusCode && res.statusCode !== 200) ? res.statusCode : 500;
    }
    
    const pathToSanitize = req.originalUrl 
      ? req.originalUrl.split('?')[0]
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

    sendErrorEvent(apiUrl, projectKey, errorEvent, timeout).catch(() => {});

    next(err);
  };
}

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
    if (process.env.NODE_ENV === 'development') {
      const axiosError = error as AxiosError;
      console.warn(
        `[Error Ingestion SDK] Failed to send error event: ${axiosError.message}`
      );
    }
    return;
  }
}

