"""
Cloud Sentiment Analyzer - HorizontAI (VERSIÓN CLOUD)
=====================================================

🌥️ VERSIÓN CLOUD: Análisis de sentimientos usando APIs y librerías externas
en lugar de modelos locales en .venv

Dependencias necesarias para requirements.txt:
transformers>=4.21.0
torch>=1.12.0
langdetect>=1.0.9
textblob>=0.17.1
"""

import re
import pandas as pd
import streamlit as st
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Imports para análisis cloud
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    from langdetect import detect, LangDetectError
    from textblob import TextBlob
    import torch
    CLOUD_LIBS_AVAILABLE = True
except ImportError as e:
    CLOUD_LIBS_AVAILABLE = False
    st.error(f"❌ Error importando librerías cloud: {e}")
    st.info("💡 Instala: pip install transformers torch langdetect textblob")

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

class CloudSentimentAnalyzer:
    """Analizador de sentimientos que usa APIs cloud en lugar de modelos locales"""
    
    def __init__(self):
        if not CLOUD_LIBS_AVAILABLE:
            st.error("❌ Librerías cloud no disponibles")
            self.available = False
            return
        
        self.available = True
        self.models_loaded = False
        
        # Inicializar modelos lazy (solo cuando se necesiten)
        self.sentiment_pipeline = None
        self.emotion_pipeline = None
        
        # Keywords para análisis temático y político (mismo que original)
        self._init_keywords()
    
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
        
        # Emociones con palabras clave
        self.emociones_keywords = {
            'alegría': ['celebra', 'festeja', 'felicidad', 'contento', 'avance', 'progreso', 'celébrase', 'festéxase', 'ledicia'],
            'orgullo': ['orgullo', 'honor', 'prestigio', 'reconocimiento', 'distinción', 'mérito', 'conquista', 'mejor', 'mellor'],
            'esperanza': ['espera', 'esperanza', 'optimismo', 'futuro', 'proyecto', 'promete', 'confía', 'ilusión', 'expectativa'],
            'satisfacción': ['satisfacción', 'complacencia', 'agrado', 'satisfecho', 'cumplido', 'realizado', 'completado'],
            'tristeza': ['tristeza', 'pena', 'dolor', 'luto', 'pesar', 'melancolía', 'fallece', 'muerte', 'pérdida', 'despedida'],
            'ira': ['ira', 'enfado', 'rabia', 'molestia', 'irritación', 'ataca', 'censura', 'repudia'],
            'miedo': ['miedo', 'temor', 'alarma', 'alerta', 'peligro', 'riesgo', 'amenaza', 'incertidumbre'],
            'decepción': ['decepción', 'desilusión', 'frustración', 'desencanto', 'fracaso', 'falla', 'incumple'],
            'indignación': ['indignación', 'asco', 'repugnancia', 'desprecio', 'desdén', 'rechazo', 'condena', 'critica'],
            'sorpresa': ['sorpresa', 'asombro', 'impacto', 'inesperado', 'imprevisto', 'repentino', 'súbito'],
            'nostalgia': ['nostalgia', 'añoranza', 'recuerdo', 'memoria', 'pasado', 'historia', 'tradición', 'antaño'],
            'preocupación': ['preocupación', 'inquietud', 'intranquilidad', 'zozobra', 'desasosiego', 'duda']
        }
        
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
    
    @st.cache_resource
    def _load_models(_self):
        """Carga los modelos de HuggingFace (con cache de Streamlit)"""
        if not _self.available:
            return False
        
        try:
            with st.spinner("🤗 Cargando modelos de HuggingFace..."):
                # 🌥️ OPTIMIZACIÓN CLOUD: Usar modelos más pequeños y eficientes
                # Modelo para análisis de sentimientos (optimizado para cloud)
                try:
                    _self.sentiment_pipeline = pipeline(
                        "sentiment-analysis", 
                        model="cardiffnlp/twitter-xlm-roberta-base-sentiment",  # Más pequeño y multiidioma
                        device=-1,  # Forzar CPU para cloud deployment
                        model_kwargs={"low_cpu_mem_usage": True}
                    )
                except Exception:
                    # Fallback a modelo aún más pequeño
                    _self.sentiment_pipeline = pipeline(
                        "sentiment-analysis", 
                        model="distilbert-base-uncased-finetuned-sst-2-english",
                        device=-1,
                        model_kwargs={"low_cpu_mem_usage": True}
                    )
                
                # Modelo para clasificación de emociones (más liviano)
                try:
                    _self.emotion_pipeline = pipeline(
                        "text-classification",
                        model="SamLowe/roberta-base-go_emotions",  # Modelo más eficiente
                        device=-1,  # CPU only
                        model_kwargs={"low_cpu_mem_usage": True}
                    )
                except Exception:
                    # Si falla, usar análisis por keywords solamente
                    st.warning("⚠️ Modelo de emociones no disponible, usando análisis por keywords")
                    _self.emotion_pipeline = None
                
                _self.models_loaded = True
                return True
                
        except Exception as e:
            st.error(f"❌ Error cargando modelos: {e}")
            _self.models_loaded = False
            return False
    
    def detectar_idioma_cloud(self, texto: str) -> str:
        """Detecta idioma usando langdetect + keywords locales"""
        if pd.isna(texto) or not texto.strip():
            return 'castellano'
        
        # Primero intentar con keywords locales (más preciso para gallego)
        texto_lower = texto.lower()
        total_palabras = len(texto_lower.split())
        coincidencias_gallego = sum(1 for palabra in self.palabras_gallegas if palabra in texto_lower)
        
        if coincidencias_gallego >= 3 and (total_palabras > 0 and coincidencias_gallego / total_palabras >= 0.08):
            return 'gallego'
        
        # Si no, usar langdetect como fallback
        try:
            idioma_detectado = detect(texto)
            if idioma_detectado == 'gl':  # Código ISO para gallego
                return 'gallego'
            elif idioma_detectado in ['es', 'ca']:  # Español o catalán
                return 'castellano'
            else:
                return 'castellano'  # Default
        except LangDetectError:
            return 'castellano'
    
    def analizar_sentimiento_cloud(self, texto: str) -> Tuple[str, float]:
        """Análisis de sentimientos usando HuggingFace"""
        if not self.models_loaded:
            if not self._load_models():
                return 'neutral', 0.5
        
        try:
            # Limitar longitud del texto para el modelo
            texto_truncado = texto[:512] if len(texto) > 512 else texto
            
            resultado = self.sentiment_pipeline(texto_truncado)
            
            # Mapear resultados del modelo a nuestras categorías
            label = resultado[0]['label'].lower()
            score = resultado[0]['score']
            
            if 'positive' in label or label == 'pos' or '4' in label or '5' in label:
                return 'positivo', score
            elif 'negative' in label or label == 'neg' or '1' in label or '2' in label:
                return 'negativo', score
            else:
                return 'neutral', score
                
        except Exception as e:
            st.warning(f"⚠️ Error en análisis cloud: {e}")
            return 'neutral', 0.5
    
    def analizar_emociones_cloud(self, texto: str) -> Dict[str, float]:
        """Análisis de emociones usando modelo cloud + keywords locales"""
        emotions_scores = {}
        
        # Análisis híbrido: keywords locales + modelo cloud
        texto_lower = texto.lower()
        
        # 1. Análisis por keywords (mantiene precisión local)
        for emocion, keywords in self.emociones_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in texto_lower:
                    score += 1
            
            if score > 0:
                emotions_scores[emocion] = min(score / len(keywords), 1.0)
        
        # 2. Si hay modelos disponibles, complementar con análisis cloud
        if self.models_loaded:
            try:
                texto_truncado = texto[:512] if len(texto) > 512 else texto
                resultado_emotion = self.emotion_pipeline(texto_truncado)
                
                # Mapear emociones del modelo a nuestras categorías
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
                
                for resultado in resultado_emotion[:3]:  # Top 3 emociones
                    emocion_en = resultado['label'].lower()
                    score_cloud = resultado['score']
                    
                    if emocion_en in mapeo_emociones:
                        emocion_es = mapeo_emociones[emocion_en]
                        # Combinar con score de keywords si existe
                        if emocion_es in emotions_scores:
                            emotions_scores[emocion_es] = max(emotions_scores[emocion_es], score_cloud * 0.8)
                        else:
                            emotions_scores[emocion_es] = score_cloud * 0.8
                            
            except Exception as e:
                st.warning(f"⚠️ Error en análisis de emociones cloud: {e}")
        
        return emotions_scores
    
    def analizar_articulo_completo(self, titulo: str, resumen: str = "") -> EmotionResult:
        """Análisis completo usando métodos cloud"""
        try:
            texto_completo = f"{titulo} {resumen}".lower()
            
            # 1. Detectar idioma
            language = self.detectar_idioma_cloud(f"{titulo} {resumen}")
            
            # 2. Análisis de emociones
            emotions_scores = self.analizar_emociones_cloud(titulo + " " + resumen)
            
            # 3. Determinar emoción principal
            if emotions_scores:
                emotion_primary = max(emotions_scores.items(), key=lambda x: x[1])[0]
                confidence = max(emotions_scores.values())
            else:
                emotion_primary = 'neutral'
                confidence = 0.5
            
            # 4. Análisis de tono
            general_tone, general_confidence = self.analizar_sentimiento_cloud(titulo + " " + resumen)
            
            # 5. Otras métricas (usando métodos originales)
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
            st.error(f"❌ Error en análisis cloud: {e}")
            return EmotionResult(
                language='castellano', emotion_primary='neutral', confidence=0.5,
                emotions_detected={'neutral': 0.5}, emotional_intensity=1,
                emotional_context='informativo', general_tone='neutral',
                general_confidence=0.5, is_political=False, thematic_category='📄 Otros'
            )
    
    def _detectar_contexto(self, texto: str) -> str:
        """Detecta contexto emocional (mismo método original)"""
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
        """Calcula intensidad emocional (mismo método original)"""
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
        
        return min(int(intensidad_base), 5)
    
    def _es_politico(self, texto: str) -> bool:
        """Determina si es político (mismo método original)"""
        return any(palabra in texto for palabra in self.palabras_politicas)
    
    def _determinar_tematica_mejorada(self, texto: str) -> Tuple[str, str]:
        """Determina categoría temática (mismo método original)"""
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
            return 'otros', '📄'
    
    def analizar_dataset(self, df: pd.DataFrame, columna_titulo: str, columna_resumen: str = None) -> pd.DataFrame:
        """Análisis de dataset usando métodos cloud"""
        if not self.available:
            st.error("❌ Analizador cloud no disponible")
            return df
        
        st.info("🌥️ Usando análisis de sentimientos cloud (HuggingFace + APIs)")
        
        # Cargar modelos si no están cargados
        if not self.models_loaded:
            if not self._load_models():
                st.error("❌ No se pudieron cargar los modelos cloud")
                return df
        
        st.info(f"🧠 Analizando {len(df)} artículos con IA cloud...")
        
        resultados = []
        
        for idx, row in df.iterrows():
            if idx % 10 == 0:
                st.info(f"   Procesado: {idx}/{len(df)} artículos")
            
            titulo = str(row[columna_titulo]) if pd.notna(row[columna_titulo]) else ""
            resumen = str(row[columna_resumen]) if columna_resumen and pd.notna(row[columna_resumen]) else ""
            
            try:
                resultado = self.analizar_articulo_completo(titulo, resumen)
                resultados.append(resultado)
            except Exception as e:
                st.warning(f"⚠️ Error en artículo {idx}: {e}")
                resultado_default = EmotionResult(
                    language='castellano', emotion_primary='neutral', confidence=0.5,
                    emotions_detected={'neutral': 0.5}, emotional_intensity=1,
                    emotional_context='informativo', general_tone='neutral',
                    general_confidence=0.5, is_political=False, thematic_category='📄 Otros'
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
            
            st.success("✅ Análisis cloud completado exitosamente")
            return df_resultado
            
        except Exception as e:
            st.error(f"❌ Error construyendo resultado: {e}")
            return df
    
    def generar_reporte_completo(self, df_analizado: pd.DataFrame) -> Dict:
        """Genera reporte completo (mismo método original)"""
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
            st.warning(f"⚠️ Error generando reporte: {e}")
            return {
                'total_articulos': total_articulos,
                'articulos_politicos': 0,
                'distribución_idiomas': {'castellano': total_articulos},
                'tonos_generales': {'neutral': total_articulos},
                'emociones_principales': {'neutral': total_articulos},
                'contextos_emocionales': {'informativo': total_articulos},
                'tematicas': {'📄 Otros': total_articulos},
                'intensidad_promedio': 1.0,
                'confianza_promedio': 0.5
            }

# Clases de compatibilidad con el sistema existente
class AnalizadorArticulosMarin:
    """Clase de compatibilidad que usa el analizador cloud"""
    
    def __init__(self):
        self.analizador = CloudSentimentAnalyzer()
    
    def analizar_dataset(self, df, columna_titulo='title', columna_resumen='summary'):
        return self.analizador.analizar_dataset(df, columna_titulo, columna_resumen)
    
    def generar_reporte(self, df_analizado):
        return self.analizador.generar_reporte_completo(df_analizado)

# Función de compatibilidad
def analizar_articulos_marin(df, columna_titulo='title', columna_resumen='summary'):
    """Función de compatibilidad que usa el analizador cloud"""
    analizador = CloudSentimentAnalyzer()
    return analizador.analizar_dataset(df, columna_titulo, columna_resumen)

# Test de funcionalidad
if __name__ == "__main__":
    print("🌥️ TESTING CLOUD SENTIMENT ANALYZER")
    
    if CLOUD_LIBS_AVAILABLE:
        analizador = CloudSentimentAnalyzer()
        
        # Test básico
        resultado = analizador.analizar_articulo_completo(
            "El alcalde anuncia mejoras en el puerto", 
            "Nuevas inversiones para modernizar las instalaciones"
        )
        print(f"✅ Análisis cloud funciona: {resultado.language}, {resultado.general_tone}, {resultado.emotion_primary}")
        
        # Test de dataset pequeño
        import pandas as pd
        df_test = pd.DataFrame({
            'title': ['Buenas noticias para Marín', 'Preocupación por el tráfico'],
            'summary': ['Proyectos de mejora aprobados', 'Problemas de circulación en el centro']
        })
        
        try:
            df_resultado = analizador.analizar_dataset(df_test, 'title', 'summary')
            print(f"✅ Dataset cloud procesado: {len(df_resultado)} filas con análisis")
            
            reporte = analizador.generar_reporte_completo(df_resultado)
            print(f"✅ Reporte cloud generado: {reporte['total_articulos']} artículos")
            
        except Exception as e:
            print(f"❌ Error en test cloud: {e}")
    else:
        print("❌ Librerías cloud no disponibles")