// Tipos principales de la aplicación

export interface Company {
  id: number;
  name: string;
  logo_path?: string;
  default_profit_margin: number;
  created_at: string;
  updated_at?: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  client_name?: string;
  location?: string;
  company_id: number;
  profit_margin: number;
  status: 'draft' | 'active' | 'completed' | 'cancelled';
  created_at: string;
  updated_at?: string;
  company?: Company;
}

export interface Budget {
  id: number;
  project_id: number;
  name: string;
  description?: string;
  version: string;
  pdf_path?: string;
  total_amount: number;
  profit_amount: number;
  final_amount: number;
  status: 'draft' | 'approved' | 'rejected';
  created_at: string;
  updated_at?: string;
  project?: Project;
  items?: BudgetItem[];
}

export interface BudgetItem {
  id: number;
  budget_id: number;
  chapter?: string;
  code?: string;
  description: string;
  unit?: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  performance_rate: number;
  labor_cost: number;
  material_cost: number;
  equipment_cost: number;
  indirect_cost: number;
  notes?: string;
  order_index: number;
  labor_percentage: number;
  material_percentage: number;
  equipment_percentage: number;
}

export interface PriceBook {
  id: number;
  name: string;
  description?: string;
  company_id: number;
  is_active: boolean;
  valid_from?: string;
  valid_to?: string;
  created_at: string;
  updated_at?: string;
  company?: Company;
  entries?: PriceEntry[];
}

export interface PriceEntry {
  id: number;
  price_book_id: number;
  code: string;
  description: string;
  unit: string;
  unit_price: number;
  labor_percentage: number;
  material_percentage: number;
  equipment_percentage: number;
  performance_rate: number;
  category?: string;
  notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  price_book?: PriceBook;
}

export interface DashboardMetrics {
  total_projects: number;
  active_budgets: number;
  total_amount: number;
  average_profit_margin: number;
  monthly_trend: Array<{
    month: string;
    total: number;
    count: number;
  }>;
}

export interface PDFUploadResponse {
  message: string;
  budget_id: number;
  items_extracted: number;
  format_detected: string;
  confidence: number;
}

export interface CalculationRequest {
  budget_id: number;
  profit_margin?: number;
  performance_adjustments?: { [key: number]: number };
}

export interface CalculationResult {
  budget_id: number;
  subtotal: number;
  profit_amount: number;
  total_amount: number;
  cost_breakdown: {
    labor_cost: number;
    material_cost: number;
    equipment_cost: number;
    indirect_cost: number;
    profit_amount: number;
    profit_margin: number;
  };
  items_calculated: number;
}

export interface MaterialsAnalysis {
  materials: { [key: string]: MaterialData };
  total_cost: number;
  total_items: number;
}

export interface MaterialData {
  quantity: number;
  unit: string;
  estimated_cost: number;
  items: Array<{
    code: string;
    description: string;
    quantity: number;
    unit_cost: number;
  }>;
}

export interface LaborAnalysis {
  total_labor_cost: number;
  total_estimated_hours: number;
  categories: { [key: string]: CategoryLaborData };
  average_hourly_rate: number;
}

export interface CategoryLaborData {
  labor_cost: number;
  estimated_hours: number;
}

// Tipos para formularios
export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'textarea' | 'date';
  required?: boolean;
  options?: Array<{ value: string | number; label: string }>;
  placeholder?: string;
  rules?: any[];
}

export interface TableColumn {
  title: string;
  dataIndex: string;
  key: string;
  render?: (value: any, record: any) => React.ReactNode;
  sorter?: (a: any, b: any) => number;
  filterDropdown?: any;
  filterIcon?: any;
  onFilter?: (value: any, record: any) => boolean;
}

// Tipos para gráficos
export interface ChartData {
  name: string;
  value: number;
  color?: string;
}

export interface TimeSeriesData {
  date: string;
  value: number;
  category?: string;
}

// Tipos de utilidad
export type Status = 'loading' | 'success' | 'error' | 'idle';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: Status;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
}

// Tipos para filtros y búsqueda
export interface SearchFilters {
  query?: string;
  status?: string;
  dateRange?: [string, string];
  category?: string;
  page?: number;
  limit?: number;
}

// Tipos para notificaciones
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  description?: string;
  duration?: number;
}