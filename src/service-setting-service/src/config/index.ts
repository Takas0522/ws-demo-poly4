import dotenv from 'dotenv';

dotenv.config();

export const config = {
  server: {
    port: parseInt(process.env.PORT || '3000', 10),
    nodeEnv: process.env.NODE_ENV || 'development',
  },
  cosmos: {
    endpoint: process.env.COSMOS_ENDPOINT || '',
    key: process.env.COSMOS_KEY || '',
    database: process.env.COSMOS_DATABASE || 'settingsdb',
    container: process.env.COSMOS_CONTAINER || 'configurations',
  },
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
    password: process.env.REDIS_PASSWORD || '',
  },
  cache: {
    ttl: parseInt(process.env.CACHE_TTL || '3600', 10),
  },
  jwt: {
    secret: process.env.JWT_SECRET || 'your-jwt-secret',
    issuer: process.env.JWT_ISSUER || 'auth-service',
  },
  logging: {
    level: process.env.LOG_LEVEL || 'info',
  },
};
