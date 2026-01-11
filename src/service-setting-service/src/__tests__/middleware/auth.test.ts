import { Request, Response, NextFunction } from 'express';
import { authenticate } from '../../middleware/auth';
import jwt from 'jsonwebtoken';
import { config } from '../../config';

jest.mock('jsonwebtoken');

describe('Auth Middleware', () => {
  let mockRequest: Partial<Request>;
  let mockResponse: Partial<Response>;
  let nextFunction: NextFunction;

  beforeEach(() => {
    mockRequest = {
      headers: {},
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

  it('should return 401 if no authorization header is provided', () => {
    authenticate(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(mockResponse.status).toHaveBeenCalledWith(401);
    expect(mockResponse.json).toHaveBeenCalledWith({ error: 'No token provided' });
    expect(nextFunction).not.toHaveBeenCalled();
  });

  it('should return 401 if authorization header does not start with Bearer', () => {
    mockRequest.headers = {
      authorization: 'Basic token123',
    };

    authenticate(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(mockResponse.status).toHaveBeenCalledWith(401);
    expect(mockResponse.json).toHaveBeenCalledWith({ error: 'No token provided' });
    expect(nextFunction).not.toHaveBeenCalled();
  });

  it('should call next if token is valid', () => {
    const mockPayload = {
      sub: 'user-123',
      tenantId: 'tenant-123',
      email: 'user@example.com',
    };

    mockRequest.headers = {
      authorization: 'Bearer valid-token',
    };

    (jwt.verify as jest.Mock).mockReturnValue(mockPayload);

    authenticate(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(jwt.verify).toHaveBeenCalledWith('valid-token', config.jwt.secret, {
      issuer: config.jwt.issuer,
    });
    expect(mockRequest.user).toEqual(mockPayload);
    expect(nextFunction).toHaveBeenCalled();
  });

  it('should return 401 if token is invalid', () => {
    mockRequest.headers = {
      authorization: 'Bearer invalid-token',
    };

    (jwt.verify as jest.Mock).mockImplementation(() => {
      throw new Error('Invalid token');
    });

    authenticate(mockRequest as Request, mockResponse as Response, nextFunction);

    expect(mockResponse.status).toHaveBeenCalledWith(401);
    expect(mockResponse.json).toHaveBeenCalledWith({ error: 'Invalid token' });
    expect(nextFunction).not.toHaveBeenCalled();
  });
});
