from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal

# Schemas base
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

# Company schemas
class CompanyBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    default_profit_margin: Decimal = Field(default=15.00, ge=0, le=100)

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    default_profit_margin: Optional[Decimal] = Field(None, ge=0, le=100)

class Company(CompanyBase):
    id: int
    logo_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

# Project schemas
class ProjectBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    client_name: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=500)
    profit_margin: Decimal = Field(default=15.00, ge=0, le=100)

class ProjectCreate(ProjectBase):
    company_id: int

class ProjectUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    client_name: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=500)
    profit_margin: Optional[Decimal] = Field(None, ge=0, le=100)
    status: Optional[str] = Field(None, regex="^(draft|active|completed|cancelled)$")

class Project(ProjectBase):
    id: int
    company_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# Budget schemas
class BudgetBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    version: str = Field(default="1.0")

class BudgetCreate(BudgetBase):
    project_id: int

class BudgetUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, regex="^(draft|approved|rejected)$")

class Budget(BudgetBase):
    id: int
    project_id: int
    pdf_path: Optional[str] = None
    total_amount: Decimal
    profit_amount: Decimal
    final_amount: Decimal
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# BudgetItem schemas
class BudgetItemBase(BaseSchema):
    chapter: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    description: str = Field(..., min_length=1)
    unit: Optional[str] = Field(None, max_length=20)
    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    performance_rate: Decimal = Field(default=1.0000, gt=0)
    notes: Optional[str] = None

class BudgetItemCreate(BudgetItemBase):
    budget_id: int

class BudgetItemUpdate(BaseSchema):
    chapter: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, min_length=1)
    unit: Optional[str] = Field(None, max_length=20)
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, gt=0)
    performance_rate: Optional[Decimal] = Field(None, gt=0)
    notes: Optional[str] = None

class BudgetItem(BudgetItemBase):
    id: int
    budget_id: int
    total_price: Decimal
    labor_cost: Decimal
    material_cost: Decimal
    equipment_cost: Decimal
    indirect_cost: Decimal
    order_index: int

    @validator('total_price', 'labor_cost', 'material_cost', 'equipment_cost', 'indirect_cost', pre=True, always=True)
    def round_decimals(cls, v):
        if v is not None:
            return round(Decimal(str(v)), 2)
        return v

# PriceBook schemas
class PriceBookBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class PriceBookCreate(PriceBookBase):
    company_id: int

class PriceBookUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None

class PriceBook(PriceBookBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# PriceEntry schemas
class PriceEntryBase(BaseSchema):
    code: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    unit: str = Field(..., max_length=20)
    unit_price: Decimal = Field(..., gt=0)
    labor_percentage: Decimal = Field(default=40.00, ge=0, le=100)
    material_percentage: Decimal = Field(default=50.00, ge=0, le=100)
    equipment_percentage: Decimal = Field(default=10.00, ge=0, le=100)
    performance_rate: Decimal = Field(default=1.0000, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_active: bool = True

class PriceEntryCreate(PriceEntryBase):
    price_book_id: int

class PriceEntryUpdate(BaseSchema):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1)
    unit: Optional[str] = Field(None, max_length=20)
    unit_price: Optional[Decimal] = Field(None, gt=0)
    labor_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    material_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    equipment_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    performance_rate: Optional[Decimal] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class PriceEntry(PriceEntryBase):
    id: int
    price_book_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

# PDF Processing schemas
class PDFUploadResponse(BaseSchema):
    filename: str
    extracted_data: Dict[str, Any]
    items_found: int
    processing_time: float

class PDFExtractionRequest(BaseSchema):
    file_path: str
    format_type: Optional[str] = None

# Calculator schemas
class CalculationRequest(BaseSchema):
    budget_id: int
    profit_margin: Optional[Decimal] = None
    performance_adjustments: Optional[Dict[int, Decimal]] = None  # item_id -> new_performance_rate

class CalculationResult(BaseSchema):
    budget_id: int
    subtotal: Decimal
    profit_amount: Decimal
    total_amount: Decimal
    cost_breakdown: Dict[str, Decimal]
    items_calculated: int

# Dashboard schemas
class DashboardMetrics(BaseSchema):
    total_projects: int
    active_budgets: int
    total_amount: Decimal
    average_profit_margin: Decimal
    monthly_trend: List[Dict[str, Any]]

class PriceComparison(BaseSchema):
    item_description: str
    current_price: Decimal
    previous_price: Decimal
    price_change: Decimal
    change_percentage: Decimal

# Export schemas
class ExportRequest(BaseSchema):
    budget_id: int
    format: str = Field(..., regex="^(pdf|excel|csv)$")
    include_logo: bool = True
    template: Optional[str] = None