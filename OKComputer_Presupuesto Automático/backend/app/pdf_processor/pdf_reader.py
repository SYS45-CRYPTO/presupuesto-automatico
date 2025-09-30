import fitz  # PyMuPDF
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PDFReader:
    """Clase principal para leer y procesar archivos PDF"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def read_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Lee un archivo PDF y extrae su contenido
        
        Args:
            file_path: Ruta al archivo PDF
            
        Returns:
            Dict con texto, metadata y información del documento
        """
        try:
            # Validar archivo
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                raise ValueError(f"Archivo demasiado grande: {file_size} bytes")
            
            # Abrir PDF
            doc = fitz.open(file_path)
            
            # Extraer información básica
            info = self._extract_pdf_info(doc)
            
            # Extraer texto de cada página
            pages_text = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                pages_text.append({
                    'page_number': page_num + 1,
                    'text': text,
                    'text_length': len(text)
                })
            
            # Detectar si es un PDF escaneado (poca o ninguna texto extraíble)
            is_scanned = self._detect_scanned_pdf(pages_text)
            
            # Cerrar documento
            doc.close()
            
            result = {
                'file_path': file_path,
                'file_name': os.path.basename(file_path),
                'file_size': file_size,
                'metadata': info,
                'pages': pages_text,
                'total_pages': len(pages_text),
                'is_scanned': is_scanned,
                'extracted_text': '\n'.join([page['text'] for page in pages_text]),
                'processing_time': 0.0  # Se llenará en el servicio principal
            }
            
            logger.info(f"PDF leído exitosamente: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error leyendo PDF {file_path}: {str(e)}")
            raise
    
    def _extract_pdf_info(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extrae metadata del PDF"""
        metadata = doc.metadata
        
        info = {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', ''),
            'format': metadata.get('format', ''),
            'encrypted': doc.is_encrypted,
            'permissions': {
                'printable': doc.is_printable,
                'copyable': not doc.is_encrypted or doc.get_page_text(0) != '',
            }
        }
        
        return info
    
    def _detect_scanned_pdf(self, pages_text: List[Dict]) -> bool:
        """
        Detecta si un PDF está escaneado basándose en la cantidad de texto
        """
        if not pages_text:
            return True
        
        # Calcular estadísticas de texto
        total_text_length = sum(page['text_length'] for page in pages_text)
        avg_text_length = total_text_length / len(pages_text)
        
        # Si el promedio de caracteres por página es muy bajo, probablemente es escaneado
        return avg_text_length < 100
    
    def extract_tables_from_page(self, page: fitz.Page) -> List[List[str]]:
        """
        Intenta extraer tablas de una página PDF
        """
        tables = []
        
        # Buscar áreas que parezcan tablas basándose en la disposición del texto
        text_dict = page.get_text("dict")
        
        if not text_dict or "blocks" not in text_dict:
            return tables
        
        # Agrupar texto por líneas horizontales (misma coordenada Y)
        lines_dict = {}
        
        for block in text_dict["blocks"]:
            if "lines" not in block:
                continue
                
            for line in block["lines"]:
                y_coord = round(line["bbox"][1], 1)  # Coordenada Y redondeada
                
                if y_coord not in lines_dict:
                    lines_dict[y_coord] = []
                
                line_text = ""
                for span in line["spans"]:
                    line_text += span["text"] + " "
                
                lines_dict[y_coord].append(line_text.strip())
        
        # Buscar patrones de tabla (líneas con estructura similar)
        if len(lines_dict) > 2:  # Mínimo 3 líneas para considerar una tabla
            y_coords = sorted(lines_dict.keys())
            
            # Buscar grupos de líneas con espaciado consistente
            table_lines = []
            prev_y = None
            
            for y in y_coords:
                if prev_y is None or (y - prev_y) < 50:  # Espaciado máximo entre filas
                    table_lines.append(y)
                else:
                    # Si tenemos suficientes líneas, considerarlo una tabla
                    if len(table_lines) >= 3:
                        table_data = []
                        for line_y in table_lines:
                            table_data.append(lines_dict[line_y])
                        tables.append(table_data)
                    
                    table_lines = [y]
                
                prev_y = y
            
            # No olvidar el último grupo
            if len(table_lines) >= 3:
                table_data = []
                for line_y in table_lines:
                    table_data.append(lines_dict[line_y])
                tables.append(table_data)
        
        return tables
    
    def get_page_images(self, file_path: str, page_number: int = 0) -> List[Dict[str, Any]]:
        """
        Extrae información de imágenes de una página específica
        """
        try:
            doc = fitz.open(file_path)
            page = doc.load_page(page_number)
            
            images = []
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    image_info = {
                        'index': img_index,
                        'xref': xref,
                        'width': pix.width,
                        'height': pix.height,
                        'colorspace': pix.colorspace,
                        'size': len(pix.tobytes()),
                        'is_scanned': pix.width > 800 and pix.height > 1000  # Aproximado para documentos
                    }
                    images.append(image_info)
                
                pix = None
            
            doc.close()
            return images
            
        except Exception as e:
            logger.error(f"Error extrayendo imágenes: {str(e)}")
            return []
    
    def save_page_as_image(self, file_path: str, page_number: int, output_path: str, dpi: int = 300) -> bool:
        """
        Convierte una página PDF en imagen para procesamiento OCR
        """
        try:
            doc = fitz.open(file_path)
            page = doc.load_page(page_number)
            
            # Convertir a imagen con alta resolución
            zoom = dpi / 72  # 72 es el DPI por defecto de PDF
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Guardar imagen
            pix.save(output_path)
            
            doc.close()
            return True
            
        except Exception as e:
            logger.error(f"Error guardando página como imagen: {str(e)}")
            return False