import Joi from 'joi';

export const createConfigurationSchema = Joi.object({
  tenantId: Joi.string().required(),
  key: Joi.string().required().min(1).max(255),
  value: Joi.any().required(),
  description: Joi.string().optional().max(1000),
  schema: Joi.string().optional(),
  isEncrypted: Joi.boolean().optional().default(false),
  parentConfigId: Joi.string().optional(),
  tags: Joi.array().items(Joi.string()).optional(),
  metadata: Joi.object().optional(),
});

export const updateConfigurationSchema = Joi.object({
  value: Joi.any().optional(),
  description: Joi.string().optional().max(1000),
  schema: Joi.string().optional(),
  isEncrypted: Joi.boolean().optional(),
  tags: Joi.array().items(Joi.string()).optional(),
  metadata: Joi.object().optional(),
  changeReason: Joi.string().optional().max(500),
}).min(1);

export const configurationQuerySchema = Joi.object({
  tenantId: Joi.string().required(),
  key: Joi.string().optional(),
  tags: Joi.array().items(Joi.string()).optional(),
  includeInherited: Joi.boolean().optional().default(false),
});

export const backupDescriptionSchema = Joi.object({
  description: Joi.string().optional().max(1000),
});
