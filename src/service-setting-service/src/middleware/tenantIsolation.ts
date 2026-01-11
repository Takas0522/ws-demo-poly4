import { Request, Response, NextFunction } from 'express';
import logger from '../utils/logger';

export const tenantIsolation = (
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  try {
    const user = req.user;
    
    if (!user) {
      res.status(401).json({ error: 'Unauthorized' });
      return;
    }

    const tenantIdFromBody = req.body?.tenantId;
    const tenantIdFromParams = req.params?.tenantId;
    const tenantIdFromQuery = req.query?.tenantId as string;

    const requestedTenantId = tenantIdFromParams || tenantIdFromBody || tenantIdFromQuery;

    if (requestedTenantId && requestedTenantId !== user.tenantId) {
      logger.warn(
        `Tenant isolation violation: User ${user.sub} attempted to access tenant ${requestedTenantId}`
      );
      res.status(403).json({ error: 'Access denied to different tenant' });
      return;
    }

    next();
  } catch (error) {
    logger.error('Tenant isolation error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
};
