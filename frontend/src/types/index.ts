export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Campaign {
  id: number;
  title: string;
  description: string | null;
  product_url: string;
  status: "PENDING" | "RESEARCHING" | "GENERATING" | "AWAITING_APPROVAL" | "COMPLETED" | "FAILED";
  created_at: string;
  user_id: number;
}

export interface Asset {
  id: number;
  campaign_id: number;
  type: "COPY" | "IMAGE" | "VIDEO";
  content: string;
  asset_metadata: string;
  created_at: string;
}

export interface AgentLog {
  id: number;
  agent_name: string;
  message: string;
  level: string;
  created_at: string;
}

export interface CampaignCreate {
  title: string;
  product_url: string;
  description?: string;
}

export interface UserSettings {
  default_llm_engine: string | null;
  default_image_engine: string | null;
  default_video_engine: string | null;
  ollama_url: string | null;
  comfyui_url: string | null;
  has_openai_key: boolean;
  has_fal_key: boolean;
  has_firecrawl_key: boolean;
}

export interface UserSettingsUpdate {
  default_llm_engine?: string;
  default_image_engine?: string;
  default_video_engine?: string;
  ollama_url?: string;
  comfyui_url?: string;
  openai_api_key?: string;
  fal_api_key?: string;
  firecrawl_api_key?: string;
}

export interface GeneratedAsset {
  id: number;
  campaign_id: number;
  asset_type: "image" | "video" | "copy";
  content: string;
  platform: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
