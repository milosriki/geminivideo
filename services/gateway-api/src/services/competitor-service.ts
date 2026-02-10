import { Pool } from 'pg';
import { v4 as uuidv4 } from 'uuid';

export interface Competitor {
  id: string;
  brand_name: string;
  website_url: string;
  ad_library_url?: string;
  logo_url?: string;
  industry?: string;
  status: 'active' | 'tracking' | 'error';
  last_scraped_at?: Date;
  ads_count: number;
}

export interface CompetitorAd {
  id: string;
  competitor_id: string;
  platform: 'facebook' | 'instagram' | 'tiktok' | 'youtube';
  format: 'image' | 'video' | 'carousel';
  thumbnail_url: string;
  video_url?: string;
  ad_copy_primary?: string;
  ad_copy_headline?: string;
  cta_text?: string;
  landing_page_url?: string;
  active_days?: number;
  impressions_estimate?: number;
  spend_estimate?: number;
  first_seen_at: Date;
  last_seen_at: Date;
  ai_analysis?: {
    hook_score: number;
    visual_structure: string[];
    transcript?: string;
    winning_factors: string[];
  };
}

export class CompetitorService {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
    this.initializeSchema();
  }

  private async initializeSchema() {
    const query = `
      CREATE TABLE IF NOT EXISTS competitors (
        id UUID PRIMARY KEY,
        brand_name VARCHAR(255) NOT NULL,
        website_url VARCHAR(500) NOT NULL,
        ad_library_url VARCHAR(500),
        logo_url VARCHAR(500),
        industry VARCHAR(100),
        status VARCHAR(50) DEFAULT 'active',
        last_scraped_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW()
      );

      CREATE TABLE IF NOT EXISTS competitor_ads (
        id UUID PRIMARY KEY,
        competitor_id UUID REFERENCES competitors(id),
        platform VARCHAR(50),
        format VARCHAR(50),
        thumbnail_url VARCHAR(500),
        video_url VARCHAR(500),
        ad_copy_primary TEXT,
        ad_copy_headline TEXT,
        cta_text VARCHAR(100),
        landing_page_url VARCHAR(500),
        active_days INTEGER DEFAULT 0,
        impressions_estimate INTEGER DEFAULT 0,
        spend_estimate INTEGER DEFAULT 0,
        first_seen_at TIMESTAMP,
        last_seen_at TIMESTAMP,
        ai_analysis JSONB,
        created_at TIMESTAMP DEFAULT NOW()
      );
    `;
    try {
      await this.pool.query(query);
      console.log('✅ Competitor tables initialized');
    } catch (error) {
      console.error('❌ Failed to initialize competitor tables:', error);
    }
  }

  async addCompetitor(brandName: string, websiteUrl: string, industry?: string): Promise<Competitor> {
    const id = uuidv4();
    // Simulate fetching logo
    const logoUrl = `https://logo.clearbit.com/${new URL(websiteUrl).hostname}`;
    
    const query = `
      INSERT INTO competitors (id, brand_name, website_url, logo_url, industry, status)
      VALUES ($1, $2, $3, $4, $5, 'tracking')
      RETURNING *
    `;
    
    const result = await this.pool.query(query, [id, brandName, websiteUrl, logoUrl, industry]);
    
    // Trigger initial scrape (simulated)
    this.simulateScrape(id);
    
    return { ...result.rows[0], ads_count: 0 };
  }

  async getCompetitors(): Promise<Competitor[]> {
    const query = `
      SELECT c.*, COUNT(ca.id) as ads_count
      FROM competitors c
      LEFT JOIN competitor_ads ca ON c.id = ca.competitor_id
      GROUP BY c.id
      ORDER BY c.created_at DESC
    `;
    const result = await this.pool.query(query);
    return result.rows.map(row => ({
      ...row,
      ads_count: parseInt(row.ads_count)
    }));
  }

  async getCompetitorAds(competitorId: string): Promise<CompetitorAd[]> {
    const query = `
      SELECT * FROM competitor_ads
      WHERE competitor_id = $1
      ORDER BY last_seen_at DESC
    `;
    const result = await this.pool.query(query, [competitorId]);
    return result.rows;
  }

  async getTrendingAds(): Promise<CompetitorAd[]> {
    // Return ads with high impressions estimate
    const query = `
      SELECT ca.*, c.brand_name, c.logo_url
      FROM competitor_ads ca
      JOIN competitors c ON ca.competitor_id = c.id
      ORDER BY ca.impressions_estimate DESC
      LIMIT 20
    `;
    const result = await this.pool.query(query);
    return result.rows;
  }

  // --- SIMULATION LOGIC ---
  
  private async simulateScrape(competitorId: string) {
    console.log(`[Scraper] Starting scrape for competitor ${competitorId}...`);
    
    // Simulate delay
    setTimeout(async () => {
      try {
        // Generate 3-5 fake ads
        const adCount = Math.floor(Math.random() * 3) + 3;
        
        for (let i = 0; i < adCount; i++) {
          const adId = uuidv4();
          const isVideo = Math.random() > 0.3;
          
          await this.pool.query(`
            INSERT INTO competitor_ads (
              id, competitor_id, platform, format, thumbnail_url, video_url,
              ad_copy_primary, ad_copy_headline, cta_text,
              active_days, impressions_estimate, spend_estimate,
              first_seen_at, last_seen_at, ai_analysis
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW(), $13)
          `, [
            adId,
            competitorId,
            Math.random() > 0.5 ? 'instagram' : 'facebook',
            isVideo ? 'video' : 'image',
            `https://source.unsplash.com/random/800x800?fitness,gym&sig=${Math.random()}`,
            isVideo ? 'https://assets.mixkit.co/videos/preview/mixkit-going-down-a-curved-highway-through-a-mountain-range-41576-large.mp4' : null,
            "Transform your body in just 30 days! 💪 #fitness #goals",
            "The Ultimate Fitness Challenge",
            "Sign Up",
            Math.floor(Math.random() * 30),
            Math.floor(Math.random() * 1000000),
            Math.floor(Math.random() * 5000),
            JSON.stringify({
              hook_score: Math.floor(Math.random() * 40) + 60,
              winning_factors: ['High energy', 'Clear value prop', 'Social proof'],
              visual_structure: ['Hook (0-3s)', 'Problem (3-10s)', 'Solution (10-20s)', 'CTA']
            })
          ]);
        }
        
        await this.pool.query(`UPDATE competitors SET status = 'active', last_scraped_at = NOW() WHERE id = $1`, [competitorId]);
        console.log(`[Scraper] Finished scraping for ${competitorId}`);
        
      } catch (err) {
        console.error(`[Scraper] Failed for ${competitorId}`, err);
      }
    }, 5000); // 5 second delay
  }
}
