"""
Visualizers - HorizontAI (VERSIÓN MEJORADA)
===========================================

Funciones para mostrar tablas, gráficos y paneles con las nuevas columnas y tono informal.
"""

import streamlit as st
import pandas as pd
from .sentiment_integration import aplicar_analisis_sentimientos, mostrar_analisis_sentimientos_compacto

def mostrar_explicacion_parametros():
    """Explicación mejorada con tono informal pero profesional"""
    with st.expander("🤓 ¿Cómo funciona nuestro análisis? (Spoiler: es bastante molón)"):
        st.markdown("""
        ### 🧠 La magia detrás del análisis
        
        Nuestro sistema no solo lee artículos, **los entiende** a nivel emocional. Aquí te contamos cómo:
        
        #### 1. 🌍 Detección de idioma
        - **Gallego** 🏴󠁥󠁳󠁧󠁡󠁿: Detecta palabras como "concello", "veciños", "celebrarase"
        - **Castellano** 🇪🇸: Identifica "ayuntamiento", "vecinos", "celebrará"
        - Si hay dudas, asume castellano (por si acaso)
        
        #### 2. 😊 Tono general (ahora con lógica coherente)
        - **Positivo**: Optimismo, buenas noticias, logros
        - **Negativo**: Críticas, problemas, malas noticias  
        - **Neutral**: Pura información sin rollo emocional
        
        💡 **Novedad**: Si la emoción principal es alegría → tono positivo (lógico, ¿no?)
        
        #### 3. 🎭 Emociones específicas (ahora más visibles)
        **Emociones positivas** ✨:
        - Alegría, Esperanza, Orgullo, Satisfacción
        
        **Emociones negativas** 😤:
        - Tristeza, Ira, Miedo, Decepción, Desprecio
        
        **Emociones complejas** 🤔:
        - Sorpresa, Nostalgia, Preocupación
        
        #### 4. 📂 Categorías temáticas (mucho más específicas)
        Ya no hay "General" genérico. Ahora reconocemos:
        - 🕊️ **Necrológicas**: Esquelas y fallecimientos
        - 💭 **Opinión**: Artículos de opinión y editoriales  
        - 🎉 **Festividades**: Fiestas y celebraciones
        - 🚌 **Transporte**: Autobuses, tráfico, movilidad
        - Y muchas más...
        
        #### 5. 📊 Métricas que importan
        - **Confianza**: Qué seguro está el algoritmo de su veredicto
        - **Intensidad**: De 1 a 5, qué tan "fuerte" es la emoción
        - **Contexto**: La situación general del artículo
        
        #### 🔬 La tecnología por dentro
        - Reconoce palabras en **español Y gallego** (¡bilingüe como debe ser!)
        - Da más peso a las emociones en títulos que en texto
        - Detecta intensificadores ("muy", "tremendo", "brutal")
        - Adaptado específicamente para el contexto político local de Marín
        
        **En resumen**: Ya no es solo análisis, es comprensión emocional real 🎯
        """)

def truncar_titulo_palabras(titulo, max_palabras=10):
    """
    Trunca un título a un número máximo de palabras
    """
    if pd.isna(titulo) or not str(titulo).strip():
        return "Sin título"
    
    palabras = str(titulo).strip().split()
    
    if len(palabras) <= max_palabras:
        return titulo
    else:
        return " ".join(palabras[:max_palabras]) + "..."

def crear_mapping_titulos_originales(df):

    mapping = {}
    
    for idx, row in df.iterrows():
        link = row.get('link', f'no_link_{idx}')  # Fallback si no hay link
        titulo_original = row.get('title', 'Sin título')
        
        # Limpiar y preservar título original
        if pd.notna(titulo_original):
            mapping[link] = str(titulo_original).strip()
        else:
            mapping[link] = 'Sin título'
    
    return mapping

def obtener_titulo_original(selected_article, mapping_titulos):

    link = selected_article.get('article_link', selected_article.get('link', ''))
    
    # Intentar recuperar desde mapping
    if link and link in mapping_titulos:
        return mapping_titulos[link]
    
    # Fallbacks si no se encuentra
    # if 'title' in selected_article:
    #     return selected_article['title']  # Título truncado como último recurso
    
    return 'Título no disponible'

def crear_mapping_titulos_articulos_comentarios(df):
    """Mapping específico para títulos de artículos desde comentarios"""
    mapping = {}
    
    for idx, row in df.iterrows():
        # Priorizar article_link, luego link
        link = row.get('article_link', row.get('link', f'no_link_{idx}'))
        
        # Priorizar title_original, luego article_title, luego title
        titulo = row.get('title_original', 
                        row.get('article_title', 
                               row.get('title', 'Sin título')))
        
        if pd.notna(titulo):
            mapping[link] = str(titulo).strip()
        else:
            mapping[link] = 'Sin título'
    
    return mapping

def mostrar_tabla_con_detalles_y_sentimientos(df, titulo_seccion, mostrar_sentimientos=False, analizador=None, es_articulos_populares=True):
    """
    Tabla mejorada con las nuevas columnas en el orden solicitado:
    1. Idioma (antes del tono)
    2. Tono general
    3. Emoción primaria  
    4. Emoción secundaria
    5. Resto de columnas
    
    🔧 CORREGIDO: Panel de detalles del artículo ANTES que el análisis general
    """
    st.info("💡 Haz clic en la columna de la izquierda de la tabla para ver detalles del artículo")

    if len(df) == 0:
        st.info(f"🤷‍♂️ No hay artículos para {titulo_seccion.lower()} (de momento)")
        return
    
    # Aplicar análisis si está habilitado
    df_display = df.copy()
    reporte = None

    # Función para guardar título completo del artículo
    mapping_titulos_originales = crear_mapping_titulos_originales(df_display)

    # Truncar títulos a 5 palabras
    df_display['title'] = df_display['title'].apply(lambda x: truncar_titulo_palabras(x, 5))

    if mostrar_sentimientos and analizador is not None:
        with st.spinner("🧠 Aplicando análisis de sentimientos..."):
            from .sentiment_integration import aplicar_analisis_sentimientos
            df_display, reporte = aplicar_analisis_sentimientos(df_display, analizador)
            
        if reporte is None:
            st.error("❌ Error aplicando análisis de sentimientos")
            mostrar_sentimientos = False
    
    # Configurar columnas básicas
    columnas_basicas = ["title", "n_visualizations", "date", "link"]
    
    if mostrar_sentimientos and reporte is not None:
        # Verificar que las nuevas columnas existan
        columnas_nuevas_necesarias = ["idioma", "tono_general", "emocion_principal", "confianza_analisis", "intensidad_emocional"]
        columnas_faltantes = [col for col in columnas_nuevas_necesarias if col not in df_display.columns]
        
        if columnas_faltantes:
            st.error(f"❌ Faltan estas columnas en el análisis: {columnas_faltantes}")
            mostrar_sentimientos = False
        else:
            # ORDEN SOLICITADO: idioma → tono → emoción primaria → emoción secundaria → resto
            if es_articulos_populares:
                columnas_analisis = ["idioma", "tono_general", "emocion_principal", 
                                   "confianza_analisis", "intensidad_emocional", "es_politico"]
                
                df_tabla = df_display[columnas_basicas + columnas_analisis].copy()
                
                # Mejorar la presentación de los datos
                df_tabla['idioma_emoji'] = df_tabla['idioma'].map({
                    'gallego': 'Gallego',
                    'castellano': 'Castellano'
                }).fillna('🤷‍♂️ No detectado')
                
                df_tabla['tono_general_emoji'] = df_tabla['tono_general'].map({
                    'positivo': '😊 Positivo',
                    'negativo': '😔 Negativo', 
                    'neutral': '😐 Neutral'
                }).fillna('🤷‍♂️ Sin definir')
                
                # Emociones con emojis
                emoji_emociones = {
                    'alegría': '😄', 'esperanza': '🌟', 'orgullo': '💪', 'satisfacción': '😌',
                    'tristeza': '😢', 'ira': '😠', 'miedo': '😨', 'decepción': '😞', 'desprecio': '🙄',
                    'sorpresa': '😲', 'nostalgia': '🥺', 'preocupación': '😟', 'neutral': '😐'
                }
                
                df_tabla['emocion_primaria_emoji'] = df_tabla['emocion_principal'].apply(
                    lambda x: f"{emoji_emociones.get(x, '🤔')} {str(x).title()}" if pd.notna(x) else "🤷‍♂️ Ninguna"
                )
                                
                df_tabla['politico_emoji'] = df_tabla['es_politico'].map({
                    True: '🏛️ Sí',
                    False: '📰 No'
                }).fillna('🤷‍♂️ No detectado')
                
                column_config = {
                    "title": "Título",
                    "n_visualizations": st.column_config.NumberColumn("👁️ Vistas", format="%d"),
                    "idioma_emoji": "🌍 Idioma",  # NUEVA COLUMNA PRIMERA
                    "tono_general_emoji": "😊 Tono",
                    "emocion_primaria_emoji": "🎭 Emoción principal",  # NUEVA COLUMNA
                    "confianza_analisis": st.column_config.NumberColumn("📊 Confianza", format="%.2f"),
                    "intensidad_emocional": st.column_config.NumberColumn("🔥 Intensidad", format="%d/5"),
                    "politico_emoji": "🏛️ ¿Político?",
                    "date": "📅 Fecha",
                    "link": st.column_config.LinkColumn("URL", display_text="🔗 Ver")
                }
                
                columnas_mostrar = ["title", "n_visualizations", "idioma_emoji", "tono_general_emoji", 
                                  "emocion_primaria_emoji", "confianza_analisis", 
                                  "intensidad_emocional", "politico_emoji", "date", "link"]
                
            else:
                # Para artículos políticos: mostrar temática en lugar de "es_político"
                columnas_analisis = ["idioma", "tono_general", "emocion_principal", 
                                   "confianza_analisis", "intensidad_emocional", "tematica"]
                
                df_tabla = df_display[columnas_basicas + columnas_analisis].copy()
                
                # Aplicar los mismos emojis y formato
                df_tabla['idioma_emoji'] = df_tabla['idioma'].map({
                    'gallego': 'Gallego',
                    'castellano': 'Castellano'
                }).fillna('🤷‍♂️ No detectado')
                
                df_tabla['tono_general_emoji'] = df_tabla['tono_general'].map({
                    'positivo': '😊 Positivo',
                    'negativo': '😔 Negativo', 
                    'neutral': '😐 Neutral'
                }).fillna('🤷‍♂️ Sin definir')
                
                emoji_emociones = {
                    'alegría': '😄', 'esperanza': '🌟', 'orgullo': '💪', 'satisfacción': '😌',
                    'tristeza': '😢', 'ira': '😠', 'miedo': '😨', 'decepción': '😞', 'desprecio': '🙄',
                    'sorpresa': '😲', 'nostalgia': '🥺', 'preocupación': '😟', 'neutral': '😐'
                }
                
                df_tabla['emocion_primaria_emoji'] = df_tabla['emocion_principal'].apply(
                    lambda x: f"{emoji_emociones.get(x, '🤔')} {str(x).title()}" if pd.notna(x) else "🤷‍♂️ Ninguna"
                )
                                
                # La temática ya viene con emoji del analizador mejorado
                df_tabla['tematica_display'] = df_tabla['tematica'].fillna("📄 Otros")
                
                column_config = {
                    "title": "Título",
                    "n_visualizations": st.column_config.NumberColumn("👁️ Vistas", format="%d"),
                    "idioma_emoji": "🌍 Idioma",  # NUEVA COLUMNA PRIMERA
                    "tono_general_emoji": "😊 Tono",
                    "emocion_primaria_emoji": "🎭 Emoción 1ª",  # NUEVA COLUMNA
                    "confianza_analisis": st.column_config.NumberColumn("📊 Confianza", format="%.2f"),
                    "intensidad_emocional": st.column_config.NumberColumn("🔥 Intensidad", format="%d/5"),
                    "tematica_display": "📂 Temática",
                    "date": "📅 Fecha",
                    "link": st.column_config.LinkColumn("URL", display_text="🔗 Ver")
                }
                
                columnas_mostrar = ["title", "n_visualizations", "idioma_emoji", "tono_general_emoji", 
                                  "emocion_primaria_emoji", "confianza_analisis", 
                                  "intensidad_emocional", "tematica_display", "date", "link"]
    
    # Tabla básica si no hay análisis
    if not mostrar_sentimientos or reporte is None:
        df_tabla = df_display[columnas_basicas].copy()
        column_config = {
            "title": "Título",
            "n_visualizations": st.column_config.NumberColumn("👁️ Vistas", format="%d"),
            "date": "📅 Fecha",
            "link": st.column_config.LinkColumn("URL", display_text="🔗 Ver artículo")
        }
        columnas_mostrar = columnas_basicas
    
    # Mostrar tabla
    try:
        event = st.dataframe(
            df_tabla[columnas_mostrar],
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=600
        )
    except Exception as e:
        st.error(f"💥 Error mostrando la tabla: {e}")
        return
    
    # Panel de detalles (si hay una fila seleccionada)
    if event.selection.rows:
        selected_idx = event.selection.rows[0]
        selected_article = df_display.iloc[selected_idx]
        
        st.divider()
        st.subheader("🔍 Detalles del artículo seleccionado")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            titulo_completo = obtener_titulo_original(selected_article, mapping_titulos_originales)
            st.write(f"**📰 {titulo_completo}**")
            st.write("**📖 Resumen:**")
            if pd.notna(selected_article.get('summary')) and str(selected_article.get('summary', '')).strip():
                st.write(selected_article['summary'])
            else:
                st.info("Sin resumen")
        
        with col2:
            st.write("**📊 Datos del artículo:**")
            st.write(f"👁️ **Vistas:** {selected_article['n_visualizations']:,}")
            st.write(f"📅 **Fecha:** {selected_article['date']}")
            st.write(f"🏢 **Fuente:** {selected_article.get('source', 'No disponible')}")
            
            # Mostrar análisis detallado si está disponible
            if mostrar_sentimientos and reporte is not None:
                mostrar_detalles_sentimientos_mejorado(selected_article)
            
            if pd.notna(selected_article.get('link')):
                st.link_button("🔗 Ver artículo completo", selected_article['link'])
            else:
                st.info("🤷‍♂️ Sin enlace disponible")
    
    # Análisis de sentimientos después de los detalles del artículo
    if mostrar_sentimientos and reporte is not None:
        st.divider()
        mostrar_analisis_sentimientos_compacto(df_display, reporte, titulo_seccion)
        mostrar_explicacion_parametros()
        
def mostrar_tabla_comentarios_con_sentimientos(df, titulo_seccion, mostrar_sentimientos=False, analizador=None, es_popular=True, reporte=None):
    """
    FUNCIÓN CORREGIDA: Inicializa variables correctamente
    """
    st.info("💡 Haz clic en la columna de la izquierda de la tabla para ver detalles del comentario")

    if len(df) == 0:
        tipo = "populares" if es_popular else "impopulares"
        st.info(f"🤷‍♂️ No hay comentarios {tipo} para {titulo_seccion.lower()}")
        return
    
    # Inicializar variables desde el principio
    columnas_mostrar = []
    column_config = {}
    
    # Aplicar análisis si está habilitado y no se ha hecho ya
    df_display = df.copy()

    # Guardar título completo
    mapping_titulos_articulos_originales = crear_mapping_titulos_articulos_comentarios(df_display)
    
    if mostrar_sentimientos and analizador is not None and reporte is None:
        with st.spinner("🧠 Analizando comentarios..."):
            df_display, reporte = aplicar_analisis_sentimientos(df, analizador)
            
        if reporte is None:
            st.error("💥 El análisis falló")
            mostrar_sentimientos = False
    
    # MAPEAR COLUMNAS SEGÚN LA ESTRUCTURA DEL DATAFRAME
    if 'vista_previa_comentario' in df_display.columns:
        # Estructura de comentarios individuales procesados
        mapeo_columnas = {
            'comment_preview': 'vista_previa_comentario',
            'comment_author': 'comment_author',
            'comment_location': 'ubicacion_comentario',
            'likes': 'likes_comentario',
            'dislikes': 'dislikes_comentario', 
            'net_score': 'net_score',
            'link': 'enlace_articulo'
        }
        
        # Calcular net_score si no existe
        if 'net_score' not in df_display.columns and 'likes_comentario' in df_display.columns and 'dislikes_comentario' in df_display.columns:
            df_display['net_score'] = df_display['likes_comentario'] - df_display['dislikes_comentario']
        
    else:
        # Estructura tradicional de comentarios extraídos
        mapeo_columnas = {
            'comment_preview': 'title',
            'comment_author': 'comment_author',
            'comment_location': 'comment_location',
            'likes': 'likes',
            'dislikes': 'dislikes',
            'net_score': 'net_score',
            'link': 'link'
        }
        
    if 'comment_preview' not in df_display.columns:
        # Determinar qué columna contiene el texto del comentario
        if 'title' in df_display.columns:
            texto_columna = 'title'  # Con análisis de sentimientos
        elif 'comment_text' in df_display.columns:
            texto_columna = 'comment_text'  # Sin análisis de sentimientos
        else:
            texto_columna = None
    
        # Una vez creado comment_preview, truncamos la vista previa a 5 palabras
        if texto_columna:
            df_display['texto_original'] = df_display[texto_columna].copy()  # Guardar original
            df_display['comment_preview'] = df_display[texto_columna].apply(
                lambda x: truncar_titulo_palabras(x, 5)  # 5 palabras
            )
    
    # RENOMBRAR COLUMNAS PARA ESTANDARIZAR
    for nombre_estandar, nombre_real in mapeo_columnas.items():
        if nombre_real in df_display.columns and nombre_estandar != nombre_real:
            df_display[nombre_estandar] = df_display[nombre_real]
    
    # 🔧 DEFINIR COLUMNAS BÁSICAS SIEMPRE
    columnas_basicas = ['comment_preview', 'comment_author', 'comment_location', 'likes', 'dislikes', 'net_score', 'link']
    
    # ANÁLISIS DE SENTIMIENTOS
    if mostrar_sentimientos and reporte is not None:
        columnas_sentimientos = ['idioma', 'tono_general', 'emocion_principal', 'confianza_analisis', 'intensidad_emocional']
        columnas_faltantes = [col for col in columnas_sentimientos if col not in df_display.columns]
        
        if not columnas_faltantes:
            # Aplicar emojis
            df_display['idioma_emoji'] = df_display['idioma'].map({
                'gallego': '🏴󠁥󠁳󠁧󠁡󠁿 Gallego',
                'castellano': '🇪🇸 Castellano'
            }).fillna('🤷‍♂️ No detectado')
            
            df_display['tono_general_emoji'] = df_display['tono_general'].map({
                'positivo': '😊 Positivo',
                'negativo': '😔 Negativo', 
                'neutral': '😐 Neutral'
            }).fillna('🤷‍♂️ Sin definir')
            
            emoji_emociones = {
                'alegría': '😄', 'esperanza': '🌟', 'orgullo': '💪', 'satisfacción': '😌',
                'tristeza': '😢', 'ira': '😠', 'miedo': '😨', 'decepción': '😞', 'desprecio': '🙄',
                'sorpresa': '😲', 'nostalgia': '🥺', 'preocupación': '😟', 'neutral': '😐'
            }
            
            df_display['emocion_principal_emoji'] = df_display['emocion_principal'].apply(
                lambda x: f"{emoji_emociones.get(x, '🤔')} {str(x).title()}" if pd.notna(x) else "🤷‍♂️ Ninguna"
            )
            
            # CONFIGURACIÓN CON SENTIMIENTOS
            column_config = {
                "comment_preview": "💬 Comentario",
                "comment_author": "👤 Autor",
                "comment_location": "📍 Ubicación",
                "likes": st.column_config.NumberColumn("👍 Likes", format="%d"),
                "dislikes": st.column_config.NumberColumn("👎 Dislikes", format="%d"),
                "net_score": st.column_config.NumberColumn("📊 Puntuación", format="%+d"),
                "idioma_emoji": "🌍 Idioma", 
                "tono_general_emoji": "😊 Tono",
                "emocion_principal_emoji": "🎭 Emoción",
                "intensidad_emocional": st.column_config.NumberColumn("🔥 Intensidad", format="%d/5"),
                "confianza_analisis": st.column_config.NumberColumn("📊 Confianza", format="%.2f"),
                "link": st.column_config.LinkColumn("🔗 Artículo", display_text="Ver")
            }
            
            columnas_mostrar = ['comment_preview', 'comment_author', 'comment_location', 'likes', 'dislikes', 'net_score',
                              'idioma_emoji', 'tono_general_emoji', 'emocion_principal_emoji', 
                              'intensidad_emocional', 'confianza_analisis', 'link']
        else:
            # Si faltan columnas de sentimientos, usar configuración básica
            mostrar_sentimientos = False
    
    # 🔧 CONFIGURACIÓN BÁSICA (SIEMPRE SE EJECUTA SI NO HAY SENTIMIENTOS)
    if not mostrar_sentimientos:
        column_config = {
            "comment_preview": "💬 Comentario",
            "comment_author": "👤 Autor", 
            "comment_location": "📍 Ubicación",
            "likes": st.column_config.NumberColumn("👍 Likes", format="%d"),
            "dislikes": st.column_config.NumberColumn("👎 Dislikes", format="%d"),
            "net_score": st.column_config.NumberColumn("📊 Puntuación", format="%d"),
            "link": st.column_config.LinkColumn("🔗 Artículo", display_text="Ver")
        }
        columnas_mostrar = columnas_basicas
    
    # 🔧 FILTRAR SOLO COLUMNAS QUE EXISTEN (SIEMPRE)
    columnas_mostrar = [col for col in columnas_mostrar if col in df_display.columns]
    
    # VERIFICACIÓN FINAL
    if not columnas_mostrar:
        st.error("❌ No se pudieron determinar las columnas a mostrar")
        st.write("Columnas disponibles:", list(df_display.columns))
        return
    
    # Mostrar tabla
    try:
        event = st.dataframe(
            df_display[columnas_mostrar],
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=600
        )
    except Exception as e:
        st.error(f"💥 Error mostrando tabla: {e}")
        st.error(f"Columnas solicitadas: {columnas_mostrar}")
        st.error(f"Columnas disponibles: {list(df_display.columns)}")
        return
            
    # 🔧 Panel de detalles si hay una fila seleccionada - CON FORMATO HORIZONTAL
    if event.selection.rows:
        selected_idx = event.selection.rows[0]
        selected_comment = df_display.iloc[selected_idx]
    
        st.divider()
        st.subheader("💬 Comentario completo")
        
        # 🔧 NUEVO: FORMATO HORIZONTAL COMPACTO EN LA PARTE SUPERIOR
        datos_horizontal = []
        
        # Autor
        if 'comment_author' in selected_comment and pd.notna(selected_comment['comment_author']):
            autor = selected_comment['comment_author']
            datos_horizontal.append(f"👤 {autor}")
        
        # Likes y Dislikes  
        likes = selected_comment.get('likes', 0)
        dislikes = selected_comment.get('dislikes', 0)
        datos_horizontal.append(f"👍 {likes}")
        datos_horizontal.append(f"👎 {dislikes}")
        
        # Ubicación
        if 'comment_location' in selected_comment and pd.notna(selected_comment['comment_location']):
            ubicacion = selected_comment['comment_location']
            if ubicacion != 'No especificada':
                datos_horizontal.append(f"📍 {ubicacion}")
        
        # Análisis de sentimientos (si está disponible)
        if mostrar_sentimientos and 'idioma' in selected_comment:
            idioma = selected_comment.get('idioma', 'no detectado')
            tono = selected_comment.get('tono_general', 'neutral')
            emocion = selected_comment.get('emocion_principal', 'neutral')
            intensidad = selected_comment.get('intensidad_emocional', 1)
            confianza = selected_comment.get('confianza_analisis', 0.0)
            
            # Emojis
            emoji_idioma = '🏴󠁥󠁳󠁧󠁡󠁿' if idioma == 'gallego' else '🇪🇸' if idioma == 'castellano' else '🤷‍♂️'
            emoji_tono = '😊' if tono == 'positivo' else '😔' if tono == 'negativo' else '😐'
            
            emoji_emociones = {
                'alegría': '😄', 'esperanza': '🌟', 'orgullo': '💪', 'satisfacción': '😌',
                'tristeza': '😢', 'ira': '😠', 'miedo': '😨', 'decepción': '😞', 'desprecio': '🙄',
                'sorpresa': '😲', 'nostalgia': '🥺', 'preocupación': '😟', 'neutral': '😐'
            }
            emoji_emocion = emoji_emociones.get(emocion, '🤔')
            
            datos_horizontal.extend([
                f"{emoji_idioma} {idioma.title()}",
                f"{emoji_tono} {tono.title()}",
                f"{emoji_emocion} {emocion.title()}",
                f"🔥 {intensidad}/5",
                f"📊 {confianza:.2f}"
            ])
        
        # 🔧 MOSTRAR INFORMACIÓN HORIZONTAL ARRIBA
        if datos_horizontal:
            linea_horizontal = " | ".join(datos_horizontal)
            st.info(f"ℹ️ **Detalles**: {linea_horizontal}")
    
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("**Texto completo:**")
            
            # SOLUCIÓN DIRECTA: Usar la columna que sabemos que funciona
            if 'texto_original' in selected_comment and pd.notna(selected_comment['texto_original']):
                texto_completo = selected_comment['texto_original'] 
            else:
                texto_completo = selected_comment.get('vista_previa_comentario', 'Sin texto disponible')
                
            if texto_completo:
                st.write(texto_completo)
            else:
                st.info("🤷‍♂️ Texto completo no disponible")
    
        with col2:
            st.write("**📊 Información:**")
            # Información básica usando nombres estandarizados
            for col, emoji, label in [
                ('comment_author', '👤', 'Autor'),
                ('comment_location', '📍', 'Ubicación'), 
                ('likes', '👍', 'Likes'),
                ('dislikes', '👎', 'Dislikes'),
                ('net_score', '📊', 'Puntuación neta')
            ]:
                if col in selected_comment and pd.notna(selected_comment[col]):
                    st.write(f"{emoji} **{label}:** {selected_comment[col]}")
        
            # Enlace del artículo
            if 'link' in selected_comment and pd.notna(selected_comment['link']):
                st.link_button("🔗 Ver artículo completo", selected_comment['link'])
    
    if mostrar_sentimientos and reporte is not None:
        st.divider()
        mostrar_analisis_sentimientos_comentarios_compacto(df_display, reporte, titulo_seccion)
        mostrar_explicacion_parametros()


def mostrar_detalles_sentimientos_comentario(selected_comment):
    """
    Mostrar detalles de sentimientos de un comentario en formato horizontal
    """
    st.write("**🧠 Análisis emocional:**")
    
    # Verificar que las columnas existen
    if 'idioma' in selected_comment:
        # 🔧 LAYOUT HORIZONTAL CON COLUMNAS
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Idioma detectado
            idioma = selected_comment.get('idioma', 'no detectado')
            emoji_idioma = '🏴󠁥󠁳󠁧󠁡󠁿' if idioma == 'gallego' else '🇪🇸' if idioma == 'castellano' else '🤷‍♂️'
            st.write(f"{emoji_idioma} **Idioma**: {idioma.title()}")
        
        with col2:
            # Tono general con color
            tono = selected_comment.get('tono_general', 'neutral')
            confianza = selected_comment.get('confianza_analisis', 0.0)
            
            if tono == 'positivo':
                st.success(f"😊 **Tono**: Positivo ({confianza:.2f})")
            elif tono == 'negativo':
                st.error(f"😔 **Tono**: Negativo ({confianza:.2f})")
            else:
                st.info(f"😐 **Tono**: Neutral ({confianza:.2f})")
        
        with col3:
            # Emoción principal
            emocion_principal = selected_comment.get('emocion_principal', 'neutral')
            st.write(f"🎭 **Emoción**: {emocion_principal.title()}")
        
        # 🔧 SEGUNDA FILA HORIZONTAL
        st.divider()
        col4, col5 = st.columns(2)
        
        with col4:
            # Intensidad emocional
            intensidad = selected_comment.get('intensidad_emocional', 1)
            st.write(f"🔥 **Intensidad**: {intensidad}/5")
        
        with col5:
            # Contexto emocional
            contexto = selected_comment.get('contexto_emocional', 'informativo')
            st.write(f"📝 **Contexto**: {contexto.title()}")
            
    else:
        st.info("ℹ️ El análisis de sentimientos no está disponible para este comentario")

def mostrar_analisis_sentimientos_comentarios_compacto(df_analizado, reporte, titulo_seccion):
    """
    🔧 FUNCIÓN CORREGIDA: Análisis de sentimientos compacto específico para comentarios
    
    LAYOUT:
    - Métricas (5 columnas)
    - Ambiente + Idiomas | Contextos detectados
    - Gráfico de emociones (ancho completo)
    """
    if reporte is None or len(reporte) == 0:
        st.error("❌ No hay reporte de comentarios disponible")
        return
    
    st.title(f"🧠 Análisis emocional - {titulo_seccion}")
    
    # Métricas principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📰 Total", reporte.get('total_articulos', 0))
    
    with col2:
        st.metric("🏛️ Políticos", reporte.get('articulos_politicos', 0))
    
    with col3:
        intensidad = reporte.get('intensidad_promedio', 0)
        st.metric("🔥 Intensidad media", f"{intensidad:.1f}/5")
    
    with col4:
        positivos = reporte.get('tonos_generales', {}).get('positivo', 0)
        st.metric("😊 Positivos", positivos)
    
    with col5:
        negativos = reporte.get('tonos_generales', {}).get('negativo', 0)
        st.metric("😔 Negativos", negativos)
    
    # 🔧 DOS COLUMNAS DE INFORMACIÓN PRIMERO
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🎯 Cómo está el ambiente:**")
        
        # Distribución de tonos
        tonos_generales = reporte.get('tonos_generales', {})
        if tonos_generales:
            total_articulos = reporte.get('total_articulos', 1)
            for tono, cantidad in tonos_generales.items():
                porcentaje = (cantidad / total_articulos) * 100
                emoji = "😊" if tono == "positivo" else "😔" if tono == "negativo" else "😐"
                st.write(f"{emoji} **{tono.title()}**: {porcentaje:.1f}%")
        
        # Distribución de idiomas
        idiomas = reporte.get('distribución_idiomas', {})
        if idiomas:
            st.write("**🌍 Idiomas detectados:**")
            total_articulos = reporte.get('total_articulos', 1)
            for idioma, cantidad in idiomas.items():
                porcentaje = (cantidad / total_articulos) * 100
                emoji = "📘" if idioma == "gallego" else "🐂"
                st.write(f"{emoji} **{idioma.title()}**: {porcentaje:.1f}%")
    
    with col2:
        # 🔧 TEMAS EN COLUMNA SEPARADA
        st.write("**📂 Temas que más interesan:**")
        tematicas = reporte.get('tematicas', {})
        if tematicas:
            for tematica, cantidad in list(tematicas.items())[:4]:
                st.write(f"• {tematica}: {cantidad} artículos")
    
    # 🔧 GRÁFICO DE EMOCIONES AL FINAL (ancho completo)
    st.write("**🎭 Emociones que más aparecen:**")
    emociones_principales = reporte.get('emociones_principales', {})
    
    if emociones_principales:
        emociones_df = pd.DataFrame(list(emociones_principales.items()), 
                                   columns=['Emoción', 'Cantidad'])
        if len(emociones_df) > 0:
            st.bar_chart(emociones_df.set_index('Emoción')['Cantidad'], height=300)
        else:
            st.info("🤷‍♂️ No hay emociones detectadas")
    else:
        st.info("🤷‍♂️ No se dectaron emociones")

def mostrar_detalles_sentimientos_mejorado(selected_article):
    """Panel de detalles mejorado con las nuevas columnas"""
    st.divider()
    st.write("**🧠 Análisis emocional completo:**")
    
    # Verificar columnas disponibles
    if 'idioma' not in selected_article:
        st.error("❌ Los datos de análisis avanzado no están disponibles")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Idioma detectado
        idioma = selected_article.get('idioma', 'no detectado')
        st.write(f"**Idioma**: {idioma.title()}")
        
        # Tono general con color
        tono = selected_article.get('tono_general', 'neutral')
        confianza = selected_article.get('confianza_analisis', 0.0)
        
        if tono == 'positivo':
            st.success(f"😊 **Tono**: Positivo (confianza: {confianza:.2f})")
        elif tono == 'negativo':
            st.error(f"😔 **Tono**: Negativo (confianza: {confianza:.2f})")
        else:
            st.info(f"😐 **Tono**: Neutral (confianza: {confianza:.2f})")
        
        # Emociones (nuevas columnas)
        emocion_principal = selected_article.get('emocion_principal', 'neutral')
        st.write(f"🎭 **Emoción principal**: {emocion_principal.title()}")
            
    with col2:
        # Intensidad emocional
        intensidad = selected_article.get('intensidad_emocional', 1)
        st.write(f"🔥 **Intensidad emocional**: {intensidad}/5")
        
        # Contexto emocional
        contexto = selected_article.get('contexto_emocional', 'informativo')
        st.write(f"📝 **Contexto**: {contexto.title()}")
        
        # Temática o político
        if 'tematica' in selected_article and pd.notna(selected_article['tematica']):
            tematica = selected_article['tematica']
            st.write(f"📂 **Temática**: {tematica}")
        
        if 'es_politico' in selected_article:
            es_politico = selected_article['es_politico']
            politico_text = "Sí" if es_politico else "No"
            emoji = "🏛️" if es_politico else "📰"
            st.write(f"{emoji} **¿Es político?**: {politico_text}")

def mostrar_analisis_sentimientos_compacto(df_analizado, reporte, titulo_seccion):
    """Análisis de sentimientos con tono más informal"""
    if reporte is None or len(reporte) == 0:
        st.error("❌ No hay reporte disponible (se fue de vacaciones)")
        return
    
    st.title(f"🧠 Análisis emocional - {titulo_seccion}")
    
    # Métricas principales
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📰 Total", reporte.get('total_articulos', 0))
    
    with col2:
        st.metric("🏛️ Políticos", reporte.get('articulos_politicos', 0))
    
    with col3:
        intensidad = reporte.get('intensidad_promedio', 0)
        st.metric("🔥 Intensidad media", f"{intensidad:.1f}/5")
    
    with col4:
        positivos = reporte.get('tonos_generales', {}).get('positivo', 0)
        st.metric("😊 Positivos", positivos)
    
    with col5:
        negativos = reporte.get('tonos_generales', {}).get('negativo', 0)
        st.metric("😔 Negativos", negativos)
    
    # Gráficos informativos
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🎭 Emociones que más aparecen:**")
        emociones_principales = reporte.get('emociones_principales', {})
        
        if emociones_principales:
            emociones_df = pd.DataFrame(list(emociones_principales.items()), 
                                       columns=['Emoción', 'Cantidad'])
            if len(emociones_df) > 0:
                st.bar_chart(emociones_df.set_index('Emoción')['Cantidad'], height=300)
            else:
                st.info("🤷‍♂️ No hay emociones detectadas")
        else:
            st.info("🤷‍♂️ Los artículos están muy zen (sin emociones)")
    
    with col2:       
        # Distribución de tonos
        tonos_generales = reporte.get('tonos_generales', {})
        if tonos_generales:
            st.write("**🎯 Cómo está el ambiente:**")
            total_articulos = reporte.get('total_articulos', 1)
            for tono, cantidad in tonos_generales.items():
                porcentaje = (cantidad / total_articulos) * 100
                emoji = "😊" if tono == "positivo" else "😔" if tono == "negativo" else "😐"
                st.write(f"{emoji} **{tono.title()}**: {porcentaje:.1f}%")
        
        # Distribución de idiomas (NUEVO)
        idiomas = reporte.get('distribución_idiomas', {})
        if idiomas:
            st.write("**🌍 Idiomas detectados:**")
            total_articulos = reporte.get('total_articulos', 1)
            for idioma, cantidad in idiomas.items():
                porcentaje = (cantidad / total_articulos) * 100
                emoji = "📘" if idioma == "gallego" else "🐂"
                st.write(f"{emoji} **{idioma.title()}**: {porcentaje:.1f}%")
        
        # Temáticas más comunes
        tematicas = reporte.get('tematicas', {})
        if tematicas:
            st.write("**📂 Temas que más interesan:**")
            for tematica, cantidad in list(tematicas.items())[:4]:
                st.write(f"• {tematica}: {cantidad} artículos")

def mostrar_tabla_articulos_polemicos(df, titulo_seccion, key_suffix=""):
    """Muestra tabla de artículos más polémicos (sin cambios)"""
    if len(df) == 0:
        st.info(f"🤷‍♂️ No hay artículos polémicos para {titulo_seccion.lower()}")
        return
    
    # Crear tabla con información relevante
    columnas_necesarias = ["title", "n_comments", "total_comment_length", "date", "link"]
    columnas_disponibles = [col for col in columnas_necesarias if col in df.columns]
    
    if not columnas_disponibles:
        st.error("❌ No se encontraron las columnas necesarias para mostrar artículos polémicos")
        return
    
    df_display = df[columnas_disponibles].copy()

    # Guardar títulos completos
    mapping_titulos_originales = crear_mapping_titulos_originales(df_display)

    # Truncar títulos a 5 palabras
    df_display['title'] = df_display['title'].apply(lambda x: truncar_titulo_palabras(x, 5))
    
    try:
        event = st.dataframe(
            df_display,
            column_config={
                "title": "Título del Artículo",
                "n_comments": st.column_config.NumberColumn("💬 Comentarios", format="%d"),
                "total_comment_length": st.column_config.NumberColumn("📝 Longitud Total", format="%d"),
                "date": "📅 Fecha",
                "link": st.column_config.LinkColumn("URL", display_text="🔗 Ver artículo")
            },
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=f"articulos_polemicos_{key_suffix}"
        )
    except Exception as e:
        st.error(f"💥 Error mostrando tabla de artículos polémicos: {e}")
        return
    
    # Panel de detalles si hay una fila seleccionada
    if event.selection.rows:
        selected_idx = event.selection.rows[0]
        selected_article = df.iloc[selected_idx]
        
        st.divider()

        # Mostrar título original del artículo
        titulo_original = obtener_titulo_original(selected_article, mapping_titulos_originales)
        st.subheader(f"**📰 Artículo:** {titulo_original}")

        # Primero contar todos los comentarios
        total_comentarios = 0
        for i in range(1, 16):
            comment_text = selected_article.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                total_comentarios += 1

        # Mostrar el total UNA VEZ
        if total_comentarios > 0:
            st.write(f"**💬 Encontrados {total_comentarios} comentarios:**")
        
        # Mostrar comentarios del artículo
        comentarios_mostrados = 0
        for i in range(1, 16):
            comment_text = selected_article.get(f'comment_{i}_text', '')
            comment_author = selected_article.get(f'comment_{i}_author', '')
            comment_likes = selected_article.get(f'comment_{i}_likes', 0)
            comment_dislikes = selected_article.get(f'comment_{i}_dislikes', 0)
            
            if pd.notna(comment_text) and str(comment_text).strip() and comentarios_mostrados < 15:
                with st.expander(f"💬 Comentario de {comment_author} | 👍 {comment_likes} | 👎 {comment_dislikes}"):
                    st.write(comment_text)
                comentarios_mostrados += 1

def mostrar_tabla_comentarios(df, titulo_seccion, es_popular=True, key_suffix=""):
    """Muestra tabla de comentarios populares o impopulares (sin cambios significativos)"""
    if len(df) == 0:
        tipo = "populares" if es_popular else "impopulares"
        st.info(f"🤷‍♂️ No hay comentarios {tipo} para {titulo_seccion.lower()}")
        return
    
    # Verificar columnas necesarias
    columnas_necesarias = ["comment_text", "comment_author", "comment_location", "likes", "dislikes", "net_score", "article_title", "article_link"]
    columnas_disponibles = [col for col in columnas_necesarias if col in df.columns]
    
    if len(columnas_disponibles) < 3:
        st.error("❌ No se encontraron suficientes columnas para mostrar comentarios")
        return
    
    # Crear tabla con información relevante
    df_display = df[columnas_disponibles].copy()

    # Guardar título original     
    mapping_titulos_articulos_originales = crear_mapping_titulos_articulos_comentarios(df_display)

    # Truncar títulos a 5 palabras
    if 'title' in df_display.columns:
        df_display['title'] = df_display['title'].apply(lambda x: truncar_titulo_palabras(x, 5))

    
    # Configurar columnas para mostrar
    columnas_tabla = ['comment_preview', 'comment_location', 'likes', 'dislikes', 'net_score', 'article_title', 'article_link']
    columnas_tabla = [col for col in columnas_tabla if col in df_display.columns]
    
    try:
        event = st.dataframe(
            df_display[columnas_tabla],
            column_config={
                "comment_preview": "Vista previa del comentario",
                "comment_location": "📍 Ubicación",
                "likes": st.column_config.NumberColumn("👍 Likes", format="%d"),
                "dislikes": st.column_config.NumberColumn("👎 Dislikes", format="%d"),
                "net_score": st.column_config.NumberColumn("📊 Puntuación neta", format="%d"),
                "article_title": "Artículo",
                "article_link": st.column_config.LinkColumn("🔗 Artículo", display_text="Ver")
            },
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=f"comentarios_{key_suffix}"
        )
    except Exception as e:
        st.error(f"💥 Error mostrando tabla de comentarios: {e}")
        return
    
    # Panel de detalles si hay una fila seleccionada
    if event.selection.rows:
        selected_idx = event.selection.rows[0]
        selected_comment = df.iloc[selected_idx]
        
        st.divider()
        st.subheader("💬 Comentario completo")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write("**Texto completo:**")
            if 'comment_text' in selected_comment:
                st.write(selected_comment['comment_text'])
            else:
                st.info("🤷‍♂️ Texto del comentario no disponible")
        
        with col2:
            st.write("**📊 Información:**")
            if 'comment_author' in selected_comment:
                st.write(f"👤 **Autor:** {selected_comment['comment_author']}")
            if 'comment_location' in selected_comment:
                st.write(f"📍 **Ubicación:** {selected_comment['comment_location']}")
            if 'likes' in selected_comment:
                st.write(f"👍 **Likes:** {selected_comment['likes']}")
            if 'dislikes' in selected_comment:
                st.write(f"👎 **Dislikes:** {selected_comment['dislikes']}")
            if 'net_score' in selected_comment:
                st.write(f"📊 **Puntuación neta:** {selected_comment['net_score']}")
            if 'article_source' in selected_comment:
                st.write(f"🏢 **Fuente:** {selected_comment['article_source']}")
            
            if 'article_title' in selected_comment:
                st.write("**📰 Artículo relacionado:**")
                titulo_articulo_completo = obtener_titulo_original(selected_comment, mapping_titulos_articulos_originales)
                st.write(titulo_articulo_completo)

            if 'article_link' in selected_comment and pd.notna(selected_comment['article_link']):
                st.link_button("🔗 Ver artículo completo", selected_comment['article_link'])
            else:
                st.info("🤷‍♂️ Enlace no disponible")

def mostrar_seccion_temporal(titulo, descripcion, datos, titulo_seccion, mostrar_sentimientos, analizador, es_articulos_populares=True):
    """Muestra una sección temporal (mayo, año, histórico) con título y descripción"""
    st.subheader(titulo)
    st.caption(descripcion)
    mostrar_tabla_con_detalles_y_sentimientos(datos, titulo_seccion, mostrar_sentimientos, analizador, es_articulos_populares)

def mostrar_seccion_comentarios_temporal(titulo, descripcion, datos, titulo_seccion, procesador_func, mostrar_func, key_suffix):
    """Muestra una sección de comentarios con filtros temporales (sin cambios)"""
    st.subheader(titulo)
    st.caption(descripcion)
    st.info("💡 Haz clic en la columna de la izquierda de la tabla para ver detalles del artículo")
    try:
        datos_procesados = procesador_func(datos)
        print(f"✅ Procesador funcionó: {len(datos_procesados)} filas")  # ← AÑADIR
        mostrar_func(datos_procesados, titulo_seccion, key_suffix=key_suffix)
    except Exception as e:
        st.error(f"💥 Error procesando datos: {e}")
        st.error(f"💥 Función que falló: {procesador_func.__name__}")

def mostrar_tabla_articulos_con_sentimientos(df, titulo, reporte=None):

    if len(df) == 0:
        st.warning(f"🤷‍♂️ No hay datos para mostrar en: {titulo}")
        return

    st.subheader(f"📋 {titulo}")

    columnas_a_mostrar = [
        'title',
        'tono_comentarios' if 'tono_comentarios' in df.columns else 'tono_general',
        'emocion_dominante' if 'emocion_dominante' in df.columns else 'emocion_principal',
        'intensidad_media' if 'intensidad_media' in df.columns else 'intensidad_emocional',
        'confianza_media' if 'confianza_media' in df.columns else 'confianza_analisis',
        'article_date' if 'article_date' in df.columns else 'date',
        'source',
        'article_link' if 'article_link' in df.columns else 'link'
    ]

    df_vista = df[columnas_a_mostrar].copy()
    df_vista.rename(columns={
        'title': 'Título',
        'tono_comentarios': 'Tono',
        'tono_general': 'Tono',
        'emocion_dominante': 'Emoción',
        'emocion_principal': 'Emoción',
        'intensidad_media': 'Intensidad',
        'intensidad_emocional': 'Intensidad',
        'confianza_media': 'Confianza',
        'confianza_analisis': 'Confianza',
        'article_date': 'Fecha',
        'date': 'Fecha',
        'source': 'Fuente',
        'article_link': 'Enlace',
        'link': 'Enlace'
    }, inplace=True)

    st.dataframe(df_vista, use_container_width=True)

    if reporte is not None:
        mostrar_analisis_sentimientos_compacto(df, reporte, titulo)

def mostrar_tabla_articulos_agregados_con_sentimientos(df, titulo, df_comentarios_originales=None, reporte=None):
    if len(df) == 0:
        st.warning(f"🤷‍♂️ No hay datos para mostrar en: {titulo}")
        return

    st.subheader(f"📋 {titulo}")
    st.info("💡 Haz clic en la columna de la izquierda para ver comentarios del artículo")
    
    # CREAR MAPPING DESDE COMENTARIOS ORIGINALES (con títulos completos)
    if df_comentarios_originales is not None:
        mapping_titulos_originales = crear_mapping_titulos_articulos_comentarios(df_comentarios_originales)
    else:
        # Fallback al DataFrame actual (puede estar truncado)
        mapping_titulos_originales = crear_mapping_titulos_originales(df)
    
    # Preparar DataFrame con presentación bonita
    df_display = df.copy()

    # GUARDAR TEXTO ORIGINAL ANTES DE TRUNCAR
    if 'title' in df_display.columns:
        df_display['texto_original_completo'] = df_display['title'].copy()

    # Truncar títulos a 5 palabras
    if 'title' in df_display.columns:
        df_display['title'] = df_display['title'].apply(lambda x: truncar_titulo_palabras(x, 5))
    
    # MAPEO DE COLUMNAS: Detectar qué columnas usar
    columnas_mapeo = {
        'titulo': 'title',
        'tono': 'tono_comentarios' if 'tono_comentarios' in df.columns else 'tono_general',
        'emocion': 'emocion_dominante' if 'emocion_dominante' in df.columns else 'emocion_principal',
        'intensidad': 'intensidad_media' if 'intensidad_media' in df.columns else 'intensidad_emocional',
        'confianza': 'confianza_media' if 'confianza_media' in df.columns else 'confianza_analisis',
        'fecha': 'article_date' if 'article_date' in df.columns else 'date',
        'enlace': 'article_link' if 'article_link' in df.columns else 'link'
    }
    
    # PRESENTACIÓN VISUAL BONITA con emojis
    df_display['tono_emoji'] = df_display[columnas_mapeo['tono']].map({
        'positivo': '😊 Positivo',
        'negativo': '😔 Negativo', 
        'neutral': '😐 Neutral'
    }).fillna('🤷‍♂️ Sin definir')
    
    # Emociones con emojis
    emoji_emociones = {
        'alegría': '😄', 'esperanza': '🌟', 'orgullo': '💪', 'satisfacción': '😌',
        'tristeza': '😢', 'ira': '😠', 'miedo': '😨', 'decepción': '😞', 'desprecio': '🙄',
        'sorpresa': '😲', 'nostalgia': '🥺', 'preocupación': '😟', 'neutral': '😐'
    }
    
    df_display['emocion_emoji'] = df_display[columnas_mapeo['emocion']].apply(
        lambda x: f"{emoji_emociones.get(x, '🤔')} {str(x).title()}" if pd.notna(x) else "🤷‍♂️ Ninguna"
    )
    
    # 🔧 NUEVO: CALCULAR NÚMERO DE COMENTARIOS EN LUGAR DE IDIOMA
    if df_comentarios_originales is not None:
        # Contar comentarios por artículo
        comentarios_por_articulo = {}
        for _, row in df_display.iterrows():
            article_link = row.get(columnas_mapeo['enlace'], '')
            article_title = row.get(columnas_mapeo['titulo'], '')
            
            if article_link:
                num_comentarios = len(df_comentarios_originales[
                    (df_comentarios_originales['link'] == article_link) | 
                    (df_comentarios_originales['title_original'] == article_title)
                ])
            else:
                num_comentarios = len(df_comentarios_originales[
                    df_comentarios_originales['title_original'] == article_title
                ])
            
            comentarios_por_articulo[article_title] = num_comentarios
        
        # Añadir columna de comentarios
        df_display['num_comentarios'] = df_display[columnas_mapeo['titulo']].map(comentarios_por_articulo).fillna(0)
    else:
        # Fallback: usar columna n_comments si existe
        df_display['num_comentarios'] = df_display.get('n_comments', 0)
    
    # CONFIGURACIÓN DE COLUMNAS (🔧 SIN IDIOMA, CON COMENTARIOS)
    column_config = {
        columnas_mapeo['titulo']: "📰 Título",
        "num_comentarios": st.column_config.NumberColumn("💬 Comentarios", format="%d"),  # 🔧 NUEVA COLUMNA
        "tono_emoji": "😊 Tono General",
        "emocion_emoji": "🎭 Emoción Dominante",
        columnas_mapeo['intensidad']: st.column_config.NumberColumn("🔥 Intensidad", format="%.1f/5"),
        columnas_mapeo['confianza']: st.column_config.NumberColumn("📊 Confianza", format="%.2f"),
        columnas_mapeo['fecha']: "📅 Fecha",
        "source": "🏢 Fuente",
        columnas_mapeo['enlace']: st.column_config.LinkColumn("🔗 Enlace", display_text="Ver artículo")
    }
    
    # COLUMNAS A MOSTRAR (🔧 COMENTARIOS EN LUGAR DE IDIOMA)
    columnas_mostrar = [columnas_mapeo['titulo'], "num_comentarios", "tono_emoji", "emocion_emoji", 
                       columnas_mapeo['intensidad'], columnas_mapeo['confianza'], 
                       columnas_mapeo['fecha'], "source", columnas_mapeo['enlace']]
    
    # Filtrar columnas que realmente existen
    columnas_mostrar = [col for col in columnas_mostrar if col in df_display.columns]
    
    # MOSTRAR TABLA CON SELECTOR
    try:
        event = st.dataframe(
            df_display[columnas_mostrar],
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=600
        )
    except Exception as e:
        st.error(f"💥 Error mostrando tabla: {e}")
        return
            
    # PANEL DE COMENTARIOS SI HAY ARTÍCULO SELECCIONADO
    if event.selection.rows and df_comentarios_originales is not None:
        selected_idx = event.selection.rows[0]
        selected_article = df_display.iloc[selected_idx]
        
        st.divider()
        
        # Mostrar título original del artículo
        titulo_original = obtener_titulo_original(selected_article, mapping_titulos_originales)
        st.subheader(f"**📰 Artículo:** {titulo_original}")
        
        # Buscar comentarios de este artículo específico
        article_link = selected_article.get(columnas_mapeo['enlace'], '')
        article_title = selected_article.get(columnas_mapeo['titulo'], '')
        
        # Filtrar comentarios del artículo seleccionado
        if article_link:
            comentarios_artículo = df_comentarios_originales[
                (df_comentarios_originales['link'] == article_link) | 
                (df_comentarios_originales['title_original'] == article_title)
            ]
        else:
            comentarios_artículo = df_comentarios_originales[
                df_comentarios_originales['title_original'] == article_title
            ]
        
        if len(comentarios_artículo) > 0:
            st.write(f"**💬 Encontrados {len(comentarios_artículo)} comentarios:**")
    
            # 🔧 ANÁLISIS BAJO DEMANDA 
            analizador = st.session_state.get('analizador_global', None)
    
            if analizador is not None:
                with st.spinner(f"🧠 Analizando {len(comentarios_artículo)} comentarios..."):
                    try:
                        from .sentiment_integration import aplicar_analisis_sentimientos
                        comentarios_analizados, _ = aplicar_analisis_sentimientos(comentarios_artículo, analizador)
                
                        # 🔧 NUEVO ORDEN 1: COMENTARIOS PRIMERO                        
                        # Mostrar comentarios individuales con análisis (CON IDIOMA)
                        for idx, comment in comentarios_analizados.iterrows():
                            comment_text = comment.get('title', '')
                            comment_author = comment.get('comment_author', 'Anónimo')
                            likes = comment.get('likes', 0)
                            dislikes = comment.get('dislikes', 0)
                            location = comment.get('comment_location', 'No especificada')
                            
                            # Construir título con análisis (CON IDIOMA)
                            titulo = f"💬 {comment_author} | 👍 {likes} | 👎 {dislikes} | 📍 {location}"
                            
                            if 'idioma' in comment:
                                idioma = comment['idioma']
                                tono = comment.get('tono_general', 'neutral')
                                emocion = comment.get('emocion_principal', 'neutral')
                                intensidad = comment.get('intensidad_emocional', 1)
                                
                                emoji_idioma = '🏴󠁥󠁳󠁧󠁡󠁿' if idioma == 'gallego' else '🇪🇸'
                                emoji_tono = '😊' if tono == 'positivo' else '😔' if tono == 'negativo' else '😐'
                                
                                titulo += f" | {emoji_idioma} {idioma.title()} | {emoji_tono} {tono.title()} | 🎭 {emocion.title()} | 🔥 {intensidad}/5"
                            
                            with st.expander(titulo):
                                st.write(comment_text)
                        
                        # 🔧 NUEVO ORDEN 2: ANÁLISIS ESPECÍFICO DESPUÉS
                        st.divider()
                        mostrar_analisis_comentarios_articulo_especifico(selected_article, comentarios_analizados, columnas_mapeo)
                                
                    except Exception as e:
                        st.error(f"❌ Error en análisis específico: {e}")
                        # Fallback sin análisis específico - SOLO COMENTARIOS
                        st.write("**📝 Comentarios individuales:**")
                        for idx, comment in comentarios_artículo.iterrows():
                            titulo = f"💬 {comment.get('comment_author', 'Anónimo')} | 👍 {comment.get('likes', 0)} | 👎 {comment.get('dislikes', 0)}"
                            with st.expander(titulo):
                                st.write(comment.get('title', ''))
            else:
                # Sin analizador - solo mostrar comentarios básicos
                st.write("**📝 Comentarios individuales:**")
                for idx, comment in comentarios_artículo.iterrows():
                    titulo = f"💬 {comment.get('comment_author', 'Anónimo')} | 👍 {comment.get('likes', 0)} | 👎 {comment.get('dislikes', 0)}"
                    with st.expander(titulo):
                        st.write(comment.get('title', ''))    
        else:
            st.info("🤷‍♂️ Este artículo no tiene comentarios")
                        
    elif event.selection.rows and df_comentarios_originales is None:
        st.info("ℹ️ Para ver comentarios individuales, proporciona el parámetro df_comentarios_originales")

    # ESTADÍSTICAS GENERALES SOLO SI NO HAY SELECCIÓN
    if reporte is not None and not event.selection.rows:
        st.divider()
        mostrar_analisis_sentimientos_compacto(df_display, reporte, titulo)

def ordenar_articulos_polemicos(df_comentarios_completos):
    """
    Función auxiliar para ordenar artículos por número de comentarios
    antes de aplicar análisis de sentimientos
    """
    if len(df_comentarios_completos) == 0:
        return pd.DataFrame()
    
    # Contar comentarios por artículo
    conteo_comentarios = df_comentarios_completos.groupby('title_original').agg({
        'title': 'first',  # Tomar el primer título
        'link': 'first',   # Tomar el primer enlace
        'source': 'first', # Tomar la primera fuente
        'date': 'first',   # Tomar la primera fecha
        'title_original': 'count'  # Contar comentarios
    }).rename(columns={'title_original': 'num_comentarios'})
    
    # Ordenar por número de comentarios descendente
    conteo_comentarios = conteo_comentarios.sort_values('num_comentarios', ascending=False)
    
    return conteo_comentarios.reset_index()

def mostrar_analisis_comentarios_articulo_especifico(selected_article, comentarios_articulo, columnas_mapeo):
    """
    🆕 NUEVA FUNCIÓN: Muestra análisis emocional específico del artículo seleccionado
    
    Args:
        selected_article: Fila del artículo seleccionado
        comentarios_articulo: DataFrame con comentarios específicos del artículo
        columnas_mapeo: Mapeo de columnas para acceso consistente
    """
    if len(comentarios_articulo) == 0:
        st.info("🤷‍♂️ Este artículo no tiene comentarios para analizar")
        return
    
    # Título del análisis específico
    article_title = selected_article.get(columnas_mapeo['titulo'], 'Artículo sin título')
    st.subheader(f"🎯 Análisis específico del artículo")
    st.write("---")

    # Verificar si los comentarios tienen análisis de sentimientos
    tiene_analisis = 'idioma' in comentarios_articulo.columns
    
    if not tiene_analisis:
        st.info("ℹ️ Los comentarios de este artículo no tienen análisis emocional procesado")
        st.write(f"📊 **Total comentarios**: {len(comentarios_articulo)}")
        return
    
    # 📊 MÉTRICAS ESPECÍFICAS DEL ARTÍCULO
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💬 Comentarios", len(comentarios_articulo))
    
    with col2:
        # Comentarios políticos (detectados por el analizador)
        if 'es_politico' in comentarios_articulo.columns:
            politicos = comentarios_articulo['es_politico'].sum()
        else:
            politicos = 0
        st.metric("🏛️ Políticos", int(politicos))
    
    with col3:
        # Intensidad promedio
        if 'intensidad_emocional' in comentarios_articulo.columns:
            intensidad_promedio = comentarios_articulo['intensidad_emocional'].mean()
            st.metric("🔥 Intensidad", f"{intensidad_promedio:.1f}/5")
        else:
            st.metric("🔥 Intensidad", "N/A")
    
    with col4:
        # Comentarios positivos
        if 'tono_general' in comentarios_articulo.columns:
            positivos = (comentarios_articulo['tono_general'] == 'positivo').sum()
            st.metric("😊 Positivos", int(positivos))
        else:
            st.metric("😊 Positivos", "N/A")
    
    with col5:
        # Comentarios negativos
        if 'tono_general' in comentarios_articulo.columns:
            negativos = (comentarios_articulo['tono_general'] == 'negativo').sum()
            st.metric("😔 Negativos", int(negativos))
        else:
            st.metric("😔 Negativos", "N/A")
    
    # 📈 GRÁFICOS ESPECÍFICOS
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**🎭 Emociones en este artículo:**")
        
        if 'emocion_principal' in comentarios_articulo.columns:
            emociones_articulo = comentarios_articulo['emocion_principal'].value_counts().to_dict()
                        
            if emociones_articulo:
                emociones_df = pd.DataFrame(list(emociones_articulo.items()), 
                                           columns=['Emoción', 'Cantidad'])
                st.bar_chart(emociones_df.set_index('Emoción')['Cantidad'], height=250)
            else:
                st.info("😐 Solo emociones neutrales detectadas")
        else:
            st.info("🤷‍♂️ Sin datos de emociones")
    
    with col2:
        st.write("**📊 Detalles específicos:**")
        
        # Distribución de tonos
        if 'tono_general' in comentarios_articulo.columns:
            tonos_articulo = comentarios_articulo['tono_general'].value_counts().to_dict()
            total_comentarios_articulo = len(comentarios_articulo)
            
            st.write("**🎯 Ambiente en comentarios:**")
            for tono, cantidad in tonos_articulo.items():
                porcentaje = (cantidad / total_comentarios_articulo) * 100
                emoji = "😊" if tono == "positivo" else "😔" if tono == "negativo" else "😐"
                st.write(f"{emoji} **{tono.title()}**: {porcentaje:.1f}% ({cantidad})")
        
        # Distribución de idiomas
        if 'idioma' in comentarios_articulo.columns:
            idiomas_articulo = comentarios_articulo['idioma'].value_counts().to_dict()
            
            st.write("**🌍 Idiomas en comentarios:**")
            for idioma, cantidad in idiomas_articulo.items():
                porcentaje = (cantidad / len(comentarios_articulo)) * 100
                emoji = "🏴󠁥󠁳󠁧󠁡󠁿" if idioma == "gallego" else "🇪🇸"
                st.write(f"{emoji} **{idioma.title()}**: {porcentaje:.1f}% ({cantidad})")
        
        # Comentarios más "intensos"
        if 'intensidad_emocional' in comentarios_articulo.columns:
            intensidad_alta = (comentarios_articulo['intensidad_emocional'] >= 4).sum()
            intensidad_baja = (comentarios_articulo['intensidad_emocional'] <= 2).sum()
            
            st.write("**🔥 Nivel de intensidad:**")
            st.write(f"🌶️ **Alta intensidad (4-5)**: {intensidad_alta}")
            st.write(f"🧊 **Baja intensidad (1-2)**: {intensidad_baja}")


def generar_reporte_comentarios_articulo(comentarios_articulo):
    """
    🆕 NUEVA FUNCIÓN: Genera un reporte específico para comentarios de un artículo
    
    Args:
        comentarios_articulo: DataFrame con comentarios del artículo específico
        
    Returns:
        Dict con estadísticas específicas del artículo
    """
    if len(comentarios_articulo) == 0:
        return None
    
    # Verificar si hay análisis de sentimientos
    tiene_analisis = all(col in comentarios_articulo.columns for col in 
                        ['idioma', 'tono_general', 'emocion_principal'])
    
    if not tiene_analisis:
        return {
            'total_comentarios': len(comentarios_articulo),
            'tiene_analisis': False
        }
    
    # Generar estadísticas específicas
    reporte_especifico = {
        'total_comentarios': len(comentarios_articulo),
        'tiene_analisis': True,
        'comentarios_politicos': comentarios_articulo.get('es_politico', pd.Series([False] * len(comentarios_articulo))).sum(),
        'distribución_idiomas': comentarios_articulo['idioma'].value_counts().to_dict(),
        'tonos_generales': comentarios_articulo['tono_general'].value_counts().to_dict(),
        'emociones_principales': comentarios_articulo['emocion_principal'].value_counts().to_dict(),
        'intensidad_promedio': comentarios_articulo.get('intensidad_emocional', pd.Series([1] * len(comentarios_articulo))).mean(),
        'confianza_promedio': comentarios_articulo.get('confianza_analisis', pd.Series([0.5] * len(comentarios_articulo))).mean()
    }
    
    return reporte_especifico