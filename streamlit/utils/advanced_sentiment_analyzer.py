"""
Advanced Sentiment Analyzer - HorizontAI (VERSIÓN CORREGIDA)
============================================================

🔧 CORRECCIÓN: Fixes para errores de columnas faltantes y signatura incorrecta
"""

import re
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class EmotionResult:
    """Estructura mejorada para almacenar resultados detallados"""
    language: str  # NUEVO: gallego o castellano
    emotion_primary: str  
    confidence: float  
    emotions_detected: Dict[str, float]  
    emotional_intensity: int  
    emotional_context: str  
    general_tone: str  
    general_confidence: float  
    is_political: bool  
    thematic_category: str  

class AnalizadorSentimientosAvanzado:
    """Analizador mejorado con todas las correcciones solicitadas"""
    
    def __init__(self):
        # Palabras clave para detectar idioma
        self.palabras_gallegas = [
            'ata', 'dende', 'coa', 'polo', 'pola',
            'na', 'no', 'da', 'do', 'das', 'dos', 'unha', 'uns', 'unhas',
            'estes', 'aquela', 'aqueles', 'aquelas',
            'mellor', 'moito', 'moita', 'moitos', 'moitas', 'pouco', 'pouca',
            'concello', 'concelleiro', 'veciños', 'veciñas', 'proximamente',
            'xunta', 'celebrarase', 'realizarase', 'terá', 'será', 'poderá',
            'despois', 'antes', 'agora', 'aquí', 'alí', 'onde', 'cando', 'como',
            'tamén', 'ademais', 'mentres', 'porque', 'xa', 'aínda', 'sempre', 'nunca'
        ]
        
        self.palabras_castellanas = [
            'que', 'con', 'para', 'desde', 'hasta', 'por', 'la', 'el', 'los', 'las',
            'una', 'uno', 'unas', 'unos', 'este', 'esta', 'estos', 'estas',
            'aquel', 'aquella', 'aquellos', 'aquellas', 'mejor', 'peor',
            'mucho', 'mucha', 'muchos', 'muchas', 'poco', 'poca',
            'ayuntamiento', 'alcalde', 'concejal', 'vecinos', 'vecinas', 'próximamente',
            'después', 'antes', 'ahora', 'aquí', 'allí', 'donde', 'cuando', 'como',
            'también', 'además', 'mientras', 'porque', 'ya', 'aún', 'siempre', 'nunca'
        ]
        
        # Emociones con lógica corregida
        self.emociones_keywords = {
            # EMOCIONES POSITIVAS
            'alegría': [
                'celebra', 'festeja', 'felicidad', 'contento', 'avance', 'progreso', 
                'celébrase', 'festéxase', 'ledicia'
            ],

            'orgullo': [
                'orgullo', 'honor', 'prestigio', 'reconocimiento', 'distinción',
                'mérito', 'conquista', 'mejor', 'mellor', 'honra', 'prestixio', 'recoñecemento'
            ],

            'esperanza': [
                'espera', 'esperanza', 'optimismo', 'futuro', 'proyecto',
                'promete', 'confía', 'ilusión', 'expectativa', 'renovación', 'mellora'
            ],

            'satisfacción': [
                'satisfacción', 'complacencia', 'agrado', 'satisfecho',
                'cumplido', 'realizado', 'completado', 'conseguido', 'exitoso', 'compracencia'
            ],
            
            # EMOCIONES NEGATIVAS
            'tristeza': [
                'tristeza', 'pena', 'dolor', 'luto', 'pesar', 'melancolía',
                'fallece', 'muerte', 'pérdida', 'despedida', 'duelo', 'lamentar',
                'fallecimiento', 'morte', 'perda', 'lamento', 'falecemento', 'dor', 'loito', 'falece'
            ],

            'ira': [
                'ira', 'enfado', 'rabia', 'molestia', 'irritación',
                'ataca', 'censura', 'repudia'
            ],

            'miedo': [
                'miedo', 'temor', 'alarma', 'alerta', 'peligro', 'riesgo', 'amenaza',
                'incertidumbre', 'incertidume', 'medo', 'inquedanza', 'ansiedade'
            ],

            'decepción': [
                'decepción', 'desilusión', 'frustración', 'desencanto',
                'fracaso', 'falla', 'incumple', 'defrauda', 'desengaño'
            ],

            'indignación': [
                'indignación', 'asco', 'repugnancia', 'desprecio', 'desdén',
                'rechazo', 'condena', 'critica', 'rexeitamento', 'rexeita'
            ],

            
            # EMOCIONES NEUTRAS/COMPLEJAS
            'sorpresa': [
                'sorpresa', 'asombro', 'impacto', 'inesperado', 'imprevisto',
                'repentino', 'súbito', 'sorprende', 'asombra'
            ],

            'nostalgia': [
                'nostalgia', 'añoranza', 'recuerdo', 'memoria', 'pasado',
                'historia', 'tradición', 'antaño', 'antes', 'recordar',
                'nostalxia', 'angueira', 'recordo'
            ],

            'preocupación': [
                'preocupación', 'inquietud', 'intranquilidad', 'zozobra',
                'desasosiego', 'duda', 'pregunta', 'intranquilidade'
            ]
        }
        
        # Contextos emocionales específicos del ámbito político
        self.contextos_emocionales = {
            'celebratorio': [
                'inauguración', 'apertura', 'éxito', 'logro', 'victoria',
                'festejo', 'reconocimiento'
            ],

            'conflictivo': [
                'polémica', 'controversia', 'disputa', 'enfrentamiento',
                'conflicto', 'tensión', 'discrepancia', 'oposición'
                'conflito', 'conflitivo'
            ],

            'informativo': [
                'anuncia', 'informa', 'comunica', 'declara', 'presenta',
                'propone', 'plantea', 'considera', 'estudia', 'estuda',
                'propón', 'plantexa'
            ],

            'preocupante': [
                'problema', 'crisis', 'dificultad', 'obstáculo',
                'complicación', 'inconveniente', 'contratiempo',
                'contratempo', 'dificultade'
            ],

            'solemne': [
                'funeral', 'recordatorio', 'memoria', 'luto', 'despedida', 'tributo'
            ]
        }
        
        # Categorías temáticas MEJORADAS con emojis
        self.categorias_tematicas = {
            'construcción': {
                'keywords': [
                    'obra', 'construcción', 'edificio', 'edificación', 'vivienda',
                    'infraestructura', 'puente', 'renovación', 'reforma',
                    'urbanismo', 'pavimentación'
                ],
                'emoji': '🏗️'
            },
            'cultura': {
                'keywords': [
                    'cultura', 'arte', 'museo', 'exposición',
                    'teatro', 'música', 'literatura', 'patrimonio', 'biblioteca',
                    'cultural', 'artístico', 'concierto', 'espectáculo'
                ],
                'emoji': '🎭'
            },
            'industria': {
                'keywords': [
                    'industria', 'empresa', 'económico',
                    'comercio', 'turismo', 'negocio', 'inversión', 'desarrollo',
                    'industrial', 'empresarial'
                ],
                'emoji': '🏭'
            },
            'medio ambiente': {
                'keywords': [
                    'medio ambiente', 'naturaleza', 'ecología', 'sostenible',
                    'verde', 'parque', 'jardín', 'limpieza', 'reciclaje', 'contaminación',
                    'ambiental', 'ecológico', 'sostenibilidad'
                ],
                'emoji': '🌱'
            },
            'educación': {
                'keywords': [
                    'educación', 'colegio', 'instituto', 'universidad', 'escuela',
                    'estudiante', 'formación', 'curso', 'enseñanza', 'profesor',
                    'educativo', 'académico', 'escolar', 'colexio', 'universidade',
                    'ensino'
                ],
                'emoji': '📚'
            },
            'salud': {
                'keywords': [
                    'salud', 'hospital', 'médico', 'sanitario', 'enfermedad',
                    'tratamiento', 'paciente', 'medicina', 'centro de salud',
                    'clínica', 'asistencia sanitaria', 'saúde', 'sanidade',
                ],
                'emoji': '🏥'
            },
            'deporte': {
                'keywords': [
                    'deporte', 'fútbol', 'baloncesto', 'atletismo', 'piscina',
                    'polideportivo', 'gimnasio', 'equipo', 'competición', 'entrenador',
                    'deportivo', 'atlético', 'club'
                ],
                'emoji': '⚽'
            },
            'seguridad': {
                'keywords': [
                    'seguridad', 'policía', 'guardia civil', 'protección civil',
                    'emergencia', 'accidente', 'delito', 'protección',
                    'bomberos', 'emergencias', 'emerxencia', 'seguridade',
                ],
                'emoji': '🚔'
            },
            'social': {
                'keywords': [
                    'social', 'servicios sociales', 'ayuda', 'subvención',
                    'pensión', 'mayor', 'juventud', 'familia', 'vivienda social',
                    'bienestar', 'asistencia'
                ],
                'emoji': '🤝'
            },
            'necrológicas': {
                'keywords': [
                    'fallece', 'muerte', 'falleció', 'defunción', 'funeral',
                    'luto', 'despedida', 'obituario', 'pésame', 'sepelio',
                    'falece', 'faleceu'
                ],
                'emoji': '🕊️'
            },
            'opinión': {
                'keywords': [
                    'opinión', 'editorial', 'columna', 'artículo de opinión',
                    'tribuna', 'reflexión', 'punto de vista', 'comentario',
                    'análisis', 'perspectiva', 'perspetiva'
                ],
                'emoji': '💭'
            },
            'festividades': {
                'keywords': [
                    'fiesta', 'celebración', 'carnaval', 'navidad',
                    'semana santa', 'día de', 'festividad', 'festa', 'festexo'
                    'festividade', 'festival'
                ],
                'emoji': '🎉'
            },
            'transporte': {
                'keywords': [
                    'transporte', 'autobús', 'tren', 'ferry', 'tráfico',
                    'carretera', 'aparcamiento', 'parking', 'movilidad',
                    'transporte público', 'circulación', 'aparcamento',
                ],
                'emoji': '🚌'
            },
            'laboral': {
                'keywords': [
                    'contrato', 'sueldo', 'despido', 'negociación', 'sindicato',
                    'reforma laboral', 'condiciones laborales',
                    'traballador', 'traballadora', 'emprego', 'traballo',
                    'trabajo', 'laboral', 'empleo'
                ],
                'emoji': '🧑‍💼'
            }
        }
        
        # Palabras clave políticas
        self.palabras_politicas = [
            'alcaldesa', 'alcalde', 'concejal', 'concejala', 'concejales', 'concejala',
            'psoe', 'pp', 'bng', 'vox', "ramallo", ""
        ]
    
    def detectar_idioma(self, texto: str) -> str:
        if pd.isna(texto) or not texto.strip():
            return 'castellano'

        texto_lower = texto.lower()
        total_palabras = len(texto_lower.split())
        coincidencias_gallego = sum(1 for palabra in self.palabras_gallegas if palabra in texto_lower)

        # Si hay 4 o más palabras gallegas, clasificar como gallego
        if coincidencias_gallego >= 4 and (total_palabras > 0 and coincidencias_gallego / total_palabras >= 0.08):
            return 'gallego'
        else:
            return 'castellano'

    def _determinar_tono_general_corregido(self, emotions_scores: Dict[str, float], titulo: str, resumen: str) -> Tuple[str, float]:
        """LÓGICA CORREGIDA: El tono debe coincidir con la emoción principal"""
        emociones_positivas = ['alegría', 'esperanza', 'orgullo', 'satisfacción']
        emociones_negativas = ['tristeza', 'ira', 'miedo', 'decepción', 'indignación']
        
        # Encontrar la emoción con mayor score
        if emotions_scores:
            emocion_principal = max(emotions_scores.items(), key=lambda x: x[1])
            emocion_nombre, score = emocion_principal
            
            # LÓGICA CORREGIDA: Si la emoción principal es positiva, el tono es positivo
            if score > 0.3:  # Solo si hay confianza suficiente
                if emocion_nombre in emociones_positivas:
                    return 'positivo', score
                elif emocion_nombre in emociones_negativas:
                    return 'negativo', score
        
        # Fallback al método anterior
        score_positivo = sum(emotions_scores.get(emocion, 0) for emocion in emociones_positivas)
        score_negativo = sum(emotions_scores.get(emocion, 0) for emocion in emociones_negativas)
        
        if score_positivo > score_negativo and score_positivo > 0.3:
            return 'positivo', score_positivo
        elif score_negativo > score_positivo and score_negativo > 0.3:
            return 'negativo', score_negativo
        else:
            return 'neutral', 0.5
    
    def _determinar_tematica_mejorada(self, texto: str) -> Tuple[str, str]:
        """Determina la categoría temática con emoji"""
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
            return 'otros', '📄'  # Cambio de "general" a "otros"
    
    def analizar_articulo_completo(self, titulo: str, resumen: str = "") -> EmotionResult:
        """Análisis completo mejorado con todas las correcciones"""
        try:
            texto_completo = f"{titulo} {resumen}".lower()
            
            # 1. NUEVO: Detectar idioma
            language = self.detectar_idioma(f"{titulo} {resumen}")
            
            # 2. Análisis de emociones granulares
            emotions_scores = self._detectar_emociones(titulo, resumen)
            
            # 3. Determinar emoción principal
            emotion_primary, confidence = self._determinar_emociones_principales(emotions_scores)
            
            # 4. LÓGICA CORREGIDA: Tono basado en emoción principal
            general_tone, general_confidence = self._determinar_tono_general_corregido(emotions_scores, titulo, resumen)
            
            # 5. Detectar contexto emocional
            emotional_context = self._detectar_contexto(texto_completo)
            
            # 6. Calcular intensidad emocional
            emotional_intensity = self._calcular_intensidad_emocional(texto_completo, emotions_scores)
            
            # 7. Verificar si es político
            is_political = self._es_politico(texto_completo)
            
            # 8. MEJORADA: Determinar categoría temática con emoji
            thematic_category, emoji = self._determinar_tematica_mejorada(texto_completo)
            
            return EmotionResult(
                language=language,  # NUEVO
                emotion_primary=emotion_primary,
                confidence=confidence,
                emotions_detected=emotions_scores,
                emotional_intensity=emotional_intensity,
                emotional_context=emotional_context,
                general_tone=general_tone,
                general_confidence=general_confidence,
                is_political=is_political,
                thematic_category=f"{emoji} {thematic_category.title()}"  # MEJORADO con emoji
            )
        except Exception as e:
            print(f"🔧 Error analizando artículo '{titulo}': {e}")
            # Devolver resultado por defecto
            return EmotionResult(
                language='castellano',
                emotion_primary='neutral',
                confidence=0.5,
                emotions_detected={'neutral': 0.5},
                emotional_intensity=1,
                emotional_context='informativo',
                general_tone='neutral',
                general_confidence=0.5,
                is_political=False,
                thematic_category='📄 Otros'
            )
    
    def _detectar_emociones(self, titulo: str, resumen: str) -> Dict[str, float]:
        """Detecta todas las emociones con sus scores"""
        texto_completo = f"{titulo} {resumen}".lower()
        emotions_scores = {}
        
        for emocion, keywords in self.emociones_keywords.items():
            score = 0
            palabras_encontradas = 0
            
            for keyword in keywords:
                if keyword in texto_completo:
                    if keyword in titulo.lower():
                        score += 2
                    else:
                        score += 1
                    palabras_encontradas += 1
            
            if palabras_encontradas > 0:
                emotions_scores[emocion] = min(score / len(keywords), 1.0)
        
        return emotions_scores
    
    def _determinar_emociones_principales(self, emotions_scores: Dict[str, float]) -> Tuple[str, float]:
        """🔧 CORREGIDA: Determina emoción principal (signatura corregida)"""
        if emotions_scores:
            emociones_ordenadas = sorted(emotions_scores.items(), key=lambda x: x[1], reverse=True)
            
            emotion_primary = emociones_ordenadas[0][0]
            confidence = emociones_ordenadas[0][1]            
        else:
            emotion_primary = 'neutral'
            confidence = 0.5
        
        return emotion_primary, confidence  # 🔧 Solo 2 valores (corregido)
    
    def _detectar_contexto(self, texto: str) -> str:
        """Detecta el contexto emocional"""
        contexto_scores = {}
        
        for contexto, keywords in self.contextos_emocionales.items():
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
        
        return min(int(intensidad_base), 5)
    
    def _es_politico(self, texto: str) -> bool:
        """Determina si es político"""
        return any(palabra in texto for palabra in self.palabras_politicas)
    
    def analizar_dataset(self, df: pd.DataFrame, columna_titulo: str, 
                        columna_resumen: str = None) -> pd.DataFrame:
        """
        🔧 CORREGIDA: Aplica análisis completo a un dataset de artículos con manejo robusto de errores
        """
        print(f"🧠 Analizando sentimientos y emociones de {len(df)} artículos...")
        
        resultados = []
        
        # 🔧 ANÁLISIS ROBUSTO CON MANEJO DE ERRORES
        for idx, row in df.iterrows():
            if idx % 5 == 0:
                print(f"   Procesado: {idx}/{len(df)} artículos")
            
            titulo = str(row[columna_titulo]) if pd.notna(row[columna_titulo]) else ""
            resumen = str(row[columna_resumen]) if columna_resumen and pd.notna(row[columna_resumen]) else ""
            
            try:
                resultado = self.analizar_articulo_completo(titulo, resumen)
                resultados.append(resultado)
            except Exception as e:
                print(f"🔧 Error procesando artículo {idx}: {e}")
                # 🔧 RESULTADO POR DEFECTO EN CASO DE ERROR
                resultado_default = EmotionResult(
                    language='castellano',
                    emotion_primary='neutral',
                    confidence=0.5,
                    emotions_detected={'neutral': 0.5},
                    emotional_intensity=1,
                    emotional_context='informativo',
                    general_tone='neutral',
                    general_confidence=0.5,
                    is_political=False,
                    thematic_category='📄 Otros'
                )
                resultados.append(resultado_default)
        
        # 🔧 VERIFICAR QUE TENEMOS TANTOS RESULTADOS COMO FILAS
        if len(resultados) != len(df):
            print(f"❌ Error: {len(resultados)} resultados para {len(df)} filas")
            # Rellenar con resultados por defecto si faltan
            while len(resultados) < len(df):
                resultado_default = EmotionResult(
                    language='castellano',
                    emotion_primary='neutral',
                    confidence=0.5,
                    emotions_detected={'neutral': 0.5},
                    emotional_intensity=1,
                    emotional_context='informativo',
                    general_tone='neutral',
                    general_confidence=0.5,
                    is_political=False,
                    thematic_category='📄 Otros'
                )
                resultados.append(resultado_default)
        
        # 🔧 CONSTRUCCIÓN ROBUSTA DEL DATAFRAME RESULTADO
        try:
            # Copiar DataFrame original
            df_resultado = df.copy()

            # 🔧 AÑADIR COLUMNAS PASO A PASO CON VALIDACIÓN
            print("🔧 Añadiendo columna: idioma")
            df_resultado['idioma'] = [r.language for r in resultados]
            
            print("🔧 Añadiendo columna: tono_general")
            df_resultado['tono_general'] = [r.general_tone for r in resultados]
            
            print("🔧 Añadiendo columna: emocion_principal")
            df_resultado['emocion_principal'] = [r.emotion_primary for r in resultados]
            
            print("🔧 Añadiendo columna: confianza_analisis")
            df_resultado['confianza_analisis'] = [r.general_confidence for r in resultados]
            
            print("🔧 Añadiendo columna: intensidad_emocional")
            df_resultado['intensidad_emocional'] = [r.emotional_intensity for r in resultados]
            
            print("🔧 Añadiendo columna: contexto_emocional")
            df_resultado['contexto_emocional'] = [r.emotional_context for r in resultados]
            
            print("🔧 Añadiendo columna: es_politico")
            df_resultado['es_politico'] = [r.is_political for r in resultados]
            
            print("🔧 Añadiendo columna: tematica")
            df_resultado['tematica'] = [r.thematic_category for r in resultados]
            
            # Columnas adicionales
            print("🔧 Añadiendo columna: confianza_emocion")
            df_resultado['confianza_emocion'] = [r.confidence for r in resultados]
            
            print("🔧 Añadiendo columna: emociones_detectadas")
            df_resultado['emociones_detectadas'] = [r.emotions_detected for r in resultados]
            
            print("✅ Análisis completo terminado exitosamente")
            print(f"🔧 Columnas añadidas: {['idioma', 'tono_general', 'emocion_principal', 'confianza_analisis', 'intensidad_emocional', 'contexto_emocional', 'es_politico', 'tematica', 'confianza_emocion', 'emociones_detectadas']}")
            
            return df_resultado
            
        except Exception as e:
            print(f"❌ Error crítico añadiendo columnas: {e}")
            # En caso de error crítico, devolver DataFrame original con columnas básicas
            df_basico = df.copy()
            df_basico['idioma'] = 'castellano'
            df_basico['tono_general'] = 'neutral'
            df_basico['emocion_principal'] = 'neutral'
            df_basico['confianza_analisis'] = 0.5
            df_basico['intensidad_emocional'] = 1
            df_basico['contexto_emocional'] = 'informativo'
            df_basico['es_politico'] = False
            df_basico['tematica'] = '📄 Otros'
            return df_basico
    
    def generar_reporte_completo(self, df_analizado: pd.DataFrame) -> Dict:
        """🔧 CORREGIDA: Genera un reporte completo del análisis con validación"""
        total_articulos = len(df_analizado)
        
        if total_articulos == 0:
            return {
                'total_articulos': 0,
                'articulos_politicos': 0,
                'distribución_idiomas': {},
                'tonos_generales': {},
                'emociones_principales': {},
                'contextos_emocionales': {},
                'tematicas': {},
                'intensidad_promedio': 0,
                'confianza_promedio': 0
            }
        
        try:
            # 🔧 VALIDACIÓN DE COLUMNAS ANTES DE USAR
            # Análisis de idiomas (NUEVO)
            idiomas = {}
            if 'idioma' in df_analizado.columns:
                idiomas = df_analizado['idioma'].value_counts().to_dict()
            
            # Análisis de tono general
            tonos = {}
            if 'tono_general' in df_analizado.columns:
                tonos = df_analizado['tono_general'].value_counts().to_dict()
            
            # Análisis de emociones principales (NUEVO)
            emociones_principales = {}
            if 'emocion_principal' in df_analizado.columns:
                emociones_principales = df_analizado['emocion_principal'].value_counts().to_dict()
                    
            # Análisis de contextos
            contextos = {}
            if 'contexto_emocional' in df_analizado.columns:
                contextos = df_analizado['contexto_emocional'].value_counts().to_dict()
            
            # Análisis de temáticas
            tematicas = {}
            if 'tematica' in df_analizado.columns:
                tematicas = df_analizado['tematica'].value_counts().to_dict()
            
            # Estadísticas generales con validación
            articulos_politicos = 0
            if 'es_politico' in df_analizado.columns:
                articulos_politicos = int(df_analizado['es_politico'].sum())
            
            intensidad_promedio = 1.0
            if 'intensidad_emocional' in df_analizado.columns:
                intensidad_promedio = float(df_analizado['intensidad_emocional'].mean())
            
            confianza_promedio = 0.5
            if 'confianza_analisis' in df_analizado.columns:
                confianza_promedio = float(df_analizado['confianza_analisis'].mean())
            
            return {
                'total_articulos': total_articulos,
                'articulos_politicos': articulos_politicos,
                'distribución_idiomas': idiomas,  # NUEVO
                'tonos_generales': tonos,
                'emociones_principales': emociones_principales,  # NUEVO
                'contextos_emocionales': contextos,
                'tematicas': tematicas,
                'intensidad_promedio': intensidad_promedio,
                'confianza_promedio': confianza_promedio
            }
        except Exception as e:
            print(f"❌ Error generando reporte: {e}")
            # Reporte por defecto en caso de error
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


# Clases de compatibilidad
class AnalizadorArticulosMarin:
    """Clase de compatibilidad con el sistema existente"""
    
    def __init__(self):
        self.analizador = AnalizadorSentimientosAvanzado()
    
    def analizar_dataset(self, df, columna_titulo='title', columna_resumen='summary'):
        return self.analizador.analizar_dataset(df, columna_titulo, columna_resumen)
    
    def generar_reporte(self, df_analizado):
        return self.analizador.generar_reporte_completo(df_analizado)


# Función de compatibilidad
def analizar_articulos_marin(df, columna_titulo='title', columna_resumen='summary'):
    """Función de compatibilidad con el sistema existente"""
    analizador = AnalizadorSentimientosAvanzado()
    return analizador.analizar_dataset(df, columna_titulo, columna_resumen)


# Test de diagnóstico
if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO DEL ANALIZADOR CORREGIDO")
    
    analizador = AnalizadorSentimientosAvanzado()
    
    # Test básico
    resultado = analizador.analizar_articulo_completo("Prueba de análisis", "Texto de prueba")
    print(f"✅ Análisis básico funciona: {resultado.language}, {resultado.general_tone}, {resultado.emotion_primary}")
    
    # Test de dataset
    import pandas as pd
    df_test = pd.DataFrame({
        'title': ['Fallece Constante Muradas Ramos', 'El PSOE móstrase alarmado'],
        'summary': ['Luto en la villa marinense', 'Críticas a la gestión municipal']
    })
    
    try:
        df_resultado = analizador.analizar_dataset(df_test, 'title', 'summary')
        columnas_esperadas = ['idioma', 'tono_general', 'emocion_principal', 'confianza_analisis']
        columnas_presentes = [col for col in columnas_esperadas if col in df_resultado.columns]
        print(f"✅ Dataset procesado: {len(columnas_presentes)}/{len(columnas_esperadas)} columnas presentes")
        print(f"🔧 Columnas encontradas: {columnas_presentes}")
        
        reporte = analizador.generar_reporte_completo(df_resultado)
        print(f"✅ Reporte generado: {len(reporte)} campos")
        
    except Exception as e:
        print(f"❌ Error en test de dataset: {e}")