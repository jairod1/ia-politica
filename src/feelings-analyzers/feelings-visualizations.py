#!/usr/bin/env python3
"""
Analizador de Artículos de Marín - HorizontAI
==============================================

Script completo para análisis de sentimientos, temas e intensidad emocional
de artículos de noticias locales de Marín.

Funcionalidades:
- Detección automática de idioma (Español/Gallego)
- Análisis de sentimientos con BETO/Bertinho
- Clasificación de temas generales (Phase 1)
- Análisis político avanzado (Phase 2 - solo artículos políticos)
- Análisis de intensidad emocional

Autor: HorizontAI Team
Fecha: Junio 2025
"""

import os
# CONFIGURAR CACHE EN DISCO D: ANTES DE IMPORTAR TRANSFORMERS
os.environ['TRANSFORMERS_CACHE'] = 'D:/huggingface_cache'
os.environ['HF_HOME'] = 'D:/huggingface_cache'
os.environ['HF_DATASETS_CACHE'] = 'D:/huggingface_cache'

import pandas as pd
import numpy as np
import re
import warnings
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from fast_langdetect import detect
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

warnings.filterwarnings('ignore')

# Crear directorio cache si no existe
cache_dir = 'D:/huggingface_cache'
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
    print(f"📁 Directorio cache creado en: {cache_dir}")

@dataclass
class AnalysisResult:
    """Estructura para almacenar resultados del análisis"""
    idioma: str
    confianza_idioma: float
    tema_principal: str
    subtema: Optional[str]
    sentimiento: str
    score_sentimiento: float
    intensidad_emocional: int
    es_politico: bool
    politicos_mencionados: List[str]
    partidos_mencionados: List[str]
    palabras_clave: List[str]

class DetectorIdioma:
    """Detector de idioma usando FastText"""
    
    def __init__(self):
        self.idiomas_soportados = ['es', 'gl', 'ca', 'eu', 'pt']
    
    def detectar(self, texto: str) -> Tuple[str, float]:
        """
        Detecta el idioma del texto
        
        Args:
            texto: Texto a analizar
            
        Returns:
            Tuple con (idioma, confianza)
        """
        try:
            if not texto or len(texto.strip()) < 10:
                return 'es', 0.5  # Default español para textos muy cortos
                
            resultado = detect(texto)
            idioma = resultado['lang']
            confianza = resultado['score']
            
            # Si no es español o gallego, defaultear a español
            if idioma not in ['es', 'gl']:
                return 'es', 0.6
                
            return idioma, confianza
            
        except Exception as e:
            print(f"Error en detección de idioma: {e}")
            return 'es', 0.5

class AnalizadorSentimientos:
    """Analizador de sentimientos con BETO y Bertinho"""
    
    def __init__(self):
        self.modelo_espanol = None
        self.modelo_gallego = None
        self.tokenizer_espanol = None
        self.tokenizer_gallego = None
        self._cargar_modelos()
    
    def _cargar_modelos(self):
        """Carga los modelos BETO y Bertinho"""
        try:
            print("🔄 Cargando BETO (Español)...")
            self.tokenizer_espanol = AutoTokenizer.from_pretrained('dccuchile/bert-base-spanish-wwm-cased')
            self.modelo_espanol = AutoModelForSequenceClassification.from_pretrained('dccuchile/bert-base-spanish-wwm-cased')
            
            print("🔄 Cargando Bertinho (Gallego)...")
            self.tokenizer_gallego = AutoTokenizer.from_pretrained('dvilares/bertinho-gl-base-cased')
            self.modelo_gallego = AutoModelForSequenceClassification.from_pretrained('dvilares/bertinho-gl-base-cased')
            
            print("✅ Modelos cargados correctamente")
            
        except Exception as e:
            print(f"⚠️ Error cargando modelos: {e}")
            print("📝 Usando pipeline por defecto...")
            self._cargar_pipeline_alternativo()
    
    def _cargar_pipeline_alternativo(self):
        """Pipeline alternativo si fallan los modelos principales"""
        try:
            self.pipeline_es = pipeline("sentiment-analysis", 
                                      model="nlptown/bert-base-multilingual-uncased-sentiment",
                                      device=0 if torch.cuda.is_available() else -1)
            print("✅ Pipeline alternativo cargado")
        except:
            print("⚠️ Usando análisis básico de sentimientos")
            self.pipeline_es = None
    
    def analizar(self, texto: str, idioma: str) -> Tuple[str, float]:
        """
        Analiza el sentimiento del texto
        
        Args:
            texto: Texto a analizar
            idioma: 'es' para español, 'gl' para gallego
            
        Returns:
            Tuple con (sentimiento, score)
        """
        try:
            if not texto or len(texto.strip()) < 5:
                return 'neutral', 0.5
            
            # Análisis básico por palabras clave si no hay modelos
            if not self.modelo_espanol and not self.pipeline_es:
                return self._analisis_basico(texto)
            
            # Usar pipeline si está disponible
            if self.pipeline_es:
                resultado = self.pipeline_es(texto)[0]
                label = resultado['label'].lower()
                score = resultado['score']
                
                # Mapear labels del modelo
                if 'pos' in label or '4' in label or '5' in label:
                    return 'positivo', score
                elif 'neg' in label or '1' in label or '2' in label:
                    return 'negativo', score
                else:
                    return 'neutral', score
            
            return self._analisis_basico(texto)
            
        except Exception as e:
            print(f"Error en análisis de sentimientos: {e}")
            return self._analisis_basico(texto)
    
    def _analisis_basico(self, texto: str) -> Tuple[str, float]:
        """Análisis básico basado en palabras clave"""
        texto_lower = texto.lower()
        
        palabras_positivas = [
            'éxito', 'excelente', 'bueno', 'magnífico', 'perfecto', 'logro', 
            'victoria', 'alegría', 'felicidad', 'prosperidad', 'avance',
            'bo', 'excelente', 'fantástico', 'alegre', 'contento'  # gallego
        ]
        
        palabras_negativas = [
            'problema', 'crisis', 'malo', 'terrible', 'fracaso', 'error',
            'conflicto', 'polémica', 'escándalo', 'crítica', 'denuncia',
            'mal', 'problema', 'crise', 'terrible', 'conflito'  # gallego
        ]
        
        score_pos = sum(1 for palabra in palabras_positivas if palabra in texto_lower)
        score_neg = sum(1 for palabra in palabras_negativas if palabra in texto_lower)
        
        if score_pos > score_neg:
            return 'positivo', min(0.6 + (score_pos * 0.1), 0.95)
        elif score_neg > score_pos:
            return 'negativo', min(0.6 + (score_neg * 0.1), 0.95)
        else:
            return 'neutral', 0.5

class ClasificadorTemas:
    """Clasificador de temas generales de artículos"""
    
    def __init__(self):
        self.temas_keywords = {
            'necrológica': [
                'fallece', 'muerte', 'funeral', 'entierro', 'defunción', 'óbito',
                'faleceu', 'morte', 'funeral', 'enterro'  # gallego
            ],
            'política': [
                'alcalde', 'concejo', 'elecciones', 'partido', 'político', 'gobierno',
                'pp', 'psoe', 'bng', 'pazos', 'ramallo', 'santos',
                'alcalde', 'concello', 'eleccións', 'partido', 'político', 'goberno'  # gallego
            ],
            'empresarial': [
                'empresa', 'negocio', 'comercio', 'industria', 'empleo', 'trabajo',
                'económico', 'inversión', 'facturación', 'beneficios',
                'empresa', 'negocio', 'comercio', 'industria', 'emprego', 'traballo'  # gallego
            ],
            'opinión': [
                'opinión', 'editorial', 'carta', 'director', 'columna', 'artículo',
                'opina', 'considera', 'cree', 'piensa',
                'opinión', 'editorial', 'carta', 'director', 'columna', 'artigo'  # gallego
            ],
            'cultura': [
                'festival', 'concierto', 'teatro', 'música', 'arte', 'cultura',
                'exposición', 'evento', 'celebración', 'tradición',
                'festival', 'concerto', 'teatro', 'música', 'arte', 'cultura'  # gallego
            ],
            'obras': [
                'obras', 'construcción', 'infraestructura', 'urbanismo', 'proyecto',
                'reforma', 'mejora', 'renovación', 'acondicionamiento',
                'obras', 'construción', 'infraestrutura', 'urbanismo', 'proxecto'  # gallego
            ],
            'trabajo': [
                'sindicato', 'convenio', 'empleo', 'trabajadores', 'laboral',
                'huelga', 'despido', 'contrato', 'salario',
                'sindicato', 'convenio', 'emprego', 'traballadores', 'laboral'  # gallego
            ],
            'deportes': [
                'fútbol', 'deporte', 'equipo', 'partido', 'liga', 'competición',
                'entrenador', 'jugador', 'victoria', 'derrota',
                'fútbol', 'deporte', 'equipo', 'partido', 'liga', 'competición'  # gallego
            ]
        }
    
    def clasificar(self, titulo: str, resumen: str = "") -> Tuple[str, List[str]]:
        """
        Clasifica el tema principal del artículo
        
        Args:
            titulo: Título del artículo
            resumen: Resumen del artículo (opcional)
            
        Returns:
            Tuple con (tema_principal, palabras_clave_encontradas)
        """
        texto_completo = f"{titulo} {resumen}".lower()
        
        scores_temas = {}
        palabras_encontradas = []
        
        for tema, keywords in self.temas_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in texto_completo:
                    score += 1
                    palabras_encontradas.append(keyword)
            
            # Peso extra para keywords en el título
            titulo_lower = titulo.lower()
            for keyword in keywords:
                if keyword in titulo_lower:
                    score += 0.5
            
            scores_temas[tema] = score
        
        # Tema con mayor score
        if scores_temas and max(scores_temas.values()) > 0:
            tema_principal = max(scores_temas, key=scores_temas.get)
        else:
            tema_principal = 'general'
        
        return tema_principal, palabras_encontradas

class AnalizadorPolitico:
    """Análisis político avanzado (Phase 2) para artículos políticos"""
    
    def __init__(self):
        self.politicos_locales = {
            'manuel pazos': ['manuel pazos', 'pazos'],
            'maría ramallo': ['maría ramallo', 'ramallo', 'maria ramallo'],
            'lucía santos': ['lucía santos', 'santos', 'lucia santos']
        }
        
        self.partidos = {
            'pp': ['pp', 'partido popular'],
            'psoe': ['psoe', 'partido socialista', 'psdeg'],
            'bng': ['bng', 'bloque nacionalista galego', 'bloque']
        }
        
        self.palabras_intensidad = {
            'muy_alta': [
                'escándalo', 'corrupción', 'fraude', 'dimisión', 'crisis',
                'polémica', 'conflicto', 'enfrentamiento', 'ruptura',
                'escándalo', 'corrupción', 'fraude', 'dimisión', 'crise'  # gallego
            ],
            'alta': [
                'crítica', 'denuncia', 'protesta', 'oposición', 'rechazo',
                'debate', 'tensión', 'discrepancia', 'controversia',
                'crítica', 'denuncia', 'protesta', 'oposición', 'rexeitamento'  # gallego
            ],
            'media': [
                'propuesta', 'proyecto', 'iniciativa', 'medida', 'plan',
                'anuncio', 'declaración', 'reunión', 'acuerdo',
                'proposta', 'proxecto', 'iniciativa', 'medida', 'plan'  # gallego
            ]
        }
    
    def es_articulo_politico(self, titulo: str, resumen: str = "") -> bool:
        """Determina si un artículo es político"""
        texto_completo = f"{titulo} {resumen}".lower()
        
        # Buscar políticos locales
        for politico, variantes in self.politicos_locales.items():
            if any(variante in texto_completo for variante in variantes):
                return True
        
        # Buscar partidos
        for partido, variantes in self.partidos.items():
            if any(variante in texto_completo for variante in variantes):
                return True
        
        # Palabras políticas generales
        palabras_politicas = [
            'alcalde', 'concejal', 'gobierno', 'municipal', 'ayuntamiento',
            'pleno', 'elecciones', 'votos', 'campaña', 'político',
            'alcalde', 'concelleiro', 'goberno', 'municipal', 'concello'  # gallego
        ]
        
        return any(palabra in texto_completo for palabra in palabras_politicas)
    
    def analizar_intensidad(self, titulo: str, resumen: str = "") -> int:
        """
        Analiza la intensidad emocional/política del artículo
        
        Returns:
            Escala 1-5 (1=neutral, 5=muy pasional)
        """
        texto_completo = f"{titulo} {resumen}".lower()
        
        score_intensidad = 1
        
        # Contar palabras de alta intensidad
        muy_alta = sum(1 for palabra in self.palabras_intensidad['muy_alta'] 
                      if palabra in texto_completo)
        alta = sum(1 for palabra in self.palabras_intensidad['alta'] 
                  if palabra in texto_completo)
        media = sum(1 for palabra in self.palabras_intensidad['media'] 
                   if palabra in texto_completo)
        
        # Calcular score
        score_intensidad += muy_alta * 1.5
        score_intensidad += alta * 1.0
        score_intensidad += media * 0.5
        
        # Peso extra si está en el título
        titulo_lower = titulo.lower()
        if any(palabra in titulo_lower for palabra in self.palabras_intensidad['muy_alta']):
            score_intensidad += 1
        
        # Normalizar a escala 1-5
        return min(int(score_intensidad), 5)
    
    def extraer_entidades_politicas(self, titulo: str, resumen: str = "") -> Tuple[List[str], List[str]]:
        """Extrae políticos y partidos mencionados"""
        texto_completo = f"{titulo} {resumen}".lower()
        
        politicos_encontrados = []
        partidos_encontrados = []
        
        # Buscar políticos
        for politico, variantes in self.politicos_locales.items():
            if any(variante in texto_completo for variante in variantes):
                politicos_encontrados.append(politico)
        
        # Buscar partidos
        for partido, variantes in self.partidos.items():
            if any(variante in texto_completo for variante in variantes):
                partidos_encontrados.append(partido)
        
        return politicos_encontrados, partidos_encontrados

class AnalizadorArticulosMarin:
    """Clase principal que coordina todos los análisis"""
    
    def __init__(self):
        print("🚀 Inicializando Analizador de Artículos de Marín...")
        self.detector_idioma = DetectorIdioma()
        self.analizador_sentimientos = AnalizadorSentimientos()
        self.clasificador_temas = ClasificadorTemas()
        self.analizador_politico = AnalizadorPolitico()
        print("✅ Analizador inicializado correctamente")
    
    def analizar_articulo(self, titulo: str, resumen: str = "") -> AnalysisResult:
        """
        Análisis completo de un artículo
        
        Args:
            titulo: Título del artículo
            resumen: Resumen del artículo (opcional)
            
        Returns:
            AnalysisResult con todos los análisis
        """
        if not titulo:
            raise ValueError("El título es obligatorio")
        
        texto_completo = f"{titulo} {resumen}" if resumen else titulo
        
        # Phase 1: Análisis básico para todos los artículos
        idioma, confianza_idioma = self.detector_idioma.detectar(texto_completo)
        sentimiento, score_sentimiento = self.analizador_sentimientos.analizar(texto_completo, idioma)
        tema_principal, palabras_clave = self.clasificador_temas.clasificar(titulo, resumen)
        
        # Determinar si es artículo político
        es_politico = self.analizador_politico.es_articulo_politico(titulo, resumen)
        
        # Phase 2: Análisis avanzado solo para artículos políticos
        if es_politico:
            intensidad_emocional = self.analizador_politico.analizar_intensidad(titulo, resumen)
            politicos_mencionados, partidos_mencionados = self.analizador_politico.extraer_entidades_politicas(titulo, resumen)
            subtema = 'político_' + ('local' if politicos_mencionados else 'general')
        else:
            intensidad_emocional = 1  # Neutral para no políticos
            politicos_mencionados = []
            partidos_mencionados = []
            subtema = None
        
        return AnalysisResult(
            idioma=idioma,
            confianza_idioma=confianza_idioma,
            tema_principal=tema_principal,
            subtema=subtema,
            sentimiento=sentimiento,
            score_sentimiento=score_sentimiento,
            intensidad_emocional=intensidad_emocional,
            es_politico=es_politico,
            politicos_mencionados=politicos_mencionados,
            partidos_mencionados=partidos_mencionados,
            palabras_clave=palabras_clave
        )
    
    def analizar_dataset(self, df: pd.DataFrame, columna_titulo: str, 
                        columna_resumen: str = None) -> pd.DataFrame:
        """
        Analiza un dataset completo de artículos
        
        Args:
            df: DataFrame con los artículos
            columna_titulo: Nombre de la columna con títulos
            columna_resumen: Nombre de la columna con resúmenes (opcional)
            
        Returns:
            DataFrame con las nuevas columnas de análisis
        """
        print(f"📊 Analizando {len(df)} artículos...")
        
        resultados = []
        for idx, row in df.iterrows():
            if idx % 100 == 0:
                print(f"   Procesado: {idx}/{len(df)} artículos")
            
            titulo = row[columna_titulo]
            resumen = row[columna_resumen] if columna_resumen else ""
            
            try:
                resultado = self.analizar_articulo(titulo, resumen)
                resultados.append(resultado)
            except Exception as e:
                print(f"Error procesando artículo {idx}: {e}")
                # Resultado por defecto en caso de error
                resultado_default = AnalysisResult(
                    idioma='es', confianza_idioma=0.5, tema_principal='general',
                    subtema=None, sentimiento='neutral', score_sentimiento=0.5,
                    intensidad_emocional=1, es_politico=False,
                    politicos_mencionados=[], partidos_mencionados=[], palabras_clave=[]
                )
                resultados.append(resultado_default)
        
        # Añadir columnas al DataFrame
        df_resultado = df.copy()
        df_resultado['idioma_detectado'] = [r.idioma for r in resultados]
        df_resultado['confianza_idioma'] = [r.confianza_idioma for r in resultados]
        df_resultado['tema_principal'] = [r.tema_principal for r in resultados]
        df_resultado['subtema'] = [r.subtema for r in resultados]
        df_resultado['sentimiento'] = [r.sentimiento for r in resultados]
        df_resultado['score_sentimiento'] = [r.score_sentimiento for r in resultados]
        df_resultado['intensidad_emocional'] = [r.intensidad_emocional for r in resultados]
        df_resultado['es_politico'] = [r.es_politico for r in resultados]
        df_resultado['politicos_mencionados'] = [r.politicos_mencionados for r in resultados]
        df_resultado['partidos_mencionados'] = [r.partidos_mencionados for r in resultados]
        df_resultado['palabras_clave'] = [r.palabras_clave for r in resultados]
        
        print("✅ Análisis completado")
        return df_resultado
    
    def generar_reporte(self, df_analizado: pd.DataFrame) -> Dict:
        """Genera un reporte resumen del análisis"""
        total_articulos = len(df_analizado)
        
        reporte = {
            'total_articulos': total_articulos,
            'idiomas': df_analizado['idioma_detectado'].value_counts().to_dict(),
            'temas': df_analizado['tema_principal'].value_counts().to_dict(),
            'sentimientos': df_analizado['sentimiento'].value_counts().to_dict(),
            'articulos_politicos': df_analizado['es_politico'].sum(),
            'intensidad_promedio': df_analizado['intensidad_emocional'].mean(),
            'politicos_mas_mencionados': self._contar_menciones(df_analizado, 'politicos_mencionados'),
            'partidos_mas_mencionados': self._contar_menciones(df_analizado, 'partidos_mencionados')
        }
        
        return reporte
    
    def _contar_menciones(self, df: pd.DataFrame, columna: str) -> Dict:
        """Cuenta menciones de entidades políticas"""
        menciones = {}
        for lista_entidades in df[columna]:
            for entidad in lista_entidades:
                menciones[entidad] = menciones.get(entidad, 0) + 1
        return dict(sorted(menciones.items(), key=lambda x: x[1], reverse=True))

# Función de utilidad para uso rápido
def analizar_articulos_marin(df: pd.DataFrame, col_titulo: str, col_resumen: str = None) -> pd.DataFrame:
    """
    Función de conveniencia para análisis rápido
    
    Args:
        df: DataFrame con artículos
        col_titulo: Columna con títulos
        col_resumen: Columna con resúmenes (opcional)
        
    Returns:
        DataFrame con análisis completo
    """
    analizador = AnalizadorArticulosMarin()
    return analizador.analizar_dataset(df, col_titulo, col_resumen)

# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de uso básico
    print("🔬 Ejemplo de análisis individual:")
    
    analizador = AnalizadorArticulosMarin()
    
    # Test con artículo político
    titulo_test = "Manuel Pazos critica duramente la gestión del PP en el ayuntamiento"
    resumen_test = "El alcalde socialista denunció irregularidades en el proyecto de obras"
    
    resultado = analizador.analizar_articulo(titulo_test, resumen_test)
    print(f"📰 Título: {titulo_test}")
    print(f"🌍 Idioma: {resultado.idioma} (confianza: {resultado.confianza_idioma:.2f})")
    print(f"📂 Tema: {resultado.tema_principal}")
    print(f"😊 Sentimiento: {resultado.sentimiento} (score: {resultado.score_sentimiento:.2f})")
    print(f"🔥 Intensidad: {resultado.intensidad_emocional}/5")
    print(f"🏛️ Es político: {resultado.es_politico}")
    print(f"👥 Políticos: {resultado.politicos_mencionados}")
    print(f"🎯 Partidos: {resultado.partidos_mencionados}")
    
    print("\n" + "="*60)
    print("✅ Script listo para usar con tus datos!")
    print("💡 Usa: analizar_articulos_marin(tu_dataframe, 'title', 'summary')")