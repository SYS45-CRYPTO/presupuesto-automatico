from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Numeric, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    logo_path = Column(String(500))
    default_profit_margin = Column(Numeric(5, 2), default=15.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    projects = relationship("Project", back_populates="company")
    price_books = relationship("PriceBook", back_populates="company")
    cost_settings = relationship("CostSetting", back_populates="company")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company_id = Column(Integer, ForeignKey("companies.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    company = relationship("Company")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    client_name = Column(String(255))
    location = Column(String(500))
    company_id = Column(Integer, ForeignKey("companies.id"))
    profit_margin = Column(Numeric(5, 2), default=15.00)
    status = Column(String(50), default="draft")  # draft, active, completed, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    company = relationship("Company", back_populates="projects")
    budgets = relationship("Budget", back_populates="project")

class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String(255), nullable=False)
    version = Column(String(50), default="1.0")
    description = Column(Text)
    pdf_path = Column(String(500))
    total_amount = Column(Numeric(12, 2), default=0.00)
    profit_amount = Column(Numeric(12, 2), default=0.00)
    final_amount = Column(Numeric(12, 2), default=0.00)
    status = Column(String(50), default="draft")  # draft, approved, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    project = relationship("Project", back_populates="budgets")
    items = relationship("BudgetItem", back_populates="budget")

class BudgetItem(Base):
    __tablename__ = "budget_items"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"))
    chapter = Column(String(100))  # Capítulo o sección
    code = Column(String(50))  # Código de partida
    description = Column(Text, nullable=False)
    unit = Column(String(20))  # Unidad (m2, m3, kg, etc.)
    quantity = Column(Numeric(12, 4), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    performance_rate = Column(Numeric(8, 4), default=1.0000)  # Rendimiento
    labor_cost = Column(Numeric(12, 2), default=0.00)  # Costo de mano de obra
    material_cost = Column(Numeric(12, 2), default=0.00)  # Costo de materiales
    equipment_cost = Column(Numeric(12, 2), default=0.00)  # Costo de equipos
    indirect_cost = Column(Numeric(12, 2), default=0.00)  # Costos indirectos
    notes = Column(Text)
    order_index = Column(Integer, default=0)
    
    # Relaciones
    budget = relationship("Budget", back_populates="items")

class PriceBook(Base):
    __tablename__ = "price_books"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    company_id = Column(Integer, ForeignKey("companies.id"))
    is_active = Column(Boolean, default=True)
    valid_from = Column(Date)
    valid_to = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    company = relationship("Company", back_populates="price_books")
    entries = relationship("PriceEntry", back_populates="price_book")

class PriceEntry(Base):
    __tablename__ = "price_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    price_book_id = Column(Integer, ForeignKey("price_books.id"))
    code = Column(String(50), nullable=False)  # Código de partida
    description = Column(Text, nullable=False)
    unit = Column(String(20), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    labor_percentage = Column(Numeric(5, 2), default=40.00)  # % mano de obra
    material_percentage = Column(Numeric(5, 2), default=50.00)  # % materiales
    equipment_percentage = Column(Numeric(5, 2), default=10.00)  # % equipos
    performance_rate = Column(Numeric(8, 4), default=1.0000)  # Rendimiento
    category = Column(String(100))  # Categoría de trabajo
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    price_book = relationship("PriceBook", back_populates="entries")
    history = relationship("PriceHistory", back_populates="price_entry")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    price_entry_id = Column(Integer, ForeignKey("price_entries.id"))
    previous_price = Column(Numeric(12, 2), nullable=False)
    new_price = Column(Numeric(12, 2), nullable=False)
    change_reason = Column(String(500))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    changed_by = Column(String(255))
    
    # Relaciones
    price_entry = relationship("PriceEntry", back_populates="history")

class PerformanceRate(Base):
    __tablename__ = "performance_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    unit = Column(String(20), nullable=False)
    daily_output = Column(Numeric(8, 4), nullable=False)  # Producción diaria
    crew_size = Column(Integer, default=1)  # Número de operarios
    crew_composition = Column(JSON)  # Composición de cuadrilla
    difficulty_factor = Column(Numeric(5, 4), default=1.0000)  # Factor de dificultad
    conditions = Column(Text)  # Condiciones de trabajo
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CostSetting(Base):
    __tablename__ = "cost_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    setting_type = Column(String(50), nullable=False)  # transport, tools, machinery, others
    name = Column(String(255), nullable=False)
    description = Column(Text)
    percentage = Column(Numeric(5, 2), default=0.00)  # Porcentaje sobre costo directo
    fixed_amount = Column(Numeric(12, 2), default=0.00)  # Monto fijo
    calculation_method = Column(String(50), default="percentage")  # percentage, fixed
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    company = relationship("Company", back_populates="cost_settings")