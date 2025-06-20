"""
Hybrid Sentiment Analyzer - HorizontAI 
======================================

🎯 VERSIÓN HÍBRIDA: Funciona con o sin dependencias cloud
- CON dependencias cloud → Usa transformers + keywords
- SIN dependencias cloud → Solo keywords (como tu versión original)
"""

import re
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass


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
    # Mock de Streamlit para que no falle
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
        def cache_resource(func): return func  # No cache
    
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

class HybridSentimentAnalyzer:
    """Analizador híbrido que funciona con o sin dependencias cloud"""
    
    def __init__(self):
        self.available = True  # Siempre disponible
        self.cloud_mode = CLOUD_LIBS_AVAILABLE
        self.models_loaded = False
        
        # Inicializar modelos cloud solo si están disponibles
        self.sentiment_pipeline = None
        self.emotion_pipeline = None
        
        # Keywords para análisis (siempre disponibles)
        self._init_keywords()
        
        if self.cloud_mode:
            print("🌥️ Modo cloud habilitado")
        else:
            print("🔧 Modo keywords únicamente")
    
    def _init_keywords(self):
        """Inicializa las palabras clave para análisis"""
        # Palabras clave para detectar idioma
        self.palabras_gallegas = [
            'ata', 'dende', 'coa', 'polo', 'pola', 'na', 'no', 'da', 'do', 'das', 'dos', 
            'unha', 'uns', 'unhas', 'estes', 'aquela', 'aqueles', 'aquelas', 'mellor', 
            'moito', 'moita', 'moitos', 'moitas', 'pouco', 'pouca', 'concello', 
            'concelleiro', 'veciños', 'veciñas', 'proximamente', 'xunta', 'celebrarase', 
            'realizarase', 'terá', 'será', 'poderá', 'despois', 'antes', 'agora', 
            'aquí', 'alí', 'onde', 'cando', 'como', 'tamén', 'ademais', 'mentres', 
            'porque', 'xa', 'aínda', 'sempre', 'nunca'
        ]
        
        # Emociones con palabras clave (REDUCIDAS A 9 CLARAS)
        self.emociones_keywords = {
            'alegría': ['celebra', 'festeja', 'felicidad', 'contento', 'avance', 'progreso', 'celébrase', 'festéxase', 'ledicia', 'disfruta', 'goza'],
            'orgullo': ['orgullo', 'honor', 'prestigio', 'reconocimiento', 'distinción', 'mérito', 'conquista', 'mejor', 'mellor', 'excelente'],
            'esperanza': ['espera', 'esperanza', 'optimismo', 'futuro', 'proyecto', 'promete', 'confía', 'ilusión', 'expectativa', 'mejorará'],
            'satisfacción': ['satisfacción', 'complacencia', 'agrado', 'satisfecho', 'cumplido', 'realizado', 'completado', 'logrado'],
            'tristeza': ['tristeza', 'pena', 'dolor', 'luto', 'pesar', 'melancolía', 'fallece', 'muerte', 'pérdida', 'despedida', 'lamentable'],
            'ira': ['ira', 'enfado', 'rabia', 'molestia', 'irritación', 'ataca', 'censura', 'repudia', 'furioso', 'indignado'],
            'miedo': ['miedo', 'temor', 'alarma', 'alerta', 'peligro', 'riesgo', 'amenaza', 'incertidumbre', 'preocupa'],
            'decepción': ['decepción', 'desilusión', 'frustración', 'desencanto', 'fracaso', 'falla', 'incumple', 'decepciona'],
            'indignación': ['indignación', 'asco', 'repugnancia', 'desprecio', 'desdén', 'rechazo', 'condena', 'critica', 'vergüenza']
        }
        
        # Patrones lingüísticos sofisticados
        self.patrones_negacion = [
            'no ', 'non ', 'nin ', 'nada', 'nunca', 'jamás', 'sin ', 'sen ', 'falta', 'carece'
        ]
        
        self.intensificadores = {
            'amplificadores': ['muy', 'súper', 'totalmente', 'completamente', 'extremadamente', 'moi', 'moito', 'moita'],
            'superlativos': ['ísimo', 'ísima', 'máximo', 'máxima', 'total', 'absoluto', 'absoluta'],
            'atenuadores': ['un poco', 'algo', 'ligeramente', 'relativamente', 'apenas', 'case'],
            'absolutos': ['siempre', 'sempre', 'todo', 'toda', 'todos', 'todas', 'nada', 'ningún', 'ninguna']
        }
        
        self.marcadores_ambiguedad = ['quizás', 'tal vez', 'posiblemente', 'puede que', 'probablemente', 'a lo mejor', 'igual']
        
        # Tono por keywords
        self.palabras_positivas = [
            'celebra', 'festeja', 'éxito', 'logro', 'mejor', 'bueno', 'excelente', 
            'progreso', 'avance', 'felicidad', 'alegría', 'satisfacción', 'honor',
            'reconocimiento', 'premio', 'inauguración', 'apertura', 'mejora'
        ]
        
        self.palabras_negativas = [
            'problema', 'crisis', 'malo', 'peor', 'fracaso', 'error', 'falla',
            'tristeza', 'pena', 'muerte', 'fallece', 'luto', 'dolor', 'ira',
            'enfado', 'critica', 'censura', 'repudia', 'ataca', 'alarma'
        ]
        
        # Categorías temáticas
        self.categorias_tematicas = {
            'construcción': {'keywords': ['obra', 'construcción', 'edificio', 'vivienda', 'infraestructura'], 'emoji': '🏗️'},
            'cultura': {'keywords': ['cultura', 'arte', 'museo', 'exposición', 'teatro', 'música'], 'emoji': '🎭'},
            'industria': {'keywords': ['industria', 'empresa', 'económico', 'comercio', 'turismo'], 'emoji': '🏭'},
            'medio ambiente': {'keywords': ['medio ambiente', 'naturaleza', 'ecología', 'sostenible', 'verde'], 'emoji': '🌱'},
            'educación': {'keywords': ['educación', 'colegio', 'instituto', 'universidad', 'escuela'], 'emoji': '📚'},
            'salud': {'keywords': ['salud', 'hospital', 'médico', 'sanitario', 'enfermedad'], 'emoji': '🏥'},
            'deporte': {'keywords': ['deporte', 'fútbol', 'baloncesto', 'atletismo', 'piscina'], 'emoji': '⚽'},
            'seguridad': {'keywords': ['seguridad', 'policía', 'guardia civil', 'protección civil'], 'emoji': '🚔'},
            'social': {'keywords': ['social', 'servicios sociales', 'ayuda', 'subvención', 'pensión'], 'emoji': '🤝'},
            'necrológicas': {'keywords': ['fallece', 'muerte', 'falleció', 'defunción', 'funeral'], 'emoji': '🕊️'},
            'festividades': {'keywords': ['fiesta', 'celebración', 'carnaval', 'navidad', 'semana santa'], 'emoji': '🎉'},
            'transporte': {'keywords': ['transporte', 'autobús', 'tren', 'ferry', 'tráfico'], 'emoji': '🚌'},
            'laboral': {'keywords': ['contrato', 'sueldo', 'despido', 'negociación', 'sindicato'], 'emoji': '🧑‍💼'}
        }
        
        # Palabras políticas
        self.palabras_politicas = ['alcaldesa', 'alcalde', 'concejal', 'concejala', 'psoe', 'pp', 'bng', 'pazos', 'ramallo', 'santos']
    
    def _load_models(self):
        """Carga los modelos cloud si están disponibles"""
        if not self.cloud_mode:
            return False
        
        if self.models_loaded:
            return True
        
        try:
            with st.spinner("🤗 Cargando modelos cloud..."):
                # Usar modelos pequeños para cloud
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis", 
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1,  # CPU only
                    model_kwargs={"low_cpu_mem_usage": True}
                )
                
                try:
                    self.emotion_pipeline = pipeline(
                        "text-classification",
                        model="SamLowe/roberta-base-go_emotions",
                        device=-1,
                        model_kwargs={"low_cpu_mem_usage": True}
                    )
                except:
                    st.warning("⚠️ Modelo de emociones no disponible, usando keywords")
                    self.emotion_pipeline = None
                
                self.models_loaded = True
                return True
        except Exception as e:
            st.warning(f"⚠️ Error cargando modelos cloud: {e}")
            self.models_loaded = False
            return False
    
    def detectar_idioma(self, texto: str) -> str:
        """Detecta idioma usando keywords + langdetect (si disponible)"""
        if pd.isna(texto) or not texto.strip():
            return 'castellano'
        
        # Método 1: Keywords locales (siempre disponible)
        texto_lower = texto.lower()
        total_palabras = len(texto_lower.split())
        coincidencias_gallego = sum(1 for palabra in self.palabras_gallegas if palabra in texto_lower)
        
        if coincidencias_gallego >= 3 and (total_palabras > 0 and coincidencias_gallego / total_palabras >= 0.08):
            return 'gallego'
        
        # Método 2: langdetect (si está disponible)
        if self.cloud_mode:
            try:
                idioma_detectado = detect(texto)
                if idioma_detectado == 'gl':
                    return 'gallego'
                elif idioma_detectado in ['es', 'ca']:
                    return 'castellano'
            except:
                pass
        
        return 'castellano'
    
    def analizar_sentimiento(self, texto: str) -> Tuple[str, float]:
        """Análisis de sentimientos híbrido"""
        # Método 1: Keywords (siempre disponible)
        texto_lower = texto.lower()
        
        score_positivo = sum(1 for palabra in self.palabras_positivas if palabra in texto_lower)
        score_negativo = sum(1 for palabra in self.palabras_negativas if palabra in texto_lower)
        
        # Método 2: Modelo cloud (si disponible)
        if self.cloud_mode and self.models_loaded and self.sentiment_pipeline:
            try:
                texto_truncado = texto[:512] if len(texto) > 512 else texto
                resultado = self.sentiment_pipeline(texto_truncado)
                
                label = resultado[0]['label'].lower()
                score_cloud = resultado[0]['score']
                
                # Combinar resultados
                if 'positive' in label or '4' in label or '5' in label:
                    score_positivo += score_cloud * 2
                elif 'negative' in label or '1' in label or '2' in label:
                    score_negativo += score_cloud * 2
            except:
                pass
        
        # Determinar tono final
        if score_positivo > score_negativo and score_positivo > 0.3:
            confidence = min(score_positivo / (score_positivo + score_negativo + 0.1), 0.95)
            return 'positivo', confidence
        elif score_negativo > score_positivo and score_negativo > 0.3:
            confidence = min(score_negativo / (score_positivo + score_negativo + 0.1), 0.95)
            return 'negativo', confidence
        else:
            return 'neutral', 0.5
    
    def analizar_emociones(self, texto: str) -> Dict[str, float]:
        """Análisis de emociones híbrido"""
        emotions_scores = {}
        texto_lower = texto.lower()
        
        # Método 1: Keywords (siempre disponible)
        for emocion, keywords in self.emociones_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in texto_lower:
                    score += 1
            
            if score > 0:
                emotions_scores[emocion] = min(score / len(keywords), 1.0)
        
        # Método 2: Modelo cloud (si disponible)
        if self.cloud_mode and self.models_loaded and self.emotion_pipeline:
            try:
                texto_truncado = texto[:512] if len(texto) > 512 else texto
                resultado_emotion = self.emotion_pipeline(texto_truncado)
                
                mapeo_emociones = {
                    'joy': 'alegría', 'happiness': 'alegría',
                    'sadness': 'tristeza', 'grief': 'tristeza',
                    'anger': 'ira', 'rage': 'ira',
                    'fear': 'miedo', 'anxiety': 'preocupación',
                    'surprise': 'sorpresa',
                    'disgust': 'indignación', 'contempt': 'indignación',
                    'pride': 'orgullo',
                    'hope': 'esperanza', 'optimism': 'esperanza'
                }
                
                for resultado in resultado_emotion[:3]:
                    emocion_en = resultado['label'].lower()
                    score_cloud = resultado['score']
                    
                    if emocion_en in mapeo_emociones:
                        emocion_es = mapeo_emociones[emocion_en]
                        if emocion_es in emotions_scores:
                            emotions_scores[emocion_es] = max(emotions_scores[emocion_es], score_cloud * 0.8)
                        else:
                            emotions_scores[emocion_es] = score_cloud * 0.8
            except:
                pass
        
        return emotions_scores
    
    def analizar_articulo_completo(self, titulo: str, resumen: str = "") -> EmotionResult:
        """Análisis completo híbrido"""
        try:
            # Cargar modelos cloud si están disponibles (lazy loading)
            if self.cloud_mode and not self.models_loaded:
                self._load_models()
            
            texto_completo = f"{titulo} {resumen}".lower()
            
            # 1. Detectar idioma
            language = self.detectar_idioma(f"{titulo} {resumen}")
            
            # 2. Análisis de emociones
            emotions_scores = self.analizar_emociones(titulo + " " + resumen)
            
            # 3. Determinar emoción principal
            if emotions_scores:
                emotion_primary = max(emotions_scores.items(), key=lambda x: x[1])[0]
                confidence = max(emotions_scores.values())
            else:
                emotion_primary = 'neutral'
                confidence = 0.5
            
            # 4. Análisis de tono
            general_tone, general_confidence = self.analizar_sentimiento(titulo + " " + resumen)
            
            # 5. Otras métricas
            emotional_context = self._detectar_contexto(texto_completo)
            emotional_intensity = self._calcular_intensidad_emocional(texto_completo, emotions_scores)
            is_political = self._es_politico(texto_completo)
            thematic_category, emoji = self._determinar_tematica_mejorada(texto_completo)
            
            return EmotionResult(
                language=language,
                emotion_primary=emotion_primary,
                confidence=confidence,
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
                emotions_detected={'neutral': 0.5}, emotional_intensity=1,
                emotional_context='informativo', general_tone='neutral',
                general_confidence=0.5, is_political=False, thematic_category='📄 Otra'
            )
    
    def _detectar_contexto(self, texto: str) -> str:
        """Detecta contexto emocional"""
        contextos_emocionales = {
            'celebratorio': ['inauguración', 'apertura', 'éxito', 'logro', 'victoria', 'festejo'],
            'conflictivo': ['polémica', 'controversia', 'disputa', 'enfrentamiento', 'conflicto'],
            'informativo': ['anuncia', 'informa', 'comunica', 'declara', 'presenta', 'propone'],
            'preocupante': ['problema', 'crisis', 'dificultad', 'obstáculo', 'complicación'],
            'solemne': ['funeral', 'recordatorio', 'memoria', 'luto', 'despedida', 'tributo']
        }
        
        contexto_scores = {}
        for contexto, keywords in contextos_emocionales.items():
            score = sum(1 for keyword in keywords if keyword in texto)
            if score > 0:
                contexto_scores[contexto] = score
        
        return max(contexto_scores, key=contexto_scores.get) if contexto_scores else 'informativo'
    
    def _calcular_intensidad_emocional(self, texto: str, emotions_scores: Dict[str, float]) -> int:
        """Calcula intensidad emocional"""
        intensificadores = ['muy', 'mucho', 'gran', 'enorme', 'tremendo', 'moi', 'moito']
        emociones_intensas = ['ira', 'tristeza', 'alegría', 'miedo', 'indignación', 'sorpresa']
        
        intensidad_base = 1
        
        for emocion, score in emotions_scores.items():
            if emocion in emociones_intensas:
                intensidad_base += score * 2
            else:
                intensidad_base += score
        
        intensificadores_encontrados = sum(1 for palabra in intensificadores if palabra in texto)
        intensidad_base += intensificadores_encontrados * 0.5
        
        return min(round(intensidad_base), 5)
    
    def _es_politico(self, texto: str) -> bool:
        """Determina si es político"""
        return any(palabra in texto for palabra in self.palabras_politicas)
    
    def _determinar_tematica_mejorada(self, texto: str) -> Tuple[str, str]:
        """Determina categoría temática"""
        tematica_scores = {}
        
        for categoria, info in self.categorias_tematicas.items():
            score = sum(1 for keyword in info['keywords'] if keyword in texto)
            if score > 0:
                tematica_scores[categoria] = score
        
        if tematica_scores:
            categoria_principal = max(tematica_scores, key=tematica_scores.get)
            emoji = self.categorias_tematicas[categoria_principal]['emoji']
            return categoria_principal, emoji
        else:
            return 'otra', '📄'
    
    def analizar_dataset(self, df: pd.DataFrame, columna_titulo: str, columna_resumen: str = None) -> pd.DataFrame:
        """Análisis de dataset híbrido"""

        resultados = []
        
        for idx, row in df.iterrows():        
            titulo = str(row[columna_titulo]) if pd.notna(row[columna_titulo]) else ""
            resumen = str(row[columna_resumen]) if columna_resumen and pd.notna(row[columna_resumen]) else ""
            
            try:
                resultado = self.analizar_articulo_completo(titulo, resumen)
                resultados.append(resultado)
            except Exception as e:
                print(f"⚠️ Error en artículo {idx}: {e}")
                resultado_default = EmotionResult(
                    language='castellano', emotion_primary='neutral', confidence=0.5,
                    emotions_detected={'neutral': 0.5}, emotional_intensity=1,
                    emotional_context='informativo', general_tone='neutral',
                    general_confidence=0.5, is_political=False, thematic_category='📄 Otra'
                )
                resultados.append(resultado_default)
        
        # Construir DataFrame resultado
        try:
            df_resultado = df.copy()
            
            # Añadir columnas de análisis
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
            error_msg = f"❌ Error construyendo resultado: {e}"
            if STREAMLIT_AVAILABLE:
                st.error(error_msg)
            else:
                print(error_msg)
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
            intensidad_promedio = float(df_analizado.get('intensidad_emocional', pd.Series()).mean()) if 'intensidad_emocional' in df_analizado.columns else 1.0
            confianza_promedio = float(df_analizado.get('confianza_analisis', pd.Series()).mean()) if 'confianza_analisis' in df_analizado.columns else 0.5
            
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
                'intensidad_promedio': 1.0,
                'confianza_promedio': 0.5
            }

# Clases de compatibilidad
class AnalizadorArticulosMarin:
    """Clase de compatibilidad híbrida"""
    
    def __init__(self):
        self.analizador = HybridSentimentAnalyzer()
    
    def analizar_dataset(self, df, columna_titulo='title', columna_resumen='summary'):
        return self.analizador.analizar_dataset(df, columna_titulo, columna_resumen)
    
    def generar_reporte(self, df_analizado):
        return self.analizador.generar_reporte_completo(df_analizado)

# Función de compatibilidad
def analizar_articulos_marin(df, columna_titulo='title', columna_resumen='summary'):
    """Función de compatibilidad híbrida"""
    analizador = HybridSentimentAnalyzer()
    return analizador.analizar_dataset(df, columna_titulo, columna_resumen)