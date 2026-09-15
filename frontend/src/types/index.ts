export interface FieldT {
  id: string;
  name: string;
  crop_type: string;
  width_m: number;
  length_m: number;
  row_spacing_m: number;
  row_direction_deg: number;
  configuration: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DetectionT {
  id: string;
  inspection_id: string;
  class_id: number;
  class_name: string;
  target_type: string;
  confidence: number;
  x1: number; y1: number; x2: number; y2: number;
  centroid_x: number; centroid_y: number;
  field_x: number | null;
  field_y: number | null;
  localization_confidence: string;
  localization_method: string;
}

export interface InspectionT {
  id: string;
  session_id: string | null;
  field_id: string;
  source_type: string;
  original_filename: string;
  original_asset_path: string;
  annotated_asset_path: string;
  model_name: string;
  model_version: string;
  detection_mode: string;
  status: string;
  detection_count: number;
  processing_time_ms: number;
  error_message: string | null;
  created_at: string;
  detections?: DetectionT[];
}

export interface TargetT {
  id: string;
  detection_id: string;
  field_id: string;
  status: string;
  priority_score: number;
  priority_explanation: string;
  notes: string;
  operator_approved: boolean;
  created_at: string;
  selected_at: string | null;
  completed_at: string | null;
  detection: DetectionT;
}

export interface RoverStatusT {
  id?: string | null;
  field_id?: string | null;
  status: string;
  position_x: number;
  position_y: number;
  heading_deg: number;
  speed_mps: number;
  safety_state: string;
  current_target_id: string | null;
  mode: string;
  message?: string | null;
}

export interface RoverEventT {
  id: string;
  event_type: string;
  payload: Record<string, any>;
  timestamp: string;
}

export interface ModelStatusT {
  backend: string;
  installed: boolean;
  loaded: boolean;
  is_generic_demo: boolean;
  model_path: string;
  model_filename: string;
  model_format: string;
  task: string;
  version: string;
  device: string;
  error: string | null;
  label: string;
  warning: string | null;
}

export interface AnalyticsSummaryT {
  total_inspections: number;
  total_detections: number;
  detections_by_target_type: Record<string, number>;
  average_confidence: number | null;
  average_inference_time_ms: number | null;
  total_targets: number;
  pending_targets: number;
  completed_interventions: number;
  target_status_distribution: Record<string, number>;
  last_inspection_at: string | null;
}
