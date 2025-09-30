import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Dict, List, Any, Optional
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Procesador OCR para extraer texto de imágenes de PDFs escaneados"""
    
    def __init__(self, language: str = 'spa'):
        self.language = language
        self.supported_languages = self._get_supported_languages()
        
        # Verificar que el idioma esté disponible
        if language not in self.supported_languages:
            logger.warning(f"Idioma '{language}' no disponible, usando 'eng'")
            self.language = 'eng'
    
    def _get_supported_languages(self) -> List[str]:
        """Obtiene la lista de idiomas disponibles para Tesseract"""
        try:
            languages = pytesseract.get_languages()
            return languages if languages else ['eng']
        except Exception as e:
            logger.error(f"Error obteniendo idiomas de Tesseract: {e}")
            return ['eng']
    
    def process_image(self, image_path: str, preprocess: bool = True) -> Dict[str, Any]:
        """
        Procesa una imagen con OCR
        
        Args:
            image_path: Ruta a la imagen
            preprocess: Si aplicar preprocesamiento de imagen
            
        Returns:
            Dict con texto extraído y metadata
        """
        try:
            # Cargar imagen
            image = Image.open(image_path)
            
            # Preprocesar si es necesario
            if preprocess:
                image = self._preprocess_image(image)
            
            # Extraer texto con OCR
            ocr_data = pytesseract.image_to_data(
                image, 
                lang=self.language, 
                output_type=pytesseract.Output.DICT
            )
            
            # Extraer texto completo
            full_text = pytesseract.image_to_string(image, lang=self.language)
            
            # Procesar datos de OCR
            processed_data = self._process_ocr_data(ocr_data)
            
            # Buscar patrones de presupuesto
            budget_patterns = self._extract_budget_patterns(full_text)
            
            result = {
                'image_path': image_path,
                'image_size': image.size,
                'text': full_text,
                'confidence': processed_data['average_confidence'],
                'word_count': len(processed_data['words']),
                'lines': processed_data['lines'],
                'words': processed_data['words'],
                'budget_patterns': budget_patterns,
                'tables_detected': self._detect_tables_in_ocr(processed_data['words'])
            }
            
            logger.info(f"OCR completado para {image_path}: {result['word_count']} palabras")
            return result
            
        except Exception as e:
            logger.error(f"Error procesando OCR para {image_path}: {str(e)}")
            raise
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Aplica mejoras a la imagen para mejorar el reconocimiento OCR
        """
        try:
            # Convertir a escala de grises
            if image.mode != 'L':
                image = image.convert('L')
            
            # Aumentar contraste
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Aumentar nitidez
            image = image.filter(ImageFilter.SHARPEN)
            
            # Aplicar umbral adaptativo para binarización
            image_array = np.array(image)
            image_array = cv2.adaptiveThreshold(
                image_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            image = Image.fromarray(image_array)
            
            # Redimensionar si la imagen es muy pequeña
            width, height = image.size
            if width < 1000 or height < 1000:
                new_width = int(width * 1.5)
                new_height = int(height * 1.5)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.warning(f"Error en preprocesamiento de imagen: {str(e)}")
            return image  # Retornar imagen original si falla el preprocesamiento
    
    def _process_ocr_data(self, ocr_data: Dict[str, List]) -> Dict[str, Any]:
        """
        Procesa los datos brutos de OCR en una estructura más útil
        """
        words = []
        lines = {}
        total_confidence = 0
        valid_words = 0
        
        n_boxes = len(ocr_data['level'])
        
        for i in range(n_boxes):
            if ocr_data['conf'][i] > 0:  # Solo palabras reconocidas con confianza
                word_info = {
                    'text': ocr_data['text'][i].strip(),
                    'confidence': ocr_data['conf'][i],
                    'x': ocr_data['left'][i],
                    'y': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i],
                    'line_num': ocr_data['line_num'][i]
                }
                
                if word_info['text']:  # Solo si hay texto
                    words.append(word_info)
                    total_confidence += ocr_data['conf'][i]
                    valid_words += 1
                    
                    # Agrupar por líneas
                    line_key = ocr_data['line_num'][i]
                    if line_key not in lines:
                        lines[line_key] = []
                    lines[line_key].append(word_info)
        
        average_confidence = total_confidence / valid_words if valid_words > 0 else 0
        
        # Ordenar palabras por posición
        words.sort(key=lambda w: (w['y'], w['x']))
        
        # Convertir líneas a lista ordenada
        line_list = []
        for line_num in sorted(lines.keys()):
            line_words = sorted(lines[line_num], key=lambda w: w['x'])
            line_text = ' '.join([w['text'] for w in line_words])
            line_list.append({
                'line_number': line_num,
                'text': line_text,
                'words': line_words,
                'y_position': line_words[0]['y'] if line_words else 0
            })
        
        return {
            'words': words,
            'lines': line_list,
            'average_confidence': average_confidence
        }
    
    def _extract_budget_patterns(self, text: str) -> Dict[str, Any]:
        """
        Busca patrones comunes en presupuestos de construcción
        """
        patterns = {
            'codes': [],
            'prices': [],
            'quantities': [],
            'units': [],
            'chapters': [],
            'descriptions': []
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Buscar códigos de partida (formatos comunes)
            code_patterns = [
                r'\b\d{2}\.\d{2}\.\d{2}\b',  # 01.01.01
                r'\b\d{3}\.\d{3}\b',        # 001.001
                r'\b[A-Z]{2,3}\d{2,4}\b',   # AB1234
                r'\b\d{1,3}\.\d{1,3}\b'    # 1.1, 12.34
            ]
            
            for pattern in code_patterns:
                matches = re.findall(pattern, line)
                patterns['codes'].extend(matches)
            
            # Buscar precios
            price_patterns = [
                r'\$?\d{1,3}(?:,\d{3})*\.?\d{0,2}',  # $1,234.56 o 1234.56
                r'\d{1,3}(?:\.\d{3})*,\d{2}',         # 1.234,56
                r'\b\d+\.\d{2}\b'                    # 123.45
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, line)
                # Filtrar valores razonables para precios
                for match in matches:
                    try:
                        value = float(match.replace('$', '').replace(',', ''))
                        if 0.01 <= value <= 1000000:  # Rango razonable para precios
                            patterns['prices'].append(match)
                    except:
                        pass
            
            # Buscar cantidades
            quantity_patterns = [
                r'\b\d+(?:\.\d+)?\s*(?:m2|m3|kg|ml|l|un|hm|km|m)\b',  # Cantidad con unidad
                r'\b\d+(?:\.\d+)?\b'  # Números simples
            ]
            
            for pattern in quantity_patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                patterns['quantities'].extend(matches)
            
            # Buscar unidades comunes
            unit_pattern = r'\b(m2|m3|kg|ml|l|un|hm|km|m|pieza|juego|global)\b'
            matches = re.findall(unit_pattern, line, re.IGNORECASE)
            patterns['units'].extend(matches)
            
            # Buscar capítulos (líneas que parecen ser títulos de sección)
            if len(line) < 100 and (line.isupper() or re.match(r'^\d+\s*[.-]', line)):
                patterns['chapters'].append(line)
            
            # Líneas largas podrían ser descripciones
            if len(line) > 20 and not any(char.isdigit() for char in line[:10]):
                patterns['descriptions'].append(line)
        
        # Limpiar duplicados
        for key in patterns:
            if isinstance(patterns[key], list):
                patterns[key] = list(set(patterns[key]))[:20]  # Limitar resultados
        
        return patterns
    
    def _detect_tables_in_ocr(self, words: List[Dict]) -> List[Dict[str, Any]]:
        """
        Intenta detectar tablas basándose en la disposición de palabras
        """
        if len(words) < 10:  # Necesitamos al menos 10 palabras
            return []
        
        # Agrupar palabras por filas basadas en coordenada Y
        rows = {}
        for word in words:
            y_key = round(word['y'] / 10) * 10  # Agrupar en bloques de 10 píxeles
            if y_key not in rows:
                rows[y_key] = []
            rows[y_key].append(word)
        
        # Filtrar filas con suficientes palabras
        table_rows = []
        for y_key, row_words in rows.items():
            if len(row_words) >= 3:  # Mínimo 3 palabras por fila
                # Ordenar por posición X
                row_words.sort(key=lambda w: w['x'])
                table_rows.append({
                    'y_position': y_key,
                    'words': row_words,
                    'text': ' '.join([w['text'] for w in row_words])
                })
        
        # Ordenar filas por posición Y
        table_rows.sort(key=lambda r: r['y_position'])
        
        # Detectar si hay suficientes filas con estructura similar
        if len(table_rows) >= 3:
            return table_rows
        
        return []
    
    def batch_process_images(self, image_paths: List[str], preprocess: bool = True) -> List[Dict[str, Any]]:
        """
        Procesa múltiples imágenes con OCR
        """
        results = []
        
        for i, image_path in enumerate(image_paths):
            try:
                logger.info(f"Procesando imagen {i+1}/{len(image_paths)}: {image_path}")
                result = self.process_image(image_path, preprocess)
                results.append(result)
            except Exception as e:
                logger.error(f"Error procesando {image_path}: {str(e)}")
                results.append({
                    'image_path': image_path,
                    'error': str(e),
                    'text': '',
                    'confidence': 0
                })
        
        return results