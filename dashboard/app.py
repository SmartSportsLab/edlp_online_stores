#!/usr/bin/env python3
"""
Panel de Inteligencia de Tienda de Club — EDA interactivo
Construido con Dash, Plotly y Bootstrap. App multipágina con analítica y catálogo.
"""

import os
import dash
from dash import dcc, html, Input, Output, callback, page_container
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from collections import Counter
import re

# Import tree map navigation
from treemap_navigation import create_treemap_layout
from horizontal_tree_diagram import create_horizontal_tree_layout
from i18n import tr, club_dropdown_options, normalize_lang

_ANALYTICS_LANG_OPTIONS = sorted(
    [
        {'label': 'Deutsch', 'value': 'de'},
        {'label': 'English', 'value': 'en'},
        {'label': 'Español', 'value': 'es'},
        {'label': 'Français', 'value': 'fr'},
        {'label': 'Italiano', 'value': 'it'},
        {'label': 'Português', 'value': 'pt'},
        {'label': '中文 (简体)', 'value': 'zh'},
    ],
    key=lambda o: o['label'].casefold(),
)

# ════════════════════════════════════════════════════════════════
# DATA
# ════════════════════════════════════════════════════════════════
_DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
_CLUB_STORES_ROOT = os.path.normpath(os.path.join(_DASHBOARD_DIR, '..'))
_PFM_PARENT = os.path.normpath(os.path.join(_DASHBOARD_DIR, '..', '..'))


def _default_master_xlsx_path():
    """Local PFM layout (…/Estudiantes/Submission) or flat repo with Submission/ next to dashboard."""
    candidates = [
        os.path.join(_PFM_PARENT, 'Submission', 'master_data.xlsx'),
        os.path.join(_CLUB_STORES_ROOT, 'Submission', 'master_data.xlsx'),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return candidates[-1]


# Canonical product feed (Submission). Override with env CLUB_STORES_MASTER_DATA if needed.
MASTER_DATA_XLSX = os.environ.get('CLUB_STORES_MASTER_DATA') or _default_master_xlsx_path()
DATA_CSV_FALLBACK = os.path.join(_CLUB_STORES_ROOT, 'data', 'master_categorized_corrected.csv')


def _load_master_products():
    """Load merged master from Excel when present, else CSV under Club Stores/data."""
    if os.path.isfile(MASTER_DATA_XLSX):
        out = pd.read_excel(MASTER_DATA_XLSX, sheet_name=0, engine='openpyxl')
        print(f"Cargando datos desde Excel: {MASTER_DATA_XLSX}")
    else:
        out = pd.read_csv(DATA_CSV_FALLBACK)
        print(f"Cargando datos desde CSV (Excel no encontrado): {DATA_CSV_FALLBACK}")
    out.columns = [str(c).strip() for c in out.columns]
    return out


df = _load_master_products()

# Rename inferred_club to club_name for dashboard compatibility
if 'inferred_club' in df.columns:
    df.rename(columns={'inferred_club': 'club_name'}, inplace=True)

# Add missing columns with default values if they don't exist
required_columns = ['original_price', 'discount_percentage', 'description', 'technical_details', 
                   'material', 'brand', 'in_stock', 'image_urls', 'scrape_timestamp', 'price_category']

for col in required_columns:
    if col not in df.columns:
        if col == 'original_price':
            df[col] = df['price']  # Use price as original_price
        elif col == 'discount_percentage':
            df[col] = 0  # No discount
        elif col == 'price_category':
            # Create price categories based on price
            df[col] = pd.cut(df['price'], bins=[0, 50000, 100000, float('inf')],
                           labels=['Económico', 'Estándar', 'Premium'])
        elif col in ['description', 'technical_details', 'material', 'brand']:
            df[col] = 'N/A'  # Default value
        elif col == 'in_stock':
            df[col] = True  # Assume in stock
        elif col == 'image_urls':
            df[col] = ''  # Empty string
        elif col == 'scrape_timestamp':
            df[col] = '2026-04-10'  # Default timestamp

# Create three-tier category column from product names for clubs without category_breadcrumb
def extract_category_tier1(name):
    """Extract broad category (Tier 1) from product name"""
    if pd.isna(name):
        return None
    
    name_lower = str(name).lower()
    
    if any(x in name_lower for x in ['camiseta', 'remera', 'jersey', 'shirt']):
        return 'Indumentaria'
    elif any(x in name_lower for x in ['short', 'pantalon', 'pant']):
        return 'Indumentaria'
    elif any(x in name_lower for x in ['zapatilla', 'botines', 'calzado', 'shoe']):
        return 'Calzado'
    elif any(x in name_lower for x in ['accesorio', 'gorra', 'mochila', 'bolso']):
        return 'Accesorios'
    elif any(x in name_lower for x in ['bebe', 'baby', 'mamadera']):
        return 'Bebés'
    elif any(x in name_lower for x in ['hogar', 'bazar', 'mate', 'taza']):
        return 'Hogar'
    else:
        return 'Otros'

def extract_category_tier2(name):
    """Extract specific category (Tier 2) from product name"""
    if pd.isna(name):
        return None
    
    name_lower = str(name).lower()
    
    if any(x in name_lower for x in ['camiseta', 'remera', 'jersey', 'shirt']):
        return 'Camisetas'
    elif any(x in name_lower for x in ['short', 'pantalon', 'pant']):
        return 'Pantalones/Shorts'
    elif any(x in name_lower for x in ['zapatilla', 'botines', 'calzado', 'shoe']):
        return 'Calzado'
    elif any(x in name_lower for x in ['accesorio', 'gorra', 'mochila', 'bolso']):
        return 'Accesorios'
    elif any(x in name_lower for x in ['bebe', 'baby', 'mamadera']):
        return 'Bebés'
    elif any(x in name_lower for x in ['hogar', 'bazar', 'mate', 'taza']):
        return 'Hogar'
    else:
        return 'Otros'

def extract_category_tier3(name):
    """Extract detailed category (Tier 3) from product name"""
    if pd.isna(name):
        return None
    
    name_lower = str(name).lower()
    
    # Camisetas
    if any(x in name_lower for x in ['camiseta titular', 'remera titular']):
        return 'Camisetas Titulares'
    elif any(x in name_lower for x in ['camiseta suplente', 'remera suplente']):
        return 'Camisetas Suplentes'
    elif any(x in name_lower for x in ['camiseta alternativa', 'remera alternativa']):
        return 'Camisetas Alternativas'
    elif any(x in name_lower for x in ['camiseta', 'remera', 'jersey', 'shirt']):
        return 'Otras Camisetas'
    
    # Pantalones/Shorts
    elif any(x in name_lower for x in ['short']):
        return 'Shorts'
    elif any(x in name_lower for x in ['pantalon', 'pant']):
        return 'Pantalones'
    
    # Calzado
    elif any(x in name_lower for x in ['zapatilla']):
        return 'Zapatillas'
    elif any(x in name_lower for x in ['botines']):
        return 'Botines'
    elif any(x in name_lower for x in ['calzado', 'shoe']):
        return 'Otros Calzado'
    
    # Accesorios
    elif any(x in name_lower for x in ['gorra']):
        return 'Gorras'
    elif any(x in name_lower for x in ['mochila', 'bolso']):
        return 'Bolsos y Mochilas'
    elif any(x in name_lower for x in ['accesorio']):
        return 'Otros Accesorios'
    
    # Bebés
    elif any(x in name_lower for x in ['bebe', 'baby']):
        return 'Artículos de Bebé'
    elif any(x in name_lower for x in ['mamadera']):
        return 'Mamaderas'
    
    # Hogar
    elif any(x in name_lower for x in ['mate']):
        return 'Mates y Accesorios'
    elif any(x in name_lower for x in ['taza']):
        return 'Tazas y Vasos'
    elif any(x in name_lower for x in ['bazar']):
        return 'Artículos de Bazar'
    elif any(x in name_lower for x in ['hogar']):
        return 'Artículos del Hogar'
    
    else:
        return 'Otros'

# Check if tier columns exist (they should in enhanced dataset)
if 'category_tier_1' in df.columns:
    print("Usando categorías de tres niveles precalculadas del dataset mejorado")
    if 'category_tier_3' not in df.columns:
        df['category_tier_3'] = df['product_name'].apply(extract_category_tier3)
else:
    print("No se encontraron columnas de nivel; generando categorías desde nombres de producto...")
    # Create three-tier category columns from product names
    df['category_tier_1'] = df['product_name'].apply(extract_category_tier1)
    df['category_tier_2'] = df['product_name'].apply(extract_category_tier2)
    df['category_tier_3'] = df['product_name'].apply(extract_category_tier3)

# Enhanced dataset already has proper categories, no need for breadcrumb processing

# Updated club colors to match actual screenshot
CLUB_COLORS = {
    'Boca Juniors':    '#FFD700',      # Gold/Yellow
    'River Plate':     '#FFFFFF',      # White
    'Racing Club':     '#00A3E0',      # Light Blue
    'Independiente':   '#7B1111',      # Dark red (distinct from Estudiantes)
    'San Lorenzo':     '#0047AB',      # Dark Blue
    'Estudiantes':     '#FF0000',      # Red
}
# Outline colors for visibility on dark background
CLUB_LINE = {
    'Boca Juniors':    '#FFFFFF',   # white outline
    'River Plate':     '#000000',   # black outline
    'Racing Club':     '#FFFFFF',   # white outline
    'Independiente':   '#E0E0E0',   # light outline on dark red fill
    'San Lorenzo':     '#5a7aaf',   # lighter outline for dark navy
    'Estudiantes':     '#FFFFFF',   # white outline
}
EDLP_CLUB = 'Estudiantes'
CLUB_ORDER = [EDLP_CLUB] + sorted([c for c in CLUB_COLORS if c != EDLP_CLUB])
CAT_ORDER = ['Indumentaria', 'Accesorios', 'Hogar & Bazar', 'Calzado', 'Ofertas / Otros']

# NEW: Age group colors
AGE_COLORS = {
    'Adulto': '#2196F3',
    'Niños': '#FF9800', 
    'Juvenil': '#4CAF50',
    'Bebés': '#9C27B0'
}

# NEW: Brand colors
BRAND_COLORS = {
    'Adidas': '#2196F3',
    'Puma': '#795548',
    'Topper': '#4CAF50',
    'Nike': '#FF5722'
}
CAT_COLORS = {
    # Tier 1 categories
    'Indumentaria': '#2196F3', 'Accesorios': '#FF9800',
    'Hogar & Bazar': '#4CAF50', 'Calzado': '#9C27B0',
    'Ofertas / Otros': '#757575', 'Ofertas': '#FF5722',
    'Niños & Juvenil': '#E91E63',
    
    # Tier 2 categories
    'Otros': '#607D8B', 'Accesorios Personales': '#FF9800',
    'Indumentaria': '#2196F3', 'Hogar': '#4CAF50',
    'Niños & Juvenil': '#E91E63', 'Fútbol': '#3F51B5',
    'Puma': '#795548', 'Other': '#9E9E9E',
    'Adulto': '#009688', 'Casual': '#FFC107',
    'Ruge': '#EC1B23', 'Merchandising': '#FF5722',
    'Entrenamiento': '#00BCD4', 'Básquet': '#FF6B35',
    'La Utilería': '#8BC34A', 'Atomik': '#673AB7',
    'Camisetas': '#2196F3', 'Colección': '#795548',
    'Novedades': '#FF9800', 'Oficiales': '#4CAF50',
    
    # Tier 3 categories (original club categories)
    'collección': '#795548', 'indumentaria': '#2196F3', 'accesorios': '#FF9800',
    'hogar': '#4CAF50', 'fútbol': '#3F51B5', 'puma': '#795548',
    'Ruge': '#EC1B23', 'tiemp libre': '#009688', 'Niños': '#E91E63',
    'Hombre': '#2196F3', 'Merchandising': '#FF5722', 'Regalería': '#4CAF50',
    'Juvenil': '#9C27B0', 'Bebés': '#FFC107', 'entrenamiento': '#00BCD4',
    'básquet': '#FF6B35', 'Mujer': '#E91E63', 'Escolar': '#607D8B',
    'La Utilería': '#8BC34A', 'oportunidades': '#FF5722', 'Atomik': '#673AB7',
    'Bazar': '#4CAF50', 'Hogar y Blanco': '#4CAF50', 'calzado': '#9C27B0',
    'Accesorios': '#FF9800', 'General': '#9E9E9E', 'temporada 2025': '#795548',
    'descuentos kappa': '#795548'
}
TIER_BINS = [0, 10_000, 30_000, 80_000, float('inf')]
TIER_LABELS = ['Económico < $10k', 'Medio $10k–$30k', 'Premium $30k–$80k', 'Lujo > $80k']
TIER_COLORS = {'Económico < $10k': '#4CAF50', 'Medio $10k–$30k': '#2196F3',
               'Premium $30k–$80k': '#FF9800', 'Lujo > $80k': '#E91E63'}

# NEW: Clean and prepare data for enhanced features
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['original_price'] = pd.to_numeric(df['original_price'], errors='coerce')

# NEW: Extract size data
def extract_sizes(size_str):
    if pd.isna(size_str):
        return []
    return [s.strip() for s in str(size_str).split(',') if s.strip()]

df['size_list'] = df['sizes_available'].apply(extract_sizes)

# Parsed sizes for tallas charts (normalized once at load; do not mutate `df` in callbacks)
LETTER_SIZES_CHART = ('XXS', 'XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL')
LETTER_SIZES_SET = frozenset(LETTER_SIZES_CHART)


def parse_sizes_for_chart(sizes_str):
    if pd.isna(sizes_str) or sizes_str == '':
        return []
    size_list = []
    for raw in str(sizes_str).split(','):
        clean_size = raw.strip()
        if not clean_size:
            continue
        if clean_size == '2XS':
            clean_size = 'XXS'
        elif clean_size == '2XL':
            clean_size = 'XXL'
        elif clean_size == '3XL':
            clean_size = 'XXXL'
        size_list.append(clean_size)
    return size_list


def categorize_size_token(size):
    """Letter (S/M/L…) vs numeric/other tokens for tallas toggle."""
    if size in LETTER_SIZES_SET:
        return 'Letter', size
    return 'Number', size


def club_variety_unique_sizes(club_name, show_letters):
    """Distinct letter or numeric size labels for one club (uses global `df`)."""
    club_df = df.loc[df['club_name'] == club_name]
    if club_df.empty:
        return 0
    club_sizes = set()
    for sizes_list in club_df['parsed_sizes']:
        for size in sizes_list:
            category, normalized_size = categorize_size_token(size)
            if (show_letters and category == 'Letter') or (
                not show_letters and category == 'Number'
            ):
                club_sizes.add(normalized_size)
    return len(club_sizes)


def all_clubs_variety_by_mode(show_letters):
    """Variety per club for KPI denominators and peer stats (clubs present in `df`)."""
    present = set(df['club_name'].dropna().unique())
    return {c: club_variety_unique_sizes(c, show_letters) for c in CLUB_ORDER if c in present}


df['parsed_sizes'] = df['sizes_available'].apply(parse_sizes_for_chart)

# NEW: Create analytics for new features
brand_stats = df.groupby(['club_name', 'brand']).size().unstack(fill_value=0)
age_stats = df.groupby(['club_name', 'age_group']).size().unstack(fill_value=0)
size_availability = df.groupby('club_name')['sizes_available'].apply(lambda x: x.notna().sum())

priced = df[df['price'].notna()].copy()
priced['price_tier'] = pd.cut(priced['price'], bins=TIER_BINS, labels=TIER_LABELS)

# Three-tier category system
TIER_OPTIONS = [
    {'label': 'Nivel 1: General (6 categorías)', 'value': 'tier_1'},
    {'label': 'Nivel 2: Intermedio (semi-estándar)', 'value': 'tier_2'},
    {'label': 'Nivel 3: Ultra-específico (original)', 'value': 'tier_3'}
]

KNOWN_BRANDS = ['kappa', 'adidas', 'nike', 'puma', 'umbro', 'le coq sportif',
                'giorgio redaelli', 'lumilagro', 'topper']

STOPWORDS = {'de', 'la', 'el', 'en', 'con', 'del', 'los', 'las', 'y', 'a',
             'para', 'por', 'un', 'una', 'que', 'se', 'es', 'al', 'lo', 'su',
             'club', 'racing', 'boca', 'river', 'plate', 'juniors',
             'independiente', 'san', 'lorenzo', 'estudiantes', 'plata'}


def ars(x):
    if pd.isna(x):
        return ''
    return f"$ {x:,.0f}".replace(',', '.')


def classify_audience(row):
    text = (str(row.get('product_name', '')) + ' ' +
            str(row.get('category', '')) + ' ' +
            str(row.get('product_url', ''))).lower()
    if any(kw in text for kw in ['bebe', 'baby', 'panalero', 'body bebe', 'enterito']):
        return 'Bebé'
    elif any(kw in text for kw in ['kids', 'nino', 'nina', 'niño', 'niña', 'infantil', 'junior']):
        return 'Niños'
    return 'Adulto'


priced['audience'] = priced.apply(classify_audience, axis=1)

# ════════════════════════════════════════════════════════════════
# PLOTLY TEMPLATE
# ════════════════════════════════════════════════════════════════
PLOT_TEMPLATE = 'plotly_dark'
ACCENT_COLOR = '#4fc3f7'
PLOT_BG = '#1e1e2f'
CARD_BG = '#2a2a3d'
PAPER_BG = '#1e1e2f'
FONT_COLOR = '#e0e0e0'

# Standard chart dimensions
CHART_HEIGHT = 400
CHART_FONT_SIZE = 14
# Category heatmap: light (fewest) → dark red (largest)
HEATMAP_COLORSCALE = [
    [0.0, '#ffffb2'],
    [0.25, '#fecc5c'],
    [0.5, '#fd8d3c'],
    [0.75, '#f03b20'],
    [1.0, '#bd0026'],
]
CHART_LAYOUT = dict(
    template=PLOT_TEMPLATE,
    paper_bgcolor=PAPER_BG,
    plot_bgcolor=PAPER_BG,
    font=dict(color=FONT_COLOR, family='Segoe UI, sans-serif', size=CHART_FONT_SIZE),
    margin=dict(l=50, r=30, t=50, b=50),
    height=CHART_HEIGHT,
)


def finalize_chart(fig):
    """Apply consistent typography (14px) to axes, titles, legend, heatmap colorbars, treemaps."""
    fig.update_layout(
        font=dict(color=FONT_COLOR, family='Segoe UI, sans-serif', size=CHART_FONT_SIZE),
        title=dict(font=dict(size=CHART_FONT_SIZE, color=FONT_COLOR)),
        legend=dict(font=dict(size=CHART_FONT_SIZE, color=FONT_COLOR)),
    )
    fig.update_xaxes(
        tickfont=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
        title_font=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
    )
    fig.update_yaxes(
        tickfont=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
        title_font=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
    )
    # Re-apply category heatmap palette last so template / merges never fall back to Viridis.
    fig.update_traces(
        colorscale=HEATMAP_COLORSCALE,
        autocolorscale=False,
        colorbar=dict(
            title=dict(font=dict(size=CHART_FONT_SIZE, color=FONT_COLOR)),
            tickfont=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
        ),
        selector=dict(type='heatmap'),
    )
    fig.update_traces(
        textfont=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
        selector=dict(type='bar'),
    )
    emphasize_edlp_in_figure(fig)
    return fig


def emphasize_edlp_in_figure(fig):
    """Bold 'Estudiantes' on chart text (titles, facet titles, legend names, heatmap / bar y-ticks, point labels)."""
    tag = f'<b>{EDLP_CLUB}</b>'
    ytick_kw = dict(
        tickfont=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
        title_font=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
    )

    lt = fig.layout.title
    if lt is not None and lt.text:
        t = str(lt.text)
        if EDLP_CLUB in t and tag not in t:
            fig.update_layout(title=dict(text=t.replace(EDLP_CLUB, tag), font=lt.font))

    for ann in fig.layout.annotations or []:
        txt = ann.text
        if not txt:
            continue
        txt = str(txt)
        if EDLP_CLUB in txt and tag not in txt:
            ann.update(text=txt.replace(EDLP_CLUB, tag))

    for tr in fig.data:
        nm = getattr(tr, 'name', None)
        is_edlp = nm == EDLP_CLUB

        if tr.type == 'scatter' and is_edlp and tr.mode and 'text' in str(tr.mode):
            tr.update(
                textfont=dict(
                    size=CHART_FONT_SIZE,
                    color='white',
                    family='Segoe UI Black, Arial Black, sans-serif',
                )
            )

        if tr.type == 'heatmap' and tr.y is not None:
            ys_raw = list(tr.y)
            if any(str(y) == EDLP_CLUB for y in ys_raw):
                ticktext = [tag if str(y) == EDLP_CLUB else str(y) for y in ys_raw]
                fig.update_yaxes(
                    tickmode='array',
                    tickvals=ys_raw,
                    ticktext=ticktext,
                    **ytick_kw,
                )

        if tr.type == 'bar' and getattr(tr, 'orientation', None) == 'h' and tr.y is not None:
            try:
                ylist = list(tr.y)
            except TypeError:
                ylist = []
            if ylist and all(isinstance(y, str) for y in ylist) and any(y == EDLP_CLUB for y in ylist):
                ticktext = [tag if y == EDLP_CLUB else y for y in ylist]
                fig.update_yaxes(
                    tickmode='array',
                    tickvals=ylist,
                    ticktext=ticktext,
                    **ytick_kw,
                )

        ori = getattr(tr, 'orientation', None)
        if tr.type == 'bar' and ori in (None, 'v') and tr.x is not None:
            try:
                xlist = [str(x) for x in tr.x]
            except TypeError:
                xlist = []
            if xlist and all(not str(x).replace('.', '').isdigit() for x in xlist) and any(
                x == EDLP_CLUB for x in xlist
            ):
                ticktext = [tag if x == EDLP_CLUB else x for x in xlist]
                fig.update_xaxes(
                    tickmode='array',
                    tickvals=list(tr.x),
                    ticktext=ticktext,
                    tickfont=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
                    title_font=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
                )

        if is_edlp:
            tr.update(name=tag)
        elif isinstance(nm, str) and nm and EDLP_CLUB in nm and tag not in nm:
            tr.update(name=nm.replace(EDLP_CLUB, tag))

    return fig

FINDING_CHART_H = 320


def _finding_fig_layout(title, yaxis_title=None):
    d = {
        **CHART_LAYOUT,
        'height': FINDING_CHART_H,
        'margin': dict(l=50, r=30, t=68, b=46),
        'title': dict(text=title, font=dict(size=CHART_FONT_SIZE)),
    }
    if yaxis_title:
        d['yaxis_title'] = yaxis_title
    return d


def _empty_finding_fig(title, msg):
    fig = go.Figure()
    fig.add_annotation(
        text=msg,
        xref='paper',
        yref='paper',
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=13, color=FONT_COLOR),
    )
    fig.update_layout(**_finding_fig_layout(title))
    return fig


def build_pf_finding_figures():
    """One static figure per thesis finding; built once at import from canonical df."""
    clubs = CLUB_ORDER
    bar_colors = [CLUB_COLORS[c] for c in clubs]
    line_colors = [CLUB_LINE[c] for c in clubs]
    out = []

    # 1 — Catálogo (cantidad de productos)
    n_prod = df.groupby('club_name').size().reindex(clubs, fill_value=0)
    fig1 = go.Figure(
        go.Bar(
            x=n_prod.values,
            y=clubs,
            orientation='h',
            marker_color=bar_colors,
            marker_line_color=line_colors,
            marker_line_width=1,
            text=n_prod.values,
            textposition='outside',
            cliponaxis=False,
        )
    )
    fig1.update_layout(**_finding_fig_layout('Hallazgo 1 — Tamaño del catálogo', yaxis_title='Club'))
    fig1.update_xaxes(title_text='Productos')
    out.append(
        (
            'Catálogo vs pares: número total de productos listados por club.',
            fig1,
        )
    )

    # 2 — Accesorios (% del catálogo en Tier 1)
    if 'category_tier_1' not in df.columns:
        out.append(
            (
                'Accesorios / lifestyle: sin columna category_tier_1.',
                _empty_finding_fig('Accesorios', 'Sin datos de categoría.'),
            )
        )
    else:
        t1 = df['category_tier_1'].astype(str)
        is_acc = t1.str.contains('accesorio', case=False, na=False) | t1.str.contains(
            'accessor', case=False, na=False
        )
        acc_pct = (
            df.assign(_a=is_acc).groupby('club_name')['_a'].mean() * 100
        ).reindex(clubs, fill_value=0)
        fig2 = go.Figure(
            go.Bar(
                x=clubs,
                y=acc_pct.values,
                marker_color=bar_colors,
                marker_line_color=line_colors,
                marker_line_width=1,
                text=[f'{v:.1f}%' for v in acc_pct.values],
                textposition='outside',
                cliponaxis=False,
            )
        )
        fig2.update_layout(**_finding_fig_layout('Peso de accesorios (Tier 1)'))
        fig2.update_yaxes(title_text='% de productos')
        out.append(
            (
                'Subrepresentación en accesorios (proxy: % de productos en Tier 1 tipo accesorios).',
                fig2,
            )
        )

    # 3 — Concentración Tier 1 (HHI)
    if 'category_tier_1' not in df.columns:
        out.append(
            (
                'Concentración de categorías: sin Tier 1.',
                _empty_finding_fig('Hallazgo 3 — Concentración Tier 1', 'Sin datos.'),
            )
        )
    else:
        def _hhi_from_series(s):
            vc = s.dropna().astype(str).value_counts(normalize=True)
            return float((vc ** 2).sum()) if len(vc) else 0.0

        hhi = df.groupby('club_name')['category_tier_1'].apply(_hhi_from_series)
        hhi = hhi.reindex(clubs, fill_value=0)
        fig3 = go.Figure(
            go.Bar(
                x=clubs,
                y=hhi.values,
                marker_color=bar_colors,
                marker_line_color=line_colors,
                marker_line_width=1,
                text=[f'{v:.3f}' for v in hhi.values],
                textposition='outside',
            )
        )
        fig3.update_layout(**_finding_fig_layout('Hallazgo 3 — Concentración Tier 1 (HHI)'))
        fig3.update_yaxes(title_text='Índice Herfindahl (Σ p²)')
        out.append(
            (
                'Balance de categorías: HHI en Tier 1 (mayor = mix más concentrado en pocas categorías).',
                fig3,
            )
        )

    # 4 — Precio promedio listado
    mp = priced.groupby('club_name')['price'].mean().reindex(clubs)
    fig4 = go.Figure(
        go.Bar(
            x=clubs,
            y=mp.values,
            marker_color=bar_colors,
            marker_line_color=line_colors,
            marker_line_width=1,
        )
    )
    fig4.update_layout(**_finding_fig_layout('Hallazgo 4 — Precio medio listado'))
    fig4.update_yaxes(title_text='ARS (promedio)', tickformat='$,.0f')
    out.append(
        (
            'Nivel de precios vs pares (promedio listado; el informe usa además ajuste por categoría).',
            fig4,
        )
    )

    # 5 — Mujer (% con género femenino en etiqueta)
    if 'gender' not in df.columns or df['gender'].notna().sum() == 0:
        out.append(
            (
                'Mujer: sin etiquetas de género.',
                _empty_finding_fig('Género (mujer)', 'Sin datos de género.'),
            )
        )
    else:
        def _is_women(x):
            s = str(x).lower()
            return any(k in s for k in ('mujer', 'woman', 'women', 'female', 'dama', 'femenino'))

        gdf = df[df['gender'].notna()]
        w_pct = (
            gdf.assign(_w=gdf['gender'].map(_is_women)).groupby('club_name')['_w'].mean() * 100
        ).reindex(clubs, fill_value=0)
        fig5 = go.Figure(
            go.Bar(
                x=clubs,
                y=w_pct.values,
                marker_color=bar_colors,
                marker_line_color=line_colors,
                marker_line_width=1,
                text=[f'{v:.1f}%' for v in w_pct.values],
                textposition='outside',
                cliponaxis=False,
            )
        )
        fig5.update_layout(**_finding_fig_layout('Productos etiquetados como mujer'))
        fig5.update_yaxes(title_text='% sobre productos con género')
        out.append(
            (
                'Oportunidad en surtido mujer: % con género explícito femenino.',
                fig5,
            )
        )

    # 6 — Amplitud Tier 2
    if 'category_tier_2' not in df.columns:
        out.append(
            (
                'Tier 2: sin columna.',
                _empty_finding_fig('Hallazgo 6 — Subcategorías', 'Sin datos.'),
            )
        )
    else:
        t2n = df.groupby('club_name')['category_tier_2'].nunique().reindex(clubs, fill_value=0)
        fig6 = go.Figure(
            go.Bar(
                x=clubs,
                y=t2n.values,
                marker_color=bar_colors,
                marker_line_color=line_colors,
                marker_line_width=1,
                text=t2n.values.astype(int),
                textposition='outside',
            )
        )
        fig6.update_layout(**_finding_fig_layout('Hallazgo 6 — Amplitud Tier 2'))
        fig6.update_yaxes(title_text='N° subcategorías únicas')
        out.append(('Menor cobertura de subcategorías (Tier 2) vs pares.', fig6))

    # 7 — Tramo premium listado (% precio ≥ 80k ARS)
    prem = priced.groupby('club_name')['price'].apply(lambda s: (s >= 80_000).mean() * 100)
    prem = prem.reindex(clubs, fill_value=0)
    fig7 = go.Figure(
        go.Bar(
            x=clubs,
            y=prem.values,
            marker_color=bar_colors,
            marker_line_color=line_colors,
            marker_line_width=1,
            text=[f'{v:.1f}%' for v in prem.values],
            textposition='outside',
        )
    )
    fig7.update_layout(**_finding_fig_layout('Hallazgo 7 — Tramo premium (listado)'))
    fig7.update_yaxes(title_text='% productos ≥ ARS 80k')
    out.append(
        (
            'Escalera premium vs grandes clubes (proxy: % de productos en tramo alto de precio).',
            fig7,
        )
    )

    # 8 — Mix demográfico inferido (audiencia)
    aud = priced.groupby(['club_name', 'audience']).size().unstack(fill_value=0)
    aud = aud.reindex(clubs).fillna(0)
    cols_a = list(aud.columns)
    fig8 = go.Figure()
    for col in sorted(cols_a, key=str):
        denom = aud.sum(axis=1).replace(0, np.nan)
        pct = 100 * aud[col] / denom
        fig8.add_trace(go.Bar(name=str(col), x=clubs, y=pct.fillna(0).values))
    fig8.update_layout(**_finding_fig_layout('Hallazgo 8 — Mix demográfico (inferido)'), barmode='stack')
    fig8.update_yaxes(title_text='% del catálogo', range=[0, 100])
    out.append(
        (
            'Sesgo a adultos vs familia/juvenil (clasificación heurística desde texto de producto).',
            fig8,
        )
    )

    # 9 — Profundidad de tallas
    df_n = df.assign(_ns=df['size_list'].apply(len))
    szm = df_n.groupby('club_name')['_ns'].mean().reindex(clubs, fill_value=0)
    fig9 = go.Figure(
        go.Bar(
            x=clubs,
            y=szm.values,
            marker_color=bar_colors,
            marker_line_color=line_colors,
            marker_line_width=1,
            text=[f'{v:.2f}' for v in szm.values],
            textposition='outside',
        )
    )
    fig9.update_layout(**_finding_fig_layout('Hallazgo 9 — Opciones de talla por producto'))
    fig9.update_yaxes(title_text='Promedio de tallas listadas')
    out.append(
        (
            'Ventaja en profundidad de tallas (promedio de tallas por producto).',
            fig9,
        )
    )

    # 10 — Colores (media colors_available)
    if 'colors_available' in df.columns:
        cv = pd.to_numeric(df['colors_available'], errors='coerce').groupby(df['club_name']).mean()
        cv = cv.reindex(clubs)
    else:
        cv = pd.Series(0.0, index=clubs)
    fig10 = go.Figure(
        go.Bar(
            x=clubs,
            y=cv.fillna(0).values,
            marker_color=bar_colors,
            marker_line_color=line_colors,
            marker_line_width=1,
            text=[f'{v:.2f}' for v in cv.fillna(0).values],
            textposition='outside',
        )
    )
    fig10.update_layout(**_finding_fig_layout('Hallazgo 10 — Colores por producto (promedio)'))
    fig10.update_yaxes(title_text='colors_available (media)')
    out.append(
        (
            'Cobertura de color vs pares (media numérica); el informe sugiere estrategia por categoría.',
            fig10,
        )
    )

    return [(caption, finalize_chart(fig)) for caption, fig in out]


PF_FINDING_ALL = build_pf_finding_figures()


def _finding_number_from_figure(fig):
    title_text = ''
    if fig and getattr(fig, 'layout', None) and getattr(fig.layout, 'title', None):
        title_text = str(fig.layout.title.text or '')
    m = re.search(r'Hallazgo\s+(\d+)', title_text)
    return int(m.group(1)) if m else None


PF_FINDING_BY_NUM = {idx: item for idx, item in enumerate(PF_FINDING_ALL, start=1)}
PF_FINDING_2 = PF_FINDING_BY_NUM.get(2)
PF_FINDING_5 = PF_FINDING_BY_NUM.get(5)

# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def filter_df(selected_club):
    if selected_club == 'Todos los Clubes':
        return df.copy(), priced.copy()
    return df[df['club_name'] == selected_club].copy(), \
           priced[priced['club_name'] == selected_club].copy()


def kpi_card(title, value, color=ACCENT_COLOR):
    return dbc.Col(dbc.Card([
        dbc.CardBody([
            html.H6(title, className='text-muted mb-1',
                     style={'fontSize': '0.8rem', 'textTransform': 'uppercase',
                            'letterSpacing': '1px'}),
            html.H3(value, style={'color': color, 'fontWeight': '700'}),
        ])
    ], style={'backgroundColor': CARD_BG, 'border': 'none',
              'borderLeft': f'4px solid {color}', 'borderRadius': '8px'}),
        xs=6, md=4, lg=2, className='mb-3')


# ════════════════════════════════════════════════════════════════
# APP INIT
# ════════════════════════════════════════════════════════════════
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{'name': 'viewport',
                'content': 'width=device-width, initial-scale=1'}],
    suppress_callback_exceptions=True,
)
server = app.server  # gunicorn / Render
app.title = 'EDLP | Inteligencia de Tienda'
app.index_string = app.index_string.replace(
    '{%favicon%}',
    '<link rel="icon" type="image/png" href="/assets/edlp-logo.png">',
)

# ════════════════════════════════════════════════════════════════
# LAYOUT
# ════════════════════════════════════════════════════════════════
tier_options = TIER_OPTIONS


def build_header(lang):
    return dbc.Navbar(
        dbc.Container([
            dbc.Row([
                dbc.Col(html.Div([
                    html.H4(tr(lang, 'header_title'), className='mb-0',
                             style={'fontWeight': '700', 'color': '#fff'}),
                    html.Small(tr(lang, 'header_sub'),
                               className='text-muted'),
                ]), width='auto'),
                dbc.Col([
                    html.A(tr(lang, 'gap_link'),
                           href='/gap-analysis',
                           className='btn btn-outline-light btn-sm ms-3',
                           style={'color': '#fff', 'borderColor': '#fff'})
                ], width='auto'),
            ], align='center', className='w-100'),
        ], fluid=True),
        color='#15152a', dark=True, className='mb-4 px-3 py-2',
        style={'borderBottom': f'2px solid {ACCENT_COLOR}'},
    )


def build_sidebar_nav(lang):
    return dbc.Nav([
        dbc.NavLink(
            [html.I(className="fas fa-chart-line me-2"), tr(lang, 'nav_analytics')],
            href="/",
            active="exact",
            className="text-light"
        ),
        dbc.NavLink(
            [html.I(className="fas fa-chart-bar me-2"), tr(lang, 'nav_gap')],
            href="/gap-analysis",
            className="text-light"
        ),
    ], vertical=True, className="bg-dark", style={"padding": "2rem"})


def section_title(text, subtitle=None, caption=None):
    children = [html.H5(text, style={'fontWeight': '700', 'color': ACCENT_COLOR,
                                      'marginBottom': '0.2rem'})]
    if subtitle:
        children.append(html.Small(subtitle, className='text-muted'))
    if caption:
        children.append(html.Small(
            caption,
            className='text-muted',
            style={'display': 'block', 'marginTop': '0.2rem', 'fontSize': '14px',
                   'color': '#9e9e9e', 'maxWidth': '720px'},
        ))
    return html.Div(children, className='mb-3 mt-4')


def build_analytics_body(lang):
    opts = club_dropdown_options(lang, CLUB_ORDER)
    return dbc.Container([
    # ── Headline Analysis ──
    section_title(
        tr(lang, 'sec_headline'),
        tr(lang, 'sec_headline_sub'),
    ),
    
    # Summary text
    dbc.Row([
        dbc.Col(
            html.P(
                id='headline-summary-text',
                children=tr(lang, 'headline_intro'),
                className='text-muted mb-3',
                style={'fontStyle': 'italic', 'fontSize': '14px'}
            ),
            md=12
        )
    ]),
    
    dbc.Row([
        dbc.Col(dcc.Graph(id='headline-dot-plot'), md=12),
    ], className='mb-4'),
    
        html.Hr(style={'borderColor': '#333'}),

    # ── 1. Price Distributions ──
    section_title(tr(lang, 'sec_price'),
                  tr(lang, 'sec_price_sub')),
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='price-club-filter',
                options=opts,
                value='Todos los Clubes',
                clearable=False,
                style={'width': '200px', 'color': '#333',
                       'backgroundColor': '#fff', 'borderRadius': '6px'},
            ),
            width='auto',
        ),
        dbc.Col(
            dbc.Switch(
                id='outlier-toggle',
                label=tr(lang, 'outliers'),
                value=False,  # default to exclude outliers
                style={'color': FONT_COLOR},
                className='mb-2',
            ),
            width='auto',
        ),
        dbc.Col(
            dbc.Switch(
                id='yaxis-scale-toggle',
                label=tr(lang, 'y_consistent'),
                value=True,  # default to consistent scale for fair comparison
                style={'color': FONT_COLOR},
                className='mb-2',
            ),
            width='auto',
        ),
    ], className='mb-2'),
    
    # Summary text
    dbc.Row([
        dbc.Col(
            html.P(
                tr(lang, 'price_intro'),
                className='text-muted mb-3',
                style={'fontStyle': 'italic', 'fontSize': '14px'}
            ),
            md=12
        )
    ]),
    
    dbc.Row([
        dbc.Col([
            html.P(
                id='price-hist-summary',
                children=tr(lang, 'loading_hist'),
                className='text-muted mb-2',
                style={'fontStyle': 'italic', 'fontSize': '14px'}
            ),
            dcc.Graph(id='price-hist'),
        ], md=6),
        dbc.Col([
            html.P(
                id='price-box-summary',
                children=tr(lang, 'loading_box'),
                className='text-muted mb-2',
                style={'fontStyle': 'italic', 'fontSize': '14px'}
            ),
            dcc.Graph(id='price-box'),
        ], md=6),
    ]),

        html.Hr(style={'borderColor': '#333'}),

    # ── 2. Product Categorization ──
    section_title(tr(lang, 'sec_category'),
                  tr(lang, 'sec_category_sub')),
    
    # Summary text
    dbc.Row([
        dbc.Col(
            html.P(
                id='category-summary-text',
                children=tr(lang, 'category_intro'),
                className='text-muted mb-3',
                style={'fontStyle': 'italic', 'fontSize': '14px'}
            ),
            md=12
        )
    ]),
    
    dbc.Row([
        dbc.Col([
            html.P(
                id='category-heatmap-summary',
                children=tr(lang, 'loading_heat'),
                className='text-muted mb-2',
                style={'fontStyle': 'italic', 'fontSize': '14px'}
            ),
            dcc.Graph(id='category-heatmap'),
        ], md=12),
    ]),
    *(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P(
                                tr(lang, 'pf2_caption'),
                                className='text-muted mb-2',
                                style={'fontStyle': 'italic', 'fontSize': '14px'},
                            ),
                            dcc.Graph(
                                figure=PF_FINDING_2[1],
                                config={'displayModeBar': True, 'displaylogo': False},
                            ),
                        ],
                        md=12,
                    ),
                ],
                className='mb-4',
            )
        ]
        if PF_FINDING_2
        else []
    ),

    # ── 3. Demographics & Target Audience Analysis ──
    section_title(tr(lang, 'sec_demo')),

    # Demographics club selector
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='demographics-club-filter',
                options=opts,
                value='Todos los Clubes',
                clearable=False,
                style={'width': '200px', 'color': '#333',
                       'backgroundColor': '#fff', 'borderRadius': '6px'},
            ),
            width='auto',
        ),
    ], className='mb-3'),
    
    dbc.Row([
        dbc.Col([
            html.H5(
                tr(lang, 'demo_age'),
                className='mb-2',
                style={'fontWeight': '700', 'color': ACCENT_COLOR, 'fontSize': '1.125rem'},
            ),
            html.Div(
                id='age-distribution-summary',
                children=dcc.Markdown(
                    tr(lang, 'loading_md'),
                    className='text-muted mb-2',
                    style={'fontSize': '14px'},
                ),
                className='mb-2',
            ),
            dcc.Graph(id='age-distribution-chart'),
        ], md=6),
        dbc.Col([
            html.H5(
                tr(lang, 'demo_gender'),
                className='mb-2',
                style={'fontWeight': '700', 'color': ACCENT_COLOR, 'fontSize': '1.125rem'},
            ),
            html.Div(
                id='gender-distribution-summary',
                children=dcc.Markdown(
                    tr(lang, 'loading_md'),
                    className='text-muted mb-2',
                    style={'fontSize': '14px'},
                ),
                className='mb-2',
            ),
            dcc.Graph(id='gender-distribution-chart'),
        ], md=6),
    ]),
    *(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P(
                                tr(lang, 'pf5_caption'),
                                className='text-muted mb-2',
                                style={'fontStyle': 'italic', 'fontSize': '14px'},
                            ),
                            dcc.Graph(
                                figure=PF_FINDING_5[1],
                                config={'displayModeBar': True, 'displaylogo': False},
                            ),
                        ],
                        md=12,
                    ),
                ],
                className='mb-4',
            )
        ]
        if PF_FINDING_5
        else []
    ),

        html.Hr(style={'borderColor': '#333'}),

    # ── 4. Navigation Visualizations ── (TEMPORARILY HIDDEN - Moving to Strategic Recommendations)
    # section_title('4. Diagrama de Árbol de Navegación', 
    #               'Estructura jerárquica de navegación por club (vista vertical)'),
    # 
    # # Summary text
    # dbc.Row([
    #     dbc.Col(
    #         html.P(
    #             id='navigation-summary-text',
    #             children="Explorar las estructuras de navegación de los sitios web de cada club para analizar la organización de categorías y la complejidad de la arquitectura de información.",
    #             className='text-muted mb-3',
    #             style={'fontStyle': 'italic', 'fontSize': '14px'}
    #         ),
    #         md=12
    #     )
    # ]),
    # 
    # # Navigation visualization selector
    # dbc.Row([
    #     dbc.Col([
    #         html.Label(
    #             "Seleccionar Club:",
    #             className='text-light mb-2',
    #             style={'fontWeight': 'bold'}
    #         ),
    #         dcc.Dropdown(
    #             id='nav-club-dropdown',
    #             options=[{'label': 'Estudiantes', 'value': 'Estudiantes'},
    #                     {'label': 'River Plate', 'value': 'River Plate'},
    #                     {'label': 'Boca Juniors', 'value': 'Boca Juniors'},
    #                     {'label': 'Racing Club', 'value': 'Racing Club'},
    #                     {'label': 'Independiente', 'value': 'Independiente'},
    #                     {'label': 'San Lorenzo', 'value': 'San Lorenzo'}],
    #             value='Estudiantes',
    #             clearable=False,
    #             style={'width': '200px', 'color': '#333',
    #                    'backgroundColor': '#fff', 'borderRadius': '6px'},
    #         ),
    #     ], width='auto'),
    #     
    #     dbc.Col([
    #         html.Label(
    #             "Nivel de Navegación:",
    #             className='text-light mb-2',
    #             style={'fontWeight': 'bold'}
    #         ),
    #         dcc.Dropdown(
    #             id='nav-tier-dropdown',
    #             options=[
    #                 {'label': 'Todos los Niveles', 'value': 'all'},
    #                 {'label': 'Nivel 1 (Categorías Principales)', 'value': '1'},
    #                 {'label': 'Nivel 2 (Subcategorías)', 'value': '2'},
    #                 {'label': 'Nivel 3 (Categorías Detalladas)', 'value': '3'},
    #                 {'label': 'Nivel 4 (Categorías Específicas)', 'value': '4'}
    #             ],
    #             value='all',
    #             clearable=False,
    #             style={'width': '250px', 'color': '#333',
    #                    'backgroundColor': '#fff', 'borderRadius': '6px'},
    #         ),
    #     ], width='auto'),
    #     
    #     dbc.Col([
    #         html.Div(
    #             id='nav-viz-stats',
    #             children="",
    #             className='text-muted mt-2',
    #             style={'fontStyle': 'italic', 'fontSize': '12px'}
    #         ),
    #     ], width='auto'),
    # ], className='mb-4'),
    # 
    # # Navigation visualization container
    # dbc.Row([
    #     dbc.Col([
    #         dcc.Graph(id='navigation-viz-chart'),
    #     ], md=12),
    # ], className="mb-3"),  # Reduced from mb-4

    # ── Footer ──
    html.Hr(style={'borderColor': '#333'}),
    
    # ── 5. Sizes Available Analysis ──
    section_title(tr(lang, 'sec_sizes'),
                  tr(lang, 'sec_sizes_sub')),
    
    # Summary text
    dbc.Row([
        dbc.Col(
            html.P(
                id='sizes-summary-text',
                children=tr(lang, 'sizes_intro'),
                className='text-muted mb-3',
                style={'fontStyle': 'italic', 'fontSize': '14px'}
            ),
            md=12
        )
    ]),
    
    # Sizes club selector and type toggle
    dbc.Row([
        dbc.Col(
            dcc.Dropdown(
                id='sizes-club-filter',
                options=opts,
                value='Todos los Clubes',
                clearable=False,
                style={'width': '200px', 'color': '#333',
                       'backgroundColor': '#fff', 'borderRadius': '6px'},
            ),
            width='auto',
        ),
        dbc.Col(
            html.Div([
                dbc.Label(tr(lang, 'size_type_label'), className='me-2', style={'color': '#fff', 'marginBottom': '0', 'marginTop': '8px'}),
                dbc.Switch(
                    id='sizes-type-toggle',
                    label=tr(lang, 'size_letters_toggle'),
                    value=True,  # True = letter sizes; False = numeric sizes
                    className='ms-2'
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
            width='auto',
        ),
        dbc.Col(
            html.Div([
                dbc.Label(tr(lang, 'scale_label'), className='me-2', style={'color': '#fff', 'marginBottom': '0', 'marginTop': '8px'}),
                dbc.Switch(
                    id='sizes-scale-toggle',
                    label=tr(lang, 'scale_consistent'),
                    value=True,  # Default to Consistente (True)
                    className='ms-2'
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'}),
            width='auto',
        ),
        dbc.Col([
            html.Div(
                id='sizes-club-info',
                children="",
                className='text-muted mt-2',
                style={'fontStyle': 'italic', 'fontSize': '14px'}
            ),
        ], width='auto'),
    ], className='mb-4'),
    
    # Size stats cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("0/0", className="card-title", id="total-sizes-count"),
                    html.P(
                        tr(lang, 'kpi_unique_sizes'),
                        className="card-text text-muted mb-0",
                        style={'fontSize': '14px'},
                    )
                ])
            ], className="text-center")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("XS", className="card-title", id="most-popular-size"),
                    html.P(tr(lang, 'kpi_popular'), className="card-text text-muted")
                ])
            ], className="text-center")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Estudiantes", className="card-title", id="most-diverse-club"),
                    html.P(tr(lang, 'kpi_diverse'), className="card-text text-muted")
                ])
            ], className="text-center")
        ], md=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("0", className="card-title", id="avg-sizes-per-club"),
                    html.P(tr(lang, 'kpi_avg_club'), className="card-text text-muted")
                ])
            ], className="text-center")
        ], md=3),
    ], className='mb-4'),
    
    # Per-club tallas (grid 2×3 when todos los clubes; una fila cuando un solo club)
    dbc.Row([
        dbc.Col([
            html.H6(
                tr(lang, 'sizes_chart_title'),
                className='text-center mb-3',
                style={'color': ACCENT_COLOR},
            ),
            html.Div(id='small-multiples-container'),
        ], md=12),
    ], className='mb-4', id='small-multiples-row'),
    html.Hr(style={'borderColor': '#333'}),
    html.Footer(
        html.Small(tr(lang, 'footer'),
                   className='text-muted'),
        className='text-center mb-4',
    ),
], fluid=True, style={'backgroundColor': PLOT_BG})


def build_analytics_shell(lang):
    lang = normalize_lang(lang)
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Span(
                    tr(lang, 'lang_label'),
                    className='text-muted me-2 align-middle',
                    style={'fontSize': '14px'},
                ),
                dcc.Dropdown(
                    id='analytics-lang',
                    options=_ANALYTICS_LANG_OPTIONS,
                    value=lang,
                    clearable=False,
                    style={
                        'width': '180px',
                        'display': 'inline-block',
                        'verticalAlign': 'middle',
                        'color': '#333',
                        'backgroundColor': '#fff',
                        'borderRadius': '6px',
                    },
                ),
            ], width='auto'),
        ], className='mb-3 pt-2 align-items-center'),
        build_analytics_body(lang),
    ], style={'backgroundColor': PLOT_BG, 'minHeight': '100vh'})

# ════════════════════════════════════════════════════════════════
# MULTI-PAGE LAYOUT
# ════════════════════════════════════════════════════════════════

# Multi-page layout
app.layout = dbc.Container([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="ui-language", data="es"),
    dbc.Row([
        dbc.Col([
            html.Div(id="sidebar-i18n", children=build_sidebar_nav("es")),
        ], md=2, style={"backgroundColor": "#2c3e50", "minHeight": "100vh"}),
        dbc.Col([
            html.Div(id="page-content"),
        ], md=10),
    ]),
], fluid=True, style={"padding": 0})


@callback(Output("sidebar-i18n", "children"), Input("ui-language", "data"))
def _translate_sidebar(lang):
    return build_sidebar_nav(normalize_lang(lang))


# Callback to handle page navigation
@callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("ui-language", "data"),
)
def render_page_content(pathname, lang):
    """Render the appropriate page based on URL and UI language."""
    lang = normalize_lang(lang)

    if pathname == "/gap-analysis":
        # Import and create simple gap analysis page
        from gap_analysis_simple import create_simple_gap_analysis_layout
        gap_analysis_layout = create_simple_gap_analysis_layout(df)
        return gap_analysis_layout
    # Temporarily disabled pages
    # elif pathname == "/catalog":
    #     # Import and create catalog here to avoid import issues
    #     from catalog import create_catalog_layout
    #     catalog_layout = create_catalog_layout(df)
    #     return catalog_layout
    # elif pathname == "/mockup-tabs":
    #     # Mockup: Tabs approach
    #     from mockup_tabs import create_tabs_mockup_layout
    #     tabs_mockup = create_tabs_mockup_layout(df)
    #     return tabs_mockup
    # elif pathname == "/mockup-toggle":
    #     # Mockup: Toggle button approach
    #     from mockup_toggle import create_toggle_mockup_layout
    #     toggle_mockup = create_toggle_mockup_layout(df)
    #     return toggle_mockup
    # elif pathname == "/recommendations":
    #     # Import and create recommendations page
    #     from recommendations import create_recommendations_layout
    #     recommendations_layout = create_recommendations_layout(df)
    #     return recommendations_layout
    else:
        # Default to analytics dashboard
        return html.Div([build_header(lang), build_analytics_shell(lang)], style={"backgroundColor": PLOT_BG})


@callback(
    Output("ui-language", "data"),
    Input("analytics-lang", "value"),
    prevent_initial_call=True,
)
def persist_analytics_language(value):
    return normalize_lang(value)

# Register catalog callbacks globally
def register_catalog_callbacks():
    """Register catalog callbacks globally."""
    # Import catalog functions and register simple callbacks
    from catalog import create_catalog_callbacks
    create_catalog_callbacks(df, app)
    print('Callbacks de catálogo registrados correctamente')

# Register gap analysis callbacks
def register_gap_analysis_callbacks_wrapper():
    """Register gap analysis callbacks globally."""
    from gap_analysis_simple import register_simple_gap_analysis_callbacks
    register_simple_gap_analysis_callbacks(app, df)
    print('Callbacks de análisis de brechas registrados correctamente')

# Register recommendations callbacks
def register_recommendations_callbacks():
    """Register recommendations callbacks globally."""
    from recommendations import update_recommendations_table, update_roi_calculator
    # Callbacks are already registered with @app.callback decorators
    print('Callbacks de recomendaciones registrados correctamente')

# Register callbacks when app starts
# Temporarily disabled catalog callbacks
# register_catalog_callbacks()
register_gap_analysis_callbacks_wrapper()
# Temporarily disabled recommendations callbacks
# register_recommendations_callbacks()

# Remove error logging for cleaner startup
print('Iniciando panel de Inteligencia de Tienda de Club...')
print(f'Cargados {len(df)} productos de {df["club_name"].nunique()} clubes.')


# ════════════════════════════════════════════════════════════════
# CALLBACKS
# ════════════════════════════════════════════════════════════════



# ── Helper: filter outliers ──
def _apply_outlier_filter(data, include_outliers):
    if include_outliers:
        return data
    Q1, Q3 = data['price'].quantile(0.25), data['price'].quantile(0.75)
    IQR = Q3 - Q1
    return data[(data['price'] >= Q1 - 1.5 * IQR) & (data['price'] <= Q3 + 1.5 * IQR)]


def _lang_code(lang):
    return normalize_lang(lang)


# ── 1. Price distributions ──
@callback(
    Output('price-hist', 'figure'),
    Output('price-hist-summary', 'children'),
    Input('price-club-filter', 'value'),
    Input('outlier-toggle', 'value'),
    Input('yaxis-scale-toggle', 'value'),
    Input('ui-language', 'data'),
)
def update_price_hist(selected_club, include_outliers, consistent_yaxis, lang):
    lang = _lang_code(lang)
    src = _apply_outlier_filter(priced, include_outliers)
    outlier_label = '' if include_outliers else tr(lang, 'outliers_suffix')

    if selected_club == 'Todos los Clubes':
        fig = make_subplots(
            rows=2,
            cols=3,
            subplot_titles=CLUB_ORDER,
            horizontal_spacing=0.08,
            vertical_spacing=0.28,
        )
        for idx, club in enumerate(CLUB_ORDER):
            r, c = idx // 3 + 1, idx % 3 + 1
            data = src[src['club_name'] == club]['price']
            med = data.median() if len(data) > 0 else 0
            # Compute bin edges for proper hovertemplate
            hist, bin_edges = np.histogram(data, bins=30)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            hover_text = [
                tr(
                    lang,
                    'hover_bin',
                    lo=f'{int(bin_edges[i]):,.0f}',
                    hi=f'{int(bin_edges[i + 1]):,.0f}',
                    n=int(hist[i]),
                )
                for i in range(len(hist))
            ]
            fig.add_trace(go.Histogram(
                x=data, marker_color=CLUB_COLORS[club],
                marker_line_color=CLUB_LINE[club],
                marker_line_width=1.5,
                opacity=0.85, nbinsx=30, showlegend=False,
                hovertext=hover_text,
                hovertemplate='%{hovertext}<extra></extra>',
            ), row=r, col=c)
            if len(data) > 0:
                # Position median text to avoid overlap with bars
                max_count = hist.max()
                text_y = max_count * 0.9  # 90% of max bar height
                fig.add_vline(x=med, line_dash='dash', line_color='white',
                              line_width=1, row=r, col=c,
                              annotation=dict(text=tr(lang, 'ann_median_facet', v=ars(med)),
                                              font_size=CHART_FONT_SIZE, font_color='white'))
        _hist_margin = dict(**CHART_LAYOUT['margin'])
        _hist_margin['b'] = max(_hist_margin.get('b', 50), 72)
        _hist_margin['t'] = max(_hist_margin.get('t', 50), 58)
        fig.update_layout(
            title=tr(lang, 'hist_title_all', extra=outlier_label),
            **{**CHART_LAYOUT, 'height': 520, 'margin': _hist_margin},
        )
        # Same $ range on every facet so shapes align across clubs
        prices_all = src['price'].dropna()
        if len(prices_all) > 0:
            px_min = float(prices_all.min())
            px_max = float(prices_all.max())
            span = max(px_max - px_min, 1.0)
            pad = max(span * 0.03, px_max * 0.02)
            x_lo = max(0.0, px_min - pad * 0.35)
            x_hi = px_max + pad
        else:
            x_lo, x_hi = 0.0, 1.0
        for ri in range(1, 3):
            for ci in range(1, 4):
                x_kw = dict(range=[x_lo, x_hi], tickformat='$,.0f')
                if ri == 2:
                    x_kw['title_text'] = tr(lang, 'price_axis')
                fig.update_xaxes(**x_kw, row=ri, col=ci)
        fig.update_yaxes(title_text=tr(lang, 'count_axis'), col=1)
        # Set y-axis range based on user preference
        if consistent_yaxis:
            max_count = max([np.histogram(src[src['club_name'] == club]['price'], bins=30)[0].max() 
                             for club in CLUB_ORDER])
            for i in range(1, 3):  # rows
                for j in range(1, 4):  # columns
                    fig.update_yaxes(range=[0, max_count * 1.1], row=i, col=j)
    else:
        data = src[src['club_name'] == selected_club]['price']
        color = CLUB_COLORS.get(selected_club, ACCENT_COLOR)
        # Compute bin edges for proper hovertemplate
        hist, bin_edges = np.histogram(data, bins=40)
        hover_text = [
            tr(
                lang,
                'hover_bin',
                lo=f'{int(bin_edges[i]):,.0f}',
                hi=f'{int(bin_edges[i + 1]):,.0f}',
                n=int(hist[i]),
            )
            for i in range(len(hist))
        ]
        fig = go.Figure(go.Histogram(
            x=data, marker_color=color,
            marker_line_color=CLUB_LINE.get(selected_club, color),
            marker_line_width=1.5,
            nbinsx=40, opacity=0.85,
            hovertext=hover_text,
            hovertemplate='%{hovertext}<extra></extra>',
        ))
        med = data.median() if len(data) > 0 else 0
        if len(data) > 0:
            # Get histogram data to position text above bars
            hist_counts, _ = np.histogram(data, bins=40)
            max_count = hist_counts.max()
            text_y = max_count * 0.9  # 90% of max bar height
            fig.add_vline(x=med, line_dash='dash', line_color='white',
                          annotation_text=tr(lang, 'ann_median_single', v=ars(med)),
                          annotation_font_color='white',
                          annotation_position='top')
        fig.update_layout(
            title=tr(lang, 'hist_title_club', club=selected_club, extra=outlier_label),
            xaxis_title=tr(lang, 'price_axis'), yaxis_title=tr(lang, 'count_axis'),
            **CHART_LAYOUT)
        fig.update_xaxes(tickformat='$,.0f',
                         tickvals=[50000, 100000, 150000],
                         ticktext=['$50k', '$100k', '$150k'])
    
    if selected_club == 'Todos los Clubes':
        summary_text = tr(lang, 'summary_hist_all')
    else:
        club_data = src[src['club_name'] == selected_club]
        if len(club_data) > 0:
            avg_price = club_data['price'].mean()
            summary_text = tr(
                lang,
                'summary_hist_club',
                club=selected_club,
                pmin=f'{club_data["price"].min():,.0f}',
                pmax=f'{club_data["price"].max():,.0f}',
                pavg=f'{avg_price:,.0f}',
            )
        else:
            summary_text = tr(lang, 'summary_hist_none', club=selected_club)

    return finalize_chart(fig), summary_text


@callback(
    Output('price-box', 'figure'),
    Output('price-box-summary', 'children'),
    Input('price-club-filter', 'value'),
    Input('outlier-toggle', 'value'),
    Input('ui-language', 'data'),
)
def update_price_box(selected_club, include_outliers, lang):
    lang = _lang_code(lang)
    src = _apply_outlier_filter(priced, include_outliers)
    outlier_label = '' if include_outliers else tr(lang, 'outliers_suffix')

    if selected_club == 'Todos los Clubes':
        fig = go.Figure()
        for club in CLUB_ORDER:
            data = src[src['club_name'] == club]['price']
            fig.add_trace(go.Box(
                y=data, name=club,
                marker_color=CLUB_COLORS[club],
                boxmean='sd',
                boxpoints='outliers' if include_outliers else False,
            ))
        fig.update_layout(title=tr(lang, 'box_title_all', extra=outlier_label),
                          yaxis_title=tr(lang, 'price_axis'),
                          showlegend=False, **CHART_LAYOUT)
        fig.update_traces(hoverinfo='skip', hovertemplate=None)
        fig.update_yaxes(tickformat='$,.0f',
                         tickvals=[50000, 100000, 150000],
                         ticktext=['$50k', '$100k', '$150k'])
    else:
        data = src[src['club_name'] == selected_club]['price']
        color = CLUB_COLORS.get(selected_club, ACCENT_COLOR)
        fig = go.Figure(go.Violin(
            y=data, name=selected_club,
            marker_color=color,
            box_visible=True, meanline_visible=True,
            points='outliers' if include_outliers else False,
        ))
        fig.update_layout(
            title=tr(lang, 'box_title_club', club=selected_club, extra=outlier_label),
            yaxis_title=tr(lang, 'price_axis'),
            showlegend=False, **CHART_LAYOUT)
        fig.update_traces(hoverinfo='skip', hovertemplate=None)
        fig.update_yaxes(tickformat='$,.0f',
                         tickvals=[50000, 100000, 150000],
                         ticktext=['$50k', '$100k', '$150k'])
    
    if selected_club == 'Todos los Clubes':
        summary_text = tr(lang, 'summary_box_all')
    else:
        club_data = src[src['club_name'] == selected_club]
        if len(club_data) > 0:
            median_price = club_data['price'].median()
            q1 = club_data['price'].quantile(0.25)
            q3 = club_data['price'].quantile(0.75)
            summary_text = tr(
                lang,
                'summary_box_club',
                club=selected_club,
                med=f'{median_price:,.0f}',
                q1=f'{q1:,.0f}',
                q3=f'{q3:,.0f}',
            )
        else:
            summary_text = tr(lang, 'summary_hist_none', club=selected_club)

    return finalize_chart(fig), summary_text


# ── Headline Analysis Callback ──
@callback(
    Output('headline-dot-plot', 'figure'),
    Output('headline-summary-text', 'children'),
    Input('url', 'pathname'),
    Input('ui-language', 'data'),
)
def update_headline_dot_plot(_pathname, lang):
    lang = _lang_code(lang)
    selected_metric = 'product_count'
    # Calculate metrics for each club
    club_metrics = {}
    
    for club in CLUB_ORDER:
        club_data = df[df['club_name'] == club]
        
        if selected_metric == 'product_count':
            club_metrics[club] = len(club_data)
            title = tr(lang, 'metric_products_title')
            xaxis_title = tr(lang, 'metric_products_axis')
            
        elif selected_metric == 'category_count':
            # Use category_tier_1 - derived from URLs and product names
            if 'category_tier_1' in club_data.columns:
                categories = club_data['category_tier_1'].dropna().nunique()
            else:
                categories = 0
            club_metrics[club] = categories
            title = tr(lang, 'metric_products_title')
            xaxis_title = tr(lang, 'metric_products_axis')
            
        elif selected_metric == 'avg_price':
            avg_price = club_data['price'].mean() if club_data['price'].notna().sum() > 0 else 0
            club_metrics[club] = avg_price
            title = tr(lang, 'metric_products_title')
            xaxis_title = tr(lang, 'metric_products_axis')
    
    # Generate dynamic Estudiantes-specific summary text
    estudiantes_value = club_metrics.get('Estudiantes', 0)
    
    # Calculate ranking (1 = best/highest)
    sorted_clubs = sorted(club_metrics.items(), key=lambda x: x[1], reverse=True)
    estudiantes_rank = next((i+1 for i, (club, value) in enumerate(sorted_clubs) if club == 'Estudiantes'), 0)
    
    # Calculate average and difference
    all_values = list(club_metrics.values())
    avg_value = sum(all_values) / len(all_values)
    diff_from_avg = estudiantes_value - avg_value
    
    if estudiantes_rank == 1:
        rank_text = tr(lang, 'rank_1')
    elif estudiantes_rank == 2:
        rank_text = tr(lang, 'rank_2')
    elif estudiantes_rank == 3:
        rank_text = tr(lang, 'rank_3')
    else:
        rank_text = tr(lang, 'rank_n', n=estudiantes_rank)
    
    if selected_metric == 'product_count':
        if diff_from_avg >= 0:
            summary_text = tr(
                lang,
                'sum_pc_above',
                rank=rank_text,
                val=estudiantes_value,
                diff=abs(diff_from_avg),
            )
        else:
            summary_text = tr(
                lang,
                'sum_pc_below',
                rank=rank_text,
                val=estudiantes_value,
                diff=abs(diff_from_avg),
            )
    elif selected_metric == 'category_count':
        if diff_from_avg >= 0:
            summary_text = f"Estudiantes ocupa el {rank_text} con {estudiantes_value} categorías de productos, {abs(diff_from_avg):.1f} por encima del promedio de clubes."
        else:
            summary_text = f"Estudiantes ocupa el {rank_text} con {estudiantes_value} categorías de productos, {abs(diff_from_avg):.1f} por debajo del promedio de clubes."
    elif selected_metric == 'avg_price':
        if diff_from_avg >= 0:
            summary_text = f"Estudiantes ocupa el {rank_text} con un precio promedio de ${estudiantes_value:,.0f}, ${abs(diff_from_avg):,.0f} por encima del promedio de clubes."
        else:
            summary_text = f"Estudiantes ocupa el {rank_text} con un precio promedio de ${estudiantes_value:,.0f}, ${abs(diff_from_avg):,.0f} por debajo del promedio de clubes."
    
    # Create figure with all clubs on a single horizontal line
    fig = go.Figure()
    
    # Add a trace for each club (for legend)
    # Track used positions to avoid overlapping
    used_positions = {}
    
    for i, club in enumerate(CLUB_ORDER):
        value = club_metrics[club]
        color = CLUB_COLORS.get(club, ACCENT_COLOR)
        
        # Format value based on metric
        if selected_metric == 'avg_price':
            text_value = f'${value:,.0f}'
        else:
            text_value = f'{value:,.0f}'
        
        # Add slight y-offset to prevent overlapping
        y_offset = 0
        if value in used_positions:
            # Offset by 0.1 for each duplicate
            y_offset = used_positions[value] * 0.1
        used_positions[value] = used_positions.get(value, 0) + 1
        
        fig.add_trace(go.Scatter(
            x=[value],
            y=[y_offset],  # Slight offset to prevent overlapping
            mode='markers+text',
            marker=dict(
                size=20,
                color=color,
                line=dict(width=2, color='white')
            ),
            text=[text_value],
            textposition='top center',
            textfont=dict(size=CHART_FONT_SIZE, color='white'),
            name=club,
            hovertemplate=f'<b>{club}</b><br>{xaxis_title}: {text_value}<extra></extra>',
        ))

    if selected_metric == 'avg_price':
        ann_text = tr(lang, 'avg_six', v=f'${avg_value:,.0f}')
    else:
        ann_text = tr(lang, 'avg_six', v=f'{avg_value:,.0f}')
    fig.add_vline(
        x=avg_value,
        line_width=1.5,
        line_dash='dash',
        line_color='rgba(200, 200, 220, 0.55)',
        annotation_text=ann_text,
        annotation_position='top right',
        annotation=dict(font_size=CHART_FONT_SIZE, font_color=FONT_COLOR),
    )

    # Update layout (legend below plot so it does not overlap the title)
    fig.update_layout(
        title=title,
        title_y=0.97,
        xaxis_title=xaxis_title,
        yaxis=dict(
            visible=False,  # Hide y-axis since all on same line
            range=[-0.2, 0.8]  # Expanded range for offsets
        ),
        showlegend=True,
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.22,
            xanchor='center',
            x=0.5,
            font=dict(size=CHART_FONT_SIZE),
        ),
        **{**CHART_LAYOUT, 'margin': dict(l=50, r=30, t=58, b=110)},
    )
    
    # Format x-axis - remove decimals for all metrics
    if selected_metric == 'avg_price':
        fig.update_xaxes(tickformat='$,.0f')
    else:
        # For product count and category count, use integer format
        fig.update_xaxes(tickformat=',.0f')
    
    return finalize_chart(fig), summary_text


# ── Product Categorization Callbacks ──
@callback(
    Output('category-heatmap', 'figure'),
    Output('category-heatmap-summary', 'children'),
    Input('url', 'pathname'),
    Input('ui-language', 'data'),
)
def update_category_heatmap(_pathname, lang):
    lang = _lang_code(lang)
    try:
        # Fixed category view to match the target screenshot:
        # - all clubs
        # - Tier 1 category taxonomy
        selected_club = 'Todos los Clubes'
        selected_tier = 'category_tier_1'
        category_col = selected_tier
        
        if category_col not in df.columns:
            # Fallback to price_category if tier doesn't exist
            category_col = 'price_category' if 'price_category' in df.columns else None
        
        if category_col is None:
            fig = go.Figure()
            fig.update_layout(
                title=tr(lang, 'no_cat_data'),
                **CHART_LAYOUT
            )
            return finalize_chart(fig), tr(lang, 'no_cat_dataset')
        
        # Create category count matrix
        category_counts = df.groupby(['club_name', category_col]).size().unstack(fill_value=0)
        
        # Define category order for Tier 1 (aligned with merged master taxonomy)
        if selected_tier == 'category_tier_1':
            category_order = [
                'match day',
                'entrenamiento',
                'moda',
                'calzado',
                'baloncesto',
                'accessories',
                'hogar',
                'other',
            ]
            ordered = [c for c in category_order if c in category_counts.columns]
            rest = [c for c in category_counts.columns if c not in ordered]
            category_counts = category_counts[ordered + rest]
        
        # Filter clubs if specific club selected
        if selected_club != 'Todos los Clubes':
            if selected_club in category_counts.index:
                category_counts = category_counts.loc[[selected_club]]
            else:
                # Club not found, create empty
                fig = go.Figure()
                fig.update_layout(
                    title=tr(lang, 'no_data_for_club', club=selected_club),
                    **CHART_LAYOUT
                )
                return finalize_chart(fig), tr(lang, 'no_data_for_club_sum', club=selected_club)
        
        z_raw = category_counts.values.astype(float)
        flat = z_raw.ravel()
        pos = flat[flat > 0]
        zmax_cap = float(np.percentile(pos, 92)) if len(pos) else max(float(np.nanmax(flat)), 1.0)
        zmax_cap = max(zmax_cap, 1.0)
        
        fig = go.Figure(
            data=go.Heatmap(
                z=z_raw,
                x=category_counts.columns,
                y=category_counts.index,
                zmin=0,
                zmax=zmax_cap,
                autocolorscale=False,
                colorscale=HEATMAP_COLORSCALE,
                text=z_raw,
                texttemplate='%{text:.0f}',
                textfont={'size': CHART_FONT_SIZE, 'color': '#111111'},
                hovertemplate=tr(lang, 'heat_hover_plotly'),
                colorbar=dict(
                    title=dict(text=tr(lang, 'colorbar_products')),
                    tickformat=',.0f',
                ),
            )
        )
        
        _heat_margin = dict(**CHART_LAYOUT['margin'])
        _heat_margin['t'] = max(_heat_margin.get('t', 50), 78)
        fig.update_layout(
            title=tr(lang, 'heat_title'),
            xaxis_title=tr(lang, 'cat_axis'),
            yaxis_title=tr(lang, 'club_axis'),
            **{**CHART_LAYOUT, 'margin': _heat_margin},
        )
        fig.update_xaxes(side='top')
        
        if selected_club == 'Todos los Clubes':
            total_categories = category_counts.shape[1]
            max_products = category_counts.values.max()
            summary_text = tr(
                lang,
                'heat_summary_all',
                nc=total_categories,
                mx=int(max_products),
            )
        else:
            club_categories = category_counts.loc[selected_club]
            non_zero_cats = int((club_categories > 0).sum())
            total_products = int(club_categories.sum())
            summary_text = tr(
                lang,
                'heat_summary_club',
                club=selected_club,
                nc=non_zero_cats,
                tp=total_products,
            )

        return finalize_chart(fig), summary_text

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(
            title=tr(lang, 'cat_error_title'),
            **CHART_LAYOUT
        )
        return finalize_chart(fig), tr(lang, 'cat_error_body', err=str(e))


def _discrete_colors_from_heatmap_scale(n: int) -> list:
    """Repeat the category heatmap hex stops when there are more than five segments."""
    stops = [c for _, c in HEATMAP_COLORSCALE]
    return [stops[i % len(stops)] for i in range(max(1, n))]


def _segment_order(raw_series: pd.Series, na_bucket: str) -> list:
    """Frequency order, with the explicit NA bucket last."""
    filled = raw_series.fillna(na_bucket).astype(str)
    vc = filled.value_counts()
    order = list(vc.index)
    if na_bucket in order:
        order = [x for x in order if x != na_bucket] + [na_bucket]
    return order


def _gender_label_for_chart(val):
    """Map raw gender to display labels; combine bebé and juventud for the gender chart."""
    if pd.isna(val):
        return np.nan
    t = str(val).strip().lower()
    if t in ('bebe', 'bebé', 'bebés', 'baby'):
        return 'Bebé y juventud'
    if t == 'juventud':
        return 'Bebé y juventud'
    return str(val).strip()


def _demographic_stacked_figure(
    filtered_df: pd.DataFrame,
    source_col: str,
    na_bucket: str,
    chart_title: str | None,
    selected_club: str,
    segment_colors: dict | None = None,
    lang: str | None = None,
) -> go.Figure:
    """100% stacked bars by club (or one club): % of that club's catalog; NA as its own segment."""
    lc = _lang_code(lang)
    fd = filtered_df.copy()
    n_total = len(fd)
    if n_total == 0:
        fig = go.Figure()
        fig.update_layout(title=chart_title, **CHART_LAYOUT)
        fig.add_annotation(
            text=tr(lc, 'no_data_short'),
            xref='paper',
            yref='paper',
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
        )
        return fig

    fd['_seg'] = fd[source_col].fillna(na_bucket).astype(str)
    seg_order = _segment_order(fd[source_col], na_bucket)
    colors = _discrete_colors_from_heatmap_scale(len(seg_order))
    color_map = {s: colors[i] for i, s in enumerate(seg_order)}
    if segment_colors:
        for key, hex_color in segment_colors.items():
            color_map[key] = hex_color

    fig = go.Figure()

    if selected_club == 'Todos los Clubes':
        clubs_present = [c for c in CLUB_ORDER if c in fd['club_name'].unique()]
        if not clubs_present:
            fig = go.Figure()
            fig.update_layout(title=chart_title, **CHART_LAYOUT)
            return fig
        counts = fd.groupby(['club_name', '_seg']).size().unstack(fill_value=0)
        counts = counts.reindex(clubs_present, fill_value=0)
        for s in seg_order:
            if s not in counts.columns:
                counts[s] = 0
        counts = counts[[s for s in seg_order if s in counts.columns]]
        club_totals = counts.sum(axis=1).replace(0, np.nan)
        pct = counts.div(club_totals, axis=0) * 100
        pct = pct.fillna(0)

        for seg in seg_order:
            if seg not in pct.columns:
                continue
            c_vals = [int(counts.loc[c, seg]) for c in clubs_present]
            t_vals = [int(club_totals.loc[c]) if pd.notna(club_totals.loc[c]) else 0 for c in clubs_present]
            customdata = [f'{c} / {t}' for c, t in zip(c_vals, t_vals)]
            if lc == 'en':
                hov = (
                    f'<b>{seg}</b><br>%{{x}}<br>%{{y:.1f}}% of club catalog'
                    '<br>%{customdata} products<extra></extra>'
                )
            else:
                hov = (
                    f'<b>{seg}</b><br>%{{x}}<br>%{{y:.1f}}% del catálogo del club'
                    '<br>%{customdata} productos<extra></extra>'
                )
            fig.add_trace(
                go.Bar(
                    name=seg,
                    x=clubs_present,
                    y=pct[seg].tolist(),
                    marker_color=color_map[seg],
                    marker_line=dict(width=1.5, color=PAPER_BG),
                    hovertemplate=hov,
                    customdata=customdata,
                )
            )
    else:
        vc = fd['_seg'].value_counts().reindex(seg_order, fill_value=0)
        for seg in seg_order:
            cnt = int(vc[seg])
            yv = (cnt / n_total * 100) if n_total else 0.0
            if lc == 'en':
                hov1 = (
                    f'<b>{seg}</b><br>{selected_club}<br>%{{y:.1f}}% of catalog'
                    f'<br>{cnt} of {n_total} products<extra></extra>'
                )
            else:
                hov1 = (
                    f'<b>{seg}</b><br>{selected_club}<br>%{{y:.1f}}% del catálogo'
                    f'<br>{cnt} de {n_total} productos<extra></extra>'
                )
            fig.add_trace(
                go.Bar(
                    name=seg,
                    x=[selected_club],
                    y=[yv],
                    marker_color=color_map[seg],
                    marker_line=dict(width=1.5, color=PAPER_BG),
                    hovertemplate=hov1,
                )
            )

    _m = dict(**CHART_LAYOUT.get('margin', {}))
    _m['r'] = max(_m.get('r', 30), 130)
    layout_kwargs = dict(
        barmode='stack',
        xaxis_title=tr(lc, 'club_axis') if selected_club == 'Todos los Clubes' else '',
        yaxis_title=tr(lc, 'y_pct_catalog'),
        yaxis=dict(range=[0, 100], ticksuffix='%', tickformat='.0f'),
        legend=dict(
            orientation='v',
            yanchor='top',
            y=1,
            xanchor='left',
            x=1.02,
            font=dict(size=CHART_FONT_SIZE, color=FONT_COLOR),
        ),
        **{**CHART_LAYOUT, 'margin': _m},
    )
    if chart_title:
        layout_kwargs['title'] = chart_title
    fig.update_layout(**layout_kwargs)
    return fig


def _age_insight_markdown(
    filtered_df: pd.DataFrame,
    na_age: str,
    n_cat: int,
    vc_all: pd.Series,
    selected_club: str,
    lang: str | None = None,
) -> str:
    lc = _lang_code(lang)
    if n_cat == 0 or len(vc_all) == 0:
        return tr(lc, 'sin_datos_show')

    dom = str(vc_all.index[0])
    dom_pct = float(vc_all.iloc[0]) / n_cat * 100
    if selected_club == 'Todos los Clubes':
        lead = tr(lc, 'age_lead_all', n=n_cat, dom=dom, pct=dom_pct)
    else:
        lead = tr(lc, 'age_lead_club', club=selected_club, n=n_cat, dom=dom, pct=dom_pct)
    return lead + tr(lc, 'age_suffix')


def _gender_insight_markdown(
    filtered_df: pd.DataFrame,
    na_g: str,
    n_cat: int,
    vc_all: pd.Series,
    selected_club: str,
    lang: str | None = None,
) -> str:
    lc = _lang_code(lang)
    if n_cat == 0 or len(vc_all) == 0:
        return tr(lc, 'sin_datos_show')

    def _hom_muj_counts(vc: pd.Series) -> tuple[float, float]:
        h = float(vc['hombre']) if 'hombre' in vc.index else 0.0
        m = float(vc['mujer']) if 'mujer' in vc.index else 0.0
        return h, m

    if selected_club == 'Todos los Clubes':
        hom_n, muj_n = _hom_muj_counts(vc_all)
        if muj_n <= 0:
            return tr(lc, 'gender_no_mujer_all')
        r = hom_n / muj_n
        return tr(lc, 'gender_ratio_all', r=r)

    fd = filtered_df.copy()
    fd['_g'] = fd['gender'].apply(_gender_label_for_chart).fillna(na_g).astype(str)
    cg = fd[fd['club_name'] == selected_club]
    if len(cg) == 0:
        return tr(lc, 'gender_no_data_club', club=selected_club)
    vc_c = cg['_g'].value_counts()
    hom_n, muj_n = _hom_muj_counts(vc_c)
    if muj_n <= 0:
        return tr(lc, 'gender_no_mujer_club', club=selected_club)
    r = hom_n / muj_n
    return tr(lc, 'gender_ratio_club', club=selected_club, r=r)


# ── Demographics & Target Audience Callbacks ──
@callback(
    Output('age-distribution-chart', 'figure'),
    Output('age-distribution-summary', 'children'),
    Input('demographics-club-filter', 'value'),
    Input('ui-language', 'data'),
)
def update_age_distribution(selected_club, lang):
    lc = _lang_code(lang)
    try:
        if selected_club == 'Todos los Clubes':
            filtered_df = df
        else:
            filtered_df = df[df['club_name'] == selected_club]

        n_cat = len(filtered_df)
        na_age = tr(lc, 'na_age')
        fd = filtered_df.copy()
        fd['_age_disp'] = fd['age_group'].fillna(na_age).astype(str)
        vc_all = fd['_age_disp'].value_counts()

        fig = _demographic_stacked_figure(
            filtered_df,
            'age_group',
            na_age,
            None,
            selected_club,
            lang=lc,
        )

        if n_cat == 0:
            summary_md = f'*{tr(lc, "no_products_filtered")}*'
        elif len(vc_all) == 0:
            summary_md = f'*{tr(lc, "no_age_data")}*'
        else:
            summary_md = _age_insight_markdown(filtered_df, na_age, n_cat, vc_all, selected_club, lang=lc)

        summary = dcc.Markdown(
            summary_md,
            className='text-muted mb-0',
            style={'fontSize': '14px'},
        )
        return finalize_chart(fig), summary

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(
            title=tr(lc, 'demo_err_age'),
            **CHART_LAYOUT
        )
        err = dcc.Markdown(
            f'*{tr(lc, "demo_err_proc", err=str(e))}*',
            className='text-danger',
            style={'fontSize': '14px'},
        )
        return finalize_chart(fig), err

@callback(
    Output('gender-distribution-chart', 'figure'),
    Output('gender-distribution-summary', 'children'),
    Input('demographics-club-filter', 'value'),
    Input('ui-language', 'data'),
)
def update_gender_distribution(selected_club, lang):
    lc = _lang_code(lang)
    try:
        if selected_club == 'Todos los Clubes':
            filtered_df = df
        else:
            filtered_df = df[df['club_name'] == selected_club]

        n_cat = len(filtered_df)
        na_g = tr(lc, 'na_gender')
        sin_genero_color = '#D3D3D3'
        fd = filtered_df.copy()
        fd['_gender_viz'] = fd['gender'].apply(_gender_label_for_chart)
        fd['_gen_disp'] = fd['_gender_viz'].fillna(na_g).astype(str)
        vc_all = fd['_gen_disp'].value_counts()

        fig = _demographic_stacked_figure(
            fd,
            '_gender_viz',
            na_g,
            None,
            selected_club,
            segment_colors={na_g: sin_genero_color},
            lang=lc,
        )

        if n_cat == 0:
            summary_md = f'*{tr(lc, "no_products_filtered")}*'
        else:
            summary_md = _gender_insight_markdown(
                filtered_df, na_g, n_cat, vc_all, selected_club, lang=lc,
            )

        summary = dcc.Markdown(
            summary_md,
            className='text-muted mb-0',
            style={'fontSize': '14px'},
        )
        return finalize_chart(fig), summary

    except Exception as e:
        fig = go.Figure()
        fig.update_layout(
            title=tr(lc, 'demo_err_gender'),
            **CHART_LAYOUT
        )
        err = dcc.Markdown(
            f'*{tr(lc, "demo_err_proc", err=str(e))}*',
            className='text-danger',
            style={'fontSize': '14px'},
        )
        return finalize_chart(fig), err

# ── 4. Navigation Visualizations Callback ──
@callback(
    Output('navigation-viz-chart', 'figure'),
    Output('nav-viz-stats', 'children'),
    [Input('nav-club-dropdown', 'value'),
     Input('nav-tier-dropdown', 'value')]
)
def update_navigation_visualization(selected_club, selected_tier):
    """Update horizontal tree diagram based on club and tier selection"""
    try:
        # Use horizontal tree diagram with tier filtering
        from horizontal_tree_diagram import create_horizontal_tree_diagram
        fig = create_horizontal_tree_diagram(selected_club, tier_filter=selected_tier)
        
        # Calculate navigation stats
        nav_df = pd.read_csv('../club_navigation_categories.csv')
        nav_df = nav_df.fillna('')
        club_data = nav_df[nav_df['club_name'] == selected_club]
        
        if not club_data.empty:
            # Filter data based on tier selection
            if selected_tier != 'all':
                tier_num = int(selected_tier)
                if tier_num == 1:
                    filtered_data = club_data[club_data['nav_level_1'] != '']
                elif tier_num == 2:
                    filtered_data = club_data[(club_data['nav_level_1'] != '') & (club_data['nav_level_2'] != '')]
                elif tier_num == 3:
                    filtered_data = club_data[(club_data['nav_level_1'] != '') & (club_data['nav_level_2'] != '') & (club_data['nav_level_3'] != '')]
                elif tier_num == 4:
                    filtered_data = club_data[(club_data['nav_level_1'] != '') & (club_data['nav_level_2'] != '') & (club_data['nav_level_3'] != '') & (club_data['nav_level_4'] != '')]
            else:
                filtered_data = club_data
            
            # Calculate statistics
            total_paths = len(filtered_data)
            unique_level_1 = filtered_data['nav_level_1'].nunique()
            unique_level_2 = filtered_data['nav_level_2'].nunique()
            unique_level_3 = filtered_data['nav_level_3'].nunique()
            unique_level_4 = filtered_data['nav_level_4'].nunique()
            
            # Calculate average depth
            depths = []
            for _, row in filtered_data.iterrows():
                depth = 0
                if pd.notna(row['nav_level_1']) and row['nav_level_1'].strip():
                    depth += 1
                if pd.notna(row['nav_level_2']) and row['nav_level_2'].strip():
                    depth += 1
                if pd.notna(row['nav_level_3']) and row['nav_level_3'].strip():
                    depth += 1
                if pd.notna(row['nav_level_4']) and row['nav_level_4'].strip():
                    depth += 1
                if depth > 0:
                    depths.append(depth)
            
            avg_depth = sum(depths) / len(depths) if depths else 0
            
            # Create tier-specific stats
            if selected_tier == 'all':
                stats = (f"{total_paths} rutas • {unique_level_1} categorías principales • "
                         f"{avg_depth:.1f} prof. media • "
                         f"{unique_level_2 + unique_level_3 + unique_level_4} subcategorías")
            else:
                tier_num = int(selected_tier)
                if tier_num == 1:
                    stats = f"{unique_level_1} categorías de nivel 1 • Estructura principal de navegación"
                elif tier_num == 2:
                    stats = f"{unique_level_2} subcategorías de nivel 2 • Organización por subcategoría"
                elif tier_num == 3:
                    stats = f"{unique_level_3} categorías de nivel 3 • Categorías detalladas"
                elif tier_num == 4:
                    stats = f"{unique_level_4} categorías de nivel 4 • Tipos de producto específicos"
        else:
            stats = "No hay datos disponibles"
        
        return finalize_chart(fig), stats
    
    except Exception as e:
        # Create error figure
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error al cargar la visualización de navegación: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=CHART_FONT_SIZE, color="gray")
        )
        fig.update_layout(
            title='Error en la visualización de navegación',
            height=600,
            template=PLOT_TEMPLATE,
            paper_bgcolor=PAPER_BG,
            plot_bgcolor=PAPER_BG,
            font=dict(color=FONT_COLOR, family='Segoe UI, sans-serif', size=CHART_FONT_SIZE),
            margin=dict(l=50, r=30, t=50, b=50)
        )
        return finalize_chart(fig), "Error al cargar datos"

# ── 5. Sizes Available Analysis Callbacks ──
def _sizes_small_multiples_layout(filtered_df, clubs_ordered, show_letters, use_consistent_scale):
    """Per-club horizontal bar charts; Estudiantes first. One club → full width, taller figure."""
    single_club = len(clubs_ordered) == 1
    fig_height = 320 if single_club else 200
    col_props = (
        {'xs': 12, 'sm': 12, 'md': 12, 'lg': 12, 'className': 'mb-3'}
        if single_club
        else {'xs': 12, 'sm': 6, 'md': 4, 'className': 'mb-3'}
    )

    global_max_count = 0
    if use_consistent_scale:
        # League-wide max so a single-club view stays comparable to the rest of the group
        scale_df = df
        clubs_for_scale = [c for c in CLUB_ORDER if c in scale_df['club_name'].unique()]
        for club in clubs_for_scale:
            club_df = scale_df[scale_df['club_name'] == club]
            club_filtered_sizes = []
            for sizes_list in club_df['parsed_sizes']:
                for size in sizes_list:
                    category, normalized_size = categorize_size_token(size)
                    if (show_letters and category == 'Letter') or (
                        not show_letters and category == 'Number'
                    ):
                        club_filtered_sizes.append(normalized_size)
            if club_filtered_sizes:
                club_size_counts = pd.Series(club_filtered_sizes).value_counts()
                global_max_count = max(global_max_count, club_size_counts.max())
    else:
        global_max_count = None

    club_charts = []
    for club in clubs_ordered:
        club_df = filtered_df[filtered_df['club_name'] == club]
        club_filtered_sizes = []
        for sizes_list in club_df['parsed_sizes']:
            for size in sizes_list:
                category, normalized_size = categorize_size_token(size)
                if (show_letters and category == 'Letter') or (
                    not show_letters and category == 'Number'
                ):
                    club_filtered_sizes.append(normalized_size)

        if not club_filtered_sizes:
            continue

        club_size_counts = pd.Series(club_filtered_sizes).value_counts()
        if show_letters:
            sz_order = list(LETTER_SIZES_CHART)
            ordered_sz = [s for s in sz_order if s in club_size_counts.index]
            extra = [s for s in club_size_counts.index if s not in sz_order]
            sm_final_order = (ordered_sz + sorted(extra))[::-1]
        else:
            num_sz = [s for s in club_size_counts.index if str(s).isdigit()]
            num_sorted = sorted(num_sz, key=int)
            non_num = [s for s in club_size_counts.index if not str(s).isdigit()]
            sm_final_order = (num_sorted + sorted(non_num))[::-1]

        club_ordered_counts = club_size_counts.reindex(sm_final_order).fillna(0)
        club_color = CLUB_COLORS.get(club, '#4FC3F7')
        club_fig = go.Figure(
            data=[
                go.Bar(
                    x=club_ordered_counts.values,
                    y=club_ordered_counts.index,
                    orientation='h',
                    marker_color=club_color,
                    marker_line_width=1,
                    marker_line_color=CLUB_LINE.get(club, '#333333'),
                    hovertemplate='<b>%{y}</b><br>Productos: %{x}<extra></extra>',
                )
            ]
        )
        if use_consistent_scale and global_max_count:
            sm_xaxis = dict(range=[0, global_max_count * 1.1], showticklabels=True)
        else:
            sm_xaxis = dict(showticklabels=True)

        club_fig.update_layout(
            title=dict(text=f'{club} ({len(club_filtered_sizes)} productos)', font=dict(size=CHART_FONT_SIZE)),
            height=fig_height,
            template=PLOT_TEMPLATE,
            paper_bgcolor=PAPER_BG,
            plot_bgcolor=PAPER_BG,
            font=dict(color=FONT_COLOR, family='Segoe UI, sans-serif', size=CHART_FONT_SIZE),
            margin=dict(l=10, r=24, t=40, b=10),
            xaxis=dict(title='', showgrid=False, **sm_xaxis),
            yaxis=dict(
                title='',
                showgrid=False,
                showticklabels=True,
                automargin=True,
            ),
        )
        club_fig = finalize_chart(club_fig)
        graph_wrap = (
            dcc.Graph(
                figure=club_fig,
                config={'displayModeBar': False, 'responsive': True},
                style={'width': '100%', 'minWidth': '100%'},
            )
            if single_club
            else dcc.Graph(figure=club_fig, config={'displayModeBar': False})
        )
        club_charts.append(dbc.Col([graph_wrap], **col_props))

    if not club_charts:
        return None
    rows_children = []
    for i in range(0, len(club_charts), 3):
        rows_children.append(
            dbc.Row(club_charts[i : i + 3], className='mb-2', justify='start')
        )
    return html.Div(rows_children)


@callback(
    Output('small-multiples-container', 'children'),
    Output('total-sizes-count', 'children'),
    Output('most-popular-size', 'children'),
    Output('most-diverse-club', 'children'),
    Output('avg-sizes-per-club', 'children'),
    Output('sizes-club-info', 'children'),
    Input('sizes-club-filter', 'value'),
    Input('sizes-type-toggle', 'value'),
    Input('sizes-scale-toggle', 'value'),
    Input('ui-language', 'data'),
)
def update_sizes_charts(selected_club, show_letters, use_consistent_scale, lang):
    lc = _lang_code(lang)
    try:
        if selected_club == 'Todos los Clubes':
            filtered_df = df
        else:
            filtered_df = df[df['club_name'] == selected_club]

        clubs_ordered = [c for c in CLUB_ORDER if c in filtered_df['club_name'].unique()]

        letter_sizes = []
        number_sizes = []
        for sizes_list in filtered_df['parsed_sizes']:
            for size in sizes_list:
                category, normalized_size = categorize_size_token(size)
                if category == 'Letter':
                    letter_sizes.append(normalized_size)
                else:
                    number_sizes.append(normalized_size)

        if show_letters:
            filtered_sizes = letter_sizes
            size_type_text = tr(lc, 'letter_sizes')
        else:
            filtered_sizes = number_sizes
            size_type_text = tr(lc, 'number_sizes')

        empty_msg = tr(lc, 'no_size_data', stype=size_type_text, club=selected_club)
        if not filtered_sizes:
            return (
                None,
                "0/0",
                tr(lc, 'no_data_short'),
                tr(lc, 'no_data_short'),
                "0",
                empty_msg,
            )

        size_counts = pd.Series(filtered_sizes).value_counts()
        if size_counts.empty:
            return (
                None,
                "0/0",
                tr(lc, 'no_data_short'),
                tr(lc, 'no_data_short'),
                "0",
                empty_msg,
            )

        small_multiples = _sizes_small_multiples_layout(
            filtered_df, clubs_ordered, show_letters, use_consistent_scale
        )

        total_unique_sizes = len(size_counts)
        most_popular_size = size_counts.index[0] if len(size_counts) > 0 else tr(lc, 'no_data_short')

        all_variety = all_clubs_variety_by_mode(show_letters)
        peer_max_variety = max(all_variety.values()) if all_variety else 0
        unique_kpi = (
            f"{total_unique_sizes}/{peer_max_variety}"
            if peer_max_variety
            else f"{total_unique_sizes}/0"
        )

        most_diverse_club = (
            max(all_variety, key=all_variety.get) if all_variety else tr(lc, 'no_data_short')
        )
        avg_sizes_per_club = (
            sum(all_variety.values()) / len(all_variety) if all_variety else 0
        )

        if selected_club == 'Todos los Clubes':
            total_filtered_products = len(filtered_sizes)
            club_info = tr(
                lc,
                'sizes_all_clubs',
                stype=size_type_text,
                n=len(clubs_ordered),
                nprod=total_filtered_products,
            )
        else:
            club_variety_count = all_variety.get(selected_club, 0)
            club_df = filtered_df[filtered_df['club_name'] == selected_club]
            club_filtered_sizes = []
            for sizes_list in club_df['parsed_sizes']:
                for size in sizes_list:
                    category, normalized_size = categorize_size_token(size)
                    if (show_letters and category == 'Letter') or (
                        not show_letters and category == 'Number'
                    ):
                        club_filtered_sizes.append(normalized_size)
            club_info = tr(
                lc,
                'sizes_one_club',
                club=selected_club,
                nvar=club_variety_count,
                stype=size_type_text,
                ntot=len(club_filtered_sizes),
            )

        return (
            small_multiples,
            unique_kpi,
            most_popular_size,
            most_diverse_club,
            f"{avg_sizes_per_club:.1f}",
            club_info,
        )

    except Exception as e:
        lc = _lang_code(lang)
        return (
            None,
            "0/0",
            tr(lc, 'no_data_short'),
            tr(lc, 'no_data_short'),
            "0",
            f"Error: {str(e)}",
        )

# ════════════════════════════════════════════════════════════════
# RUN
# ════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True, port=8051)  # Enabled debug mode for auto-reload
