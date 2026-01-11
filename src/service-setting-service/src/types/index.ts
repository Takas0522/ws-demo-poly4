export interface Configuration {
  id: string;
  tenantId: string;
  key: string;
  value: unknown;
  description?: string;
  schema?: string;
  isEncrypted: boolean;
  version: number;
  parentConfigId?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
  updatedBy: string;
}

export interface ConfigurationVersion {
  id: string;
  configId: string;
  tenantId: string;
  version: number;
  value: unknown;
  changedBy: string;
  changedAt: Date;
  changeReason?: string;
}

export interface ConfigurationBackup {
  id: string;
  tenantId: string;
  backupDate: Date;
  configurations: Configuration[];
  createdBy: string;
  description?: string;
}

export interface CreateConfigurationDto {
  tenantId: string;
  key: string;
  value: unknown;
  description?: string;
  schema?: string;
  isEncrypted?: boolean;
  parentConfigId?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface UpdateConfigurationDto {
  value?: unknown;
  description?: string;
  schema?: string;
  isEncrypted?: boolean;
  tags?: string[];
  metadata?: Record<string, unknown>;
  changeReason?: string;
}

export interface ConfigurationQuery {
  tenantId: string;
  key?: string;
  tags?: string[];
  includeInherited?: boolean;
}

export interface JwtPayload {
  sub: string;
  tenantId: string;
  email?: string;
  roles?: string[];
  iat?: number;
  exp?: number;
  iss?: string;
}
