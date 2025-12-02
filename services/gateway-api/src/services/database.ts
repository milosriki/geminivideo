/**
 * Database Service - Production-grade Prisma client with connection pooling
 * Provides CRUD operations, transactions, and query optimization
 */

import { PrismaClient, Prisma } from '@prisma/client';
import type {
  User,
  Asset,
  Clip,
  Campaign,
  Experiment,
  Prediction,
  Conversion,
  KnowledgeDocument,
  UserRole,
  AssetStatus,
  ClipStatus,
  CampaignStatus,
  CampaignObjective,
  ExperimentStatus,
  ConversionSource,
} from '@prisma/client';

/**
 * Singleton Database Service with connection pooling
 */
export class DatabaseService {
  private static instance: DatabaseService;
  private prisma: PrismaClient;
  private isConnected: boolean = false;

  private constructor() {
    // Initialize Prisma Client with connection pooling
    this.prisma = new PrismaClient({
      datasources: {
        db: {
          url: process.env.DATABASE_URL,
        },
      },
      log: process.env.NODE_ENV === 'development'
        ? ['query', 'info', 'warn', 'error']
        : ['error'],
    });

    // Connection pool configuration via DATABASE_URL query params:
    // postgresql://user:password@host:port/db?connection_limit=10&pool_timeout=20
  }

  /**
   * Get singleton instance
   */
  public static getInstance(): DatabaseService {
    if (!DatabaseService.instance) {
      DatabaseService.instance = new DatabaseService();
    }
    return DatabaseService.instance;
  }

  /**
   * Connect to database
   */
  public async connect(): Promise<void> {
    if (this.isConnected) {
      return;
    }

    try {
      await this.prisma.$connect();
      this.isConnected = true;
      console.log('✅ Database connected successfully');
    } catch (error) {
      console.error('❌ Database connection failed:', error);
      throw error;
    }
  }

  /**
   * Disconnect from database
   */
  public async disconnect(): Promise<void> {
    if (!this.isConnected) {
      return;
    }

    try {
      await this.prisma.$disconnect();
      this.isConnected = false;
      console.log('✅ Database disconnected successfully');
    } catch (error) {
      console.error('❌ Database disconnection failed:', error);
      throw error;
    }
  }

  /**
   * Get Prisma client for direct queries
   */
  public getClient(): PrismaClient {
    return this.prisma;
  }

  // ============================================================================
  // User Operations
  // ============================================================================

  async createUser(data: {
    email: string;
    name: string;
    role?: UserRole;
    passwordHash?: string;
    apiKey?: string;
    settings?: any;
  }): Promise<User> {
    return this.prisma.user.create({
      data,
    });
  }

  async getUserById(id: string): Promise<User | null> {
    return this.prisma.user.findUnique({
      where: { id, deletedAt: null },
    });
  }

  async getUserByEmail(email: string): Promise<User | null> {
    return this.prisma.user.findUnique({
      where: { email, deletedAt: null },
    });
  }

  async getUserByApiKey(apiKey: string): Promise<User | null> {
    return this.prisma.user.findUnique({
      where: { apiKey, deletedAt: null },
    });
  }

  async updateUser(id: string, data: Partial<User>): Promise<User> {
    return this.prisma.user.update({
      where: { id },
      data,
    });
  }

  async deleteUser(id: string, soft: boolean = true): Promise<User> {
    if (soft) {
      return this.prisma.user.update({
        where: { id },
        data: { deletedAt: new Date() },
      });
    }
    return this.prisma.user.delete({
      where: { id },
    });
  }

  async listUsers(params: {
    skip?: number;
    take?: number;
    where?: Prisma.UserWhereInput;
    orderBy?: Prisma.UserOrderByWithRelationInput;
  }): Promise<User[]> {
    const { skip = 0, take = 100, where = {}, orderBy = { createdAt: 'desc' } } = params;
    return this.prisma.user.findMany({
      skip,
      take,
      where: { ...where, deletedAt: null },
      orderBy,
    });
  }

  // ============================================================================
  // Asset Operations
  // ============================================================================

  async createAsset(data: {
    userId: string;
    filename: string;
    originalName: string;
    mimeType: string;
    fileSize: bigint;
    gcsUrl: string;
    gcsBucket: string;
    gcsPath: string;
    thumbnailUrl?: string;
    duration?: number;
    width?: number;
    height?: number;
    fps?: number;
    bitrate?: number;
    codec?: string;
    metadata?: any;
  }): Promise<Asset> {
    return this.prisma.asset.create({
      data,
    });
  }

  async getAssetById(id: string): Promise<Asset | null> {
    return this.prisma.asset.findUnique({
      where: { id, deletedAt: null },
      include: {
        user: true,
        clips: true,
      },
    });
  }

  async updateAsset(id: string, data: Partial<Asset>): Promise<Asset> {
    return this.prisma.asset.update({
      where: { id },
      data,
    });
  }

  async updateAssetStatus(id: string, status: AssetStatus, error?: string): Promise<Asset> {
    return this.prisma.asset.update({
      where: { id },
      data: {
        status,
        processingError: error,
      },
    });
  }

  async deleteAsset(id: string, soft: boolean = true): Promise<Asset> {
    if (soft) {
      return this.prisma.asset.update({
        where: { id },
        data: { deletedAt: new Date() },
      });
    }
    return this.prisma.asset.delete({
      where: { id },
    });
  }

  async listAssets(params: {
    userId?: string;
    skip?: number;
    take?: number;
    where?: Prisma.AssetWhereInput;
    orderBy?: Prisma.AssetOrderByWithRelationInput;
  }): Promise<Asset[]> {
    const { userId, skip = 0, take = 100, where = {}, orderBy = { createdAt: 'desc' } } = params;
    return this.prisma.asset.findMany({
      skip,
      take,
      where: {
        ...where,
        ...(userId && { userId }),
        deletedAt: null,
      },
      orderBy,
      include: {
        clips: {
          where: { deletedAt: null },
          orderBy: { rank: 'asc' },
        },
      },
    });
  }

  // ============================================================================
  // Clip Operations
  // ============================================================================

  async createClip(data: {
    assetId: string;
    startTime: number;
    endTime: number;
    duration: number;
    clipUrl?: string;
    thumbnailUrl?: string;
    features?: any;
    faceCount?: number;
    hasText?: boolean;
    hasSpeech?: boolean;
    hasMusic?: boolean;
    metadata?: any;
  }): Promise<Clip> {
    return this.prisma.clip.create({
      data,
    });
  }

  async getClipById(id: string): Promise<Clip | null> {
    return this.prisma.clip.findUnique({
      where: { id, deletedAt: null },
      include: {
        asset: true,
        predictions: true,
      },
    });
  }

  async updateClip(id: string, data: Partial<Clip>): Promise<Clip> {
    return this.prisma.clip.update({
      where: { id },
      data,
    });
  }

  async updateClipScoring(id: string, scores: {
    score?: number;
    viralScore?: number;
    engagementScore?: number;
    brandSafetyScore?: number;
    rank?: number;
    status?: ClipStatus;
  }): Promise<Clip> {
    return this.prisma.clip.update({
      where: { id },
      data: scores,
    });
  }

  async deleteClip(id: string, soft: boolean = true): Promise<Clip> {
    if (soft) {
      return this.prisma.clip.update({
        where: { id },
        data: { deletedAt: new Date() },
      });
    }
    return this.prisma.clip.delete({
      where: { id },
    });
  }

  async listClips(params: {
    assetId?: string;
    skip?: number;
    take?: number;
    where?: Prisma.ClipWhereInput;
    orderBy?: Prisma.ClipOrderByWithRelationInput;
  }): Promise<Clip[]> {
    const { assetId, skip = 0, take = 100, where = {}, orderBy = { rank: 'asc' } } = params;
    return this.prisma.clip.findMany({
      skip,
      take,
      where: {
        ...where,
        ...(assetId && { assetId }),
        deletedAt: null,
      },
      orderBy,
    });
  }

  async getTopClips(params: {
    assetId?: string;
    limit?: number;
    minScore?: number;
  }): Promise<Clip[]> {
    const { assetId, limit = 10, minScore = 0 } = params;
    return this.prisma.clip.findMany({
      where: {
        ...(assetId && { assetId }),
        deletedAt: null,
        score: { gte: minScore },
        status: ClipStatus.SCORED,
      },
      orderBy: { score: 'desc' },
      take: limit,
      include: {
        asset: true,
      },
    });
  }

  // ============================================================================
  // Campaign Operations
  // ============================================================================

  async createCampaign(data: {
    userId: string;
    name: string;
    description?: string;
    objective?: CampaignObjective;
    budget: number;
    dailyBudget?: number;
    currency?: string;
    metaCampaignId?: string;
    metaAdSetId?: string;
    metaAccountId?: string;
    targetAudience?: any;
    targetLocations?: any;
    targetAgeRange?: any;
    startDate?: Date;
    endDate?: Date;
    metadata?: any;
  }): Promise<Campaign> {
    return this.prisma.campaign.create({
      data: {
        ...data,
        budget: new Prisma.Decimal(data.budget),
        dailyBudget: data.dailyBudget ? new Prisma.Decimal(data.dailyBudget) : undefined,
      },
    });
  }

  async getCampaignById(id: string): Promise<Campaign | null> {
    return this.prisma.campaign.findUnique({
      where: { id, deletedAt: null },
      include: {
        user: true,
        experiments: true,
        conversions: true,
      },
    });
  }

  async updateCampaign(id: string, data: Partial<Campaign>): Promise<Campaign> {
    return this.prisma.campaign.update({
      where: { id },
      data,
    });
  }

  async updateCampaignMetrics(id: string, metrics: {
    totalSpend?: number;
    totalImpressions?: bigint;
    totalClicks?: bigint;
    totalConversions?: bigint;
  }): Promise<Campaign> {
    return this.prisma.campaign.update({
      where: { id },
      data: {
        ...(metrics.totalSpend && { totalSpend: new Prisma.Decimal(metrics.totalSpend) }),
        ...(metrics.totalImpressions && { totalImpressions: metrics.totalImpressions }),
        ...(metrics.totalClicks && { totalClicks: metrics.totalClicks }),
        ...(metrics.totalConversions && { totalConversions: metrics.totalConversions }),
      },
    });
  }

  async deleteCampaign(id: string, soft: boolean = true): Promise<Campaign> {
    if (soft) {
      return this.prisma.campaign.update({
        where: { id },
        data: { deletedAt: new Date() },
      });
    }
    return this.prisma.campaign.delete({
      where: { id },
    });
  }

  async listCampaigns(params: {
    userId?: string;
    skip?: number;
    take?: number;
    where?: Prisma.CampaignWhereInput;
    orderBy?: Prisma.CampaignOrderByWithRelationInput;
  }): Promise<Campaign[]> {
    const { userId, skip = 0, take = 100, where = {}, orderBy = { createdAt: 'desc' } } = params;
    return this.prisma.campaign.findMany({
      skip,
      take,
      where: {
        ...where,
        ...(userId && { userId }),
        deletedAt: null,
      },
      orderBy,
      include: {
        experiments: true,
      },
    });
  }

  // ============================================================================
  // Experiment Operations
  // ============================================================================

  async createExperiment(data: {
    campaignId: string;
    name: string;
    description?: string;
    variants?: any;
    startDate?: Date;
    endDate?: Date;
    metadata?: any;
  }): Promise<Experiment> {
    return this.prisma.experiment.create({
      data,
    });
  }

  async getExperimentById(id: string): Promise<Experiment | null> {
    return this.prisma.experiment.findUnique({
      where: { id, deletedAt: null },
      include: {
        campaign: true,
      },
    });
  }

  async updateExperiment(id: string, data: Partial<Experiment>): Promise<Experiment> {
    return this.prisma.experiment.update({
      where: { id },
      data,
    });
  }

  async selectExperimentWinner(id: string, winnerVariantId: string, confidence: number): Promise<Experiment> {
    return this.prisma.experiment.update({
      where: { id },
      data: {
        winnerVariantId,
        winnerSelectedAt: new Date(),
        confidence,
        status: ExperimentStatus.COMPLETED,
      },
    });
  }

  async deleteExperiment(id: string, soft: boolean = true): Promise<Experiment> {
    if (soft) {
      return this.prisma.experiment.update({
        where: { id },
        data: { deletedAt: new Date() },
      });
    }
    return this.prisma.experiment.delete({
      where: { id },
    });
  }

  // ============================================================================
  // Prediction Operations
  // ============================================================================

  async createPrediction(data: {
    clipId: string;
    modelVersion: string;
    modelType?: string;
    predictedRoas?: number;
    predictedCtr?: number;
    predictedCpc?: number;
    predictedCpa?: number;
    predictedEngagement?: number;
    features?: any;
    confidence?: number;
    metadata?: any;
  }): Promise<Prediction> {
    return this.prisma.prediction.create({
      data,
    });
  }

  async getPredictionById(id: string): Promise<Prediction | null> {
    return this.prisma.prediction.findUnique({
      where: { id },
      include: {
        clip: {
          include: {
            asset: true,
          },
        },
      },
    });
  }

  async updatePredictionActuals(id: string, actuals: {
    actualRoas?: number;
    actualCtr?: number;
    actualCpc?: number;
    actualCpa?: number;
    actualEngagement?: number;
    predictionError?: number;
  }): Promise<Prediction> {
    return this.prisma.prediction.update({
      where: { id },
      data: actuals,
    });
  }

  async getPredictionsByClip(clipId: string): Promise<Prediction[]> {
    return this.prisma.prediction.findMany({
      where: { clipId },
      orderBy: { createdAt: 'desc' },
    });
  }

  // ============================================================================
  // Conversion Operations
  // ============================================================================

  async createConversion(data: {
    campaignId?: string;
    source?: ConversionSource;
    externalId?: string;
    value: number;
    currency?: string;
    attributedClipId?: string;
    attributedAdId?: string;
    timestamp?: Date;
    metadata?: any;
  }): Promise<Conversion> {
    return this.prisma.conversion.create({
      data: {
        ...data,
        value: new Prisma.Decimal(data.value),
      },
    });
  }

  async getConversionById(id: string): Promise<Conversion | null> {
    return this.prisma.conversion.findUnique({
      where: { id },
      include: {
        campaign: true,
      },
    });
  }

  async listConversions(params: {
    campaignId?: string;
    startDate?: Date;
    endDate?: Date;
    skip?: number;
    take?: number;
  }): Promise<Conversion[]> {
    const { campaignId, startDate, endDate, skip = 0, take = 100 } = params;
    return this.prisma.conversion.findMany({
      skip,
      take,
      where: {
        ...(campaignId && { campaignId }),
        ...(startDate && endDate && {
          timestamp: {
            gte: startDate,
            lte: endDate,
          },
        }),
      },
      orderBy: { timestamp: 'desc' },
    });
  }

  // ============================================================================
  // Knowledge Document Operations
  // ============================================================================

  async createKnowledgeDocument(data: {
    name: string;
    description?: string;
    content: string;
    embedding: number[];
    embeddingModel?: string;
    category: string;
    tags?: string[];
    version?: number;
    source?: string;
    author?: string;
    metadata?: any;
  }): Promise<KnowledgeDocument> {
    return this.prisma.knowledgeDocument.create({
      data,
    });
  }

  async getKnowledgeDocumentById(id: string): Promise<KnowledgeDocument | null> {
    return this.prisma.knowledgeDocument.findUnique({
      where: { id, deletedAt: null },
    });
  }

  async updateKnowledgeDocument(id: string, data: Partial<KnowledgeDocument>): Promise<KnowledgeDocument> {
    return this.prisma.knowledgeDocument.update({
      where: { id },
      data,
    });
  }

  async deleteKnowledgeDocument(id: string, soft: boolean = true): Promise<KnowledgeDocument> {
    if (soft) {
      return this.prisma.knowledgeDocument.update({
        where: { id },
        data: { deletedAt: new Date() },
      });
    }
    return this.prisma.knowledgeDocument.delete({
      where: { id },
    });
  }

  async searchKnowledgeDocuments(params: {
    category?: string;
    tags?: string[];
    skip?: number;
    take?: number;
  }): Promise<KnowledgeDocument[]> {
    const { category, tags, skip = 0, take = 100 } = params;
    return this.prisma.knowledgeDocument.findMany({
      skip,
      take,
      where: {
        deletedAt: null,
        ...(category && { category }),
        ...(tags && tags.length > 0 && {
          tags: {
            hasSome: tags,
          },
        }),
      },
      orderBy: { createdAt: 'desc' },
    });
  }

  // ============================================================================
  // Transaction Support
  // ============================================================================

  /**
   * Execute operations within a transaction
   */
  async transaction<T>(
    fn: (tx: Prisma.TransactionClient) => Promise<T>
  ): Promise<T> {
    return this.prisma.$transaction(fn);
  }

  /**
   * Execute raw SQL query (use with caution)
   */
  async executeRaw(query: string, ...values: any[]): Promise<number> {
    return this.prisma.$executeRawUnsafe(query, ...values);
  }

  /**
   * Execute raw SQL query and return results
   */
  async queryRaw<T = any>(query: string, ...values: any[]): Promise<T[]> {
    return this.prisma.$queryRawUnsafe(query, ...values);
  }

  // ============================================================================
  // Health Check
  // ============================================================================

  /**
   * Check database connection health
   */
  async healthCheck(): Promise<boolean> {
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      return true;
    } catch (error) {
      console.error('Database health check failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const db = DatabaseService.getInstance();

// Export types for convenience
export type {
  User,
  Asset,
  Clip,
  Campaign,
  Experiment,
  Prediction,
  Conversion,
  KnowledgeDocument,
  UserRole,
  AssetStatus,
  ClipStatus,
  CampaignStatus,
  CampaignObjective,
  ExperimentStatus,
  ConversionSource,
};
