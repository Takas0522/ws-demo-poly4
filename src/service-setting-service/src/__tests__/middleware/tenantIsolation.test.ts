import { Request, Response, NextFunction } from 'express';
import { tenantIsolation } from '../../middleware/tenantIsolation';

describe('Tenant Isolation Middleware', () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let nextFunction: NextFunction;

  beforeEach(() => {
    mockRequest = {
      user: {
        sub: 'user-123',
        tenantId: 'tenant-123',
      },
      params: {},
      body: {},
      query: {},
    };
    mockResponse = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
    };
    nextFunction = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should call next if no tenant id is requested', () => {
    tenantIsolation(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(nextFunction).toHaveBeenCalled();
    expect(mockResponse.status).not.toHaveBeenCalled();
  });

  it('should call next if requested tenant matches user tenant', () => {
    mockRequest.body = { tenantId: 'tenant-123' };

    tenantIsolation(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(nextFunction).toHaveBeenCalled();
    expect(mockResponse.status).not.toHaveBeenCalled();
  });

  it('should return 403 if requested tenant does not match user tenant', () => {
    mockRequest.body = { tenantId: 'tenant-456' };

    tenantIsolation(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(mockResponse.status).toHaveBeenCalledWith(403);
    expect(mockResponse.json).toHaveBeenCalledWith({
      error: 'Access denied to different tenant',
    });
    expect(nextFunction).not.toHaveBeenCalled();
  });

  it('should return 401 if user is not authenticated', () => {
    mockRequest.user = undefined;

    tenantIsolation(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(mockResponse.status).toHaveBeenCalledWith(401);
    expect(mockResponse.json).toHaveBeenCalledWith({ error: 'Unauthorized' });
    expect(nextFunction).not.toHaveBeenCalled();
  });

  it('should check tenant id from params', () => {
    mockRequest.params = { tenantId: 'tenant-123' };

    tenantIsolation(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(nextFunction).toHaveBeenCalled();
  });

  it('should check tenant id from query', () => {
    mockRequest.query = { tenantId: 'tenant-123' };

    tenantIsolation(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(nextFunction).toHaveBeenCalled();
  });
});
