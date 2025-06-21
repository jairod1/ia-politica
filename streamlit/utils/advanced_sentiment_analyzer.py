"""
Hybrid Sentiment Analyzer - HorizontAI (VERSIÓN CORREGIDA BASADA EN DATOS REALES)
================================================================================

🔧 CORRECCIONES APLICADAS basadas en análisis de 15 comentarios reales:
- Detección de gallego mejorada con patrones reales
- Eliminado sesgo hacia "neutral" 
- Detección política agresiva
- Intensidades realistas
- Emociones más precisas según contexto político

🎯 CALIBRADO ESPECÍFICAMENTE para comentarios políticos de Galicia
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
    """Detecta sarcasmo e ironía contextual - MEJORADO"""
    def __init__(self):
        # 🔧 PATRONES REALES observados en los comentarios
        self.patrones_sarcasmo = {
            'elogios_falsos': [
                'menos mal que',
                'ojalá que',
                'parabéns por',
                'de cando en vez',
                'ás veces pasa'
            ],
            'criticas_indirectas': [
                'demagogia a todo trapo',
                'espectáculo circense',
                'fantochada',
                'siniestra figura',
                'madre mía esto es asqueroso'
            ]
        }
    
    def detectar_sarcasmo(self, texto: str, contexto_politico: str = None) -> float:
        """Detecta probabilidad de sarcasmo (0.0-1.0)"""
        texto_lower = texto.lower()
        score_sarcasmo = 0.0
        
        # Patrones de elogios falsos
        for patron in self.patrones_sarcasmo['elogios_falsos']:
            if patron in texto_lower:
                score_sarcasmo += 0.6
        
        # Críticas indirectas
        for patron in self.patrones_sarcasmo['criticas_indirectas']:
            if patron in texto_lower:
                score_sarcasmo += 0.8
        
        return min(score_sarcasmo, 1.0)

class ContextoPolitico:
    """Detecta contexto político - MEJORADO con datos reales"""
    def __init__(self):
        # 🔧 TÉRMINOS POLÍTICOS REALES observados
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
        
        # Términos que GARANTIZAN categoría política
        self.palabras_politicas_obligatorias = [
            'pp', 'psoe', 'bng', 'partido popular', 'socialista', 'bloque',
            'alcaldesa', 'alcalde', 'gobierno', 'dictadura', 'franco', 'franquista',
            'democracia', 'demócrata', 'memoria histórica', 'golpismo',
            'carmela silva', 'feijoo', 'politico', 'política', 'prisión'
        ]
    
    def es_politico(self, texto: str) -> bool:
        """DETECCIÓN POLÍTICA EXPANDIDA"""
        texto_lower = texto.lower()
        
        # Políticos específicos observados
        politicos_reales = [
            'pedro sánchez', 'sánchez', 'psoe', 'bng', 'pp',
            'concello', 'alcaldesa', 'concejales', 'xunta',
            'gobierno', 'ministros', 'casa real', 'borbones',
            'emérito', 'juan carlos', 'defensa'
        ]
        
        # Términos administrativos que son políticos
        administrativos = [
            'recaudación del estado', 'servicios públicos',
            'cesión de terrenos', 'funcionarios', 'horas extras'
        ]
        
        # Si menciona CUALQUIER término → es político
        return any(termino in texto_lower for termino in politicos_reales + administrativos)

class HybridSentimentAnalyzer:
    """Analizador corregido basado en datos reales"""
    
    def __init__(self):
        self.available = True
        self.cloud_mode = CLOUD_LIBS_AVAILABLE
        self.models_loaded = False
        self.detector_sarcasmo = SarcasmDetector()
        self.contexto_politico = ContextoPolitico()
        
        # 🔧 PATRONES DE GALLEGO REALES (observados en comentarios)
        self.palabras_gallegas_reales = [
            # Observadas en comentarios reales:
            'cando', 'vez', 'ás veces', 'unha', 'persoa', 'demócrata', 'moi', 'mais', 'pode',
            'parabéns', 'vir', 'civilización', 'agora', 'convenza', 'nega', 'cambiar', 'rúas',
            'enaltecen', 'golpismo', 'desde', 'grove', 'esa', 'se nega', 'ao',
            # Tradicionales:
            'dende', 'coa', 'polo', 'pola', 'na', 'no', 'da', 'do', 'das', 'dos',
            'ata', 'sempre', 'nunca', 'tamén', 'ademais', 'porque', 'aínda',
            'concello', 'veciños', 'celebrarase', 'realizarase', 'terá', 'poderá'
        ]
        
        # Frases completas en gallego observadas
        self.frases_gallegas = [
            'de cando en vez', 'ás veces pasa', 'persoa decente e demócrata',
            'parabéns por vir', 'agora que convenza', 'esa alcaldesa de marín',
            'que se nega a cambiar', 'rúas que enaltecen ao golpismo'
        ]
        
        self._init_keywords()
        
        if self.cloud_mode:
            print("🌥️ Modo cloud habilitado")
        else:
            print("🔧 Modo keywords únicamente")
    
    def _init_keywords(self):
        """Inicializa palabras clave CORREGIDAS"""
        
        # 🔧 EMOCIONES REALES observadas en comentarios
        self.emociones_keywords = {
            'ira': [
                'asqueroso', 'prisión', 'tiene que estar en prisión', 'madre mía',
                'barbaridad', 'barbaro', 'delincuentes', 'vergonzosa', 'asco'
            ],
            'indignación': [
                'demagogia', 'fantochada', 'siniestra figura', 'caradurismo',
                'espectáculo circense', 'golpismo', 'dictadura', 'Franco'
            ],
            'decepción': [
                'perdió el norte', 'da más pena', 'difícil de entender',
                'en contra de todo', 'cada vez da más pena'
            ],
            'esperanza': [
                'ojalá que', 'futuro inmenso', 'se lo merece', 'aparece unha persoa decente',
                'parabéns por vir', 'democracia e civilización'
            ],
            'satisfacción': [
                'menos mal que', 'hay alguna demócrata', 'condena la dictadura',
                'persoa decente', 'pode pasar'
            ],
            'desprecio': [
                'demagogia a todo trapo', 'siniestra figura', 'puntos oscuros',
                'caradurismo', 'hacer equilibrio'
            ],
            'tristeza': [
                'da más pena', 'cada vez da más pena', 'tiempo pasados',
                'memoria histórica', 'odios y enfrentamientos'
            ],
            'preocupación': [
                'cuanto tiempo ha de pasar', 'engendran odios', 'futuro violento',
                'jóvenes desconozcan', 'tiempos pasados'
            ],
            'alegría': [
                'parabéns', 'civilización', 'democracia', 'aparece unha persoa',
                'convenza a feijoo'
            ]
        }
        
        # 🔧 PALABRAS NEGATIVAS REALES
        self.palabras_negativas = [
            'perdió el norte', 'da más pena', 'demagogia', 'caradurismo', 'siniestra',
            'puntos oscuros', 'fantochada', 'asqueroso', 'prisión', 'dictadura',
            'golpismo', 'odios', 'enfrentamientos', 'violento', 'difícil de entender',
            'en contra de todo', 'demagogia a todo trapo'
        ]
        
        # 🔧 PALABRAS POSITIVAS REALES  
        self.palabras_positivas = [
            'ojalá que', 'futuro inmenso', 'se lo merece', 'menos mal que',
            'demócrata', 'condena la dictadura', 'parabéns', 'persoa decente',
            'democracia', 'civilización', 'aparece unha persoa', 'pode pasar'
        ]
        
        # 🔧 CATEGORÍAS TEMÁTICAS CORREGIDAS
        self.categorias_tematicas = {
            'politica': {
                'keywords': [
                    'pp', 'psoe', 'bng', 'partido', 'alcaldesa', 'alcalde', 'gobierno',
                    'dictadura', 'franco', 'franquista', 'democracia', 'demócrata',
                    'memoria histórica', 'golpismo', 'carmela silva', 'feijoo',
                    'prisión', 'política', 'político', 'militancia', 'líderes'
                ],
                'emoji': '🏛️'
            },
            'social': {
                'keywords': ['futuro', 'jóvenes', 'tiempos', 'historia', 'civilización'],
                'emoji': '🤝'
            },
            'construcción': {
                'keywords': ['obra', 'construcción', 'edificio', 'vivienda', 'rúas'],
                'emoji': '🏗️'
            }
        }
    
    def detectar_idioma(self, texto: str, es_titulo: bool = False) -> str:
        """MANEJO DE TEXTOS MIXTOS"""
        texto_lower = texto.lower()
        
        # Palabras que GARANTIZAN gallego
        gallego_fuerte = ['grazas', 'moi', 'teña', 'non', 'pois', 'súa', 'desde a coruña']
        
        # Patrones mixtos (gallego + castellano)
        if any(palabra in texto_lower for palabra in gallego_fuerte):
            return 'gallego'
        
        # Umbral más bajo para detectar gallego
        palabras_gallegas = texto_lower.split()
        coincidencias = sum(1 for palabra in self.palabras_gallegas_reales 
                        if palabra in palabras_gallegas)
        
        # Reducir umbral a 1 palabra gallega
        if coincidencias >= 1 and len(palabras_gallegas) <= 10:  
            return 'gallego'
        
        return 'castellano'
    
    def analizar_sentimiento(self, texto: str) -> Tuple[str, float]:
        """VERSIÓN AGRESIVA - eliminar conservadurismo excesivo"""
        texto_lower = texto.lower()
        
        score_positivo = 0
        score_negativo = 0
        
        # 🔧 PATRONES POSITIVOS REALES observados
        patrones_positivos = [
            'felicitaciones', 'estupendo', 'enhorabuena', 'me gusta', 
            'que bueno', 'preciosísimo', 'gracias', 'buen día',
            '😂', '👏', '❤️', '¡que viva!', 'grazas'
        ]
        
        # 🔧 PATRONES NEGATIVOS REALES observados  
        patrones_negativos = [
            'patético', 'vergonzosa', 'delincuentes', 'barbaridad',
            'que raro que', 'absurdas', 'ineptitud', 'sofocante'
        ]
        
        # 🔧 DETECCIÓN DE SARCASMO
        patrones_sarcasmo = [
            'barato, barato', 'venga aplaudamos', 'que raro que',
            'claro [nombre] no', 'menos mal que', 'por supuesto'
        ]
        
        # Scoring más agresivo
        for patron in patrones_positivos:
            if patron in texto_lower:
                score_positivo += 3  # Aumentado de 2
        
        for patron in patrones_negativos:
            if patron in texto_lower:
                score_negativo += 3  # Aumentado de 2
        
        # Detectar sarcasmo (invertir polaridad)
        es_sarcastico = any(patron in texto_lower for patron in patrones_sarcasmo)
        if es_sarcastico:
            score_positivo, score_negativo = score_negativo, score_positivo
        
        # 🔧 UMBRALES MÁS BAJOS (menos conservador)
        if score_positivo > score_negativo and score_positivo >= 1:  # Era >= 2
            return 'positivo', min(0.8 + (score_positivo * 0.1), 0.95)
        elif score_negativo > score_positivo and score_negativo >= 1:  # Era >= 2  
            return 'negativo', min(0.8 + (score_negativo * 0.1), 0.95)
        else:
            return 'neutral', 0.6
    
    def analizar_emociones(self, texto: str) -> Dict[str, float]:
        """EMOCIONES REALES observadas en comentarios"""
        
        emociones_mejoradas = {
            'alegría': [
                'felicitaciones', 'estupendo', 'enhorabuena', 'me gusta',
                'que bueno', 'preciosísimo', '😂', '👏', 'grazas',
                'que viva', 'buen día'
            ],
            'ira': [
                'vergonzosa', 'delincuentes', 'barbaridad', 'patético',
                'ineptitud', 'absurdas', 'bribón'
            ],
            'desprecio': [
                'barato, barato', 'venga aplaudamos', 'que raro que',
                'lamecús', 'súbditos'
            ],
            'decepción': [
                'no se han enterado', 'miopia', 'no acabamos nunca',
                'deberían ser excelentes'
            ],
            'satisfacción': [
                'tiene toda la razón', 'hace bien', 'debería ampliar',
                'concuerdo'
            ]
        }
        
        emotions_scores = {}
        texto_lower = texto.lower()
        
        for emocion, keywords in emociones_mejoradas.items():
            score_total = 0
            
            for keyword in keywords:
                if keyword in texto_lower:
                    score_total += 2.5  # Más agresivo
            
            if score_total > 0:
                emotions_scores[emocion] = min(score_total / len(keywords), 1.0)
        
        return emotions_scores
    
    def _calcular_intensidad_realista(self, texto: str, emotions_scores: Dict[str, float]) -> int:
        """Calcula intensidad REALISTA (no siempre 1)"""
        texto_lower = texto.lower()
        
        # 🔧 BASE según longitud y contenido
        intensidad_base = 2  # Cambiar de 1 a 2
        
        # Palabras que indican alta intensidad
        palabras_intensas = [
            'prisión', 'asqueroso', 'madre mía', 'siniestra figura',
            'ojalá que', 'futuro inmenso', 'parabéns', 'barbaridad'
        ]
        
        for palabra in palabras_intensas:
            if palabra in texto_lower:
                intensidad_base += 1
        
        # Signos de exclamación/interrogación
        if '!' in texto or '¡' in texto:
            intensidad_base += 1
        
        # Mayúsculas (énfasis)
        if len([c for c in texto if c.isupper()]) > 5:
            intensidad_base += 1
        
        # Máximo score de emociones detectadas
        if emotions_scores:
            max_emotion_score = max(emotions_scores.values())
            if max_emotion_score > 0.7:
                intensidad_base += 1
        
        return min(intensidad_base, 5)
    
    def _determinar_tematica_politica(self, texto: str) -> Tuple[str, str]:
        """Determinación temática AGRESIVA hacia política"""
        texto_lower = texto.lower()
        
        # 🔧 SI DETECTA CUALQUIER TÉRMINO POLÍTICO → POLÍTICA
        if self.contexto_politico.es_politico(texto):
            return 'politica', '🏛️'
        
        # Verificar otras categorías solo si NO es político
        for categoria, info in self.categorias_tematicas.items():
            if categoria != 'politica':
                score = sum(1 for keyword in info['keywords'] if keyword in texto_lower)
                if score > 0:
                    return categoria, info['emoji']
        
        return 'otra', '📄'
    
    @lru_cache(maxsize=1000)  # Cache para textos repetidos    
    def analizar_articulo_completo(self, titulo: str, resumen: str = "") -> EmotionResult:
        """Análisis completo CORREGIDO"""
        try:
            texto_completo = f"{titulo} {resumen}"
            
            # 1. Detectar idioma (corregido)
            language = self.detectar_idioma(texto_completo)
            
            # 2. Análisis de emociones (corregido)
            emotions_scores = self.analizar_emociones(texto_completo)
            
            # 3. Emoción principal
            if emotions_scores:
                emotion_primary = max(emotions_scores.items(), key=lambda x: x[1])[0]
                confidence_emocion = max(emotions_scores.values())
            else:
                emotion_primary = 'neutral'
                confidence_emocion = 0.5
            
            # 4. Tono (corregido)
            general_tone, general_confidence = self.analizar_sentimiento(texto_completo)
            
            # 5. Intensidad realista
            emotional_intensity = self._calcular_intensidad_realista(texto_completo, emotions_scores)
            
            # 6. Temática (corregido)
            thematic_category, emoji = self._determinar_tematica_politica(texto_completo)
            
            # 7. Detección política
            is_political = self.contexto_politico.es_politico(texto_completo)
            
            # 8. Contexto emocional
            emotional_context = 'conflictivo' if general_tone == 'negativo' else 'esperanzador' if general_tone == 'positivo' else 'informativo'
            
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
                thematic_category=f"{emoji} {thematic_category.title()}"
            )
            
        except Exception as e:
            print(f"❌ Error en análisis: {e}")
            return EmotionResult(
                language='castellano', emotion_primary='neutral', confidence=0.5,
                emotions_detected={'neutral': 0.5}, emotional_intensity=2,
                emotional_context='informativo', general_tone='neutral',
                general_confidence=0.5, is_political=False, thematic_category='📄 Otra'
            )

    def analizar_dataset(self, df: pd.DataFrame, columna_titulo: str, columna_resumen: str = None) -> pd.DataFrame:
        """Análisis optimizado con batches y progress bar"""
        
        if len(df) == 0:
            return df
        
        resultados = []
        batch_size = 50  # Procesar de 50 en 50
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        # Inicializar barra de progreso si está disponible
        progress_bar = None
        if hasattr(st, 'progress'):
            progress_bar = st.progress(0)
            st.info(f"🧠 Procesando {len(df)} artículos en {total_batches} lotes...")
        
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
                        print(f"⚠️ Error en artículo {idx}: {e}")
                        resultado_default = EmotionResult(
                            language='castellano', emotion_primary='neutral', confidence=0.5,
                            emotions_detected={'neutral': 0.5}, emotional_intensity=2,
                            emotional_context='informativo', general_tone='neutral',
                            general_confidence=0.5, is_political=False, thematic_category='📄 Otra'
                        )
                        batch_resultados.append(resultado_default)
                
                resultados.extend(batch_resultados)
                
                # Actualizar progreso
                if progress_bar:
                    progress = (batch_idx + 1) / total_batches
                    progress_bar.progress(progress)
            
            # Limpiar barra de progreso
            if progress_bar:
                progress_bar.empty()
                st.success(f"✅ Análisis completado: {len(resultados)} artículos procesados")
            
            # Construir DataFrame resultado (igual que antes)
            df_resultado = df.copy()
            
            # Añadir columnas optimizado
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
                'tematicas': {'📄 Otra': total_articulos},
                'intensidad_promedio': 2.0,
                'confianza_promedio': 0.7
            }

# Clases de compatibilidad
class AnalizadorArticulosMarin:
    """Clase de compatibilidad corregida"""
    
    def __init__(self):
        self.analizador = HybridSentimentAnalyzer()
    
    def analizar_dataset(self, df, columna_titulo='title', columna_resumen='summary'):
        return self.analizador.analizar_dataset(df, columna_titulo, columna_resumen)
    
    def generar_reporte(self, df_analizado):
        return self.analizador.generar_reporte_completo(df_analizado)

# Función de compatibilidad
def analizar_articulos_marin(df, columna_titulo='title', columna_resumen='summary'):
    """Función de compatibilidad corregida"""
    analizador = HybridSentimentAnalyzer()
    return analizador.analizar_dataset(df, columna_titulo, columna_resumen)