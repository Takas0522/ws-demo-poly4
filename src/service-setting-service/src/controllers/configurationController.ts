import { Request, Response } from 'express';
import { ConfigurationService } from '../services/configurationService';
import {
  CreateConfigurationDto,
  UpdateConfigurationDto,
  ConfigurationQuery,
} from '../types';
import logger from '../utils/logger';

export class ConfigurationController {
  constructor(private configService: ConfigurationService) {}

  create = async (req: Request, res: Response): Promise<void> => {
    const dto: CreateConfigurationDto = req.body;
    const userId = req.user?.sub || 'system';

    const config = await this.configService.create(dto, userId);
    res.status(201).json(config);
    logger.info(`Configuration created: ${config.id}`);
  };

  getById = async (req: Request, res: Response): Promise<void> => {
    const { id } = req.params;
    const tenantId = req.user?.tenantId || '';
    const includeInherited = req.query.includeInherited === 'true';

    const config = await this.configService.getById(id, tenantId, includeInherited);
    res.json(config);
  };

  getByKey = async (req: Request, res: Response): Promise<void> => {
    const { key } = req.params;
    const tenantId = req.user?.tenantId || '';
    const includeInherited = req.query.includeInherited === 'true';

    const config = await this.configService.getByKey(key, tenantId, includeInherited);
    res.json(config);
  };

  list = async (req: Request, res: Response): Promise<void> => {
    const tenantId = req.user?.tenantId || '';
    const query: ConfigurationQuery = {
      tenantId,
      key: req.query.key as string | undefined,
      tags: req.query.tags ? (req.query.tags as string).split(',') : undefined,
      includeInherited: req.query.includeInherited === 'true',
    };

    const configs = await this.configService.list(query);
    res.json(configs);
  };

  update = async (req: Request, res: Response): Promise<void> => {
    const { id } = req.params;
    const tenantId = req.user?.tenantId || '';
    const userId = req.user?.sub || 'system';
    const dto: UpdateConfigurationDto = req.body;

    const config = await this.configService.update(id, tenantId, dto, userId);
    res.json(config);
    logger.info(`Configuration updated: ${id}`);
  };

  delete = async (req: Request, res: Response): Promise<void> => {
    const { id } = req.params;
    const tenantId = req.user?.tenantId || '';

    await this.configService.delete(id, tenantId);
    res.status(204).send();
    logger.info(`Configuration deleted: ${id}`);
  };

  backup = async (req: Request, res: Response): Promise<void> => {
    const tenantId = req.user?.tenantId || '';
    const userId = req.user?.sub || 'system';
    const { description } = req.body;

    const result = await this.configService.backup(tenantId, userId, description);
    res.json(result);
    logger.info(`Backup created for tenant ${tenantId}`);
  };

  restore = async (req: Request, res: Response): Promise<void> => {
    const { backupId } = req.params;
    const tenantId = req.user?.tenantId || '';
    const userId = req.user?.sub || 'system';

    await this.configService.restore(backupId, tenantId, userId);
    res.json({ message: 'Backup restored successfully' });
    logger.info(`Backup restored for tenant ${tenantId}`);
  };
}
