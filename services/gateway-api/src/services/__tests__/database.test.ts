/**
 * Database Service Tests
 * Tests for Prisma database operations
 */

import { DatabaseService } from '../database';
import { UserRole, AssetStatus, ClipStatus } from '@prisma/client';

describe('DatabaseService', () => {
  let db: DatabaseService;

  beforeAll(async () => {
    db = DatabaseService.getInstance();
    await db.connect();
  });

  afterAll(async () => {
    await db.disconnect();
  });

  describe('Connection Management', () => {
    it('should connect to database', async () => {
      const isHealthy = await db.healthCheck();
      expect(isHealthy).toBe(true);
    });

    it('should return singleton instance', () => {
      const instance1 = DatabaseService.getInstance();
      const instance2 = DatabaseService.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe('User Operations', () => {
    let testUserId: string;

    it('should create a user', async () => {
      const user = await db.createUser({
        email: `test-${Date.now()}@example.com`,
        name: 'Test User',
        role: UserRole.USER,
      });

      expect(user).toBeDefined();
      expect(user.id).toBeDefined();
      expect(user.email).toContain('test-');
      expect(user.role).toBe(UserRole.USER);

      testUserId = user.id;
    });

    it('should get user by id', async () => {
      const user = await db.getUserById(testUserId);
      expect(user).toBeDefined();
      expect(user?.id).toBe(testUserId);
    });

    it('should get user by email', async () => {
      const user = await db.getUserById(testUserId);
      if (user) {
        const foundUser = await db.getUserByEmail(user.email);
        expect(foundUser).toBeDefined();
        expect(foundUser?.id).toBe(testUserId);
      }
    });

    it('should update user', async () => {
      const updatedUser = await db.updateUser(testUserId, {
        name: 'Updated Name',
      });
      expect(updatedUser.name).toBe('Updated Name');
    });

    it('should list users', async () => {
      const users = await db.listUsers({ take: 10 });
      expect(Array.isArray(users)).toBe(true);
      expect(users.length).toBeGreaterThan(0);
    });

    it('should soft delete user', async () => {
      const deletedUser = await db.deleteUser(testUserId, true);
      expect(deletedUser.deletedAt).toBeDefined();

      // Should not find soft-deleted user
      const user = await db.getUserById(testUserId);
      expect(user).toBeNull();
    });
  });

  describe('Asset Operations', () => {
    let testUserId: string;
    let testAssetId: string;

    beforeAll(async () => {
      // Create test user
      const user = await db.createUser({
        email: `asset-test-${Date.now()}@example.com`,
        name: 'Asset Test User',
      });
      testUserId = user.id;
    });

    it('should create an asset', async () => {
      const asset = await db.createAsset({
        userId: testUserId,
        filename: 'test-video.mp4',
        originalName: 'Test Video.mp4',
        mimeType: 'video/mp4',
        fileSize: BigInt(1000000),
        gcsUrl: `gs://test-bucket/test-${Date.now()}.mp4`,
        gcsBucket: 'test-bucket',
        gcsPath: 'videos/test.mp4',
        duration: 120.5,
        width: 1920,
        height: 1080,
      });

      expect(asset).toBeDefined();
      expect(asset.id).toBeDefined();
      expect(asset.userId).toBe(testUserId);
      expect(asset.status).toBe(AssetStatus.PENDING);

      testAssetId = asset.id;
    });

    it('should get asset by id', async () => {
      const asset = await db.getAssetById(testAssetId);
      expect(asset).toBeDefined();
      expect(asset?.id).toBe(testAssetId);
      expect(asset?.user).toBeDefined();
    });

    it('should update asset status', async () => {
      const asset = await db.updateAssetStatus(testAssetId, AssetStatus.READY);
      expect(asset.status).toBe(AssetStatus.READY);
    });

    it('should list assets', async () => {
      const assets = await db.listAssets({ userId: testUserId });
      expect(Array.isArray(assets)).toBe(true);
      expect(assets.length).toBeGreaterThan(0);
    });
  });

  describe('Clip Operations', () => {
    let testAssetId: string;
    let testClipId: string;

    beforeAll(async () => {
      // Create test user and asset
      const user = await db.createUser({
        email: `clip-test-${Date.now()}@example.com`,
        name: 'Clip Test User',
      });

      const asset = await db.createAsset({
        userId: user.id,
        filename: 'clip-test-video.mp4',
        originalName: 'Clip Test Video.mp4',
        mimeType: 'video/mp4',
        fileSize: BigInt(1000000),
        gcsUrl: `gs://test-bucket/clip-test-${Date.now()}.mp4`,
        gcsBucket: 'test-bucket',
        gcsPath: 'videos/clip-test.mp4',
      });

      testAssetId = asset.id;
    });

    it('should create a clip', async () => {
      const clip = await db.createClip({
        assetId: testAssetId,
        startTime: 0,
        endTime: 15,
        duration: 15,
        features: {
          hasLogo: true,
          emotion: 'happy',
        },
        hasText: true,
        hasSpeech: true,
      });

      expect(clip).toBeDefined();
      expect(clip.id).toBeDefined();
      expect(clip.assetId).toBe(testAssetId);
      expect(clip.status).toBe(ClipStatus.PENDING);

      testClipId = clip.id;
    });

    it('should update clip scoring', async () => {
      const clip = await db.updateClipScoring(testClipId, {
        score: 0.85,
        viralScore: 0.75,
        engagementScore: 0.90,
        rank: 1,
        status: ClipStatus.SCORED,
      });

      expect(clip.score).toBe(0.85);
      expect(clip.viralScore).toBe(0.75);
      expect(clip.status).toBe(ClipStatus.SCORED);
    });

    it('should get top clips', async () => {
      const topClips = await db.getTopClips({
        assetId: testAssetId,
        limit: 5,
        minScore: 0.5,
      });

      expect(Array.isArray(topClips)).toBe(true);
    });
  });

  describe('Campaign Operations', () => {
    let testUserId: string;
    let testCampaignId: string;

    beforeAll(async () => {
      const user = await db.createUser({
        email: `campaign-test-${Date.now()}@example.com`,
        name: 'Campaign Test User',
      });
      testUserId = user.id;
    });

    it('should create a campaign', async () => {
      const campaign = await db.createCampaign({
        userId: testUserId,
        name: 'Test Campaign',
        objective: 'CONVERSIONS',
        budget: 1000,
        dailyBudget: 50,
        currency: 'USD',
      });

      expect(campaign).toBeDefined();
      expect(campaign.id).toBeDefined();
      expect(campaign.userId).toBe(testUserId);

      testCampaignId = campaign.id;
    });

    it('should update campaign metrics', async () => {
      const campaign = await db.updateCampaignMetrics(testCampaignId, {
        totalSpend: 150.50,
        totalImpressions: BigInt(10000),
        totalClicks: BigInt(500),
        totalConversions: BigInt(25),
      });

      expect(campaign.totalSpend.toString()).toBe('150.5');
      expect(campaign.totalImpressions).toBe(BigInt(10000));
    });

    it('should list campaigns', async () => {
      const campaigns = await db.listCampaigns({ userId: testUserId });
      expect(Array.isArray(campaigns)).toBe(true);
      expect(campaigns.length).toBeGreaterThan(0);
    });
  });

  describe('Transaction Support', () => {
    it('should execute operations in a transaction', async () => {
      const result = await db.transaction(async (tx) => {
        const user = await tx.user.create({
          data: {
            email: `transaction-test-${Date.now()}@example.com`,
            name: 'Transaction Test',
          },
        });

        return user;
      });

      expect(result).toBeDefined();
      expect(result.id).toBeDefined();
    });

    it('should rollback on error', async () => {
      try {
        await db.transaction(async (tx) => {
          await tx.user.create({
            data: {
              email: `rollback-test-${Date.now()}@example.com`,
              name: 'Rollback Test',
            },
          });

          // Force error
          throw new Error('Test error');
        });
      } catch (error) {
        expect(error).toBeDefined();
      }
    });
  });
});
