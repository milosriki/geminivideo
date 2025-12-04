import { AdvancedEdit } from '../types';

export interface EditTemplate {
  id: string;
  name: string;
  description: string;
  category: 'reels' | 'story' | 'feed' | 'custom';
  edits: AdvancedEdit[];
  previewImage: string;
  estimatedDuration: number;
  tags: string[];
}

// Built-in templates
const BUILT_IN_TEMPLATES: EditTemplate[] = [
  {
    id: 'vertical-reel',
    name: 'Vertical Reel',
    description: 'Optimized vertical 9:16 format with animated captions for Instagram Reels and TikTok',
    category: 'reels',
    edits: [
      { id: '1', type: 'crop', ratio: '9:16' },
      { id: '2', type: 'text', text: 'Your Caption Here', start: '0', end: '3', position: 'bottom', fontSize: 48 },
      { id: '3', type: 'fade', typeIn: true, typeOut: true, duration: 0.5 },
      { id: '4', type: 'color', brightness: 1.1, contrast: 1.15, saturation: 1.2 },
    ],
    previewImage: '/templates/vertical-reel.png',
    estimatedDuration: 30,
    tags: ['vertical', 'social', 'captions', 'mobile-first'],
  },
  {
    id: 'fast-hook',
    name: 'Fast Hook',
    description: 'Speed up first 3 seconds to 1.5x with attention-grabbing text overlay to hook viewers',
    category: 'reels',
    edits: [
      { id: '1', type: 'trim', start: '0', end: '3' },
      { id: '2', type: 'speed', factor: 1.5 },
      { id: '3', type: 'text', text: 'WAIT FOR IT!', start: '0', end: '2', position: 'center', fontSize: 64 },
      { id: '4', type: 'color', brightness: 1.15, contrast: 1.25, saturation: 1.3 },
      { id: '5', type: 'volume', level: 1.2 },
    ],
    previewImage: '/templates/fast-hook.png',
    estimatedDuration: 15,
    tags: ['hook', 'fast', 'attention', 'speed'],
  },
  {
    id: 'cinematic',
    name: 'Cinematic Look',
    description: 'Professional color grading with vignette and smooth fades for a cinematic feel',
    category: 'feed',
    edits: [
      { id: '1', type: 'color', brightness: 0.95, contrast: 1.3, saturation: 0.9 },
      { id: '2', type: 'filter', name: 'vignette' },
      { id: '3', type: 'fade', typeIn: true, typeOut: true, duration: 1.0 },
      { id: '4', type: 'crop', ratio: '16:9' },
    ],
    previewImage: '/templates/cinematic.png',
    estimatedDuration: 60,
    tags: ['cinematic', 'professional', 'color-grading', 'moody'],
  },
  {
    id: 'silent-text',
    name: 'Silent with Text',
    description: 'Muted video with bold text captions and CTA overlay for sound-off viewing',
    category: 'feed',
    edits: [
      { id: '1', type: 'mute' },
      { id: '2', type: 'text', text: 'Main Caption', start: '0', end: '5', position: 'center', fontSize: 56 },
      { id: '3', type: 'text', text: 'CALL TO ACTION', start: '5', end: '10', position: 'bottom', fontSize: 44 },
      { id: '4', type: 'color', brightness: 1.1, contrast: 1.2, saturation: 1.15 },
      { id: '5', type: 'crop', ratio: '1:1' },
    ],
    previewImage: '/templates/silent-text.png',
    estimatedDuration: 10,
    tags: ['silent', 'captions', 'text-heavy', 'cta'],
  },
  {
    id: 'before-after',
    name: 'Before & After',
    description: 'Split screen transformation with dramatic reveal for showcasing changes',
    category: 'reels',
    edits: [
      { id: '1', type: 'crop', ratio: '9:16' },
      { id: '2', type: 'text', text: 'BEFORE', start: '0', end: '3', position: 'top', fontSize: 52 },
      { id: '3', type: 'filter', name: 'grayscale' },
      { id: '4', type: 'text', text: 'AFTER', start: '3', end: '6', position: 'top', fontSize: 52 },
      { id: '5', type: 'color', brightness: 1.2, contrast: 1.3, saturation: 1.4 },
      { id: '6', type: 'fade', typeIn: true, typeOut: false, duration: 0.3 },
    ],
    previewImage: '/templates/before-after.png',
    estimatedDuration: 15,
    tags: ['transformation', 'comparison', 'dramatic', 'split'],
  },
  {
    id: 'testimonial',
    name: 'Testimonial Focus',
    description: 'Face-focused settings with enhanced audio and subtle vignette for authentic testimonials',
    category: 'story',
    edits: [
      { id: '1', type: 'crop', ratio: '9:16' },
      { id: '2', type: 'color', brightness: 1.05, contrast: 1.1, saturation: 1.05 },
      { id: '3', type: 'filter', name: 'vignette' },
      { id: '4', type: 'volume', level: 1.3 },
      { id: '5', type: 'text', text: 'Real Customer', start: '0', end: '2', position: 'bottom', fontSize: 36 },
    ],
    previewImage: '/templates/testimonial.png',
    estimatedDuration: 30,
    tags: ['testimonial', 'ugc', 'authentic', 'face'],
  },
  {
    id: 'product-hero',
    name: 'Product Hero',
    description: 'Product-focused with enhanced colors and smooth speed control to showcase features',
    category: 'feed',
    edits: [
      { id: '1', type: 'crop', ratio: '1:1' },
      { id: '2', type: 'speed', factor: 0.8 },
      { id: '3', type: 'color', brightness: 1.15, contrast: 1.25, saturation: 1.35 },
      { id: '4', type: 'fade', typeIn: true, typeOut: true, duration: 0.5 },
      { id: '5', type: 'text', text: 'Product Name', start: '0', end: '3', position: 'bottom', fontSize: 48 },
    ],
    previewImage: '/templates/product-hero.png',
    estimatedDuration: 15,
    tags: ['product', 'ecommerce', 'showcase', 'hero'],
  },
  {
    id: 'ugc-style',
    name: 'UGC Raw Style',
    description: 'Authentic user-generated content look with minimal editing and natural feel',
    category: 'reels',
    edits: [
      { id: '1', type: 'crop', ratio: '9:16' },
      { id: '2', type: 'color', brightness: 1.02, contrast: 1.05, saturation: 0.98 },
      { id: '3', type: 'volume', level: 1.1 },
      { id: '4', type: 'text', text: '@username', start: '0', end: '1', position: 'top', fontSize: 32 },
    ],
    previewImage: '/templates/ugc-style.png',
    estimatedDuration: 20,
    tags: ['ugc', 'raw', 'authentic', 'natural'],
  },
  {
    id: 'tutorial',
    name: 'Tutorial Step-by-Step',
    description: 'Clear text overlays with slow motion for educational and how-to content',
    category: 'feed',
    edits: [
      { id: '1', type: 'crop', ratio: '16:9' },
      { id: '2', type: 'speed', factor: 0.7 },
      { id: '3', type: 'text', text: 'Step 1', start: '0', end: '5', position: 'top', fontSize: 52 },
      { id: '4', type: 'text', text: 'Follow along...', start: '0', end: '5', position: 'bottom', fontSize: 40 },
      { id: '5', type: 'color', brightness: 1.1, contrast: 1.15, saturation: 1.1 },
    ],
    previewImage: '/templates/tutorial.png',
    estimatedDuration: 45,
    tags: ['tutorial', 'education', 'how-to', 'step-by-step'],
  },
  {
    id: 'story-format',
    name: 'Story Optimized',
    description: '15-second vertical story format with quick cuts and bold text for Instagram Stories',
    category: 'story',
    edits: [
      { id: '1', type: 'crop', ratio: '9:16' },
      { id: '2', type: 'trim', start: '0', end: '15' },
      { id: '3', type: 'text', text: 'SWIPE UP', start: '12', end: '15', position: 'bottom', fontSize: 44 },
      { id: '4', type: 'color', brightness: 1.15, contrast: 1.2, saturation: 1.25 },
      { id: '5', type: 'fade', typeIn: true, typeOut: false, duration: 0.3 },
      { id: '6', type: 'volume', level: 1.2 },
    ],
    previewImage: '/templates/story-format.png',
    estimatedDuration: 15,
    tags: ['story', 'vertical', 'quick', 'swipe-up'],
  },
];

export class TemplateManager {
  private static readonly STORAGE_KEY = 'customTemplates';
  private customTemplates: EditTemplate[] = [];

  constructor() {
    this.loadCustomTemplates();
  }

  /**
   * Get all built-in templates
   */
  getBuiltInTemplates(): EditTemplate[] {
    return [...BUILT_IN_TEMPLATES];
  }

  /**
   * Get all templates (built-in + custom)
   */
  getAllTemplates(): EditTemplate[] {
    return [...BUILT_IN_TEMPLATES, ...this.customTemplates];
  }

  /**
   * Get template by ID
   */
  getTemplateById(id: string): EditTemplate | undefined {
    const allTemplates = this.getAllTemplates();
    return allTemplates.find(template => template.id === id);
  }

  /**
   * Get templates by category
   */
  getTemplatesByCategory(category: 'reels' | 'story' | 'feed' | 'custom'): EditTemplate[] {
    const allTemplates = this.getAllTemplates();
    return allTemplates.filter(template => template.category === category);
  }

  /**
   * Search templates by name, description, or tags
   */
  searchTemplates(query: string): EditTemplate[] {
    const lowerQuery = query.toLowerCase();
    const allTemplates = this.getAllTemplates();

    return allTemplates.filter(template =>
      template.name.toLowerCase().includes(lowerQuery) ||
      template.description.toLowerCase().includes(lowerQuery) ||
      template.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    );
  }

  /**
   * Apply template to a video file by generating edit array
   * Note: Some edits like text may need customization per video
   */
  applyTemplate(template: EditTemplate, videoFile?: File): AdvancedEdit[] {
    // Clone the edits with new IDs to avoid conflicts
    return template.edits.map((edit, index) => ({
      ...edit,
      id: `${template.id}-${Date.now()}-${index}`,
    }));
  }

  /**
   * Create a custom template from current edits
   */
  createCustomTemplate(
    name: string,
    description: string,
    edits: AdvancedEdit[],
    tags: string[] = [],
    estimatedDuration: number = 30
  ): EditTemplate {
    const template: EditTemplate = {
      id: `custom-${Date.now()}`,
      name,
      description,
      category: 'custom',
      edits: edits.map((edit, index) => ({
        ...edit,
        id: `${index}`,
      })),
      previewImage: '/templates/custom.png',
      estimatedDuration,
      tags: ['custom', ...tags],
    };

    return template;
  }

  /**
   * Save a custom template to localStorage
   */
  saveCustomTemplate(template: EditTemplate): void {
    // Ensure it's marked as custom
    const customTemplate = { ...template, category: 'custom' as const };

    // Check if template already exists
    const existingIndex = this.customTemplates.findIndex(t => t.id === template.id);

    if (existingIndex >= 0) {
      // Update existing template
      this.customTemplates[existingIndex] = customTemplate;
    } else {
      // Add new template
      this.customTemplates.push(customTemplate);
    }

    // Persist to localStorage
    this.persistCustomTemplates();
  }

  /**
   * Delete a custom template
   */
  deleteCustomTemplate(templateId: string): boolean {
    const initialLength = this.customTemplates.length;
    this.customTemplates = this.customTemplates.filter(t => t.id !== templateId);

    if (this.customTemplates.length < initialLength) {
      this.persistCustomTemplates();
      return true;
    }

    return false;
  }

  /**
   * Load custom templates from localStorage
   */
  loadCustomTemplates(): EditTemplate[] {
    try {
      const stored = localStorage.getItem(TemplateManager.STORAGE_KEY);
      if (stored) {
        this.customTemplates = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load custom templates:', error);
      this.customTemplates = [];
    }

    return this.customTemplates;
  }

  /**
   * Get all custom templates
   */
  getCustomTemplates(): EditTemplate[] {
    return [...this.customTemplates];
  }

  /**
   * Export template as JSON string
   */
  exportTemplate(template: EditTemplate): string {
    return JSON.stringify(template, null, 2);
  }

  /**
   * Import template from JSON string
   */
  importTemplate(json: string): EditTemplate {
    try {
      const template = JSON.parse(json) as EditTemplate;

      // Validate required fields
      if (!template.id || !template.name || !template.edits) {
        throw new Error('Invalid template format');
      }

      // Generate new ID to avoid conflicts
      const importedTemplate: EditTemplate = {
        ...template,
        id: `imported-${Date.now()}`,
        category: 'custom',
      };

      // Save to custom templates
      this.saveCustomTemplate(importedTemplate);

      return importedTemplate;
    } catch (error) {
      throw new Error(`Failed to import template: ${error}`);
    }
  }

  /**
   * Export all custom templates as JSON
   */
  exportAllCustomTemplates(): string {
    return JSON.stringify(this.customTemplates, null, 2);
  }

  /**
   * Import multiple templates from JSON
   */
  importMultipleTemplates(json: string): EditTemplate[] {
    try {
      const templates = JSON.parse(json) as EditTemplate[];

      if (!Array.isArray(templates)) {
        throw new Error('Invalid format: expected array of templates');
      }

      const importedTemplates: EditTemplate[] = [];

      templates.forEach(template => {
        const importedTemplate: EditTemplate = {
          ...template,
          id: `imported-${Date.now()}-${Math.random()}`,
          category: 'custom',
        };

        this.saveCustomTemplate(importedTemplate);
        importedTemplates.push(importedTemplate);
      });

      return importedTemplates;
    } catch (error) {
      throw new Error(`Failed to import templates: ${error}`);
    }
  }

  /**
   * Persist custom templates to localStorage
   */
  private persistCustomTemplates(): void {
    try {
      localStorage.setItem(
        TemplateManager.STORAGE_KEY,
        JSON.stringify(this.customTemplates)
      );
    } catch (error) {
      console.error('Failed to save custom templates:', error);
    }
  }

  /**
   * Duplicate a template (useful for creating variations)
   */
  duplicateTemplate(templateId: string, newName?: string): EditTemplate | undefined {
    const original = this.getTemplateById(templateId);

    if (!original) {
      return undefined;
    }

    const duplicated: EditTemplate = {
      ...original,
      id: `duplicate-${Date.now()}`,
      name: newName || `${original.name} (Copy)`,
      category: 'custom',
    };

    this.saveCustomTemplate(duplicated);
    return duplicated;
  }

  /**
   * Get template statistics
   */
  getTemplateStats(): {
    total: number;
    byCategory: Record<string, number>;
    custom: number;
    builtIn: number;
  } {
    const allTemplates = this.getAllTemplates();

    const byCategory = allTemplates.reduce((acc, template) => {
      acc[template.category] = (acc[template.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total: allTemplates.length,
      byCategory,
      custom: this.customTemplates.length,
      builtIn: BUILT_IN_TEMPLATES.length,
    };
  }
}

// Singleton instance
export const templateManager = new TemplateManager();
