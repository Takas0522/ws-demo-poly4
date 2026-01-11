import express, { Express } from 'express';
import cors from 'cors';
import 'express-async-errors';
import { config } from './config';
import routes from './routes';
import { errorHandler } from './middleware/errorHandler';
import { cosmosDBClient } from './repositories/cosmosClient';
import { cacheService } from './services/cacheService';
import logger from './utils/logger';

export class App {
  public app: Express;

  constructor() {
    this.app = express();
    this.setupMiddleware();
    this.setupRoutes();
    this.setupErrorHandling();
  }

  private setupMiddleware(): void {
    this.app.use(cors());
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // Request logging
    this.app.use((req, _res, next) => {
      logger.info(`${req.method} ${req.path}`);
      next();
    });
  }

  private setupRoutes(): void {
    this.app.use('/api', routes);
  }

  private setupErrorHandling(): void {
    this.app.use(errorHandler);
  }

  async initialize(): Promise<void> {
    try {
      // Initialize CosmosDB
      await cosmosDBClient.initialize();
      logger.info('CosmosDB initialized');

      // Initialize Cache
      await cacheService.connect();
      logger.info('Cache service connected');
    } catch (error) {
      logger.error('Failed to initialize application:', error);
      throw error;
    }
  }

  async start(): Promise<void> {
    await this.initialize();

    this.app.listen(config.server.port, () => {
      logger.info(
        `Service Settings Service is running on port ${config.server.port}`
      );
      logger.info(`Environment: ${config.server.nodeEnv}`);
    });
  }

  async shutdown(): Promise<void> {
    logger.info('Shutting down application...');
    await cacheService.disconnect();
    logger.info('Application shutdown complete');
  }
}
