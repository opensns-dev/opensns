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
  updated_at?: string;
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
  brand_kit_id?: number;
  template_id?: number;
}

export interface UserSettings {
  default_llm_engine: string | null;
  default_image_engine: string | null;
  default_video_engine: string | null;
  default_ugc_engine: string | null;
  ugc_enabled: boolean;
  ugc_avatar_id: string | null;
  ugc_voice_id: string | null;
  ollama_url: string | null;
  comfyui_url: string | null;
  sadtalker_url: string | null;
  has_openai_key: boolean;
  has_fal_key: boolean;
  has_firecrawl_key: boolean;
  has_heygen_key: boolean;
  has_did_key: boolean;
  has_anthropic_key: boolean;
  has_google_key: boolean;
  has_groq_key: boolean;
  ai_disclosure_enabled: boolean;
  ai_label_text: string;
  ai_label_position: string;
  tts_enabled: boolean;
  default_tts_engine: string | null;
  tts_voice_id: string | null;
  bgm_enabled: boolean;
  default_bgm_engine: string | null;
  bgm_style: string | null;
  default_stt_engine: string | null;
  has_elevenlabs_key: boolean;
}

export interface TTSVoiceInfo {
  voice_id: string;
  name: string;
  language: string;
  preview_url: string | null;
  engine: string;
}

export interface TTSVoicesResponse {
  voices: TTSVoiceInfo[];
  engine: string;
}

export interface UserSettingsUpdate {
  default_llm_engine?: string;
  default_image_engine?: string;
  default_video_engine?: string;
  default_ugc_engine?: string;
  ugc_enabled?: boolean;
  ugc_avatar_id?: string;
  ugc_voice_id?: string;
  ollama_url?: string;
  comfyui_url?: string;
  sadtalker_url?: string;
  openai_api_key?: string;
  fal_api_key?: string;
  firecrawl_api_key?: string;
  heygen_api_key?: string;
  did_api_key?: string;
  anthropic_api_key?: string;
  google_api_key?: string;
  groq_api_key?: string;
  ai_disclosure_enabled?: boolean;
  ai_label_text?: string;
  ai_label_position?: string;
  tts_enabled?: boolean;
  default_tts_engine?: string;
  tts_voice_id?: string;
  bgm_enabled?: boolean;
  default_bgm_engine?: string;
  bgm_style?: string;
  default_stt_engine?: string;
  elevenlabs_api_key?: string;
}

export interface UGCEngineInfo {
  engine: string;
  name: string;
  supports_ugc: boolean;
  requires_api_key: boolean;
  has_api_key: boolean;
}

export interface UGCEnginesResponse {
  engines: UGCEngineInfo[];
  default_engine: string | null;
}

export interface AvatarInfo {
  avatar_id: string;
  name: string;
  preview_url: string | null;
  gender: string | null;
  style: string | null;
}

export interface VoiceInfo {
  voice_id: string;
  name: string;
  language: string;
  gender: string | null;
  preview_url: string | null;
}

export interface AvatarsResponse {
  avatars: AvatarInfo[];
  engine: string;
}

export interface VoicesResponse {
  voices: VoiceInfo[];
  engine: string;
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

export type RepurposeStatus = "PENDING" | "EXTRACTING" | "TRANSCRIBING" | "GENERATING" | "COMPLETED" | "FAILED";
export type ToneStyle = "FORMAL" | "CASUAL" | "FRIENDLY";
export type ContentPlatform = "NAVER_BLOG" | "X_THREAD" | "INSTAGRAM" | "BRUNCH" | "NAVER_POST" | "SHORT_CLIP";

export interface RepurposeJob {
  id: number;
  youtube_url: string;
  video_title: string | null;
  video_duration: number | null;
  status: RepurposeStatus;
  tone_style: ToneStyle;
  target_platforms: string[];
  transcript: string | null;
  summary: string | null;
  key_points: string[] | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepurposeContent {
  id: number;
  job_id: number;
  platform: ContentPlatform;
  content: string;
  content_metadata: Record<string, unknown>;
  created_at: string;
}

export interface RepurposeJobCreate {
  youtube_url: string;
  tone_style?: ToneStyle;
  target_platforms?: ContentPlatform[];
}

// ============ Template Types ============

export type TemplateIndustry = "BEAUTY" | "HEALTH" | "FOOD" | "IT_SAAS" | "FASHION" | "EDUCATION" | "REAL_ESTATE" | "FINANCE" | "TRAVEL" | "PET";
export type TemplatePlatform = "INSTAGRAM" | "FACEBOOK" | "GOOGLE_ADS" | "NAVER" | "TIKTOK";
export type TemplateLayout = "SINGLE_IMAGE" | "CAROUSEL" | "VIDEO_COVER" | "TEXT_OVERLAY" | "SPLIT_VIEW" | "PRODUCT_HERO";

export interface Template {
  id: number;
  name: string;
  description: string;
  industry: TemplateIndustry;
  platform: TemplatePlatform;
  layout: TemplateLayout;
  copy_template: Record<string, string>;
  style_config: Record<string, unknown>;
  preview_url: string | null;
  is_active: boolean;
}

// ============ Brand Kit Types ============

export interface BrandKit {
  id: number;
  user_id: number;
  name: string;
  is_default: boolean;
  logo_url: string | null;
  primary_color: string | null;
  secondary_color: string | null;
  accent_color: string | null;
  font_heading: string | null;
  font_body: string | null;
  tone_of_voice: string | null;
  brand_values: string[];
  target_audience: string | null;
  guidelines: string | null;
  created_at: string;
  updated_at: string;
}

export interface BrandKitCreate {
  name: string;
  is_default?: boolean;
  logo_url?: string;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  font_heading?: string;
  font_body?: string;
  tone_of_voice?: string;
  brand_values?: string[];
  target_audience?: string;
  guidelines?: string;
}

export interface BrandKitUpdate extends Partial<BrandKitCreate> {}

// ============ Publishing Types ============

export type PublishPlatformType = "FACEBOOK" | "INSTAGRAM";
export type PublishStatus = "PENDING" | "PUBLISHING" | "PUBLISHED" | "FAILED";

export interface PublishConnection {
  id: number;
  platform: PublishPlatformType;
  account_id: string | null;
  account_name: string | null;
  page_id: string | null;
  page_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface PublishLog {
  id: number;
  campaign_id: number;
  platform: PublishPlatformType;
  status: PublishStatus;
  external_post_id: string | null;
  external_url: string | null;
  error_message: string | null;
  created_at: string;
}

export interface PublishRequest {
  platform: PublishPlatformType;
  asset_ids?: number[];
  caption?: string;
  targeting?: Record<string, unknown>;
  budget?: Record<string, unknown>;
}

// ============ A/B Testing Types ============

export interface AdVariant {
  id: number;
  campaign_id: number;
  name: string;
  variant_label: string;
  copy_headline: string | null;
  copy_body: string | null;
  copy_cta: string | null;
  image_asset_id: number | null;
  platform: string | null;
  is_control: boolean;
  variant_metadata: Record<string, unknown>;
  created_at: string;
}

export interface AdVariantCreate {
  name: string;
  variant_label?: string;
  copy_headline?: string;
  copy_body?: string;
  copy_cta?: string;
  image_asset_id?: number;
  platform?: string;
  is_control?: boolean;
}

// ============ Team Collaboration Types ============

export type TeamRole = "OWNER" | "ADMIN" | "EDITOR" | "VIEWER";
export type InviteStatus = "PENDING" | "ACCEPTED" | "DECLINED" | "EXPIRED";

export interface TeamMember {
  id: number;
  team_owner_id: number;
  user_id: number | null;
  email: string;
  role: TeamRole;
  invite_status: InviteStatus;
  invited_at: string;
  accepted_at: string | null;
}

export interface TeamMemberCreate {
  email: string;
  role?: TeamRole;
}

export interface TeamMemberUpdate {
  role?: TeamRole;
}

// ============ Ad Performance Types ============

export type AdPerformanceSource = "FACEBOOK" | "INSTAGRAM" | "GOOGLE_ADS" | "MANUAL";

export interface AdPerformance {
  id: number;
  campaign_id: number;
  source: AdPerformanceSource;
  date: string;
  impressions: number;
  clicks: number;
  conversions: number;
  spend_cents: number;
  revenue_cents: number;
  ctr: number | null;
  cpc_cents: number | null;
  cpa_cents: number | null;
  roas: number | null;
  created_at: string;
}

export interface AdPerformanceSummary {
  total_impressions: number;
  total_clicks: number;
  total_conversions: number;
  total_spend_cents: number;
  total_revenue_cents: number;
  avg_ctr: number | null;
  avg_cpc_cents: number | null;
  avg_roas: number | null;
  days_tracked: number;
}

// ============ Public API Key Types ============

export interface ApiKey {
  id: number;
  name: string;
  key_prefix: string;
  scopes: string;
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface ApiKeyCreate {
  name: string;
  scopes?: string;
  expires_in_days?: number | null;
}

export interface ApiKeyCreated {
  id: number;
  name: string;
  key: string;
  key_prefix: string;
  scopes: string;
  expires_at: string | null;
  created_at: string;
}

// ============ Prediction vs Actual Types ============

export interface PredictionComparison {
  id: number;
  campaign_id: number;
  predicted_ctr: number | null;
  predicted_engagement_rate: number | null;
  predicted_conversion_rate: number | null;
  predicted_quality_score: number | null;
  actual_ctr: number | null;
  actual_engagement_rate: number | null;
  actual_conversion_rate: number | null;
  actual_impressions: number | null;
  actual_clicks: number | null;
  actual_conversions: number | null;
  accuracy_score: number | null;
  ctr_deviation: number | null;
  last_synced_at: string | null;
  created_at: string;
}

export interface PredictionAccuracySummary {
  total_campaigns: number;
  avg_accuracy_score: number | null;
  avg_ctr_deviation: number | null;
  best_accuracy_campaign_id: number | null;
  worst_accuracy_campaign_id: number | null;
  prediction_count: number;
}

// ============ Scheduling Types ============

export type ScheduleStatus = "PENDING" | "SCHEDULED" | "PUBLISHING" | "PUBLISHED" | "FAILED" | "CANCELLED";
export type ScheduleRecurrence = "NONE" | "DAILY" | "WEEKLY" | "MONTHLY";

export interface ScheduledPost {
  id: number;
  campaign_id: number;
  platform: string;
  publish_connection_id: number | null;
  scheduled_at: string;
  published_at: string | null;
  status: ScheduleStatus;
  recurrence: ScheduleRecurrence;
  asset_ids: number[];
  copy_text: string | null;
  error: string | null;
  created_at: string;
}

export interface ScheduledPostCreate {
  campaign_id: number;
  platform: string;
  scheduled_at: string;
  publish_connection_id?: number | null;
  recurrence?: ScheduleRecurrence;
  asset_ids?: number[];
  copy_text?: string;
}

export interface ScheduledPostUpdate {
  scheduled_at?: string;
  platform?: string;
  recurrence?: ScheduleRecurrence;
  asset_ids?: number[];
  copy_text?: string;
  status?: ScheduleStatus;
}

export interface CalendarView {
  month: number;
  year: number;
  posts: ScheduledPost[];
  total_scheduled: number;
  total_published: number;
  total_failed: number;
}

// ============ Autopilot Types ============

export type AutopilotCadence = "DAILY" | "WEEKLY" | "MONTHLY";
export type AutopilotRunStatus =
  | "RUNNING"
  | "AWAITING_APPROVAL"
  | "COMPLETED"
  | "FAILED"
  | "EXPIRED"
  | "SKIPPED";

export interface AutopilotRule {
  id: number;
  user_id: number;
  enabled: boolean;
  timezone: string;
  cadence: string;
  days_of_week: number[] | null;
  time_of_day: string;
  next_run_at: string;
  last_run_at: string | null;
  run_count: number;
  consecutive_failures: number;
  last_failure_reason: string | null;
  product_url: string;
  brand_kit_id: number | null;
  platform_targets: string[];
  asset_types: string[];
  num_variations: number;
  auto_publish: boolean;
  publish_connection_ids: number[] | null;
  requires_approval: boolean;
  approval_timeout_hours: number;
  created_at: string;
  updated_at: string;
}

export interface AutopilotRunLog {
  id: number;
  rule_id: number;
  campaign_id: number | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  error: string | null;
  credits_estimated: number;
  credits_used: number;
  retry_count: number;
  publish_status: string | null;
}

export interface AutopilotRuleCreate {
  product_url: string;
  platform_targets?: string[];
  cadence: AutopilotCadence;
  days_of_week?: number[] | null;
  time_of_day?: string;
  timezone?: string;
  num_variations?: number;
  brand_kit_id?: number | null;
  asset_types?: string[];
  requires_approval?: boolean;
  auto_publish?: boolean;
  publish_connection_ids?: number[];
}

export interface AutopilotRuleUpdate {
  platform_targets?: string[];
  cadence?: AutopilotCadence;
  days_of_week?: number[] | null;
  time_of_day?: string;
  timezone?: string;
  num_variations?: number;
  brand_kit_id?: number | null;
  product_url?: string;
  asset_types?: string[];
  auto_publish?: boolean;
  publish_connection_ids?: number[];
  requires_approval?: boolean;
}

export type NotificationType = "AUTOPILOT_COMPLETE" | "AUTOPILOT_FAILED" | "AUTOPILOT_DISABLED" | "CREDITS_LOW" | "APPROVAL_NEEDED" | "PUBLISH_COMPLETE" | "PUBLISH_FAILED";

export interface Notification {
  id: number;
  user_id: number;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// ============ Custom Voice / Avatar Types ============

export type VoiceCloneStatus = "PENDING" | "PROCESSING" | "READY" | "FAILED";

export interface CustomVoice {
  id: number;
  name: string;
  language: string;
  sample_url: string;
  provider: string;
  provider_voice_id: string | null;
  status: VoiceCloneStatus;
  error: string | null;
  created_at: string;
}

export interface CustomVoiceCreate {
  name: string;
  language?: string;
  sample_url: string;
  provider?: string;
}

export interface CustomAvatar {
  id: number;
  name: string;
  provider: string;
  provider_avatar_id: string | null;
  preview_url: string | null;
  photo_url: string;
  status: VoiceCloneStatus;
  error: string | null;
  created_at: string;
}

export interface CustomAvatarCreate {
  name: string;
  provider?: string;
  photo_url: string;
}

// ============ White-Label Types ============

export interface WhiteLabelConfig {
  id: number;
  brand_name: string;
  logo_url: string | null;
  favicon_url: string | null;
  primary_color: string;
  secondary_color: string;
  custom_domain: string | null;
  custom_css: string | null;
  email_from_name: string | null;
  email_from_address: string | null;
  hide_powered_by: boolean;
  is_active: boolean;
  created_at: string;
}

export interface WhiteLabelConfigCreate {
  brand_name: string;
  logo_url?: string | null;
  favicon_url?: string | null;
  primary_color?: string;
  secondary_color?: string;
  custom_domain?: string | null;
  custom_css?: string | null;
  email_from_name?: string | null;
  email_from_address?: string | null;
  hide_powered_by?: boolean;
}

export interface WhiteLabelConfigUpdate {
  brand_name?: string;
  logo_url?: string | null;
  favicon_url?: string | null;
  primary_color?: string;
  secondary_color?: string;
  custom_domain?: string | null;
  custom_css?: string | null;
  email_from_name?: string | null;
  email_from_address?: string | null;
  hide_powered_by?: boolean;
}

// ============ Ad Serving Types ============

export type AdServingStatus = "DRAFT" | "ACTIVE" | "PAUSED" | "EXPIRED" | "ARCHIVED";

export interface AdUnit {
  id: number;
  campaign_id: number;
  name: string;
  embed_code: string | null;
  target_url: string;
  asset_id: number | null;
  status: AdServingStatus;
  starts_at: string | null;
  ends_at: string | null;
  total_impressions: number;
  total_clicks: number;
  daily_impression_cap: number | null;
  daily_click_cap: number | null;
  ctr: number | null;
  created_at: string;
}

export interface AdUnitCreate {
  campaign_id: number;
  name: string;
  target_url: string;
  asset_id?: number | null;
  starts_at?: string | null;
  ends_at?: string | null;
  daily_impression_cap?: number | null;
  daily_click_cap?: number | null;
}

export interface AdUnitUpdate {
  name?: string;
  target_url?: string;
  asset_id?: number | null;
  status?: AdServingStatus;
  starts_at?: string | null;
  ends_at?: string | null;
  daily_impression_cap?: number | null;
  daily_click_cap?: number | null;
}

export interface AdServingStats {
  ad_unit_id: number;
  total_impressions: number;
  total_clicks: number;
  ctr: number | null;
  impressions_today: number;
  clicks_today: number;
}

// ============ Product Photography AI Types ============

export type ProductPhotoStatus = "PENDING" | "REMOVING_BG" | "GENERATING" | "COMPLETED" | "FAILED";
export type ProductPhotoAngle = "FRONT" | "SIDE" | "TOP_DOWN" | "LIFESTYLE" | "MODEL_HOLDING" | "STUDIO";

export interface ProductPhoto {
  id: number;
  user_id: number;
  campaign_id: number | null;
  original_image_url: string;
  bg_removed_url: string | null;
  status: ProductPhotoStatus;
  angles: string[];
  results: Array<{ angle: string; image_url: string }>;
  scene_prompt: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductPhotoCreate {
  original_image_url: string;
  campaign_id?: number | null;
  angles?: ProductPhotoAngle[];
  scene_prompt?: string;
}

// ============ AI Content Labeling Types ============

export type AILabelPosition = "TOP_LEFT" | "TOP_RIGHT" | "BOTTOM_LEFT" | "BOTTOM_RIGHT" | "NONE";

export interface AIDisclosure {
  labeled: boolean;
  label_text: string;
  position: AILabelPosition;
}

// ============ Billing Types ============

export type BillingPeriod = "MONTHLY" | "ANNUAL";
export type PlanTier = "FREE" | "BASIC" | "BYOK" | "PRO" | "ULTRA";

// ============ Provider Registry Types ============

export type ProviderType = "llm" | "image" | "video" | "ugc" | "scraper" | "tts" | "stt" | "bgm";

export interface ProviderCapability {
  name: string;
  description: string;
}

export interface ProviderRegistryItem {
  name: string;
  display_name: string;
  provider_type: ProviderType;
  capabilities: ProviderCapability[];
  requires_key: boolean;
  requires_url: boolean;
  key_placeholder?: string;
  url_placeholder?: string;
  shared_credentials_note?: string;
  shared_credentials_with?: string[];
  is_local: boolean;
  description: string;
  documentation_url?: string;
}

export interface ProviderRegistryResponse {
  providers: ProviderRegistryItem[];
}

export interface ProviderCredentialSummary {
  provider_name: string;
  display_name: string;
  provider_type: ProviderType;
  is_configured: boolean;
  has_key: boolean;
  has_url: boolean;
  last_tested_at?: string;
  last_test_success?: boolean;
}

export interface ProviderCredentialsResponse {
  credentials: ProviderCredentialSummary[];
}

export interface ProviderCredentialCreate {
  provider_name: string;
  credential_key?: string;
  endpoint_url?: string;
}

export type ProviderCredentialTestType = "connection" | "compatibility";

export interface ProviderCredentialTestResult {
  provider_name: string;
  success: boolean;
  message: string;
   test_type?: ProviderCredentialTestType;
}
