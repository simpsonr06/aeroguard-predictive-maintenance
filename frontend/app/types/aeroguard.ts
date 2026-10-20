export interface HealthResponse {
  status: string
  model_loaded: boolean
  preprocessor_loaded: boolean
  dataset_loaded: boolean
  dataset_name: string
  n_train_engines: number
  n_test_engines: number
  production_model_name: string
}

export interface RulBin {
  bin_start: number
  bin_end: number
  count: number
  label?: string
}

export interface TopCriticalEngine {
  engine_id: number
  cycle: number
  pred_rul: number
  true_rul?: number
  health_status: string
  priority: string
  action_recommendation: string
}

export interface PriorityEngineItem {
  engine_id: number
  last_cycle: number
  predicted_rul: number
  status: 'critical' | 'warning' | 'healthy' | string
  action: string
}

export interface FleetSummaryResponse {
  total_engines: number
  healthy_count: number
  warning_count: number
  critical_count: number
  mean_predicted_rul: number
  min_predicted_rul: number
  max_predicted_rul: number
  critical_threshold: number
  warning_threshold: number
  rul_distribution: RulBin[]
  top_critical_engines: TopCriticalEngine[]
  engine_count?: number
  total_cycles?: number
  rul_stats?: {
    mean: number
    std: number
    median: number
  }
  histogram?: RulBin[]
  min_cycles?: number
  max_cycles?: number
  avg_trajectory_length?: number
  priority_engines?: PriorityEngineItem[]
}

export interface EngineItem {
  engine_id: number
  total_observations: number
  predicted_rul: number
  status: string
  priority: string
}

export interface EngineListResponse {
  engines: EngineItem[]
  dataset: string
  count: number
}

export interface EngineDetailResponse {
  engine_id: number
  fleet_type: string
  total_logged_cycles: number
  cutoff_cycle: number
  max_cycle: number
  min_cycle: number
  pred_rul: number
  raw_pred_rul: number
  true_rul?: number | null
  prediction_error?: number | null
  health_status: string
  priority: string
  action_recommendation: string
  rationale: string
  observations: Record<string, any>[]
  sensor_descriptions: Record<string, { name: string; unit: string; desc: string }>
  prediction?: {
    predicted_rul: number
    status: string
    priority?: string
  }
}

export interface PredictionRequest {
  engine_id: number
  cutoff_cycle?: number
  dataset?: 'test' | 'train'
  fleet_type?: string
}

export interface PredictionResponse {
  engine_id: number
  cutoff_cycle: number
  total_available_cycles: number
  pred_rul: number
  predicted_rul: number
  raw_pred_rul: number
  clipping_policy: string
  target_clipped?: boolean
  true_rul?: number | null
  prediction_error?: number | null
  health_status: string
  status: string
  priority: string
  action_recommendation: string
  action: string
  rationale: string
  reason: string
  model_name: string
  model?: string
  features_summary?: {
    feature_count: number
    top_features: Record<string, number>
  }
}

export interface SensorItem {
  channel: string
  id: string
  name: string
  unit: string
  desc: string
  description: string
  is_constant: boolean
  is_invariant: boolean
  status: string
}

export interface DegradingSensorTrend {
  id: string
  name: string
  direction: 'upward' | 'downward' | string
  correlation_with_cycle: number
}

export interface SensorsSummaryResponse {
  sensors: SensorItem[]
  invariant_channels: string[]
  informative_channels: string[]
  pruning_rationale: string
  total_sensors?: number
  informative_count?: number
  invariant_count?: number
  top_degrading_sensors?: DegradingSensorTrend[]
}

export interface ModelMetricsResponse {
  selected_model: string
  best_model: string
  official_test_metrics: Record<string, Record<string, any>>
  cutoff_cv_metrics: Record<string, Record<string, any>>
  full_trajectory_cv_metrics: Record<string, Record<string, any>>
  failure_point_cv_metrics: Record<string, Record<string, any>>
  evaluation_regimes_info?: Record<string, string>
}

export interface MaintenanceItem {
  engine_id: number
  cycle: number
  pred_rul: number
  predicted_rul: number
  priority: string
  health_status: string
  status: string
  action_recommendation: string
  action: string
  rationale: string
  reason: string
  true_rul?: number | null
  prediction_error?: number | null
}

export type MaintenanceQueueResponse = MaintenanceItem[]
