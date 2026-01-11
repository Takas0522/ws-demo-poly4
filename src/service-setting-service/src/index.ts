import { App } from './app';
import logger from './utils/logger';

const app = new App();

// Handle graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM signal received');
  await app.shutdown();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT signal received');
  await app.shutdown();
  process.exit(0);
});

// Handle unhandled rejections
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Start the application
app.start().catch((error) => {
  logger.error('Failed to start application:', error);
  process.exit(1);
});
