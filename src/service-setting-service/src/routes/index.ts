import { Router } from 'express';
import { createConfigurationRoutes } from './configurationRoutes';
import { ConfigurationController } from '../controllers/configurationController';
import { ConfigurationService } from '../services/configurationService';
import { ConfigurationRepository } from '../repositories/configurationRepository';
import { cacheService } from '../services/cacheService';

const router = Router();

// Initialize dependencies
const repository = new ConfigurationRepository();
const configService = new ConfigurationService(repository, cacheService);
const configController = new ConfigurationController(configService);

// Mount routes
router.use('/configurations', createConfigurationRoutes(configController));

// Health check endpoint (no auth required)
router.get('/health', (_req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'service-setting-service',
  });
});

export default router;
