import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

export interface Campaign {
  id: string;
  name: string;
  status: 'draft' | 'active' | 'paused' | 'completed';
  objective: string;
  budget: number;
  platforms: string[];
  createdAt: Date;
  updatedAt: Date;
  metrics?: {
    impressions: number;
    clicks: number;
    conversions: number;
    spend: number;
    roas: number;
  };
}

export interface WizardData {
  name: string;
  objective: string;
  budget: number;
  platforms: string[];
  targetAudience?: string;
  creativeStyle?: string;
  hookStyle?: string;
  variants?: number;
  creativeSettings: {
    aspectRatio?: string;
    duration?: number;
    style?: string;
    tone?: string;
  };
}

export interface CampaignState {
  campaigns: Campaign[];
  currentCampaign: Campaign | null;
  wizardStep: number;
  wizardData: WizardData;
  isLoading: boolean;

  setCampaigns: (campaigns: Campaign[]) => void;
  setCurrentCampaign: (campaign: Campaign | null) => void;
  setWizardStep: (step: number) => void;
  updateWizardData: (data: Partial<WizardData>) => void;
  resetWizard: () => void;
  addCampaign: (campaign: Campaign) => void;
  updateCampaign: (id: string, updates: Partial<Campaign>) => void;
  deleteCampaign: (id: string) => void;
}

const initialWizardData: WizardData = {
  name: '',
  objective: '',
  budget: 0,
  platforms: [],
  targetAudience: '',
  creativeStyle: '',
  hookStyle: '',
  variants: 1,
  creativeSettings: {},
};

export const useCampaignStore = create<CampaignState>()(
  immer((set) => ({
    campaigns: [],
    currentCampaign: null,
    wizardStep: 1,
    wizardData: initialWizardData,
    isLoading: false,

    setCampaigns: (campaigns) => set({ campaigns }),

    setCurrentCampaign: (campaign) => set({ currentCampaign: campaign }),

    setWizardStep: (step) => set({ wizardStep: step }),

    updateWizardData: (data) => set((state) => {
      state.wizardData = { ...state.wizardData, ...data };
      if (data.creativeSettings) {
        state.wizardData.creativeSettings = {
          ...state.wizardData.creativeSettings,
          ...data.creativeSettings,
        };
      }
    }),

    resetWizard: () => set({
      wizardStep: 1,
      wizardData: initialWizardData,
    }),

    addCampaign: (campaign) => set((state) => {
      state.campaigns.push(campaign);
    }),

    updateCampaign: (id, updates) => set((state) => {
      const index = state.campaigns.findIndex((c) => c.id === id);
      if (index !== -1) {
        state.campaigns[index] = { ...state.campaigns[index], ...updates };
      }
      if (state.currentCampaign?.id === id) {
        state.currentCampaign = { ...state.currentCampaign, ...updates };
      }
    }),

    deleteCampaign: (id) => set((state) => {
      state.campaigns = state.campaigns.filter((c) => c.id !== id);
      if (state.currentCampaign?.id === id) {
        state.currentCampaign = null;
      }
    }),
  }))
);
