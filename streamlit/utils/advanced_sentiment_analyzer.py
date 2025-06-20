"""
Analizadores de Sentimientos Especializados - HorizontAI
=======================================================

Sistema dual con analizadores específicos para artículos y comentarios.
"""

import re
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass
from functools import lru_cache

@dataclass
class EmotionResult:
    """Estructura unificada para resultados de análisis"""
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
    analyzer_type: str  # ← NUEVO: 'article' o 'comment'

class BaseLanguageDetector:
    """Detector de idioma compartido"""
    def __init__(self):
        self.palabras_gallegas = [
            'cando', 'vez', 'ás veces', 'unha', 'persoa', 'moi', 'mais', 'pode',
            'parabéns', 'vir', 'agora', 'convenza', 'nega', 'cambiar', 'rúas',
            'concello', 'veciños', 'celebrarase', 'realizarase', 'terá', 'poderá',
            'dende', 'coa', 'polo', 'pola', 'na', 'no', 'da', 'do', 'das', 'dos'
        ]
        
    def detectar_idioma(self, texto: str) -> str:
        """Detecta gallego vs castellano"""
        texto_lower = texto.lower()
        
        # Palabras que GARANTIZAN gallego
        gallego_fuerte = ['grazas', 'moi', 'teña', 'non', 'pois', 'súa']
        if any(palabra in texto_lower for palabra in gallego_fuerte):
            return 'gallego'
        
        # Conteo de palabras gallegas
        palabras_texto = texto_lower.split()
        coincidencias = sum(1 for palabra in self.palabras_gallegas 
                          if palabra in palabras_texto)
        
        if coincidencias >= 1 and len(palabras_texto) <= 10:  
            return 'gallego'
        
        return 'castellano'

class PoliticalContextDetector:
    """Detector de contexto político mejorado"""
    def __init__(self):
        self.terminos_politicos = [
            'pp', 'psoe', 'bng', 'partido popular', 'socialista', 'bloque',
            'alcaldesa', 'alcalde', 'gobierno', 'dictadura', 'franco', 'franquista',
            'democracia', 'demócrata', 'memoria histórica', 'golpismo',
            'carmela silva', 'feijoo', 'politico', 'política', 'prisión',
            'concello', 'concejales', 'xunta', 'ministros', 'borbones'
        ]
        
        self.terminos_administrativos = [
            'recaudación del estado', 'servicios públicos', 'cesión de terrenos',
            'funcionarios', 'horas extras', 'adjudicación', 'concesión',
            'licitación', 'subvención', 'presupuesto municipal'
        ]
    
    def es_politico(self, texto: str) -> bool:
        """Detecta contenido político"""
        texto_lower = texto.lower()
        todos_terminos = self.terminos_politicos + self.terminos_administrativos
        return any(termino in texto_lower for termino in todos_terminos)

class ArticleSentimentAnalyzer(BaseLanguageDetector, PoliticalContextDetector):
    """
    🗞️ ANALIZADOR ESPECIALIZADO PARA ARTÍCULOS
    
    Diseñado para detectar:
    - Controversias sutiles en lenguaje periodístico
    - Emociones implícitas en contexto político-administrativo
    - Tono profesional con matices
    """
    
    def __init__(self):
        super().__init__()
        
        # 🗞️ PATRONES ESPECÍFICOS PARA ARTÍCULOS PERIODÍSTICOS
        self.patrones_controversy = {
            'sutil_negativo': [
                'a pesar de que', 'sin embargo', 'no obstante', 'aunque',
                'cuestiona', 'critica', 'denuncia', 'irregular', 'polémico',
                'rechaza', 'renuncia', 'abandona', 'dimite', 'suspende',
                'prefirieron renunciar', 'otras ofertas de mayor cuantía',
                'investigación', 'expediente', 'sanción'
            ],
            'sutil_positivo': [
                'logra', 'consigue', 'alcanza', 'inaugura', 'estrena',
                'celebra', 'homenaje', 'reconocimiento', 'galardón',
                'éxito', 'triunfo', 'victoria', 'aprobación unánime',
                'récord', 'histórico', 'primera vez'
            ],
            'administrativo_positivo': [
                'adjudicación', 'concesión', 'aprobación', 'autorización',
                'mejora', 'modernización', 'renovación', 'ampliación',
                'inversión', 'subvención', 'financiación'
            ],
            'administrativo_negativo': [
                'paralizado', 'retrasado', 'suspendido', 'rechazado',
                'denegado', 'conflicto', 'disputa', 'irregularidad'
            ]
        }
        
        # 🗞️ EMOCIONES ESPECÍFICAS PARA NOTICIAS
        self.emociones_articulos = {
            'expectativa': [
                'espera', 'prevé', 'planifica', 'proyecta', 'próximo',
                'futuro', 'programado', 'anunciado'
            ],
            'preocupación': [
                'alerta', 'advierte', 'riesgo', 'peligro', 'emergencia',
                'urgente', 'grave', 'serio', 'preocupante'
            ],
            'satisfacción': [
                'satisfecho', 'contento', 'agradecido', 'complacido',
                'exitoso', 'logrado', 'conseguido'
            ],
            'decepción': [
                'decepcionado', 'frustrado', 'lamentable', 'desafortunado',
                'inesperado', 'sorprendente negativamente'
            ],
            'orgullo': [
                'orgulloso', 'honor', 'prestigio', 'reconocimiento',
                'mérito', 'destacado', 'sobresaliente'
            ]
        }
        
        # 🗞️ CATEGORÍAS TEMÁTICAS ESPECÍFICAS
        self.categorias_tematicas = {
            'administracion': {
                'keywords': [
                    'adjudicación', 'concesión', 'licitación', 'concurso público',
                    'presupuesto', 'ordenanza', 'normativa', 'reglamento'
                ],
                'emoji': '🏛️'
            },
            'necrologicas': {
                'keywords': [
                    'fallece', 'falleció', 'muerte', 'esquela', 'funeral',
                    'sepelio', 'tanatorio', 'velatorio', 'defunción'
                ],
                'emoji': '🕊️'
            },
            'eventos': {
                'keywords': [
                    'festival', 'fiesta', 'celebración', 'evento', 'concierto',
                    'exposición', 'muestra', 'certamen'
                ],
                'emoji': '🎉'
            },
            'deportes': {
                'keywords': [
                    'boxeo', 'fútbol', 'baloncesto', 'deporte', 'competición',
                    'campeonato', 'torneo', 'club deportivo'
                ],
                'emoji': '⚽'
            },
            'infraestructuras': {
                'keywords': [
                    'obras', 'construcción', 'paseo marítimo', 'carretera',
                    'edificio', 'instalaciones', 'mejoras'
                ],
                'emoji': '🏗️'
            }
        }
    
    def analizar_tono_articulo(self, texto: str) -> Tuple[str, float]:
        """Análisis específico para artículos periodísticos"""
        texto_lower = texto.lower()
        
        score_positivo = 0.0
        score_negativo = 0.0
        
        # Controversias sutiles (peso alto)
        for patron in self.patrones_controversy['sutil_negativo']:
            if patron in texto_lower:
                score_negativo += 2.0
        
        for patron in self.patrones_controversy['sutil_positivo']:
            if patron in texto_lower:
                score_positivo += 2.0
        
        # Términos administrativos
        for patron in self.patrones_controversy['administrativo_negativo']:
            if patron in texto_lower:
                score_negativo += 1.5
                
        for patron in self.patrones_controversy['administrativo_positivo']:
            if patron in texto_lower:
                score_positivo += 1.5
        
        # 🗞️ UMBRALES ESPECÍFICOS PARA ARTÍCULOS (más conservadores)
        if score_positivo > score_negativo and score_positivo >= 1.5:
            return 'positivo', min(0.7 + (score_positivo * 0.1), 0.9)
        elif score_negativo > score_positivo and score_negativo >= 1.5:
            return 'negativo', min(0.7 + (score_negativo * 0.1), 0.9)
        else:
            return 'neutral', 0.7
    
    def analizar_emociones_articulo(self, texto: str) -> Dict[str, float]:
        """Detección de emociones específicas en artículos"""
        emotions_scores = {}
        texto_lower = texto.lower()
        
        for emocion, keywords in self.emociones_articulos.items():
            score_total = 0.0
            
            for keyword in keywords:
                if keyword in texto_lower:
                    score_total += 1.5
            
            if score_total > 0:
                emotions_scores[emocion] = min(score_total / len(keywords), 1.0)
        
        return emotions_scores
    
    def determinar_tematica_articulo(self, texto: str) -> Tuple[str, str]:
        """Categorización temática específica para artículos"""
        texto_lower = texto.lower()
        
        for categoria, info in self.categorias_tematicas.items():
            score = sum(1 for keyword in info['keywords'] if keyword in texto_lower)
            if score > 0:
                return categoria, info['emoji']
        
        return 'otra', '📄'

class CommentSentimentAnalyzer(BaseLanguageDetector, PoliticalContextDetector):
    """
    💬 ANALIZADOR ESPECIALIZADO PARA COMENTARIOS
    
    Diseñado para detectar:
    - Emociones directas y explícitas
    - Lenguaje coloquial y argot local
    - Opiniones claras y contundentes
    """
    
    def __init__(self):
        super().__init__()
        
        # 💬 PATRONES ESPECÍFICOS PARA COMENTARIOS DIRECTOS
        self.emociones_comentarios = {
            'ira': [
                'asqueroso', 'vergüenza', 'indignante', 'caradurismo',
                'que raro que', 'madre mía', 'barbaridad', 'delincuentes',
                'prisión', 'tiene que estar en prisión'
            ],
            'alegría': [
                'me gusta', 'que bueno', 'genial', 'perfecto', 'ole',
                'bravo', 'fenomenal', 'estupendo', 'maravilloso',
                'fantástico', '😂', '👏', '❤️'
            ],
            'desprecio': [
                'lamentable', 'patético', 'ridículo', 'penoso',
                'demagogia a todo trapo', 'espectáculo circense'
            ],
            'satisfacción': [
                'menos mal que', 'por fin', 'ya era hora',
                'me parece bien', 'tiene razón', 'correcto'
            ],
            'decepción': [
                'que pena', 'qué lástima', 'decepcionante',
                'cada vez da más pena', 'perdió el norte'
            ],
            'esperanza': [
                'ojalá que', 'espero que', 'confío en que',
                'futuro inmenso', 'se lo merece'
            ]
        }
        
        # 💬 PATRONES DE SARCASMO E IRONÍA
        self.patrones_sarcasmo = [
            'menos mal que', 'por supuesto', 'claro que sí',
            'faltaría más', 'venga aplaudamos', 'que sorpresa'
        ]
    
    def analizar_tono_comentario(self, texto: str) -> Tuple[str, float]:
        """Análisis específico para comentarios directos"""
        texto_lower = texto.lower()
        
        score_positivo = 0.0
        score_negativo = 0.0
        
        # Emociones directas (más sensible)
        for emocion, keywords in self.emociones_comentarios.items():
            for keyword in keywords:
                if keyword in texto_lower:
                    if emocion in ['ira', 'desprecio', 'decepción']:
                        score_negativo += 1.0
                    elif emocion in ['alegría', 'satisfacción', 'esperanza']:
                        score_positivo += 1.0
        
        # Detectar sarcasmo (invertir polaridad)
        es_sarcastico = any(patron in texto_lower for patron in self.patrones_sarcasmo)
        if es_sarcastico and score_positivo > 0:
            score_positivo, score_negativo = score_negativo, score_positivo
        
        # 💬 UMBRALES ESPECÍFICOS PARA COMENTARIOS (más sensibles)
        if score_positivo > score_negativo and score_positivo >= 0.5:
            return 'positivo', min(0.6 + (score_positivo * 0.2), 0.95)
        elif score_negativo > score_positivo and score_negativo >= 0.5:
            return 'negativo', min(0.6 + (score_negativo * 0.2), 0.95)
        else:
            return 'neutral', 0.6
    
    def analizar_emociones_comentario(self, texto: str) -> Dict[str, float]:
        """Detección de emociones específicas en comentarios"""
        emotions_scores = {}
        texto_lower = texto.lower()
        
        for emocion, keywords in self.emociones_comentarios.items():
            score_total = 0.0
            
            for keyword in keywords:
                if keyword in texto_lower:
                    score_total += 2.0  # Más peso para emociones directas
            
            if score_total > 0:
                emotions_scores[emocion] = min(score_total / len(keywords), 1.0)
        
        return emotions_scores

class HybridSentimentCoordinator:
    """
    🎯 COORDINADOR PRINCIPAL
    
    Decide qué analizador usar según el contexto y coordina los resultados.
    """
    
    def __init__(self):
        self.article_analyzer = ArticleSentimentAnalyzer()
        self.comment_analyzer = CommentSentimentAnalyzer()
    
    def analizar_con_contexto(self, texto: str, contexto: str = 'auto') -> EmotionResult:
        """
        Analiza texto usando el analizador apropiado
        
        Args:
            texto: Texto a analizar
            contexto: 'article', 'comment', o 'auto' para detección automática
        """
        
        # Detección automática de contexto
        if contexto == 'auto':
            contexto = self._detectar_contexto(texto)
        
        # Seleccionar analizador apropiado
        if contexto == 'article':
            return self._analizar_articulo(texto)
        else:
            return self._analizar_comentario(texto)
    
    def _detectar_contexto(self, texto: str) -> str:
        """Detecta automáticamente si es artículo o comentario"""
        # Heurísticas para detectar contexto
        longitud = len(texto.split())
        
        # Indicadores de artículo
        indicadores_articulo = [
            'adjudicado', 'concedido', 'aprobado', 'fallece',
            'celebrará', 'inauguró', 'según fuentes'
        ]
        
        # Indicadores de comentario
        indicadores_comentario = [
            'me parece', 'creo que', 'opino', 'no entiendo',
            'que vergüenza', 'genial', 'ole'
        ]
        
        tiene_articulo = any(ind in texto.lower() for ind in indicadores_articulo)
        tiene_comentario = any(ind in texto.lower() for ind in indicadores_comentario)
        
        if tiene_articulo or longitud > 15:
            return 'article'
        elif tiene_comentario or longitud < 8:
            return 'comment'
        else:
            return 'article'  # Por defecto
    
    def _analizar_articulo(self, texto: str) -> EmotionResult:
        """Análisis usando el analizador de artículos"""
        analyzer = self.article_analyzer
        
        # Detectar idioma
        language = analyzer.detectar_idioma(texto)
        
        # Análisis de tono
        general_tone, general_confidence = analyzer.analizar_tono_articulo(texto)
        
        # Análisis de emociones
        emotions_scores = analyzer.analizar_emociones_articulo(texto)
        
        # Emoción principal
        if emotions_scores:
            emotion_primary = max(emotions_scores.items(), key=lambda x: x[1])[0]
            confidence = max(emotions_scores.values())
        else:
            emotion_primary = 'neutral'
            confidence = 0.5
        
        # Intensidad (más conservadora para artículos)
        emotional_intensity = 2 if emotions_scores else 1
        
        # Temática
        tematica, emoji = analyzer.determinar_tematica_articulo(texto)
        thematic_category = f"{emoji} {tematica.title()}"
        
        # Contexto y política
        is_political = analyzer.es_politico(texto)
        emotional_context = 'informativo' if general_tone == 'neutral' else 'controvertido'
        
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
            thematic_category=thematic_category,
            analyzer_type='article'
        )
    
    def _analizar_comentario(self, texto: str) -> EmotionResult:
        """Análisis usando el analizador de comentarios"""
        analyzer = self.comment_analyzer
        
        # Detectar idioma
        language = analyzer.detectar_idioma(texto)
        
        # Análisis de tono
        general_tone, general_confidence = analyzer.analizar_tono_comentario(texto)
        
        # Análisis de emociones
        emotions_scores = analyzer.analizar_emociones_comentario(texto)
        
        # Emoción principal
        if emotions_scores:
            emotion_primary = max(emotions_scores.items(), key=lambda x: x[1])[0]
            confidence = max(emotions_scores.values())
        else:
            emotion_primary = 'neutral'
            confidence = 0.5
        
        # Intensidad (más alta para comentarios directos)
        emotional_intensity = 3 + len(emotions_scores) if emotions_scores else 2
        emotional_intensity = min(emotional_intensity, 5)
        
        # Temática simplificada para comentarios
        is_political = analyzer.es_politico(texto)
        thematic_category = '🏛️ Política' if is_political else '💬 Opinión'
        
        # Contexto emocional
        if general_tone == 'positivo':
            emotional_context = 'apoyo'
        elif general_tone == 'negativo':
            emotional_context = 'crítica'
        else:
            emotional_context = 'neutral'
        
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
            thematic_category=thematic_category,
            analyzer_type='comment'
        )

# Funciones de compatibilidad para la aplicación existente
class AnalizadorArticulosMarin:
    """Clase de compatibilidad que usa el sistema especializado"""
    
    def __init__(self):
        self.coordinator = HybridSentimentCoordinator()
    
    def analizar_dataset(self, df, columna_titulo='title', columna_resumen='summary'):
        """Analiza dataset detectando automáticamente el contexto"""
        resultados = []
        
        for _, row in df.iterrows():
            titulo = str(row[columna_titulo]) if pd.notna(row[columna_titulo]) else ""
            resumen = str(row[columna_resumen]) if columna_resumen and pd.notna(row[columna_resumen]) else ""
            
            # Texto completo para análisis
            texto_completo = f"{titulo} {resumen}".strip()
            
            # Decidir contexto basado en la estructura del DataFrame
            if 'comment_author' in row or 'likes' in row:
                contexto = 'comment'
            else:
                contexto = 'article'
            
            resultado = self.coordinator.analizar_con_contexto(texto_completo, contexto)
            resultados.append(resultado)
        
        # Convertir a DataFrame con columnas esperadas
        df_resultado = df.copy()
        
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
        df_resultado['tipo_analizador'] = [r.analyzer_type for r in resultados]  # ← NUEVO
        
        return df_resultado
    
    def generar_reporte(self, df_analizado):
        """Genera reporte considerando el tipo de analizador usado"""
        total_articulos = len(df_analizado)
        
        if total_articulos == 0:
            return {'total_articulos': 0}
        
        # Separar por tipo de analizador
        articulos = df_analizado[df_analizado.get('tipo_analizador', 'article') == 'article']
        comentarios = df_analizado[df_analizado.get('tipo_analizador', 'comment') == 'comment']
        
        reporte = {
            'total_articulos': total_articulos,
            'total_articulos_periodisticos': len(articulos),
            'total_comentarios': len(comentarios),
            'articulos_politicos': int(df_analizado.get('es_politico', pd.Series()).sum()),
            'distribución_idiomas': df_analizado.get('idioma', pd.Series()).value_counts().to_dict(),
            'tonos_generales': df_analizado.get('tono_general', pd.Series()).value_counts().to_dict(),
            'emociones_principales': df_analizado.get('emocion_principal', pd.Series()).value_counts().to_dict(),
            'contextos_emocionales': df_analizado.get('contexto_emocional', pd.Series()).value_counts().to_dict(),
            'tematicas': df_analizado.get('tematica', pd.Series()).value_counts().to_dict(),
            'intensidad_promedio': float(df_analizado.get('intensidad_emocional', pd.Series()).mean()),
            'confianza_promedio': float(df_analizado.get('confianza_analisis', pd.Series()).mean())
        }
        
        return reporte

def analizar_articulos_marin(df, columna_titulo='title', columna_resumen='summary'):
    """Función de compatibilidad"""
    analizador = AnalizadorArticulosMarin()
    return analizador.analizar_dataset(df, columna_titulo, columna_resumen)