# Plan de Desarrollo - Sistema de Automatización de Presupuestos de Obra

## Arquitectura General

### Stack Tecnológico
- **Backend**: FastAPI (Python) - API REST robusta y rápida
- **Frontend**: React.js con TypeScript - Interfaz moderna y reactiva
- **Base de Datos**: PostgreSQL - Almacenamiento robusto y escalable
- **Almacenamiento de Archivos**: Local/S3 para PDFs y documentos
- **Procesamiento de PDFs**: PyMuPDF (fitz) + pytesseract para OCR
- **Generación de PDFs**: ReportLab para PDFs profesionales
- **Manejo de Excel**: pandas + openpyxl para lectura/escritura

## Módulos del Sistema

### 1. Módulo de Lectura de PDFs (pdf_processor/)
**Ubicación**: `/backend/app/pdf_processor/`
- **Función**: Extraer información de presupuestos en formato PDF
- **Componentes**:
  - `pdf_reader.py`: Lectura básica de PDFs con PyMuPDF
  - `ocr_processor.py`: Procesamiento OCR para PDFs escaneados
  - `data_extractor.py`: Extracción de partidas, cantidades, precios
  - `format_detector.py`: Detección automática de formatos
- **Características**:
  - Soporte para múltiples formatos de presupuesto
  - OCR para documentos escaneados
  - Validación y limpieza de datos extraídos

### 2. Módulo de Libro de Precios (price_book/)
**Ubicación**: `/backend/app/price_book/`
- **Función**: Gestión de base de datos de precios unitarios
- **Componentes**:
  - `models.py`: Modelos de datos para partidas y precios
  - `importer.py`: Importación desde Excel/CSV
  - `price_service.py`: Lógica de búsqueda y actualización
  - `history_tracker.py**: Seguimiento de cambios de precios
- **Características**:
  - Importación masiva desde Excel/CSV
  - Búsqueda por código o descripción
  - Historial completo de precios
  - Alertas de precios fuera de rango

### 3. Módulo de Cálculos (calculator/)
**Ubicación**: `/backend/app/calculator/`
- **Función**: Realizar cálculos automáticos de presupuestos
- **Componentes**:
  - `budget_calculator.py`: Cálculo principal de presupuestos
  - `performance_service.py**: Gestión de rendimientos de operarios
  - `profit_service.py**: Configuración de porcentajes de beneficio
  - `cost_calculator.py**: Cálculo de costos indirectos
- **Características**:
  - Cálculo automático con rendimientos
  - Configuración de beneficios por proyecto
  - Simulaciones en tiempo real
  - Desglose de costos indirectos

### 4. Módulo de Generación de Documentos (document_generator/)
**Ubicación**: `/backend/app/document_generator/`
- **Función**: Crear PDFs profesionales y exportar datos
- **Componentes**:
  - `pdf_generator.py`: Generación de PDFs con ReportLab
  - `excel_exporter.py**: Exportación a Excel
  - `csv_exporter.py**: Exportación a CSV
  - `template_manager.py**: Gestión de plantillas
- **Características**:
  - PDFs profesionales con logo opcional
  - Múltiples formatos de exportación
  - Plantillas personalizables

### 5. Módulo de API (api/)
**Ubicación**: `/backend/app/api/`
- **Función**: Interfaz REST para el frontend
- **Componentes**:
  - `routes/`: Endpoints organizados por funcionalidad
  - `middleware/`: Autenticación, validación, logging
  - `schemas/`: Modelos Pydantic para validación
  - `dependencies/**: Dependencias compartidas
- **Características**:
  - API RESTful documentada
  - Validación automática de datos
  - Manejo de errores robusto

### 6. Frontend (frontend/)
**Ubicación**: `/frontend/`
- **Función**: Interfaz de usuario moderna y reactiva
- **Componentes**:
  - `components/`: Componentes React reutilizables
  - `pages/**: Páginas principales de la aplicación
  - `services/**: Llamadas a la API
  - `contexts/**: Gestión de estado global
  - `hooks/**: Hooks personalizados
- **Características**:
  - Dashboard analítico con gráficos
  - Carga y visualización de PDFs
  - Editor de presupuestos en tiempo real
  - Comparación de versiones

## Flujo de Datos

1. **Entrada**: Usuario sube PDF de presupuesto
2. **Procesamiento**: 
   - PDF → Extracción de datos → Validación
   - Búsqueda en libro de precios → Cálculos automáticos
3. **Salida**: Generación de PDF/Excel con presupuesto final
4. **Almacenamiento**: Presupuesto guardado en base de datos
5. **Análisis**: Dashboard con métricas y comparaciones

## Estructura de Base de Datos

### Tablas Principales:
- `projects`: Información de proyectos
- `budgets`: Presupuestos generados
- `budget_items`: Partidas individuales
- `price_books`: Libros de precios
- `price_entries`: Entradas de precios
- `price_history`: Historial de cambios
- `performance_rates`: Rendimientos de operarios
- `cost_settings**: Configuración de costos

## Seguridad y Rendimiento

- Autenticación JWT
- Validación de entrada de datos
- Límites de tamaño de archivos
- Optimización de consultas
- Caché para datos frecuentes
- Compresión de respuestas

## Instalación y Despliegue

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

3. **Base de Datos**:
   - PostgreSQL configurado
   - Migraciones automáticas con Alembic

## Próximos Pasos

1. Implementar módulo de lectura de PDFs
2. Crear sistema de base de datos
3. Desarrollar API REST
4. Construir frontend React
5. Integrar generación de documentos
6. Pruebas y optimización