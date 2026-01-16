import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { Request, Response, NextFunction } from 'express';
import axios from 'axios';
import { errorIngestionMiddleware, ErrorIngestionOptions } from '../src/index';

vi.mock('axios');
const mockedAxios = vi.mocked(axios);

describe('errorIngestionMiddleware', () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let mockNext: NextFunction;
  let options: ErrorIngestionOptions;

  beforeEach(() => {
    vi.clearAllMocks();

    options = {
      apiUrl: 'https://api.example.com',
      projectKey: 'test-project',
      timeout: 5000,
    };

    mockRequest = {
      method: 'GET',
      path: '/users/123',
      originalUrl: '/users/123',
      headers: {},
    };

    mockResponse = {
      statusCode: 500,
    };

    mockNext = vi.fn();
    mockedAxios.post.mockResolvedValue({ status: 200 });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should capture error and send to backend', async () => {
    const error = new Error('Test error');
    error.stack = 'Error: Test error\n  at test.js:1:1';

    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockedAxios.post).toHaveBeenCalledTimes(1);
    expect(mockedAxios.post).toHaveBeenCalledWith(
      'https://api.example.com/api/v1/events',
      expect.objectContaining({
        project_key: 'test-project',
        message: 'Test error',
        method: 'GET',
        status_code: 500,
      }),
      expect.objectContaining({
        timeout: 5000,
        headers: {
          'Content-Type': 'application/json',
        },
      })
    );

    expect(mockNext).toHaveBeenCalledWith(error);
  });

  it('should sanitize path with numeric IDs', async () => {
    mockRequest.path = '/users/123/orders/456';
    mockRequest.originalUrl = '/users/123/orders/456';

    const error = new Error('Test error');
    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        path: '/users/:id/orders/:id',
      }),
      expect.any(Object)
    );
  });

  it('should sanitize path with UUIDs', async () => {
    const uuid = '550e8400-e29b-41d4-a716-446655440000';
    mockRequest.path = `/users/${uuid}`;
    mockRequest.originalUrl = `/users/${uuid}`;

    const error = new Error('Test error');
    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        path: '/users/:id',
      }),
      expect.any(Object)
    );
  });

  it('should remove query string from path', async () => {
    mockRequest.originalUrl = '/users/123?page=1&limit=10';

    const error = new Error('Test error');
    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        path: '/users/:id',
      }),
      expect.any(Object)
    );
  });

  it('should use error statusCode if available', async () => {
    const error = new Error('Test error') as any;
    error.statusCode = 404;

    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        status_code: 404,
      }),
      expect.any(Object)
    );
  });

  it('should use default statusCode 500 if not provided', async () => {
    mockResponse.statusCode = 200;

    const error = new Error('Test error');
    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        status_code: 500,
      }),
      expect.any(Object)
    );
  });

  it('should include stack trace in error event', async () => {
    const error = new Error('Test error');
    error.stack = 'Error: Test error\n  at test.js:1:1\n  at main.js:5:10';

    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        stack: 'Error: Test error\n  at test.js:1:1\n  at main.js:5:10',
      }),
      expect.any(Object)
    );
  });

  it('should not send duplicate errors', async () => {
    const INGESTED = Symbol.for('error_ingested');
    const error = new Error('Test error') as any;
    error[INGESTED] = true;

    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockedAxios.post).not.toHaveBeenCalled();
    expect(mockNext).toHaveBeenCalledWith(error);
  });

  it('should handle axios errors gracefully', async () => {
    mockedAxios.post.mockRejectedValue(new Error('Network error'));

    const error = new Error('Test error');
    const middleware = errorIngestionMiddleware(options);
    
    expect(() => {
      middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);
    }).not.toThrow();

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockNext).toHaveBeenCalledWith(error);
  });

  it('should use custom timeout if provided', async () => {
    options.timeout = 10000;

    const error = new Error('Test error');
    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(Object),
      expect.objectContaining({
        timeout: 10000,
      })
    );
  });

  it('should include ISO timestamp', async () => {
    const error = new Error('Test error');
    const middleware = errorIngestionMiddleware(options);
    middleware(error as Error, mockRequest as Request, mockResponse as Response, mockNext);

    await new Promise(resolve => setTimeout(resolve, 100));

    const callArgs = mockedAxios.post.mock.calls[0];
    const eventData = callArgs[1] as any;
    
    expect(eventData.timestamp).toBeDefined();
    expect(typeof eventData.timestamp).toBe('string');
    expect(() => new Date(eventData.timestamp)).not.toThrow();
  });
});
