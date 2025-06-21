"""
Hybrid Sentiment Analyzer - HorizontAI (VERSIÓN REFACTORIZADA)
==============================================================

🔧 REFACTORIZACIÓN: Separación clara entre análisis de comentarios y visualizaciones
- ComentariosSentimentAnalyzer: Optimizado para comentarios individuales (emocional, coloquial)
- VisualizacionesSentimentAnalyzer: Optimizado para artículos/títulos (informativo, formal)
- HybridSentimentAnalyzer: Wrapper que decide qué analizador usar
"""

import re
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass
from functools import lru_cache

# Intentar importar librerías cloud (opcional)
try:
    from transformers import pipeline
    from langdetect import detect, LangDetectError
    import torch
    CLOUD_LIBS_AVAILABLE = True
    print("✅ Librerías cloud disponibles")
except ImportError:
    CLOUD_LIBS_AVAILABLE = False
    print("⚠️ Librerías cloud no disponibles, usando solo keywords")

# Importar Streamlit solo si está disponible
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    class MockStreamlit:
        @staticmethod
        def error(msg): print(f"ERROR: {msg}")
        @staticmethod
        def warning(msg): print(f"WARNING: {msg}")
        @staticmethod
        def info(msg): print(f"INFO: {msg}")
        @staticmethod
        def success(msg): print(f"SUCCESS: {msg}")
        @staticmethod
        def spinner(msg): return MockContextManager()
        @staticmethod
        def cache_resource(func): return func
    
    class MockContextManager:
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    st = MockStreamlit()

@dataclass
class EmotionResult:
    """Estructura para almacenar resultados de análisis"""
    language: str
    emotion_primary: str  
    confidence: float  
    emotions_detected: Dict[str, float]  
    emotional_intensity: int  
    emotional_context: str  
    general_tone: str  
    general_confidence: float  
    is_political: bool  
    thematic_category: str  

class SarcasmDetector:
    """Detecta sarcasmo e ironía contextual"""
    def __init__(self):
        self.patrones_sarcasmo = {
            'elogios_falsos': [
                'menos mal que', 'ojalá que', 'parabéns por',
                'de cando en vez', 'ás veces pasa'
            ],
            'criticas_indirectas': [
                'demagogia a todo trapo', 'espectáculo circense',
                'fantochada', 'siniestra figura', 'madre mía esto es asqueroso'
            ]
        }
    
    def detectar_sarcasmo(self, texto: str, contexto_politico: str = None) -> float:
        """Detecta probabilidad de sarcasmo (0.0-1.0)"""
        texto_lower = texto.lower()
        score_sarcasmo = 0.0
        
        for patron in self.patrones_sarcasmo['elogios_falsos']:
            if patron in texto_lower:
                score_sarcasmo += 0.6
        
        for patron in self.patrones_sarcasmo['criticas_indirectas']:
            if patron in texto_lower:
                score_sarcasmo += 0.8
        
        return min(score_sarcasmo, 1.0)

class ContextoPolitico:
    """Detecta contexto político"""
    def __init__(self):
        self.figuras_politicas = {
            'carmela silva': {
                'variantes': ['carmela silva', 'carmela', 'silva'],
                'contexto': 'controversia_politica'
            },
            'alcaldesa': {
                'variantes': ['alcaldesa', 'alcaldesa de marin', 'alcalde'],
                'contexto': 'gobierno_local'
            }
        }
        
        self.palabras_politicas_obligatorias = [
            'pp', 'psoe', 'bng', 'partido popular', 'socialista', 'bloque',
            'alcaldesa', 'alcalde', 'gobierno', 'dictadura', 'franco', 'franquista',
            'democracia', 'demócrata', 'memoria histórica', 'golpismo',
            'carmela silva', 'feijoo', 'politico', 'política', 'prisión',
            'concello', 'concejales', 'xunta', 'ministros'
        ]
    
    def es_politico(self, texto: str) -> bool:
        """Detección política expandida"""
        texto_lower = texto.lower()
        return any(termino in texto_lower for termino in self.palabras_politicas_obligatorias)

class ComentariosSentimentAnalyzer:
    """Analizador específico para comentarios individuales (emocional, coloquial)"""
    
    def __init__(self):
        self.detector_sarcasmo = SarcasmDetector()
        self.contexto_politico = ContextoPolitico()
        
        # Palabras gallegas específicas de comentarios
        self.palabras_gallegas_comentarios = [
            'cando', 'vez', 'ás veces', 'unha', 'persoa', 'demócrata', 'moi', 'mais', 'pode',
            'parabéns', 'vir', 'civilización', 'agora', 'convenza', 'nega', 'cambiar', 'rúas',
            'enaltecen', 'golpismo', 'desde', 'grove', 'esa', 'se nega', 'ao',
            'grazas', 'teña', 'non', 'pois', 'súa', 'desde a coruña'
        ]
        
        # Emociones específicas para comentarios (más granulares y emocionales)
        self.emociones_comentarios = {
            'ira': [
                'asqueroso', 'prisión', 'tiene que estar en prisión', 'madre mía',
                'barbaridad', 'barbaro', 'delincuentes', 'vergonzosa', 'asco',
                'patético', 'ineptitud', 'bribón'
            ],
            'indignación': [
                'demagogia', 'fantochada', 'siniestra figura', 'caradurismo',
                'espectáculo circense', 'golpismo', 'dictadura', 'Franco'
            ],
            'decepción': [
                'perdió el norte', 'da más pena', 'difícil de entender',
                'en contra de todo', 'cada vez da más pena', 'no se han enterado'
            ],
            'esperanza': [
                'ojalá que', 'futuro inmenso', 'se lo merece', 'aparece unha persoa decente',
                'parabéns por vir', 'democracia e civilización'
            ],
            'satisfacción': [
                'menos mal que', 'hay alguna demócrata', 'condena la dictadura',
                'persoa decente', 'pode pasar', 'tiene toda la razón'
            ],
            'desprecio': [
                'demagogia a todo trapo', 'siniestra figura', 'puntos oscuros',
                'caradurismo', 'hacer equilibrio', 'lamecús', 'súbditos'
            ],
            'alegría': [
                'felicitaciones', 'estupendo', 'enhorabuena', 'me gusta',
                'que bueno', 'preciosísimo', 'grazas', 'que viva'
            ]
        }
        
        # Palabras de intensidad para comentarios
        self.palabras_intensas_comentarios = [
            'prisión', 'asqueroso', 'madre mía', 'siniestra figura',
            'ojalá que', 'futuro inmenso', 'parabéns', 'barbaridad',
            'patético', 'vergonzosa', 'delincuentes'
        ]
    
    def detectar_idioma_comentario(self, texto: str) -> str:
        """Detección de idioma específica para comentarios"""
        texto_lower = texto.lower()
        
        # Palabras que GARANTIZAN gallego en comentarios
        gallego_fuerte = ['grazas', 'moi', 'teña', 'non', 'pois', 'súa']
        
        if any(palabra in texto_lower for palabra in gallego_fuerte):
            return 'gallego'
        
        # Umbral más bajo para comentarios cortos
        palabras_gallegas = texto_lower.split()
        coincidencias = sum(1 for palabra in self.palabras_gallegas_comentarios 
                          if palabra in palabras_gallegas)
        
        if coincidencias >= 1 and len(palabras_gallegas) <= 10:  
            return 'gallego'
        
        return 'castellano'
    
    def analizar_sentimiento_comentario(self, texto: str) -> Tuple[str, float]:
        """Análisis de sentimiento específico para comentarios"""
        texto_lower = texto.lower()
        
        score_positivo = 0
        score_negativo = 0
        
        # Patrones específicos de comentarios
        patrones_positivos_comentarios = [
            'felicitaciones', 'estupendo', 'enhorabuena', 'me gusta', 
            'que bueno', 'preciosísimo', 'gracias', 'buen día',
            'grazas', 'tiene toda la razón', 'hace bien'
        ]
        
        patrones_negativos_comentarios = [
            'patético', 'vergonzosa', 'delincuentes', 'barbaridad',
            'que raro que', 'absurdas', 'ineptitud', 'sofocante',
            'asqueroso', 'prisión', 'madre mía'
        ]
        
        # Scoring agresivo para comentarios emocionales
        for patron in patrones_positivos_comentarios:
            if patron in texto_lower:
                score_positivo += 3
        
        for patron in patrones_negativos_comentarios:
            if patron in texto_lower:
                score_negativo += 3
        
        # Detectar sarcasmo
        es_sarcastico = self.detector_sarcasmo.detectar_sarcasmo(texto)
        if es_sarcastico > 0.5:
            score_positivo, score_negativo = score_negativo, score_positivo
        
        # Umbrales bajos para comentarios
        if score_positivo > score_negativo and score_positivo >= 1:
            return 'positivo', min(0.8 + (score_positivo * 0.1), 0.95)
        elif score_negativo > score_positivo and score_negativo >= 1:
            return 'negativo', min(0.8 + (score_negativo * 0.1), 0.95)
        else:
            return 'neutral', 0.6
    
    def analizar_emociones_comentario(self, texto: str) -> Dict[str, float]:
        """Análisis de emociones específico para comentarios"""
        emotions_scores = {}
        texto_lower = texto.lower()
        
        for emocion, keywords in self.emociones_comentarios.items():
            score_total = 0
            
            for keyword in keywords:
                if keyword in texto_lower:
                    score_total += 2.5  # Más agresivo para comentarios
            
            if score_total > 0:
                emotions_scores[emocion] = min(score_total / len(keywords), 1.0)
        
        return emotions_scores
    
    def calcular_intensidad_comentario(self, texto: str, emotions_scores: Dict[str, float]) -> int:
        """Intensidad específica para comentarios"""
        texto_lower = texto.lower()
        intensidad_base = 2
        
        # Palabras intensas en comentarios
        for palabra in self.palabras_intensas_comentarios:
            if palabra in texto_lower:
                intensidad_base += 1
        
        # Signos de exclamación/interrogación (común en comentarios)
        if '!' in texto or '¡' in texto:
            intensidad_base += 1
        
        # Mayúsculas (énfasis en comentarios)
        if len([c for c in texto if c.isupper()]) > 5:
            intensidad_base += 1
        
        # Máximo score de emociones
        if emotions_scores:
            max_emotion_score = max(emotions_scores.values())
            if max_emotion_score > 0.7:
                intensidad_base += 1
        
        return min(intensidad_base, 5)

class VisualizacionesSentimentAnalyzer:
    """Analizador específico para artículos/visualizaciones (informativo, formal) - VERSIÓN OPTIMIZADA"""
    
    def __init__(self):
        self.contexto_politico = ContextoPolitico()
        
        # Palabras gallegas específicas para artículos
        self.palabras_gallegas_articulos = [
            'concello', 'veciños', 'celebrarase', 'realizarase', 'terá', 'poderá',
            'desde', 'coa', 'polo', 'pola', 'na', 'no', 'da', 'do', 'das', 'dos',
            'ata', 'sempre', 'nunca', 'tamén', 'ademais', 'porque', 'aínda'
        ]
        
        # 🔧 EMOCIONES EXPANDIDAS Y MÁS ESPECÍFICAS para artículos
        self.emociones_articulos = {
            'tristeza': [
                # Necrológicas - palabras clave más específicas
                'fallece', 'fallecimiento', 'muerte', 'muere', 'falleció',
                'esquela', 'funeral', 'defunción', 'velatorio', 'cementerio',
                'sepelio', 'duelo', 'luto', 'despedida', 'último adiós',
                'cierre', 'clausura', 'pérdida', 'despedida', 'fin', 'último'
            ],
            'alegría': [
                # Eventos positivos, fiestas, celebraciones
                'fiesta', 'festival', 'celebración', 'celebra', 'celebrar',
                'festividad', 'evento', 'verbena', 'romería', 'procesión',
                'inauguración', 'inaugura', 'apertura', 'abre', 'nuevo',
                'boda', 'nacimiento', 'graduación', 'concierto', 'actuación', 
                'espectáculo', 'grupo', 'cantantes',
                # 🎯 ÉXITOS DEPORTIVOS/PERSONALES - EXPANDIDO
                'éxito', 'exitoso', 'victoria', 'gana', 'ganador', 'primer puesto',
                'medalla', 'premio', 'distinción', 'honor', 'homenaje', 'llenó'
            ],
            'orgullo': [
                # 🎯 ÉXITOS DEPORTIVOS ESPECÍFICOS - NUEVA SECCIÓN EXPANDIDA
                'campeón', 'campeonato', 'campeón de', 'se proclama', 'proclama',
                'triunfa', 'triunfo', 'triunfante', 'consigue', 'consiguiendo',
                'oro', 'plata', 'bronce', 'mejor', 'mejor de', 'tirador',
                'olimpiadas', 'competición', 'torneo', 'copa', 'título',
                # Reconocimientos generales
                'reconocimiento', 'logro', 'conseguido', 'alcanza', 'supera', 
                'récord', 'representará', 'seleccionado', 'elegido', 'destacado'
            ],
            'esperanza': [
                # Desarrollo, mejoras, proyectos futuros
                'desarrollo', 'crecimiento', 'mejora', 'avance', 'progreso',
                'inversión', 'modernización', 'renovación', 'futuro',
                'proyecto', 'planifica', 'construirá', 'ampliará'
            ],
            'preocupación': [
                # Problemas, conflictos, demoras
                'problema', 'dificultad', 'crisis', 'reducción', 'corte',
                'suspensión', 'retraso', 'conflicto', 'denuncia', 'queja',
                'esperando', 'espera', 'demora', 'paralizado', 'bloqueo'
            ],
            'satisfacción': [
                # Finalizaciones exitosas, completaciones
                'finalización', 'completado', 'terminado', 'acabado',
                'cumplido', 'realizado', 'entregado', 'adjudicado'
            ]
        }
        
        # 🔧 CATEGORÍAS TEMÁTICAS EXPANDIDAS para artículos
        self.categorias_tematicas_articulos = {
            'necrologicas': {  # PRIMERA PRIORIDAD
                'keywords': [
                    'fallecimiento', 'fallece', 'falleció', 'muerte', 'muere',
                    'esquela', 'funeral', 'defunción', 'velatorio', 'cementerio',
                    'sepelio', 'duelo', 'luto', 'despedida', 'último adiós',
                    'descanse en paz', 'd.e.p', 'años de edad'
                ],
                'emoji': '🕊️'
            },
            'festividades': {  # SEGUNDA PRIORIDAD
                'keywords': [
                    'fiesta', 'festival', 'celebración', 'celebra', 'celebrar',
                    'festividad', 'evento', 'verbena', 'romería', 'procesión',
                    'feria', 'carnaval', 'concierto', 'actuación', 'espectáculo',
                    'homenaje', 'inauguración', 'apertura', 'clausura',
                    'grupo', 'cantantes', 'músicos', 'folclore', 'tradicional',
                    'cultural', 'arte', 'exposición', 'muestra'
                ],
                'emoji': '🎉'
            },
            'deportes': {  # TERCERA PRIORIDAD
                'keywords': [
                    'fútbol', 'baloncesto', 'deportivo', 'club', 'equipo',
                    'competición', 'torneo', 'liga', 'entrenamiento', 'boxeo',
                    'campeón', 'campeonato', 'olimpiadas', 'medalla', 'copa',
                    'taekwondo', 'tirador', 'cerveza', 'sei', 'colegio',
                    'pabellón', 'victoria', 'triunfo', 'ganador', 'gana',
                    # 🎯 PALABRAS ESPECÍFICAS QUE SE PERDÍAN
                    'mejor de', 'mejor tirador', 'triunfa', 'consigue',
                    'oro', 'plata', 'bronce', 'primer puesto', 'llenó',
                    'se proclama', 'proclama', 'conseguido', 'título'
                ],
                'emoji': '⚽'
            },
            'politica': {
                'keywords': [
                    'alcalde', 'alcaldesa', 'concejo', 'concello', 'pleno', 'concejal',
                    'partido', 'político', 'elecciones', 'campaña', 'gobierno',
                    'oposición', 'debate', 'moción', 'presupuesto', 'ordenanza',
                    'xunta', 'tramita', 'concesión', 'licencia'
                ],
                'emoji': '🏛️'
            },
            'religion': {  # Sin prioridad específica
                'keywords': [
                    'capilla', 'iglesia', 'parroquia', 'sacerdote', 'religioso',
                    'franciscano', 'san diego', 'san narciso', 'misa', 'fiesta religiosa',
                    'colegio inmaculada', 'caridad', 'hermanas'
                ],
                'emoji': '⛪'
            },
            'infraestructura': {
                'keywords': [
                    'carretera', 'puente', 'obra', 'construcción', 'urbanismo',
                    'saneamiento', 'agua', 'luz', 'gas', 'internet', 'edificio',
                    'viviendas', 'kiosko', 'pabellón', 'paseo'
                ],
                'emoji': '🏗️'
            },
            'economia': {
                'keywords': [
                    'empresa', 'negocio', 'empleo', 'trabajo', 'industria',
                    'comercio', 'inversión', 'económico', 'financiación',
                    'tecnopesca', 'hostelería', 'adjudicados', 'puestos'
                ],
                'emoji': '💰'
            },
            'educacion': {
                'keywords': [
                    'colegio', 'instituto', 'universidad', 'educación', 'estudiante',
                    'profesor', 'curso', 'escuela', 'formación', 'alumnos'
                ],
                'emoji': '📚'
            },
            'medio_ambiente': {
                'keywords': [
                    'parque', 'jardín', 'verde', 'sostenible', 'ecológico',
                    'medio ambiente', 'reciclaje', 'limpieza'
                ],
                'emoji': '🌱'
            }
        }
    
    def detectar_idioma_articulo(self, titulo: str, resumen: str = "") -> str:
        """Detección de idioma específica para artículos"""
        texto_completo = f"{titulo} {resumen}".lower()
        
        # Para artículos, buscar patrones más formales
        patrones_gallego_formal = [
            'concello de', 'veciños e veciñas', 'celebrarase o',
            'realizarase na', 'terá lugar', 'poderá participar'
        ]
        
        if any(patron in texto_completo for patron in patrones_gallego_formal):
            return 'gallego'
        
        # Conteo de palabras gallegas con umbral más alto para artículos
        palabras = texto_completo.split()
        coincidencias = sum(1 for palabra in self.palabras_gallegas_articulos 
                          if palabra in palabras)
        
        # Umbral más alto para artículos (más conservador)
        if coincidencias >= 2 and len(palabras) > 5:
            return 'gallego'
        
        return 'castellano'
    
    def analizar_sentimiento_articulo(self, titulo: str, resumen: str = "") -> Tuple[str, float]:
        """Análisis de sentimiento específico para artículos - VERSIÓN OPTIMIZADA"""
        texto_completo = f"{titulo} {resumen}".lower()
        
        score_positivo = 0
        score_negativo = 0
        
        # 🔧 PATRONES EXPANDIDOS Y MÁS SENSIBLES
        patrones_positivos_articulos = [
            # Eventos y celebraciones (FESTIVIDADES - NUEVA PRIORIDAD)
            'fiesta', 'festival', 'celebración', 'celebra', 'festividad',
            'evento', 'verbena', 'romería', 'procesión', 'concierto',
            'actuación', 'espectáculo', 'homenaje', 'grupo', 'cantantes',
            'inauguración', 'inaugura', 'apertura', 'abre', 'nuevo', 'nueva',
            # 🎯 ÉXITOS DEPORTIVOS ESPECÍFICOS - EXPANDIDO
            'triunfa', 'triunfo', 'triunfante', 'campeón', 'campeonato',
            'consigue', 'consiguiendo', 'se proclama', 'proclama',
            'tirador', 'mejor', 'mejor de', 'oro', 'plata', 'bronce',
            'ganador', 'gana', 'victoria', 'primer puesto', 'llenó',
            'éxito', 'exitoso', 'medalla', 'premio', 'copa', 'título',
            'olimpiadas', 'competición exitosa', 'torneo', 'conseguido',
            # Desarrollo y mejoras
            'desarrollo', 'crecimiento', 'mejora', 'avance', 'progreso',
            'inversión', 'renovación', 'modernización', 'proyecto',
            # Reconocimientos
            'reconocimiento', 'distinción', 'honor', 'mérito', 'destacado'
        ]
        
        patrones_negativos_articulos = [
            # Problemas y conflictos
            'problema', 'conflicto', 'crisis', 'dificultad', 'error',
            'retraso', 'suspensión', 'reducción', 'corte', 'cancelación',
            # Situaciones problemáticas
            'esperando', 'espera', 'demora', 'paralizado', 'bloqueo',
            'denuncia', 'queja', 'protesta', 'rechaza', 'opone',
            # Necrológicas y pérdidas
            'fallece', 'fallecimiento', 'muerte', 'muere', 'falleció',
            'cierre', 'clausura', 'pérdida', 'despedida'
        ]
        
        # 🔧 SCORING MÁS AGRESIVO (umbrales más bajos)
        for patron in patrones_positivos_articulos:
            if patron in texto_completo:
                # Dar más peso si está en el título
                if patron in titulo.lower():
                    score_positivo += 3
                else:
                    score_positivo += 2
        
        for patron in patrones_negativos_articulos:
            if patron in texto_completo:
                # Dar más peso si está en el título
                if patron in titulo.lower():
                    score_negativo += 3
                else:
                    score_negativo += 2
        
        # 🔧 UMBRALES MUCHO MÁS BAJOS (menos conservador)
        if score_positivo > score_negativo and score_positivo >= 1:  # Era >= 2
            return 'positivo', min(0.65 + (score_positivo * 0.05), 0.90)
        elif score_negativo > score_positivo and score_negativo >= 1:  # Era >= 2
            return 'negativo', min(0.65 + (score_negativo * 0.05), 0.90)
        else:
            return 'neutral', 0.6
    
    def analizar_emociones_articulo(self, titulo: str, resumen: str = "") -> Dict[str, float]:
        """Análisis de emociones específico para artículos - VERSIÓN OPTIMIZADA"""
        emotions_scores = {}
        texto_completo = f"{titulo} {resumen}".lower()
        
        for emocion, keywords in self.emociones_articulos.items():
            score_total = 0
            
            for keyword in keywords:
                if keyword in texto_completo:
                    # 🔧 MÁS PESO al título (donde está la emoción principal)
                    if keyword in titulo.lower():
                        score_total += 4.0  # Era 2.0
                    else:
                        score_total += 2.0  # Era 1.0
            
            # 🔧 UMBRAL MÁS BAJO para detectar emociones
            if score_total > 0:
                emotions_scores[emocion] = min(score_total / max(len(keywords), 5), 1.0)
        
        return emotions_scores
    
    def calcular_intensidad_articulo(self, titulo: str, resumen: str, emotions_scores: Dict[str, float]) -> int:
        """Intensidad específica para artículos - VERSIÓN OPTIMIZADA"""
        intensidad_base = 2  # Aumentado de 1 a 2
        
        # 🔧 PALABRAS QUE INDICAN ALTA INTENSIDAD EN ARTÍCULOS
        palabras_alta_intensidad = [
            # Necrológicas (alta intensidad emocional)
            'fallece', 'fallecimiento', 'muerte', 'falleció',
            # Éxitos importantes
            'campeón', 'triunfa', 'oro', 'primer puesto', 'récord',
            # Eventos especiales
            'histórico', 'primer', 'único', 'gran', 'importante',
            'nuevo', 'innovador', 'revolucionario', 'última hora'
        ]
        
        texto_completo = f"{titulo} {resumen}".lower()
        
        # Contar palabras de alta intensidad
        for palabra in palabras_alta_intensidad:
            if palabra in texto_completo:
                intensidad_base += 1
        
        # 🔧 BONUS por tipo de artículo
        if 'fallece' in texto_completo or 'fallecimiento' in texto_completo:
            intensidad_base += 2  # Necrológicas son siempre intensas
        
        if any(word in texto_completo for word in ['campeón', 'triunfa', 'oro']):
            intensidad_base += 1  # Éxitos deportivos/personales
        
        # Máximo score de emociones (umbral más bajo)
        if emotions_scores:
            max_emotion_score = max(emotions_scores.values())
            if max_emotion_score > 0.3:  # Era 0.5
                intensidad_base += 1
        
        return min(intensidad_base, 5)  # Máximo 5
    
    def determinar_tematica_articulo(self, titulo: str, resumen: str = "") -> Tuple[str, str]:
        """Determinación temática específica para artículos - CON PRIORIDADES ACTUALIZADAS"""
        texto_completo = f"{titulo} {resumen}".lower()
        
        # 🔧 NUEVO ORDEN DE PRIORIDAD según solicitud:
        # 1. Necrológicas, 2. Festividades, 3. Deportes, 4. Política
        categorias_prioritarias = ['necrologicas', 'festividades', 'deportes', 'politica']
        
        # Verificar categorías prioritarias primero
        for categoria in categorias_prioritarias:
            if categoria in self.categorias_tematicas_articulos:
                info = self.categorias_tematicas_articulos[categoria]
                score = sum(1 for keyword in info['keywords'] if keyword in texto_completo)
                if score > 0:
                    return categoria, info['emoji']
        
        # Si no es ninguna prioritaria, buscar en otras categorías
        for categoria, info in self.categorias_tematicas_articulos.items():
            if categoria not in categorias_prioritarias:
                score = sum(1 for keyword in info['keywords'] if keyword in texto_completo)
                if score > 0:
                    return categoria, info['emoji']
        
        return 'general', '📄'

class HybridSentimentAnalyzer:
    """Wrapper que decide qué analizador usar según el tipo de contenido"""
    
    def __init__(self):
        self.available = True
        self.cloud_mode = CLOUD_LIBS_AVAILABLE
        self.models_loaded = False
        
        # Inicializar analizadores específicos
        self.comentarios_analyzer = ComentariosSentimentAnalyzer()
        self.visualizaciones_analyzer = VisualizacionesSentimentAnalyzer()
        
        if self.cloud_mode:
            print("🌥️ Modo cloud habilitado")
        else:
            print("🔧 Modo keywords únicamente")
    
    def detectar_tipo_contenido(self, texto: str, tiene_resumen: bool = False) -> str:
        """Detecta si es un comentario o un artículo/visualización"""
        # Si tiene resumen, es claramente un artículo
        if tiene_resumen:
            return 'articulo'
        
        # Heurísticas para determinar el tipo
        if len(texto) < 100:  # Comentarios suelen ser más cortos
            # 🎯 EXCEPCIÓN: Títulos deportivos pueden ser cortos pero son artículos
            patrones_titulos_deportivos = [
                'campeón', 'triunfa', 'mejor de', 'tirador', 'oro', 'medalla',
                'se proclama', 'conseguido', 'olimpiadas', 'copa'
            ]
            
            if any(patron in texto.lower() for patron in patrones_titulos_deportivos):
                return 'articulo'
                
            return 'comentario'
        
        # Buscar patrones típicos de títulos de artículo
        patrones_articulo = [
            'inaugura', 'presenta', 'celebra', 'anuncia', 'aprueba',
            'concello', 'ayuntamiento', 'alcalde', 'alcaldesa',
            # 🎯 AÑADIR patrones deportivos
            'campeón', 'triunfa', 'ganador', 'medalla', 'oro'
        ]
        
        if any(patron in texto.lower() for patron in patrones_articulo):
            return 'articulo'
        
        # Por defecto, asumir comentario
        return 'comentario'
    
    def analizar_articulo_completo(self, titulo: str, resumen: str = "") -> EmotionResult:
        """Análisis completo que decide qué analizador usar"""
        try:
            # Determinar tipo de contenido
            tipo_contenido = self.detectar_tipo_contenido(titulo, bool(resumen.strip()))
            
            if tipo_contenido == 'comentario':
                return self._analizar_comentario(titulo)
            else:
                return self._analizar_articulo(titulo, resumen)
                
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return self._crear_resultado_default()
    
    def _analizar_comentario(self, texto: str) -> EmotionResult:
        """Análisis específico para comentarios"""
        analyzer = self.comentarios_analyzer
        
        # Detectar idioma
        language = analyzer.detectar_idioma_comentario(texto)
        
        # Análisis de emociones
        emotions_scores = analyzer.analizar_emociones_comentario(texto)
        
        # Emoción principal
        if emotions_scores:
            emotion_primary = max(emotions_scores.items(), key=lambda x: x[1])[0]
            confidence_emocion = max(emotions_scores.values())
        else:
            emotion_primary = 'neutral'
            confidence_emocion = 0.5
        
        # Tono general
        general_tone, general_confidence = analyzer.analizar_sentimiento_comentario(texto)
        
        # Intensidad
        emotional_intensity = analyzer.calcular_intensidad_comentario(texto, emotions_scores)
        
        # Contexto y categoría
        is_political = analyzer.contexto_politico.es_politico(texto)
        emotional_context = 'conflictivo' if general_tone == 'negativo' else 'esperanzador' if general_tone == 'positivo' else 'conversacional'
        thematic_category = '🏛️ Política' if is_political else '💬 Comentario'
        
        return EmotionResult(
            language=language,
            emotion_primary=emotion_primary,
            confidence=confidence_emocion,
            emotions_detected=emotions_scores,
            emotional_intensity=emotional_intensity,
            emotional_context=emotional_context,
            general_tone=general_tone,
            general_confidence=general_confidence,
            is_political=is_political,
            thematic_category=thematic_category
        )
    
    def _analizar_articulo(self, titulo: str, resumen: str = "") -> EmotionResult:
        """Análisis específico para artículos/visualizaciones"""
        analyzer = self.visualizaciones_analyzer
        
        # Detectar idioma
        language = analyzer.detectar_idioma_articulo(titulo, resumen)
        
        # Análisis de emociones
        emotions_scores = analyzer.analizar_emociones_articulo(titulo, resumen)
        
        # Emoción principal
        if emotions_scores:
            emotion_primary = max(emotions_scores.items(), key=lambda x: x[1])[0]
            confidence_emocion = max(emotions_scores.values())
        else:
            emotion_primary = 'neutral'
            confidence_emocion = 0.6
        
        # Tono general
        general_tone, general_confidence = analyzer.analizar_sentimiento_articulo(titulo, resumen)
        
        # 🎯 COHERENCIA TONO-EMOCIÓN: Ajustar tono basado en emoción detectada
        if emotion_primary in ['alegría', 'orgullo', 'satisfacción', 'esperanza'] and general_tone == 'neutral':
            general_tone = 'positivo'
            general_confidence = max(general_confidence, 0.7)
        elif emotion_primary in ['tristeza', 'preocupación'] and general_tone == 'neutral':
            general_tone = 'negativo'
            general_confidence = max(general_confidence, 0.7)
        
        # Intensidad
        emotional_intensity = analyzer.calcular_intensidad_articulo(titulo, resumen, emotions_scores)
        
        # Temática y contexto
        tematica, emoji = analyzer.determinar_tematica_articulo(titulo, resumen)
        is_political = analyzer.contexto_politico.es_politico(f"{titulo} {resumen}")
        emotional_context = 'informativo' if general_tone == 'neutral' else 'optimista' if general_tone == 'positivo' else 'preocupante'
        thematic_category = f"{emoji} {tematica.title()}"
        
        return EmotionResult(
            language=language,
            emotion_primary=emotion_primary,
            confidence=confidence_emocion,
            emotions_detected=emotions_scores,
            emotional_intensity=emotional_intensity,
            emotional_context=emotional_context,
            general_tone=general_tone,
            general_confidence=general_confidence,
            is_political=is_political,
            thematic_category=thematic_category
        )
    
    def _crear_resultado_default(self) -> EmotionResult:
        """Crea un resultado por defecto en caso de error"""
        return EmotionResult(
            language='castellano',
            emotion_primary='neutral',
            confidence=0.5,
            emotions_detected={'neutral': 0.5},
            emotional_intensity=2,
            emotional_context='informativo',
            general_tone='neutral',
            general_confidence=0.5,
            is_political=False,
            thematic_category='📄 General'
        )
    
    def analizar_dataset(self, df: pd.DataFrame, columna_titulo: str, columna_resumen: str = None) -> pd.DataFrame:
        """Análisis optimizado con batches y progress bar"""
        
        if len(df) == 0:
            return df
        
        resultados = []
        batch_size = 50
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        # Inicializar barra de progreso si está disponible
        progress_bar = None
        if hasattr(st, 'progress'):
            progress_bar = st.progress(0)
            st.info(f"🧠 Procesando {len(df)} elementos en {total_batches} lotes...")
        
        try:
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(df))
                batch = df.iloc[start_idx:end_idx]
                
                # Procesar lote
                batch_resultados = []
                for idx, row in batch.iterrows():
                    titulo = str(row[columna_titulo]) if pd.notna(row[columna_titulo]) else ""
                    resumen = str(row[columna_resumen]) if columna_resumen and pd.notna(row[columna_resumen]) else ""
                    
                    try:
                        resultado = self.analizar_articulo_completo(titulo, resumen)
                        batch_resultados.append(resultado)
                    except Exception as e:
                        print(f"⚠️ Error en elemento {idx}: {e}")
                        batch_resultados.append(self._crear_resultado_default())
                
                resultados.extend(batch_resultados)
                
                # Actualizar progreso
                if progress_bar:
                    progress = (batch_idx + 1) / total_batches
                    progress_bar.progress(progress)
            
            # Limpiar barra de progreso
            if progress_bar:
                progress_bar.empty()
                st.success(f"✅ Análisis completado: {len(resultados)} elementos procesados")
            
            # Construir DataFrame resultado
            df_resultado = df.copy()
            
            # Añadir columnas
            df_resultado['idioma'] = [r.language for r in resultados]
            df_resultado['tono_general'] = [r.general_tone for r in resultados]
            df_resultado['emocion_principal'] = [r.emotion_primary for r in resultados]
            df_resultado['confianza_analisis'] = [r.general_confidence for r in resultados]
            df_resultado['intensidad_emocional'] = [r.emotional_intensity for r in resultados]
            df_resultado['contexto_emocional'] = [r.emotional_context for r in resultados]
            df_resultado['es_politico'] = [r.is_political for r in resultados]
            df_resultado['tematica'] = [r.thematic_category for r in resultados]
            df_resultado['confianza_emocion'] = [r.confidence for r in resultados]
            df_resultado['emociones_detectadas'] = [r.emotions_detected for r in resultados]
            
            return df_resultado
            
        except Exception as e:
            if progress_bar:
                progress_bar.empty()
            error_msg = f"❌ Error en procesamiento por lotes: {e}"
            print(error_msg)
            if hasattr(st, 'error'):
                st.error(error_msg)
            return df
        
    def generar_reporte_completo(self, df_analizado: pd.DataFrame) -> Dict:
        """Genera reporte completo"""
        total_articulos = len(df_analizado)
        
        if total_articulos == 0:
            return {'total_articulos': 0, 'articulos_politicos': 0}
        
        try:
            # Estadísticas básicas
            idiomas = df_analizado.get('idioma', pd.Series()).value_counts().to_dict()
            tonos = df_analizado.get('tono_general', pd.Series()).value_counts().to_dict()
            emociones_principales = df_analizado.get('emocion_principal', pd.Series()).value_counts().to_dict()
            contextos = df_analizado.get('contexto_emocional', pd.Series()).value_counts().to_dict()
            tematicas = df_analizado.get('tematica', pd.Series()).value_counts().to_dict()
            
            articulos_politicos = int(df_analizado.get('es_politico', pd.Series()).sum()) if 'es_politico' in df_analizado.columns else 0
            intensidad_promedio = float(df_analizado.get('intensidad_emocional', pd.Series()).mean()) if 'intensidad_emocional' in df_analizado.columns else 2.0
            confianza_promedio = float(df_analizado.get('confianza_analisis', pd.Series()).mean()) if 'confianza_analisis' in df_analizado.columns else 0.7
            
            return {
                'total_articulos': total_articulos,
                'articulos_politicos': articulos_politicos,
                'distribución_idiomas': idiomas,
                'tonos_generales': tonos,
                'emociones_principales': emociones_principales,
                'contextos_emocionales': contextos,
                'tematicas': tematicas,
                'intensidad_promedio': intensidad_promedio,
                'confianza_promedio': confianza_promedio
            }
            
        except Exception as e:
            print(f"⚠️ Error generando reporte: {e}")
            return {
                'total_articulos': total_articulos,
                'articulos_politicos': 0,
                'distribución_idiomas': {'castellano': total_articulos},
                'tonos_generales': {'neutral': total_articulos},
                'emociones_principales': {'neutral': total_articulos},
                'contextos_emocionales': {'informativo': total_articulos},
                'tematicas': {'📄 General': total_articulos},
                'intensidad_promedio': 2.0,
                'confianza_promedio': 0.7
            }

# Clases de compatibilidad
class AnalizadorArticulosMarin:
    """Clase de compatibilidad refactorizada"""
    
    def __init__(self):
        self.analizador = HybridSentimentAnalyzer()
    
    def analizar_dataset(self, df, columna_titulo='title', columna_resumen='summary'):
        return self.analizador.analizar_dataset(df, columna_titulo, columna_resumen)
    
    def generar_reporte(self, df_analizado):
        return self.analizador.generar_reporte_completo(df_analizado)

# Función de compatibilidad
def analizar_articulos_marin(df, columna_titulo='title', columna_resumen='summary'):
    """Función de compatibilidad refactorizada"""
    analizador = HybridSentimentAnalyzer()
    return analizador.analizar_dataset(df, columna_titulo, columna_resumen)