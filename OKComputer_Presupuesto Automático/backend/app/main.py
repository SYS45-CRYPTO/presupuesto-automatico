from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import shutil
from pathlib import Path
from datetime import datetime
import logging

# Importar modelos y esquemas
from .models.database import engine, Base, get_db
from .models.models import *
from .models.schemas import *

# Importar servicios
from .pdf_processor import PDFReader, OCRProcessor, DataExtractor, FormatDetector
from .price_book import PriceBookImporter, PriceService, HistoryTracker
from .calculator import BudgetCalculator, PerformanceService, ProfitService, CostCalculator
from .document_generator import PDFGenerator, ExcelExporter, CSVExporter, TemplateManager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear tablas de base de datos
Base.metadata.create_all(bind=engine)

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Automatización de Presupuestos de Obra",
    description="API para gestión completa de presupuestos de construcción",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Orígenes permitidos para React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directorios de archivos
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Rutas de la API
@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema de Automatización de Presupuestos de Obra",
        "version": "1.0.0",
        "status": "operational"
    }

# ===== ENDPOINTS DE COMPAÑÍAS =====

@app.post("/companies/", response_model=Company)
async def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """Crea una nueva compañía"""
    try:
        db_company = Company(**company.dict())
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        return db_company
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/companies/", response_model=List[Company])
async def get_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtiene todas las compañías"""
    companies = db.query(Company).offset(skip).limit(limit).all()
    return companies

@app.get("/companies/{company_id}", response_model=Company)
async def get_company(company_id: int, db: Session = Depends(get_db)):
    """Obtiene una compañía por ID"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Compañía no encontrada")
    return company

# ===== ENDPOINTS DE PROYECTOS =====

@app.post("/projects/", response_model=Project)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Crea un nuevo proyecto"""
    try:
        db_project = Project(**project.dict())
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/projects/", response_model=List[Project])
async def get_projects(company_id: Optional[int] = None, skip: int = 0, limit: int = 100, 
                      db: Session = Depends(get_db)):
    """Obtiene todos los proyectos, opcionalmente filtrados por compañía"""
    query = db.query(Project)
    if company_id:
        query = query.filter(Project.company_id == company_id)
    projects = query.offset(skip).limit(limit).all()
    return projects

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Obtiene un proyecto por ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project

# ===== ENDPOINTS DE PRESUPUESTOS =====

@app.post("/budgets/", response_model=Budget)
async def create_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    """Crea un nuevo presupuesto"""
    try:
        db_budget = Budget(**budget.dict())
        db.add(db_budget)
        db.commit()
        db.refresh(db_budget)
        return db_budget
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/budgets/", response_model=List[Budget])
async def get_budgets(project_id: Optional[int] = None, skip: int = 0, limit: int = 100,
                     db: Session = Depends(get_db)):
    """Obtiene todos los presupuestos, opcionalmente filtrados por proyecto"""
    query = db.query(Budget)
    if project_id:
        query = query.filter(Budget.project_id == project_id)
    budgets = query.offset(skip).limit(limit).all()
    return budgets

@app.get("/budgets/{budget_id}", response_model=Budget)
async def get_budget(budget_id: int, db: Session = Depends(get_db)):
    """Obtiene un presupuesto por ID"""
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return budget

# ===== ENDPOINTS DE PROCESAMIENTO DE PDFS =====

@app.post("/pdf/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Sube y procesa un archivo PDF de presupuesto"""
    try:
        # Validar archivo
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
        
        # Guardar archivo
        file_path = UPLOAD_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Procesar PDF
        pdf_reader = PDFReader()
        ocr_processor = OCRProcessor()
        data_extractor = DataExtractor()
        format_detector = FormatDetector()
        
        # Leer PDF
        pdf_data = pdf_reader.read_pdf(str(file_path))
        
        # Aplicar OCR si es necesario
        if pdf_data['is_scanned']:
            # Convertir páginas a imágenes y aplicar OCR
            # Nota: En producción, usar pdf2image
            ocr_result = {"text": "Contenido extraído con OCR", "confidence": 0.85}
            pdf_data['extracted_text'] = ocr_result['text']
        
        # Detectar formato
        format_analysis = format_detector.detect_format(pdf_data['extracted_text'])
        
        # Extraer partidas
        budget_items = data_extractor.extract_budget_items(
            pdf_data['extracted_text'], 
            format_analysis['detected_format']
        )
        
        # Crear presupuesto
        budget_name = f"Presupuesto extraído - {file.filename}"
        budget = BudgetCreate(
            project_id=project_id,
            name=budget_name,
            description=f"Presupuesto extraído automáticamente de {file.filename}",
            version="1.0"
        )
        
        db_budget = Budget(**budget.dict())
        db.add(db_budget)
        db.commit()
        db.refresh(db_budget)
        
        # Crear items del presupuesto
        for item_data in budget_items:
            budget_item = BudgetItem(
                budget_id=db_budget.id,
                chapter=item_data.get('chapter', ''),
                code=item_data.get('code', ''),
                description=item_data.get('description', ''),
                unit=item_data.get('unit', ''),
                quantity=Decimal(str(item_data.get('quantity', 0))),
                unit_price=Decimal(str(item_data.get('unit_price', 0))),
                total_price=Decimal(str(item_data.get('total_price', 0))),
                performance_rate=Decimal('1.0')
            )
            db.add(budget_item)
        
        db.commit()
        
        return {
            "message": "PDF procesado exitosamente",
            "budget_id": db_budget.id,
            "items_extracted": len(budget_items),
            "format_detected": format_analysis['format_name'],
            "confidence": format_analysis['confidence']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS DE CÁLCULOS =====

@app.post("/budgets/{budget_id}/calculate")
async def calculate_budget(
    budget_id: int,
    calculation_request: CalculationRequest,
    db: Session = Depends(get_db)
):
    """Calcula el presupuesto con rendimientos y beneficios"""
    try:
        calculator = BudgetCalculator(db)
        result = calculator.calculate_budget(calculation_request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/budgets/{budget_id}/simulate")
async def simulate_budget(
    budget_id: int,
    profit_margin: Optional[float] = None,
    performance_adjustments: Optional[Dict[str, float]] = None,
    db: Session = Depends(get_db)
):
    """Realiza una simulación de cálculo sin guardar cambios"""
    try:
        calculator = BudgetCalculator(db)
        result = calculator.calculate_simulation(
            budget_id=budget_id,
            profit_margin=Decimal(str(profit_margin)) if profit_margin else None,
            performance_adjustments=performance_adjustments
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS DE LIBROS DE PRECIOS =====

@app.post("/price-books/", response_model=PriceBook)
async def create_price_book(price_book: PriceBookCreate, db: Session = Depends(get_db)):
    """Crea un nuevo libro de precios"""
    try:
        db_price_book = PriceBook(**price_book.dict())
        db.add(db_price_book)
        db.commit()
        db.refresh(db_price_book)
        return db_price_book
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/price-books/", response_model=List[PriceBook])
async def get_price_books(company_id: Optional[int] = None, active_only: bool = True,
                         skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtiene todos los libros de precios"""
    query = db.query(PriceBook)
    if company_id:
        query = query.filter(PriceBook.company_id == company_id)
    if active_only:
        query = query.filter(PriceBook.is_active == True)
    price_books = query.offset(skip).limit(limit).all()
    return price_books

@app.post("/price-books/{price_book_id}/import")
async def import_price_book(
    price_book_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Importa precios desde archivo Excel/CSV"""
    try:
        # Validar archivo
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
        
        # Guardar archivo
        file_path = UPLOAD_DIR / f"price_book_{price_book_id}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Importar precios
        importer = PriceBookImporter()
        result = importer.import_from_file(str(file_path), price_book_id)
        
        if result['success']:
            # Crear entradas en la base de datos
            price_service = PriceService(db)
            price_service.batch_create_price_entries(result['entries'])
            
            return {
                "message": "Precios importados exitosamente",
                "entries_created": len(result['entries']),
                "stats": result['stats']
            }
        else:
            raise HTTPException(status_code=400, detail=result.get('errors', 'Error en importación'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS DE EXPORTACIÓN =====

@app.post("/budgets/{budget_id}/export/pdf")
async def export_budget_pdf(
    budget_id: int,
    include_logo: bool = True,
    template: str = "standard",
    db: Session = Depends(get_db)
):
    """Exporta un presupuesto a PDF"""
    try:
        # Obtener datos del presupuesto
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        # Preparar datos para exportación
        budget_data = {
            "id": budget.id,
            "name": budget.name,
            "version": budget.version,
            "final_amount": budget.final_amount,
            "profit_amount": budget.profit_amount,
            "total_amount": budget.total_amount,
            "project": {
                "name": budget.project.name,
                "client_name": budget.project.client_name,
                "location": budget.project.location
            },
            "company": {
                "name": budget.project.company.name,
                "logo_path": budget.project.company.logo_path
            },
            "items": [
                {
                    "id": item.id,
                    "chapter": item.chapter,
                    "code": item.code,
                    "description": item.description,
                    "unit": item.unit,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "labor_percentage": item.labor_percentage,
                    "material_percentage": item.material_percentage,
                    "equipment_percentage": item.equipment_percentage
                }
                for item in budget.items
            ],
            "cost_breakdown": {
                "labor_cost": sum(item.total_price * item.labor_percentage / 100 for item in budget.items),
                "material_cost": sum(item.total_price * item.material_percentage / 100 for item in budget.items),
                "equipment_cost": sum(item.total_price * item.equipment_percentage / 100 for item in budget.items),
                "indirect_cost": budget.total_amount * 0.1,  # Ejemplo
                "profit_amount": budget.profit_amount
            }
        }
        
        # Generar PDF
        output_path = OUTPUT_DIR / f"budget_{budget_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_generator = PDFGenerator()
        
        success = pdf_generator.generate_budget_pdf(
            budget_data=budget_data,
            output_path=str(output_path),
            include_logo=include_logo,
            template=template
        )
        
        if success:
            return FileResponse(
                path=str(output_path),
                filename=f"presupuesto_{budget.name}.pdf",
                media_type='application/pdf'
            )
        else:
            raise HTTPException(status_code=500, detail="Error generando PDF")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/budgets/{budget_id}/export/excel")
async def export_budget_excel(
    budget_id: int,
    include_charts: bool = True,
    db: Session = Depends(get_db)
):
    """Exporta un presupuesto a Excel"""
    try:
        # Obtener datos del presupuesto
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        # Preparar datos (similar a PDF)
        budget_data = {
            "id": budget.id,
            "name": budget.name,
            "final_amount": budget.final_amount,
            "profit_amount": budget.profit_amount,
            "total_amount": budget.total_amount,
            "project": {
                "name": budget.project.name,
                "client_name": budget.project.client_name,
                "location": budget.project.location
            },
            "items": [
                {
                    "chapter": item.chapter,
                    "code": item.code,
                    "description": item.description,
                    "unit": item.unit,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                }
                for item in budget.items
            ]
        }
        
        # Generar Excel
        output_path = OUTPUT_DIR / f"budget_{budget_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        excel_exporter = ExcelExporter()
        
        success = excel_exporter.export_budget_to_excel(
            budget_data=budget_data,
            output_path=str(output_path),
            include_charts=include_charts
        )
        
        if success:
            return FileResponse(
                path=str(output_path),
                filename=f"presupuesto_{budget.name}.xlsx",
                media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            raise HTTPException(status_code=500, detail="Error generando Excel")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS DE DASHBOARD =====

@app.get("/dashboard/metrics")
async def get_dashboard_metrics(company_id: Optional[int] = None, 
                              db: Session = Depends(get_db)):
    """Obtiene métricas para el dashboard"""
    try:
        # Query base
        query = db.query(Budget)
        if company_id:
            query = query.join(Project).filter(Project.company_id == company_id)
        
        budgets = query.all()
        
        # Calcular métricas
        total_projects = len(set(budget.project_id for budget in budgets))
        active_budgets = len([b for b in budgets if b.status == 'active'])
        total_amount = sum(budget.final_amount for budget in budgets)
        
        # Calcular margen de beneficio promedio
        if budgets:
            avg_profit_margin = sum(
                (b.profit_amount / b.total_amount * 100) 
                for b in budgets if b.total_amount > 0
            ) / len(budgets)
        else:
            avg_profit_margin = 0
        
        # Tendencia mensual (simplificada)
        monthly_trend = []
        for month in range(6):
            month_date = datetime.now().replace(day=1) - pd.DateOffset(months=month)
            month_budgets = [b for b in budgets if b.created_at.month == month_date.month]
            monthly_trend.append({
                "month": month_date.strftime("%Y-%m"),
                "total": sum(b.final_amount for b in month_budgets),
                "count": len(month_budgets)
            })
        
        return {
            "total_projects": total_projects,
            "active_budgets": active_budgets,
            "total_amount": total_amount,
            "average_profit_margin": avg_profit_margin,
            "monthly_trend": monthly_trend
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== ENDPOINTS DE ANÁLISIS =====

@app.get("/budgets/{budget_id}/analysis/materials")
async def get_materials_analysis(budget_id: int, db: Session = Depends(get_db)):
    """Obtiene análisis de materiales para un presupuesto"""
    try:
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        calculator = BudgetCalculator(db)
        materials_analysis = calculator.calculate_material_list(budget_id)
        
        return materials_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/budgets/{budget_id}/analysis/labor")
async def get_labor_analysis(budget_id: int, db: Session = Depends(get_db)):
    """Obtiene análisis de mano de obra para un presupuesto"""
    try:
        budget = db.query(Budget).filter(Budget.id == budget_id).first()
        if not budget:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        calculator = BudgetCalculator(db)
        labor_analysis = calculator.calculate_labor_hours(budget_id)
        
        return labor_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check
@app.get("/health")
async def health_check():
    """Verifica el estado del servicio"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)