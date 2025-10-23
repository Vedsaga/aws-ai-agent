// Comprehensive API Types for Multi-Agent Orchestration System

// ==================== Common Types ====================

export type JobStatus =
  | 'pending'
  | 'processing'
  | 'accepted'
  | 'completed'
  | 'failed'
  | 'cancelled';

export type Priority = 'low' | 'normal' | 'high' | 'urgent';

export type ConfigType =
  | 'domain'
  | 'agent'
  | 'playbook'
  | 'dependency_graph'
  | 'template';

// ==================== Ingest API Types ====================

export interface IngestRequest {
  domain_id: string;
  text: string;
  images?: string[];
  source?: string;
  priority?: Priority;
  reporter_contact?: string;
}

export interface IngestResponse {
  job_id: string;
  status: JobStatus;
  message: string;
  timestamp: string;
  estimated_completion_seconds?: number;
}

export interface IncidentRecord {
  incident_id: string;
  job_id: string;
  tenant_id: string;
  domain_id: string;
  raw_text: string;
  status: JobStatus;
  created_at: string;
  created_by: string;
  source: string;
  priority: Priority;
  images?: string[];
  reporter_contact?: string;
  structured_data?: StructuredIncidentData;
  location?: GeoLocation;
  category?: string;
  timestamp?: string;
  confidence?: number;
}

export interface StructuredIncidentData {
  processing_status: string;
  agents_executed: string[];
  entities?: Record<string, any>;
  temporal_info?: TemporalInfo;
  geo_info?: GeoInfo;
  category_info?: CategoryInfo;
  [key: string]: any;
}

export interface TemporalInfo {
  detected_time?: string;
  time_range?: {
    start?: string;
    end?: string;
  };
  relative_time?: string;
  confidence?: number;
}

export interface GeoInfo {
  address?: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
  place_id?: string;
  confidence?: number;
  location_type?: string;
}

export interface CategoryInfo {
  primary_category?: string;
  sub_categories?: string[];
  tags?: string[];
  confidence?: number;
}

// ==================== Query API Types ====================

export interface QueryRequest {
  domain_id: string;
  question: string;
  filters?: QueryFilters;
  include_visualizations?: boolean;
}

export interface QueryFilters {
  date_range?: {
    start?: string;
    end?: string;
  };
  location?: {
    latitude: number;
    longitude: number;
    radius_km?: number;
  };
  category?: string[];
  priority?: Priority[];
  status?: JobStatus[];
  [key: string]: any;
}

export interface QueryResponse {
  job_id: string;
  status: JobStatus;
  message: string;
  timestamp: string;
  estimated_completion_seconds?: number;
}

export interface QueryResult {
  job_id: string;
  tenant_id: string;
  domain_id: string;
  question: string;
  status: JobStatus;
  created_at: string;
  created_by: string;
  filters?: QueryFilters;
  include_visualizations?: boolean;
  agent_results: Record<string, AgentResult>;
  summary: string;
  answer?: string;
  visualizations?: Visualization[];
  data?: any[];
  metadata?: QueryMetadata;
}

export interface AgentResult {
  agent_name: string;
  status: JobStatus;
  output: string;
  structured_data?: any;
  confidence?: number;
  execution_time_ms?: number;
  error?: string;
}

export interface QueryMetadata {
  total_results: number;
  execution_time_ms: number;
  agents_used: string[];
  data_sources: string[];
}

// ==================== Status Polling Types ====================

export interface StatusUpdate {
  job_id: string;
  status: JobStatus;
  progress: number;
  message: string;
  timestamp: string;
  current_step?: string;
  agent_updates?: AgentStatusUpdate[];
  result?: any;
  error?: string;
}

export interface AgentStatusUpdate {
  agent_name: string;
  status: JobStatus;
  progress: number;
  message: string;
  timestamp: string;
  output?: string;
  error?: string;
}

// ==================== Config API Types ====================

export interface ConfigRequest {
  type: ConfigType;
  config: DomainConfig | AgentConfig | PlaybookConfig | any;
}

export interface ConfigResponse {
  configs: ConfigItem[];
  count: number;
}

export interface ConfigItem {
  config_id: string;
  tenant_id: string;
  config_type: ConfigType;
  name: string;
  description?: string;
  config: any;
  version: number;
  is_active: boolean;
  created_at: string;
  created_by: string;
  updated_at?: string;
  updated_by?: string;
  created_by_me?: boolean;
  tags?: string[];
}

export interface DomainConfig {
  domain_id: string;
  name: string;
  description: string;
  icon?: string;
  color?: string;
  ingest_agents: string[];
  query_agents: string[];
  tools?: string[];
  settings?: DomainSettings;
  examples?: DomainExample[];
}

export interface DomainSettings {
  max_parallel_agents?: number;
  timeout_seconds?: number;
  enable_caching?: boolean;
  require_approval?: boolean;
  [key: string]: any;
}

export interface DomainExample {
  type: 'ingest' | 'query';
  text: string;
  description?: string;
}

export interface AgentConfig {
  agent_id: string;
  name: string;
  description: string;
  agent_type: 'ingestion' | 'query' | 'custom';
  model?: string;
  prompt_template?: string;
  tools?: string[];
  parameters?: Record<string, any>;
  validation_rules?: ValidationRule[];
  output_schema?: any;
}

// Alias for backward compatibility
export type Agent = AgentConfig;

export interface ValidationRule {
  field: string;
  rule: string;
  message?: string;
}

export interface PlaybookConfig {
  playbook_id: string;
  name: string;
  description: string;
  domain_id: string;
  steps: PlaybookStep[];
  triggers?: PlaybookTrigger[];
}

export interface PlaybookStep {
  step_id: string;
  agent_id: string;
  depends_on?: string[];
  condition?: string;
  parameters?: Record<string, any>;
}

export interface PlaybookTrigger {
  type: 'schedule' | 'event' | 'manual';
  config: any;
}

// ==================== Data API Types ====================

export interface DataRequest {
  type?: 'incidents' | 'queries' | 'agents' | 'tools';
  filters?: DataFilters;
  pagination?: PaginationParams;
  sort?: SortParams;
}

export interface DataFilters {
  domain_id?: string;
  status?: JobStatus[];
  date_range?: {
    start: string;
    end: string;
  };
  search?: string;
  [key: string]: any;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface SortParams {
  field: string;
  order: 'asc' | 'desc';
}

export interface DataResponse<T = any> {
  data: T[];
  total: number;
  page?: number;
  limit?: number;
  has_more?: boolean;
}

// ==================== GeoJSON and Map Types ====================

export interface GeoLocation {
  type: 'Point' | 'Polygon' | 'LineString';
  coordinates: number[] | number[][] | number[][][];
  properties?: Record<string, any>;
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: 'Point' | 'Polygon' | 'LineString' | 'MultiPoint' | 'MultiPolygon';
    coordinates: any;
  };
  properties: {
    id?: string;
    name?: string;
    description?: string;
    category?: string;
    status?: string;
    timestamp?: string;
    [key: string]: any;
  };
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

// ==================== Visualization Types ====================

export interface Visualization {
  type: 'chart' | 'map' | 'table' | 'timeline' | 'heatmap';
  title?: string;
  description?: string;
  data: any;
  config?: VisualizationConfig;
}

export interface VisualizationConfig {
  chart_type?: 'bar' | 'line' | 'pie' | 'scatter';
  x_axis?: string;
  y_axis?: string;
  color_by?: string;
  [key: string]: any;
}

// ==================== Error Types ====================

export interface ApiError {
  error: string;
  error_code?: string;
  timestamp: string;
  details?: any;
}

// ==================== Tool Registry Types ====================

export interface ToolConfig {
  tool_id: string;
  name: string;
  description: string;
  tool_type: 'api' | 'function' | 'database' | 'external';
  parameters?: ToolParameter[];
  endpoint?: string;
  authentication?: ToolAuth;
}

export interface ToolParameter {
  name: string;
  type: string;
  required: boolean;
  description?: string;
  default?: any;
}

export interface ToolAuth {
  type: 'none' | 'api_key' | 'oauth' | 'basic';
  config?: Record<string, any>;
}

// ==================== Realtime (AppSync) Types ====================

export interface RealtimeStatusUpdate {
  job_id: string;
  status: JobStatus;
  progress: number;
  message: string;
  timestamp: string;
  agent_name?: string;
  step?: string;
  data?: any;
}

export interface AppSyncSubscriptionData {
  onStatusUpdate: RealtimeStatusUpdate;
}

// ==================== Batch Operations ====================

export interface BatchRequest {
  operations: BatchOperation[];
}

export interface BatchOperation {
  operation_id: string;
  type: 'ingest' | 'query' | 'config';
  data: any;
}

export interface BatchResponse {
  results: BatchResult[];
  total: number;
  succeeded: number;
  failed: number;
}

export interface BatchResult {
  operation_id: string;
  status: 'success' | 'failure';
  data?: any;
  error?: string;
}

// ==================== Chat/Message Types ====================

export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    job_id?: string;
    agent?: string;
    confidence?: number;
    [key: string]: any;
  };
  attachments?: ChatAttachment[];
}

export interface ChatAttachment {
  type: 'image' | 'file' | 'location' | 'data';
  url?: string;
  name?: string;
  data?: any;
}

export interface ChatHistory {
  session_id: string;
  domain_id: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

// ==================== Analytics Types ====================

export interface AnalyticsMetrics {
  total_incidents: number;
  total_queries: number;
  avg_resolution_time_seconds: number;
  success_rate: number;
  active_jobs: number;
  failed_jobs: number;
  by_category?: Record<string, number>;
  by_status?: Record<string, number>;
  by_priority?: Record<string, number>;
  timeline?: TimelineData[];
}

export interface TimelineData {
  timestamp: string;
  value: number;
  label?: string;
}

// ==================== User Preferences ====================

export interface UserPreferences {
  theme?: 'light' | 'dark' | 'auto';
  default_domain?: string;
  map_style?: string;
  notification_settings?: NotificationSettings;
  display_settings?: DisplaySettings;
}

export interface NotificationSettings {
  email_notifications: boolean;
  push_notifications: boolean;
  status_updates: boolean;
  daily_summary: boolean;
}

export interface DisplaySettings {
  show_confidence_scores: boolean;
  show_agent_details: boolean;
  compact_mode: boolean;
  auto_refresh: boolean;
  refresh_interval_seconds: number;
}
