import pandas as pd
import matplotlib.pyplot as plt

# Refactorizar la función original en sub-funciones reutilizables
def generar_visualizaciones_politicas(vis_total: pd.DataFrame):
    """
    Genera y muestra todas las visualizaciones de interés político.
    """
    visualizar_por_politico(vis_total)
    visualizar_por_partido(vis_total)
    visualizar_por_mes(vis_total)
    visualizar_por_tematica_inferida(vis_total)


def visualizar_por_politico(vis_total: pd.DataFrame):
    politicos = ['Ramallo', 'Pazos', 'Santos']
    vis_politicos = [
        vis_total[vis_total['title'].str.contains("Ramallo", case=False, na=False)]['n_visualizations'].sum(),
        vis_total[vis_total['title'].str.contains("Pazos", case=False, na=False)]['n_visualizations'].sum(),
        vis_total[vis_total['title'].str.contains("Santos", case=False, na=False)]['n_visualizations'].sum()
    ]

    fig, ax = plt.subplots()
    ax.bar(politicos, vis_politicos)
    ax.set_title("🏛️ Visualizaciones por político")
    ax.set_ylabel("Visualizaciones")
    ax.set_xlabel("Político")
    plt.tight_layout()
    plt.show()


def visualizar_por_partido(vis_total: pd.DataFrame):
    partidos = ['PP', 'PSOE', 'BNG']
    vis_partidos = [
        vis_total[vis_total['title'].str.contains(r"\bPP\b|partido popular", case=False, na=False)]['n_visualizations'].sum(),
        vis_total[vis_total['title'].str.contains("psoe|partido socialista", case=False, na=False)]['n_visualizations'].sum(),
        vis_total[vis_total['title'].str.contains("bng|bloque", case=False, na=False)]['n_visualizations'].sum()
    ]

    fig, ax = plt.subplots()
    ax.bar(partidos, vis_partidos, color='gray')
    ax.set_title("🔍 Visualizaciones por partido")
    ax.set_ylabel("Visualizaciones")
    ax.set_xlabel("Partido")
    plt.tight_layout()
    plt.show()


def visualizar_por_mes(vis_total: pd.DataFrame):
    vis_total['year_month'] = vis_total['date'].astype(str).str[:7]
    monthly_views = vis_total.groupby('year_month')['n_visualizations'].sum().reset_index()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(monthly_views['year_month'], monthly_views['n_visualizations'], marker='o')
    ax.set_title("📅 Visualizaciones totales por mes")
    ax.set_ylabel("Visualizaciones")
    ax.set_xlabel("Mes")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def visualizar_por_tematica_inferida(vis_total: pd.DataFrame):
    def inferir_tematica(texto):
        texto = str(texto).lower()
        if any(p in texto for p in ["ramallo", "pazos", "santos", "concejal", "concelleiro", "alcaldesa", "alcalde", "candidato"]):
            return "🏛️ Política"
        elif any(e in texto for e in ["falleció", "esquela", "funeral", "necrológica", "velatorio"]):
            return "🕊️ Necrológicas"
        elif any(f in texto for f in ["fiesta", "verbena", "festival", "romería", "celebración"]):
            return "🎉 Festividades"
        elif any(t in texto for t in ["bus", "autobús", "tráfico", "movilidad", "transporte"]):
            return "🚌 Transporte"
        elif any(o in texto for o in ["opinión", "editorial", "carta al director"]):
            return "💭 Opinión"
        else:
            return "📄 Otra"

    vis_total["tematica"] = vis_total["title"].combine_first(vis_total["summary"]).apply(inferir_tematica)
    temas_vis = vis_total.groupby('tematica')['n_visualizations'].sum().sort_values(ascending=False)
    temas_vis = temas_vis[temas_vis.index != "📄 Otra"]

    fig, ax = plt.subplots(figsize=(10, 5))
    temas_vis.plot(kind='bar', ax=ax)
    ax.set_title("📂 Visualizaciones por temática (sin 'Otra')")
    ax.set_xlabel("Temática")
    ax.set_ylabel("Total de visualizaciones")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()
