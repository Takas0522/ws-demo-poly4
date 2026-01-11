import { Router } from 'express';
import { ConfigurationController } from '../controllers/configurationController';
import { authenticate } from '../middleware/auth';
import { tenantIsolation } from '../middleware/tenantIsolation';
import { validate } from '../middleware/validation';
import {
  createConfigurationSchema,
  updateConfigurationSchema,
  backupDescriptionSchema,
} from '../validators';

export function createConfigurationRoutes(
  controller: ConfigurationController
): Router {
  const router = Router();

  // All routes require authentication and tenant isolation
  router.use(authenticate);
  router.use(tenantIsolation);

  // CRUD operations
  router.post(
    '/',
    validate(createConfigurationSchema),
    controller.create
  );

  router.get('/', controller.list);

  router.get('/key/:key', controller.getByKey);

  router.get('/:id', controller.getById);

  router.put(
    '/:id',
    validate(updateConfigurationSchema),
    controller.update
  );

  router.delete('/:id', controller.delete);

  // Backup and restore operations
  router.post(
    '/backup',
    validate(backupDescriptionSchema),
    controller.backup
  );

  router.post('/restore/:backupId', controller.restore);

  return router;
}
