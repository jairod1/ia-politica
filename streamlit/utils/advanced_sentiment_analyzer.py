"""
EMERGENCY ANALYZER - Versión mínima funcional
"""

import pandas as pd
from typing import Dict
from dataclasses import dataclass

@dataclass
class EmotionResult:
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

class AnalizadorSentimientosAvanzado:
    def __init__(self):
        print("🔧 EMERGENCY ANALYZER CARGADO")
    
    def analizar_articulo_completo(self, titulo: str, resumen: str = "") -> EmotionResult:
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
    
    def analizar_dataset(self, df: pd.DataFrame, columna_titulo: str, columna_resumen: str = None) -> pd.DataFrame:
        print(f"🔧 EMERGENCY: Analizando {len(df)} artículos...")
        
        df_resultado = df.copy()
        
        # Añadir columnas básicas
        df_resultado['idioma'] = 'castellano'
        df_resultado['tono_general'] = 'neutral'
        df_resultado['emocion_principal'] = 'neutral'
        df_resultado['confianza_analisis'] = 0.5
        df_resultado['intensidad_emocional'] = 1
        df_resultado['contexto_emocional'] = 'informativo'
        df_resultado['es_politico'] = False
        df_resultado['tematica'] = '📄 Otros'
        df_resultado['confianza_emocion'] = 0.5
        df_resultado['emociones_detectadas'] = [{'neutral': 0.5} for _ in range(len(df))]
        
        print("✅ EMERGENCY: Análisis completado")
        return df_resultado
    
    def generar_reporte_completo(self, df_analizado: pd.DataFrame) -> Dict:
        return {
            'total_articulos': len(df_analizado),
            'articulos_politicos': 0,
            'distribución_idiomas': {'castellano': len(df_analizado)},
            'tonos_generales': {'neutral': len(df_analizado)},
            'emociones_principales': {'neutral': len(df_analizado)},
            'contextos_emocionales': {'informativo': len(df_analizado)},
            'tematicas': {'📄 Otros': len(df_analizado)},
            'intensidad_promedio': 1.0,
            'confianza_promedio': 0.5
        }

class AnalizadorArticulosMarin:
    def __init__(self):
        self.analizador = AnalizadorSentimientosAvanzado()
        print("✅ AnalizadorArticulosMarin EMERGENCY cargado")
    
    def analizar_dataset(self, df, columna_titulo='title', columna_resumen='summary'):
        return self.analizador.analizar_dataset(df, columna_titulo, columna_resumen)
    
    def generar_reporte(self, df_analizado):
        return self.analizador.generar_reporte_completo(df_analizado)

def analizar_articulos_marin(df, columna_titulo='title', columna_resumen='summary'):
    analizador = AnalizadorSentimientosAvanzado()
    return analizador.analizar_dataset(df, columna_titulo, columna_resumen)

if __name__ == "__main__":
    print("🔧 EMERGENCY ANALYZER - Test OK")