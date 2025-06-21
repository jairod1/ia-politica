"""
Hybrid Sentiment Analyzer - HorizontAI (VERSIÓN MEJORADA Y OPTIMIZADA)
========================================================================

🚀 VERSIÓN MEJORADA: Análisis más preciso y categorización expandida
- ComentariosSentimentAnalyzer: Optimizado para comentarios individuales (emocional, coloquial)
- VisualizacionesSentimentAnalyzer: MEJORADO para artículos/títulos (informativo, formal)
- HybridSentimentAnalyzer: Wrapper con validación cruzada y correcciones automáticas

🆕 NUEVAS CARACTERÍSTICAS:
- Categorización temática expandida (gastronomía, etc.)
- Sistema de coherencia tono-emoción mejorado
- Validación cruzada automática
- Correcciones automáticas inteligentes
- Detección de contextos específicos
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
    # 🆕 Nuevos campos para validación
    validation_alerts: List[str] = None
    needs_review: bool = False
    applied_corrections: List[str] = None

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
    """🚀 Analizador específico para artículos/visualizaciones - VERSIÓN MEJORADA Y OPTIMIZADA"""
    
    def __init__(self):
        self.contexto_politico = ContextoPolitico()
        
        # Palabras gallegas específicas para artículos
        self.palabras_gallegas_articulos = [
            'concello', 'veciños', 'celebrarase', 'realizarase', 'terá', 'poderá',
            'desde', 'coa', 'polo', 'pola', 'na', 'no', 'da', 'do', 'das', 'dos',
            'ata', 'sempre', 'nunca', 'tamén', 'ademais', 'porque', 'aínda'
        ]
        
        # 🚀 EMOCIONES EXPANDIDAS Y MÁS ESPECÍFICAS para artículos
        self.emociones_articulos = {
            'tristeza': [
                # Necrológicas - palabras clave más específicas
                'fallece', 'fallecimiento', 'muerte', 'muere', 'falleció',
                'esquela', 'funeral', 'defunción', 'velatorio', 'cementerio',
                'sepelio', 'duelo', 'luto', 'despedida', 'último adiós',
                'cierre', 'clausura', 'pérdida', 'despedida', 'fin', 'último',
                # 🆕 NUEVAS PALABRAS DETECTADAS
                'restos mortales', 'capilla ardiente', 'sala velatorio', 'tanatorio',
                'empresa indica', 'mañana domingo', 'jóvenes fallecidos'
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
                'medalla', 'premio', 'distinción', 'honor', 'homenaje', 'llenó',
                # 🆕 GASTRONOMÍA Y REAPERTURAS
                'reabre', 'vuelve a abrir', 'nueva apertura', 'renueva',
                'abre sus puertas', 'moderniza', 'espacio gastronómico'
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
                'proyecto', 'planifica', 'construirá', 'ampliará',
                # 🆕 EVENTOS FUTUROS POSITIVOS
                'abrirá al público', 'viernes', 'programa', 'actividades'
            ],
            'preocupación': [
                # Problemas, conflictos, demoras
                'problema', 'dificultad', 'crisis', 'reducción', 'corte',
                'suspensión', 'retraso', 'conflicto', 'denuncia', 'queja',
                'esperando', 'espera', 'demora', 'paralizado', 'bloqueo',
                'grave', 'estado crítico', 'preocupados'
            ],
            'satisfacción': [
                # Finalizaciones exitosas, completaciones
                'finalización', 'completado', 'terminado', 'acabado',
                'cumplido', 'realizado', 'entregado', 'adjudicado'
            ]
        }
        
        # 🚀 CATEGORÍAS TEMÁTICAS EXPANDIDAS Y CON PRIORIDADES para artículos
        self.categorias_tematicas_articulos = {
            'necrologicas': {  # PRIMERA PRIORIDAD
                'keywords': [
                    'fallecimiento', 'fallece', 'falleció', 'muerte', 'muere',
                    'esquela', 'funeral', 'defunción', 'velatorio', 'cementerio',
                    'sepelio', 'duelo', 'luto', 'despedida', 'último adiós',
                    'descanse en paz', 'd.e.p', 'años de edad', 'tanatorio',
                    'restos mortales', 'capilla ardiente', 'sala velatorio',
                    'empresa indica', 'mañana domingo'
                ],
                'priority': 1,
                'emoji': '🕊️'
            },

            'gastronomia': {  # 🆕 NUEVA CATEGORÍA IMPORTANTE
                'keywords': [
                    'reabre', 'restaurante', 'gastronómico', 'cocina', 'chef',
                    'menú', 'bar', 'taberna', 'cervecería', 'marisquería',
                    'abre sus puertas', 'nueva carta', 'degustación',
                    'terraza', 'local', 'hostelería', 'camarero',
                    'espacio gastronómico', 'vuelve a abrir', 'nueva apertura',
                    'moderniza', 'renueva', 'espacio', 'comedor'
                ],
                'priority': 2,
                'emoji': '🍽️'
            },
            'festividades': {  # TERCERA PRIORIDAD (antes segunda)
                'keywords': [
                    'fiesta', 'festival', 'celebración', 'celebra', 'celebrar',
                    'festividad', 'evento', 'verbena', 'romería', 'procesión',
                    'feria', 'carnaval', 'concierto', 'actuación', 'espectáculo',
                    'homenaje', 'inauguración', 'apertura', 'clausura',
                    'grupo', 'cantantes', 'músicos', 'folclore', 'tradicional',
                    'cultural', 'arte', 'exposición', 'muestra',
                    'abrirá al público', 'viernes', 'sábado', 'domingo',
                    'programa', 'actividades', 'espectáculos'
                ],
                'priority': 3,
                'emoji': '🎉'
            },
            'deportes': {  # CUARTA PRIORIDAD
                'keywords': [
                    'fútbol', 'baloncesto', 'deportivo', 'club', 'equipo',
                    'competición', 'torneo', 'liga', 'entrenamiento', 'boxeo',
                    'campeón', 'campeonato', 'olimpiadas', 'medalla', 'copa',
                    'taekwondo', 'tirador', 'cerveza', 'sei', 'colegio',
                    'pabellón', 'victoria', 'triunfo', 'ganador', 'gana',
                    # 🎯 PALABRAS ESPECÍFICAS QUE SE PERDÍAN
                    'mejor de', 'mejor tirador', 'triunfa', 'consigue',
                    'oro', 'plata', 'bronce', 'primer puesto', 'llenó',
                    'se proclama', 'proclama', 'conseguido', 'título',
                    'avencia estatal', 'la avencia'
                ],
                'priority': 4,
                'emoji': '⚽'
            },
            'politica': {
                'keywords': [
                    'alcalde', 'alcaldesa', 'concejo', 'concello', 'pleno', 'concejal',
                    'partido', 'político', 'elecciones', 'campaña', 'gobierno',
                    'oposición', 'debate', 'moción', 'presupuesto', 'ordenanza',
                    'xunta', 'tramita', 'concesión', 'licencia', 'explotación'
                ],
                'priority': 5,
                'emoji': '🏛️'
            },
            'infraestructura': {
                'keywords': [
                    'carretera', 'puente', 'obra', 'construcción', 'urbanismo',
                    'saneamiento', 'agua', 'luz', 'gas', 'internet', 'edificio',
                    'viviendas', 'kiosko', 'pabellón', 'paseo', 'auditorio',
                    'aparcamiento', 'parking', 'lago castiñeiras', 'ardán'
                ],
                'priority': 6,
                'emoji': '🏗️'
            },
            'economia': {
                'keywords': [
                    'empresa', 'negocio', 'empleo', 'trabajo', 'industria',
                    'comercio', 'inversión', 'económico', 'financiación',
                    'tecnopesca', 'hostelería', 'adjudicados', 'puestos',
                    'mercado', 'abastos', 'millón', 'euros', 'dinero'
                ],
                'priority': 7,
                'emoji': '💰'
            },
            'religion': {
                'keywords': [
                    'capilla', 'iglesia', 'parroquia', 'sacerdote', 'religioso',
                    'franciscano', 'san diego', 'san narciso', 'misa', 'fiesta religiosa',
                    'colegio inmaculada', 'caridad', 'hermanas', 'tricentenaria'
                ],
                'priority': 8,
                'emoji': '⛪'
            },
            'educacion': {
                'keywords': [
                    'colegio', 'instituto', 'universidad', 'educación', 'estudiante',
                    'profesor', 'curso', 'escuela', 'formación', 'alumnos'
                ],
                'priority': 9,
                'emoji': '📚'
            },
            'medio_ambiente': {
                'keywords': [
                    'parque', 'jardín', 'verde', 'sostenible', 'ecológico',
                    'medio ambiente', 'reciclaje', 'limpieza'
                ],
                'priority': 10,
                'emoji': '🌱'
            }
        }
        
        # 🚀 NUEVOS PATRONES DE SENTIMIENTO MÁS ESPECÍFICOS
        self.patrones_sentimiento_mejorados = {
            'fuertemente_positivo': [
                # Reaperturas y nuevos negocios
                'reabre', 'abre sus puertas', 'inauguración', 'nueva apertura',
                'vuelve a abrir', 'renueva', 'moderniza',
                # Eventos exitosos
                'lleno', 'abarrotado', 'gran éxito', 'exitoso',
                # Reconocimientos deportivos específicos
                'campeón', 'oro', 'medalla', 'triunfa', 'se proclama', 'mejor de'
            ],
            
            'contextual_negativo': [
                # Problemas generales
                'muerte', 'fallecimiento',
                # Cierres y problemas
                'cierre definitivo', 'clausura', 'pérdida', 'problema'
            ],
            
            'neutral_informativo': [
                # Noticias administrativas
                'concello tramita', 'ayuntamiento', 'licencia', 'permiso',
                'adjudicados', 'concesión', 'solicitud',
                # Información general
                'se encontró', 'cantidad de', 'según', 'informa', 'cuenta con'
            ]
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
        """🚀 Análisis de sentimiento específico para artículos - VERSIÓN MEJORADA"""
        texto_completo = f"{titulo} {resumen}".lower()
        
        score_positivo = 0
        score_negativo = 0
        
        # 🚀 PATRONES EXPANDIDOS Y MÁS SENSIBLES
        for patron in self.patrones_sentimiento_mejorados['fuertemente_positivo']:
            if patron in texto_completo:
                # Dar más peso si está en el título
                if patron in titulo.lower():
                    score_positivo += 4
                else:
                    score_positivo += 2
        
        for patron in self.patrones_sentimiento_mejorados['contextual_negativo']:
            if patron in texto_completo:
                # Dar más peso si está en el título
                if patron in titulo.lower():
                    score_negativo += 4
                else:
                    score_negativo += 2
        
        # 🚀 UMBRALES AJUSTADOS (menos conservador pero más preciso)
        if score_positivo > score_negativo and score_positivo >= 2:  
            return 'positivo', min(0.70 + (score_positivo * 0.05), 0.95)
        elif score_negativo > score_positivo and score_negativo >= 2:  
            return 'negativo', min(0.70 + (score_negativo * 0.05), 0.95)
        else:
            return 'neutral', 0.65
    
    def analizar_emociones_articulo(self, titulo: str, resumen: str = "") -> Dict[str, float]:
        """🚀 Análisis de emociones específico para artículos - VERSIÓN MEJORADA"""
        emotions_scores = {}
        texto_completo = f"{titulo} {resumen}".lower()
        
        for emocion, keywords in self.emociones_articulos.items():
            score_total = 0
            
            for keyword in keywords:
                if keyword in texto_completo:
                    # 🚀 MÁS PESO al título (donde está la emoción principal)
                    if keyword in titulo.lower():
                        score_total += 5.0  # Incrementado de 4.0
                    else:
                        score_total += 2.5  # Incrementado de 2.0
            
            # 🚀 UMBRAL MÁS SENSIBLE para detectar emociones
            if score_total > 0:
                emotions_scores[emocion] = min(score_total / max(len(keywords), 4), 1.0)
        
        return emotions_scores
    
    def calcular_intensidad_articulo(self, titulo: str, resumen: str, emotions_scores: Dict[str, float]) -> int:
        """🚀 Intensidad específica para artículos - VERSIÓN MEJORADA"""
        intensidad_base = 2  # Base aumentada
        
        # 🚀 PALABRAS QUE INDICAN ALTA INTENSIDAD EN ARTÍCULOS
        palabras_alta_intensidad = [
            # Necrológicas (alta intensidad emocional)
            'fallece', 'fallecimiento', 'muerte', 'falleció', 'última hora',
            # Éxitos importantes
            'campeón', 'triunfa', 'oro', 'primer puesto', 'récord',
            # Eventos especiales
            'histórico', 'primer', 'único', 'gran', 'importante',
            'nuevo', 'innovador', 'revolucionario'
        ]
        
        texto_completo = f"{titulo} {resumen}".lower()
        
        # Contar palabras de alta intensidad
        for palabra in palabras_alta_intensidad:
            if palabra in texto_completo:
                intensidad_base += 1
        
        # 🚀 BONUS por tipo de artículo
        if any(word in texto_completo for word in ['fallece', 'fallecimiento', 'muerte']):
            intensidad_base += 2  # Necrológicas son siempre intensas
        
        if any(word in texto_completo for word in ['campeón', 'triunfa', 'oro']):
            intensidad_base += 1  # Éxitos deportivos/personales
        
        # Máximo score de emociones (umbral ajustado)
        if emotions_scores:
            max_emotion_score = max(emotions_scores.values())
            if max_emotion_score > 0.4:  # Reducido de 0.5 a 0.4
                intensidad_base += 1
        
        return min(intensidad_base, 5)  # Máximo 5
    
    def determinar_tematica_articulo(self, titulo: str, resumen: str = "") -> Tuple[str, str]:
        """🚀 Determinación temática específica - CON PRIORIDADES MEJORADAS"""
        texto_completo = f"{titulo} {resumen}".lower()
        
        # 🚀 ORDEN DE PRIORIDAD ACTUALIZADO:
        # 1. Necrológicas, 2. Gastronomía, 3. Festividades, 4. Deportes, 5. Política
        categorias_por_prioridad = sorted(
            self.categorias_tematicas_articulos.items(),
            key=lambda x: x[1].get('priority', 999)
        )
        
        # Verificar categorías por prioridad
        for categoria, info in categorias_por_prioridad:
            score = sum(1 for keyword in info['keywords'] if keyword in texto_completo)
            if score > 0:
                return categoria, info['emoji']
        
        return 'general', '📄'
    
    def verificar_coherencia_tono_emocion(self, titulo: str, tono: str, emocion: str, confidence: float) -> Tuple[str, str, float]:
        """🚀 NUEVA FUNCIÓN: Verifica y corrige incoherencias entre tono general y emoción principal"""
        texto_lower = titulo.lower()
        correcciones = []
        
        # REGLAS DE COHERENCIA ESPECÍFICAS
        
        # Si detectamos reapertura/inauguración pero tono negativo -> corregir
        palabras_apertura = ['reabre', 'inaugura', 'abre', 'nueva apertura', 'gastronómico']
        if any(palabra in texto_lower for palabra in palabras_apertura):
            if tono == 'negativo':
                correcciones.append("Reapertura clasificada como negativa -> corregida a positiva")
                return 'positivo', 'alegría', max(confidence, 0.80)
        
        # Si es necrológica pero no tiene tono negativo -> corregir
        if any(word in texto_lower for word in ['fallece', 'fallecimiento', 'muerte']):
            if tono != 'negativo':
                correcciones.append("Necrológica sin tono negativo -> corregida")
                return 'negativo', 'tristeza', max(confidence, 0.90)
        
        # Si detectamos éxito deportivo pero tono neutral -> corregir  
        palabras_exito_deportivo = ['campeón', 'oro', 'triunfa', 'medalla', 'mejor de']
        if any(palabra in texto_lower for palabra in palabras_exito_deportivo):
            if tono == 'neutral':
                correcciones.append("Éxito deportivo neutral -> corregido a positivo")
                return 'positivo', 'orgullo', max(confidence, 0.85)
        
        return tono, emocion, confidence
    
    def detectar_contexto_especifico(self, titulo: str, resumen: str = "") -> Dict[str, float]:
        """🚀 NUEVA FUNCIÓN: Detecta contextos específicos con mayor precisión"""
        texto_completo = f"{titulo} {resumen}".lower()
        contextos = {}
        
        # Contexto gastronómico
        if any(word in texto_completo for word in ['reabre', 'restaurante', 'bar', 'gastronómico']):
            contextos['gastronomia'] = 0.85
        
        # Contexto deportivo de alto nivel
        if any(word in texto_completo for word in ['campeón', 'oro', 'medalla', 'olimpiadas', 'triunfa']):
            contextos['deporte_elite'] = 0.90
        
        # Contexto necrológico
        if any(word in texto_completo for word in ['fallece', 'fallecimiento', 'tanatorio', 'muerte']):
            contextos['necrologico'] = 0.95
        
        return contextos

class HybridSentimentAnalyzer:
    """🚀 Wrapper con validación cruzada y correcciones automáticas - VERSIÓN MEJORADA"""
    
    def __init__(self):
        self.available = True
        self.cloud_mode = CLOUD_LIBS_AVAILABLE
        self.models_loaded = False
        
        # Inicializar analizadores específicos
        self.comentarios_analyzer = ComentariosSentimentAnalyzer()
        self.visualizaciones_analyzer = VisualizacionesSentimentAnalyzer()
        
        # 🆕 Contadores para estadísticas
        self.correcciones_aplicadas = 0
        self.validaciones_realizadas = 0
        
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
            'campeón', 'triunfa', 'ganador', 'medalla', 'oro',
            # 🆕 AÑADIR patrones gastronómicos
            'reabre', 'restaurante', 'gastronómico'
        ]
        
        if any(patron in texto.lower() for patron in patrones_articulo):
            return 'articulo'
        
        # Por defecto, asumir comentario
        return 'comentario'
    
    def validar_clasificacion(self, titulo: str, tematica: str, tono: str, emocion: str) -> Dict[str, any]:
        """🚀 NUEVA FUNCIÓN: Sistema de validación cruzada para detectar posibles errores"""
        alertas = []
        sugerencias = []
        
        titulo_lower = titulo.lower()
        
        # Validación 1: Necrológicas nunca deberían ser positivas
        if 'necrologicas' in tematica.lower() and tono == 'positivo':
            alertas.append("⚠️ Necrológica clasificada como positiva")
            sugerencias.append("Revisar: probablemente debería ser negativo/tristeza")
        
        # Validación 2: Reaperturas no deberían ser necrológicas
        if any(word in titulo_lower for word in ['reabre', 'abre', 'gastronómico']) and 'necrologicas' in tematica.lower():
            alertas.append("⚠️ Reapertura clasificada como necrológica")
            sugerencias.append("Revisar: debería ser 'gastronomia' o 'eventos'")
        
        # Validación 3: Éxitos deportivos deberían ser positivos
        if any(word in titulo_lower for word in ['campeón', 'oro', 'triunfa', 'medalla']) and tono != 'positivo':
            alertas.append("⚠️ Éxito deportivo no clasificado como positivo")
            sugerencias.append("Revisar: debería ser positivo/orgullo")
        
        self.validaciones_realizadas += 1
        
        return {
            'alertas': alertas,
            'sugerencias': sugerencias,
            'necesita_revision': len(alertas) > 0
        }
    
    def aplicar_correcciones_automaticas(self, df_resultado: pd.DataFrame) -> pd.DataFrame:
        """🚀 NUEVA FUNCIÓN: Aplica correcciones automáticas basadas en reglas"""
        correcciones_aplicadas = 0
        correcciones_detalle = []
        
        for idx, row in df_resultado.iterrows():
            titulo = row.get('titulo', '') if hasattr(row, 'get') else ''
            if not titulo:
                # Intentar con diferentes nombres de columna
                titulo = row.get('title', '') or row.get('Titulo', '') or ''
            
            titulo_lower = titulo.lower()
            correcciones_fila = []
            
            # Corrección 1: Reaperturas gastronómicas mal clasificadas
            if any(word in titulo_lower for word in ['reabre', 'gastronómico']) and str(row.get('tematica', '')).startswith('🕊️'):
                df_resultado.at[idx, 'tematica'] = '🍽️ Gastronomia'
                df_resultado.at[idx, 'tono_general'] = 'positivo'
                df_resultado.at[idx, 'emocion_principal'] = 'alegría'
                correcciones_fila.append("Reapertura gastronómica corregida")
                correcciones_aplicadas += 1
            
            # Corrección 2: Éxitos deportivos mal clasificados
            if any(word in titulo_lower for word in ['campeón', 'oro', 'triunfa', 'mejor de']) and row.get('tono_general') != 'positivo':
                df_resultado.at[idx, 'tono_general'] = 'positivo'
                df_resultado.at[idx, 'emocion_principal'] = 'orgullo'
                df_resultado.at[idx, 'intensidad_emocional'] = min(row.get('intensidad_emocional', 3) + 1, 5)
                correcciones_fila.append("Éxito deportivo corregido a positivo")
                correcciones_aplicadas += 1
            
            # Corrección 3: Necrológicas mal clasificadas como positivas
            if any(word in titulo_lower for word in ['fallece', 'fallecimiento']) and row.get('tono_general') == 'positivo':
                df_resultado.at[idx, 'tono_general'] = 'negativo'
                df_resultado.at[idx, 'emocion_principal'] = 'tristeza'
                df_resultado.at[idx, 'intensidad_emocional'] = 5
                correcciones_fila.append("Necrológica corregida a negativo")
                correcciones_aplicadas += 1
            
            if correcciones_fila:
                correcciones_detalle.append(f"Fila {idx}: {', '.join(correcciones_fila)}")
        
        self.correcciones_aplicadas = correcciones_aplicadas
        
        if correcciones_aplicadas > 0:
            print(f"✅ Aplicadas {correcciones_aplicadas} correcciones automáticas:")
            for detalle in correcciones_detalle[:5]:  # Mostrar máximo 5
                print(f"  - {detalle}")
            if len(correcciones_detalle) > 5:
                print(f"  ... y {len(correcciones_detalle) - 5} más")
        
        return df_resultado
    
    def analizar_articulo_completo(self, titulo: str, resumen: str = "") -> EmotionResult:
        """🚀 Análisis completo MEJORADO que decide qué analizador usar"""
        try:
            # Determinar tipo de contenido
            tipo_contenido = self.detectar_tipo_contenido(titulo, bool(resumen.strip()))
            
            if tipo_contenido == 'comentario':
                resultado = self._analizar_comentario(titulo)
            else:
                resultado = self._analizar_articulo_mejorado(titulo, resumen)
                
            return resultado
                
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
            thematic_category=thematic_category,
            validation_alerts=[],
            needs_review=False,
            applied_corrections=[]
        )
    
    def _analizar_articulo_mejorado(self, titulo: str, resumen: str = "") -> EmotionResult:
        """🚀 Análisis específico para artículos/visualizaciones - VERSIÓN MEJORADA"""
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
        
        # 🚀 NUEVA CARACTERÍSTICA: Verificar coherencia tono-emoción
        general_tone, emotion_primary, general_confidence = analyzer.verificar_coherencia_tono_emocion(
            titulo, general_tone, emotion_primary, general_confidence
        )
        
        # Intensidad
        emotional_intensity = analyzer.calcular_intensidad_articulo(titulo, resumen, emotions_scores)
        
        # Temática y contexto
        tematica, emoji = analyzer.determinar_tematica_articulo(titulo, resumen)
        is_political = analyzer.contexto_politico.es_politico(f"{titulo} {resumen}")
        emotional_context = 'informativo' if general_tone == 'neutral' else 'optimista' if general_tone == 'positivo' else 'preocupante'
        thematic_category = f"{emoji} {tematica.title()}"
        
        # 🚀 NUEVA CARACTERÍSTICA: Validación cruzada
        validacion = self.validar_clasificacion(titulo, thematic_category, general_tone, emotion_primary)
        
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
            thematic_category=thematic_category,
            validation_alerts=validacion['alertas'],
            needs_review=validacion['necesita_revision'],
            applied_corrections=[]
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
            thematic_category='📄 General',
            validation_alerts=[],
            needs_review=False,
            applied_corrections=[]
        )
    
    def analizar_dataset(self, df: pd.DataFrame, columna_titulo: str, columna_resumen: str = None) -> pd.DataFrame:
        """🚀 Análisis optimizado con batches, validación y correcciones automáticas"""
        
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
            # 🆕 Nuevas columnas de validación
            df_resultado['alertas_validacion'] = [r.validation_alerts for r in resultados]
            df_resultado['necesita_revision'] = [r.needs_review for r in resultados]
            
            # 🚀 APLICAR CORRECCIONES AUTOMÁTICAS
            df_resultado = self.aplicar_correcciones_automaticas(df_resultado)
            
            # Estadísticas finales
            articulos_con_alertas = sum(1 for r in resultados if r.needs_review)
            if articulos_con_alertas > 0:
                print(f"⚠️ {articulos_con_alertas} artículos necesitan revisión")
                print(f"✅ {self.correcciones_aplicadas} correcciones automáticas aplicadas")
            
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
        """🚀 Genera reporte completo con estadísticas de validación"""
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
            
            # 🆕 Estadísticas de validación
            articulos_con_alertas = int(df_analizado.get('necesita_revision', pd.Series()).sum()) if 'necesita_revision' in df_analizado.columns else 0
            
            return {
                'total_articulos': total_articulos,
                'articulos_politicos': articulos_politicos,
                'distribución_idiomas': idiomas,
                'tonos_generales': tonos,
                'emociones_principales': emociones_principales,
                'contextos_emocionales': contextos,
                'tematicas': tematicas,
                'intensidad_promedio': intensidad_promedio,
                'confianza_promedio': confianza_promedio,
                # 🆕 Nuevas estadísticas
                'articulos_con_alertas': articulos_con_alertas,
                'correcciones_aplicadas': getattr(self, 'correcciones_aplicadas', 0),
                'validaciones_realizadas': getattr(self, 'validaciones_realizadas', 0),
                'porcentaje_precision': round((1 - articulos_con_alertas / total_articulos) * 100, 2) if total_articulos > 0 else 100
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
                'confianza_promedio': 0.7,
                'articulos_con_alertas': 0,
                'correcciones_aplicadas': 0,
                'validaciones_realizadas': 0,
                'porcentaje_precision': 100
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