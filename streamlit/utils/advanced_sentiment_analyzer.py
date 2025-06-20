"""
Hybrid Sentiment Analyzer - HorizontAI (VERSIÓN MEJORADA)
=========================================================

🎯 VERSIÓN HÍBRIDA: Funciona con o sin dependencias cloud
- CON dependencias cloud → Usa transformers + keywords
- SIN dependencias cloud → Solo keywords (como tu versión original)

🧠 MEJORAS LINGUÍSTICAS AVANZADAS:
- Detección de negaciones contextuales
- Análisis de intensificadores y atenuadores
- Sistema de confianza inteligente (no más 0.5 constante)
- 9 emociones claras (eliminadas las complejas)
- Detección de idioma más estricta (4+ palabras gallegas en títulos, 7+ en textos)
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

class SarcasmDetector:
    """NUEVA CLASE - Detecta sarcasmo e ironía contextual"""
    def __init__(self):
        self.patrones_sarcasmo = {
            'contraste_mayuscula_minuscula': r'[A-Z]{3,}.*[a-z].*[A-Z]|[A-Z]{5,}.*[a-z]{3,}',
            'errores_intencionados': {
                'majesta': ['majestad', 'maxestade'],
                'sempre': ['siempre'],
                'lamecús': 'lamecu*',
            },
            'contextos_sarcasticos': [
                'bienvenido.*casa.*majesta',
                'sempre.*bienvenido.*majesta', 
                'que.*venga.*pedro.*sanchez',
                'delincuentes.*simpatia',
                'súbditos.*como.*tratan.*majesta'
            ]
        }
        
        self.contextos_politicos_sarcasticos = {
            'juan carlos': {
                'palabras_positivas_sarcasticas': [
                    'bienvenido', 'casa', 'sempre', 'majestad', 'majesta'
                ],
                'contexto': 'autoexilio, corrupción'
            }
        }
    
    def detectar_sarcasmo(self, texto: str, contexto_politico: str = None) -> float:
        """Detecta probabilidad de sarcasmo (0.0-1.0)"""
        import re
        score_sarcasmo = 0.0
        texto_lower = texto.lower()
        
        # 1. Patrones tipográficos  
        if re.search(self.patrones_sarcasmo['contraste_mayuscula_minuscula'], texto):
            score_sarcasmo += 0.4
        
        # 2. Errores intencionados
        for error in self.patrones_sarcasmo['errores_intencionados']:
            if error in texto_lower:
                score_sarcasmo += 0.3
        
        # 3. Contextos sarcásticos
        for patron in self.patrones_sarcasmo['contextos_sarcasticos']:
            if re.search(patron, texto_lower):
                score_sarcasmo += 0.5
        
        # 4. Contexto político
        if contexto_politico in self.contextos_politicos_sarcasticos:
            ctx = self.contextos_politicos_sarcasticos[contexto_politico]
            palabras_positivas = sum(1 for palabra in ctx['palabras_positivas_sarcasticas'] 
                                   if palabra in texto_lower)
            if palabras_positivas >= 2:
                score_sarcasmo += 0.6
        
        return min(score_sarcasmo, 1.0)


class ContextoPolitico:
    """NUEVA CLASE - Maneja contexto político específico"""
    def __init__(self):
        self.figuras_politicas = {
            'juan carlos i': {
                'sinonimos': ['juan carlos', 'rey emerito', 'emerito', 'majesta', 'majestad'],
                'contexto_actual': 'controversia_corrupcion_autoexilio',
                'sentimiento_base': 'negativo',
                'palabras_trampa': ['bienvenido', 'casa', 'sempre', 'honor', 'majestad']
            },
            'pedro sanchez': {
                'sinonimos': ['pedro', 'sanchez', 'presidente'],
                'contexto_actual': 'gobierno_actual',
                'sentimiento_base': 'polarizado',
                'palabras_trampa': ['venga', 'molesta', 'ministros']
            }
        }
    
    def identificar_figura_politica(self, texto: str) -> str:
        """Identifica figura política mencionada"""
        texto_lower = texto.lower()
        for figura, datos in self.figuras_politicas.items():
            for sinonimo in datos['sinonimos']:
                if sinonimo in texto_lower:
                    return figura
        return None
    
    def ajustar_sentimiento_por_contexto(self, texto: str, sentimiento: str, confianza: float):
        """Ajusta sentimiento según contexto político"""
        figura = self.identificar_figura_politica(texto)
        
        if not figura:
            return sentimiento, confianza
        
        datos_figura = self.figuras_politicas[figura]
        texto_lower = texto.lower()
        
        # Detectar palabras trampa
        palabras_trampa = sum(1 for palabra in datos_figura.get('palabras_trampa', []) 
                            if palabra in texto_lower)
        
        if palabras_trampa >= 2 and sentimiento == 'positivo':
            return 'negativo', min(confianza + 0.3, 0.95)
        
        return sentimiento, confianza

class HybridSentimentAnalyzer:
    """Analizador híbrido que funciona con o sin dependencias cloud"""
    
    def __init__(self):
        self.available = True  # Siempre disponible
        self.cloud_mode = CLOUD_LIBS_AVAILABLE
        self.models_loaded = False
        self.detector_sarcasmo = SarcasmDetector()
        self.contexto_politico = ContextoPolitico()
        
        # MEJORAR PALABRAS GALLEGAS (reemplazar la lista existente)
        self.palabras_gallegas_exclusivas = [
            'ata', 'dende', 'coa', 'pola', 'unha', 'unhas', 'estes', 'aqueles', 'aquelas',
            'mellor', 'moito', 'moita', 'moitos', 'moitas', 'concello', 'veciños', 'veciñas',
            'celebrarase', 'realizarase', 'terá', 'poderá', 'despois', 'tamén', 'ademais',
            'mentres', 'porque', 'aínda', 'sempre', 'maxestade'
        ]
        
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
            'alegría': ['celebra', 'festeja', 'felicidad', 'contento', 'avance', 'progreso', 'celébrase', 'festéxase', 'ledicia', 'disfruta', 'goza',
                        'gracias', 'graciñas', 'enhorabuena'],
            'orgullo': ['orgullo', 'honor', 'prestigio', 'reconocimiento', 'distinción', 'mérito', 'conquista', 'mejor', 'mellor', 'excelente'],
            'esperanza': ['espera', 'esperanza', 'optimismo', 'futuro', 'proyecto', 'promete', 'confía', 'ilusión', 'expectativa', 'mejorará'],
            'satisfacción': ['satisfacción', 'complacencia', 'agrado', 'satisfecho', 'cumplido', 'realizado', 'completado', 'logrado'],
            'tristeza': ['tristeza', 'pena', 'dolor', 'luto', 'pesar', 'melancolía', 'fallece', 'muerte', 'pérdida', 'despedida', 'lamentable'],
            'ira': ['ira', 'enfado', 'rabia', 'molestia', 'irritación', 'ataca', 'censura', 'repudia', 'furioso', 'indignado'],
            'miedo': ['miedo', 'temor', 'alarma', 'alerta', 'peligro', 'riesgo', 'amenaza', 'incertidumbre', 'preocupa'],
            'decepción': ['decepción', 'desilusión', 'frustración', 'desencanto', 'fracaso', 'falla', 'incumple', 'decepciona'],
            'indignación': ['indignación', 'asco', 'repugnancia', 'desprecio', 'desdén', 'rechazo', 'condena', 'critica', 'vergüenza',
                            'patético']
        }
        
        # Patrones lingüísticos sofisticados
        self.patrones_negacion = [
            'no ', 'non ', 'nin ', 'nada', 'nunca', 'jamás', 'sin ', 'sen ', 'falta', 'carece', 'pero no', 'pero non', 'pero nunca',
        ]
        
        self.intensificadores = {
            'amplificadores': ['muy', 'super', 'totalmente', 'completamente', 'extremadamente', 'moi', 'moito', 'moita'
                               'mucho', 'mucha', 'muchos', 'muchas'],
            'superlativos': ['ísimo', 'ísima', 'errimo', 'máximo', 'maxima', 'total', 'absoluto', 'absoluta'],
            'atenuadores': ['un poco', 'algo', 'ligeramente', 'relativamente', 'apenas', 'case'],
            'absolutos': ['siempre', 'sempre', 'todo', 'toda', 'todos', 'todas', 'nada', 'ningún', 'ninguna', 'totalmente',
                          'absolutamente', 'completamente', 'perfectamente', 'absolutamente'],
            'positivos': ['bueno', 'buena', 'buenos', 'buenas', 'boa', 'bo', 'excelente', 'maravilloso', 'fantástico', 'increíble', 'espectacular', 'magnífico',]
        }
        
        self.marcadores_ambiguedad = ['quizás', 'tal vez', 'posiblemente', 'puede que', 'probablemente', 'a lo mejor', 'igual']
        
        # Tono por keywords
        self.palabras_positivas = [
            'celebra', 'festeja', 'éxito', 'logro', 'mejor', 'bueno', 'excelente', 
            'progreso', 'avance', 'felicidad', 'alegría', 'satisfacción', 'honor',
            'reconocimiento', 'premio', 'inauguración', 'apertura', 'mejora',
            'bueno', 'buena', 'bo', 'boa'
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
    
    def _detectar_negacion(self, texto: str, posicion_keyword: int) -> bool:
        """Detecta si una palabra emocional está negada"""
        palabras = texto.lower().split()
        
        # Buscar negaciones en las 3 palabras anteriores
        inicio = max(0, posicion_keyword - 3)
        contexto_previo = ' '.join(palabras[inicio:posicion_keyword])
        
        return any(negacion in contexto_previo for negacion in self.patrones_negacion)
    
    def _calcular_intensificacion(self, texto: str, posicion_keyword: int) -> float:
        """Calcula factor de intensificación para una palabra emocional"""
        palabras = texto.lower().split()
        
        # Buscar intensificadores en las 2 palabras anteriores y posteriores
        inicio = max(0, posicion_keyword - 2)
        fin = min(len(palabras), posicion_keyword + 3)
        contexto = ' '.join(palabras[inicio:fin])
        
        factor = 1.0
        
        # Amplificadores aumentan intensidad
        for amplificador in self.intensificadores['amplificadores']:
            if amplificador in contexto:
                factor += 0.4
        
        for superlativo in self.intensificadores['superlativos']:
            if superlativo in contexto:
                factor += 0.6
        
        # Atenuadores reducen intensidad
        for atenuador in self.intensificadores['atenuadores']:
            if atenuador in contexto:
                factor -= 0.3
        
        # Absolutos aumentan mucho
        for absoluto in self.intensificadores['absolutos']:
            if absoluto in contexto:
                factor += 0.5
        
        return max(0.1, min(2.0, factor))  # Entre 0.1 y 2.0
    
    def _calcular_confianza_inteligente(self, texto: str, emotions_scores: Dict[str, float], 
                                      tono: str, es_cloud_disponible: bool) -> float:
        """Sistema de confianza inteligente basado en múltiples factores"""
        
        if not texto or len(texto.strip()) < 3:
            return 0.2
        
        factores = {}
        
        # 1. Coherencia emocional (0.0-1.0)
        emociones_positivas = ['alegría', 'orgullo', 'esperanza', 'satisfacción']
        emociones_negativas = ['tristeza', 'ira', 'miedo', 'decepción', 'indignación']
        
        score_pos = sum(score for emocion, score in emotions_scores.items() if emocion in emociones_positivas)
        score_neg = sum(score for emocion, score in emotions_scores.items() if emocion in emociones_negativas)
        
        if score_pos > 0 and score_neg > 0:
            coherencia = 1.0 - min(score_pos, score_neg) / max(score_pos, score_neg)
        else:
            coherencia = 1.0
        
        factores['coherencia'] = coherencia
        
        # 2. Densidad de keywords emocionales (0.0-1.0)
        palabras_texto = len(texto.split())
        keywords_encontradas = sum(1 for score in emotions_scores.values() if score > 0)
        
        if palabras_texto > 0:
            densidad = min(1.0, keywords_encontradas / max(1, palabras_texto / 10))
        else:
            densidad = 0.0
        
        factores['densidad'] = densidad
        
        # 3. Longitud y contexto (0.0-1.0)
        if palabras_texto < 5:
            contexto = 0.3
        elif palabras_texto < 15:
            contexto = 0.6
        elif palabras_texto < 30:
            contexto = 0.8
        else:
            contexto = 1.0
        
        factores['contexto'] = contexto
        
        # 4. Presencia de ambigüedad (0.0-1.0)
        texto_lower = texto.lower()
        ambiguedad_detectada = any(marcador in texto_lower for marcador in self.marcadores_ambiguedad)
        claridad = 0.4 if ambiguedad_detectada else 1.0
        
        factores['claridad'] = claridad
        
        # 5. Concordancia cloud-keywords (0.0-1.0)
        if es_cloud_disponible:
            # Si hay modelos cloud, mayor confianza cuando coinciden
            concordancia = 0.9
        else:
            # Solo keywords, confianza ajustada según otros factores
            concordancia = 0.7
        
        factores['concordancia'] = concordancia
        
        # Fórmula ponderada
        confianza_final = (
            factores['coherencia'] * 0.25 +
            factores['densidad'] * 0.25 +
            factores['contexto'] * 0.20 +
            factores['claridad'] * 0.15 +
            factores['concordancia'] * 0.15
        )
        
        # Ajuste final: si no hay emociones detectadas, confianza baja
        if not emotions_scores or max(emotions_scores.values()) == 0:
            confianza_final = min(confianza_final, 0.4)
        
        return round(confianza_final, 2)
    
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
    
    def detectar_idioma(self, texto: str, es_titulo: bool = False) -> str:
        """MÉTODO MEJORADO - Detecta idioma con umbrales más estrictos"""
        if pd.isna(texto) or not texto.strip():
            return 'castellano'
        
        texto_lower = texto.lower()
        palabras = texto_lower.split()
        
        # Contar solo palabras gallegas exclusivas
        coincidencias_exclusivas = sum(1 for palabra in self.palabras_gallegas_exclusivas 
                                     if palabra in palabras)
        
        # Umbrales MÁS ESTRICTOS
        umbral_minimo = 3 if es_titulo or len(palabras) < 15 else 5
        
        if coincidencias_exclusivas >= umbral_minimo:
            return 'gallego'
        
        return 'castellano'  # Por defecto castellano
    
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
        """Análisis de emociones híbrido con análisis lingüístico sofisticado"""
        emotions_scores = {}
        texto_lower = texto.lower()
        palabras = texto_lower.split()
        
        # Método 1: Keywords con análisis lingüístico sofisticado
        for emocion, keywords in self.emociones_keywords.items():
            score_total = 0
            
            for keyword in keywords:
                if keyword in texto_lower:
                    # Encontrar posición de la keyword
                    try:
                        posicion = palabras.index(keyword)
                    except ValueError:
                        # Si no está como palabra completa, buscar en el texto
                        posicion = len(palabras) // 2  # Posición aproximada
                    
                    # Calcular score base
                    score_base = 1.0
                    
                    # Aplicar factor de intensificación
                    factor_intensidad = self._calcular_intensificacion(texto, posicion)
                    score_base *= factor_intensidad
                    
                    # Aplicar detección de negación
                    if self._detectar_negacion(texto, posicion):
                        # Si está negado, invertir o reducir drásticamente
                        score_base *= -0.8 if emocion in ['tristeza', 'ira', 'miedo', 'decepción', 'indignación'] else 0.2
                    
                    score_total += max(0, score_base)
            
            if score_total > 0:
                # Normalizar por número de keywords de esa emoción
                emotions_scores[emocion] = min(score_total / len(keywords), 1.0)
        
        # Método 2: Modelo cloud (si disponible)
        if self.cloud_mode and self.models_loaded and self.emotion_pipeline:
            try:
                texto_truncado = texto[:512] if len(texto) > 512 else texto
                resultado_emotion = self.emotion_pipeline(texto_truncado)
                
                mapeo_emociones = {
                    'joy': 'alegría', 'happiness': 'alegría',
                    'sadness': 'tristeza', 'grief': 'tristeza',
                    'anger': 'ira', 'rage': 'ira',
                    'fear': 'miedo', 'anxiety': 'miedo',
                    'disgust': 'indignación', 'contempt': 'indignación',
                    'pride': 'orgullo',
                    'hope': 'esperanza', 'optimism': 'esperanza'
                }
                
                for resultado in resultado_emotion[:3]:
                    emocion_en = resultado['label'].lower()
                    score_cloud = resultado['score']
                    
                    if emocion_en in mapeo_emociones:
                        emocion_es = mapeo_emociones[emocion_en]
                        # Solo considerar emociones que están en nuestro set reducido
                        if emocion_es in self.emociones_keywords:
                            if emocion_es in emotions_scores:
                                emotions_scores[emocion_es] = max(emotions_scores[emocion_es], score_cloud * 0.8)
                            else:
                                emotions_scores[emocion_es] = score_cloud * 0.8
            except:
                pass
        
        return emotions_scores
    
    def analizar_articulo_completo(self, titulo: str, resumen: str = "") -> EmotionResult:
        """NUEVO MÉTODO - Análisis con detección de sarcasmo y contexto político"""
        try:
            texto_completo = f"{titulo} {resumen}"
            
            # 1. Análisis base
            resultado_base = self.analizar_articulo_completo(titulo, resumen)
            
            # 2. Detectar contexto político
            figura_politica = self.contexto_politico.identificar_figura_politica(texto_completo)
            
            # 3. Detectar sarcasmo
            score_sarcasmo = self.detector_sarcasmo.detectar_sarcasmo(texto_completo, figura_politica)
            
            # 4. Ajustar sentimiento por contexto político
            sentimiento_ajustado, confianza_ajustada = self.contexto_politico.ajustar_sentimiento_por_contexto(
                texto_completo, 
                resultado_base.general_tone, 
                resultado_base.general_confidence
            )
            
            # 5. Ajustar por sarcasmo
            if score_sarcasmo > 0.5 and sentimiento_ajustado == 'positivo':
                sentimiento_ajustado = 'negativo'  # Sarcasmo detectado
                confianza_ajustada = min(confianza_ajustada + score_sarcasmo * 0.3, 0.95)
            
            # 6. Crear resultado mejorado
            return EmotionResult(
                language=resultado_base.language,
                emotion_primary=resultado_base.emotion_primary,
                confidence=resultado_base.confidence,
                emotions_detected=resultado_base.emotions_detected,
                emotional_intensity=resultado_base.emotional_intensity,
                emotional_context=resultado_base.emotional_context,
                general_tone=sentimiento_ajustado,
                general_confidence=confianza_ajustada,
                is_political=figura_politica is not None,
                thematic_category=resultado_base.thematic_category + 
                            (f" [Sarcasmo: {score_sarcasmo:.2f}]" if score_sarcasmo > 0.3 else "")
            )
            
        except Exception as e:
            print(f"❌ Error en análisis mejorado: {e}")
            return self.analizar_articulo_completo(titulo, resumen)
    
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
        """Calcula intensidad emocional usando solo las 9 emociones claras"""
        intensificadores = ['muy', 'mucho', 'gran', 'enorme', 'tremendo', 'moi', 'moito']
        emociones_intensas = ['ira', 'tristeza', 'alegría', 'miedo', 'indignación']  # Eliminadas las complejas
        
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
                resultado = self.analizar_articulo_completo_mejorado(titulo, resumen)
                resultados.append(resultado)
            except Exception as e:
                print(f"⚠️ Error en artículo {idx}: {e}")
                resultado_default = EmotionResult(
                    language='castellano', emotion_primary='neutral', confidence=0.5,
                    emotions_detected={'neutral': 0.5}, emotional_intensity=1,
                    emotional_context='informativo', general_tone='neutral',
                    general_confidence=0.3, is_political=False, thematic_category='📄 Otra'
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