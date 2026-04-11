export interface Voice {
  id: string;
  provider: string;
  provider_voice_id: string;
  name: string;
  description: string | null;
  gender: string;
  age_group: string;
  accent: string | null;
  language: string;
  provider_model: string | null;
  texture: string | null;
  pitch: string | null;
  traits: Record<string, number | null>;
  use_cases: string[];
  personality_tags: string[];
  style_tags: string[];
  cost_per_min_usd: number | null;
  latency_tier: string | null;
  preview_url: string | null;
  status: string;
  metadata_source: string | null;
  enrichment_status: string | null;
  enrichment_attempts: number;
  ready: boolean;
}

export interface VoiceListResponse {
  voices: Voice[];
  total: number;
  ready_count: number;
  providers: string[];
  filters: FilterOptions;
}

export interface FilterOptions {
  genders: string[];
  age_groups: string[];
  textures: string[];
  pitches: string[];
  use_cases: string[];
  enrichment_statuses: string[];
  providers: string[];
}
