"""
Análisis de brechas — pestañas
Muestra catálogo actual por club y oportunidades frente a Estudiantes.
"""

from difflib import SequenceMatcher
from datetime import datetime
import re
import unicodedata
from urllib.parse import urlencode

from dash import dcc, html, dash_table, Input, Output, State
from dash.dash_table.Format import Format, Scheme, Symbol
import dash_bootstrap_components as dbc
import pandas as pd

FILTRO_TODOS = 'Todos los Clubes'
CLUB_DEFAULT = 'Estudiantes'

PLOT_BG = '#1a1a2e'
CARD_BG = '#2a2a3e'
FONT_COLOR = '#e0e0e0'
ACCENT = '#4fc3f7'
MUTED = '#9e9e9e'

_ES_RENAME = {
    'category_tier_1': 'Categoría',
    'category_tier_2': 'Subcategoría',
    'price': 'Precio',
    'sizes_available': 'Tallas',
    'age_group': 'Edad',
    'gender': 'Género',
}

_COLS = [
    'Producto',
    'category_tier_1',
    'category_tier_2',
    'price',
    'sizes_available',
    'age_group',
    'gender',
    'Temporada',
    'Colores',
    'Club',
]
_FILTER_KEYS = ['club', 'category', 'subcategory', 'sizes', 'age', 'gender', 'colours', 'search']
_GAP_CTX_CACHE = {}
PAGE_SIZE_DEFAULT = 100
PAGE_SIZE_OPTIONS = [50, 100, 200]
ALL_LABELS = {
    'club': 'Todos los Clubes',
    'category': 'Todas las Categorías',
    'subcategory': 'Todas las Subcategorías',
    'sizes': 'Todas las Tallas',
    'age': 'Todas las Edades',
    'gender': 'Todos los Géneros',
    'colours': 'Todos los Colores',
}


def _extract_size_tokens(value):
    if pd.isna(value):
        return []
    tokens = [_normalize_size_label(t.strip()) for t in str(value).split(',') if t.strip()]
    # Preserve order while removing duplicates
    return list(dict.fromkeys(tokens))


def _normalize_size_label(value):
    txt = '' if pd.isna(value) else str(value).strip()
    if not txt:
        return txt
    ascii_key = unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore').decode('ascii').lower()
    if ascii_key == 'unico':
        return 'Único'
    return txt


def _normalize_sizes_string(value):
    tokens = _extract_size_tokens(value)
    return ', '.join(tokens) if tokens else 'N/A'


def _normalize_name(value):
    txt = '' if pd.isna(value) else str(value)
    txt = unicodedata.normalize('NFKD', txt)
    txt = txt.encode('ascii', 'ignore').decode('ascii')
    txt = txt.lower()
    txt = re.sub(r'[^a-z0-9]+', ' ', txt)
    return re.sub(r'\s+', ' ', txt).strip()


def _fuzzy_match_exists(candidate, references, threshold=0.93):
    if not candidate or not references:
        return False
    # Lightweight fuzzy guard for near-duplicates beyond normalized exact matching.
    return any(SequenceMatcher(None, candidate, ref).ratio() >= threshold for ref in references)


def _prepare_catalog(df):
    out = df.copy()
    out['club_name'] = out.get('club_name', '').fillna('').astype(str).str.strip()
    out['product_name'] = out.get('product_name', '').fillna('Producto sin nombre').astype(str).str.strip()
    out['category_tier_1'] = out.get('category_tier_1', '').fillna('Sin categoría')
    out['category_tier_2'] = out.get('category_tier_2', '').fillna('N/A')
    out['price'] = pd.to_numeric(out.get('price', 0), errors='coerce').fillna(0)
    out['sizes_available'] = out.get('sizes_available', '').fillna('N/A').apply(_normalize_sizes_string)
    out['sizes_tokens'] = out['sizes_available'].apply(_extract_size_tokens)
    out['age_group'] = out.get('age_group', '').fillna('N/A').astype(str)
    out['gender'] = out.get('gender', '').fillna('N/A').astype(str)
    out['product_url'] = out.get('product_url', pd.Series(index=out.index, dtype=str)).fillna('').astype(str)
    out['colors_available'] = pd.to_numeric(out.get('colors_available', 1), errors='coerce').fillna(1)
    out['Temporada'] = '2025-26'
    out['Colores'] = out['colors_available'].apply(lambda x: '1+' if x and x > 1 else '1')
    out['Club'] = out['club_name']
    out['Producto'] = out.apply(
        lambda r: f"[{r['product_name']}]({r['product_url']})" if str(r['product_url']).strip() else str(r['product_name']),
        axis=1,
    )
    out['product_norm'] = out['product_name'].apply(_normalize_name)
    return out


def _mode_or_first(series):
    vals = series.dropna()
    if vals.empty:
        return ''
    mode_vals = vals.mode()
    return mode_vals.iloc[0] if not mode_vals.empty else vals.iloc[0]


def _dedupe_gap_products(gap_detail):
    if gap_detail.empty:
        gap_detail['club_set'] = [[]]
        return gap_detail.iloc[0:0].copy()

    grouped = gap_detail.groupby('product_norm', as_index=False)
    out = grouped.agg(
        product_name=('product_name', _mode_or_first),
        product_url=('product_url', _mode_or_first),
        category_tier_1=('category_tier_1', _mode_or_first),
        category_tier_2=('category_tier_2', _mode_or_first),
        price=('price', 'median'),
        sizes_available=('sizes_available', _mode_or_first),
        age_group=('age_group', _mode_or_first),
        gender=('gender', _mode_or_first),
        Temporada=('Temporada', _mode_or_first),
        Colores=('Colores', _mode_or_first),
    )
    clubs_per_norm = grouped.agg(
        club_set=('club_name', lambda s: sorted(set(s.dropna().astype(str))))
    )
    out = out.merge(clubs_per_norm, on='product_norm', how='left')
    out['Club'] = out['club_set'].apply(lambda xs: ', '.join(xs) if xs else '')
    out['Clubes'] = out['club_set'].apply(lambda xs: len(xs) if isinstance(xs, list) else 0)
    out['sizes_available'] = out['sizes_available'].apply(_normalize_sizes_string)
    out['sizes_tokens'] = out['sizes_available'].apply(_extract_size_tokens)
    out['Producto'] = out.apply(
        lambda r: f"[{r['product_name']}]({r['product_url']})" if str(r['product_url']).strip() else str(r['product_name']),
        axis=1,
    )
    return out.sort_values('product_name')


def _assign_gap_priority(gap_unique):
    out = gap_unique.copy()
    if out.empty:
        out['Prioridad'] = []
        return out

    max_clubes = max(int(out['Clubes'].max()), 1)
    q1 = float(out['price'].quantile(0.25))
    q3 = float(out['price'].quantile(0.75))

    def _score(row):
        score = 0
        # Coverage signal: seen in more clubs = stronger demand indicator.
        clubes = int(row.get('Clubes', 0))
        if clubes >= max(3, int(round(max_clubes * 0.5))):
            score += 2
        elif clubes >= 2:
            score += 1
        # Mid-price opportunities are often easier to activate commercially.
        p = float(row.get('price', 0))
        if q1 <= p <= q3:
            score += 1
        return score

    out['_priority_score'] = out.apply(_score, axis=1)
    out['Prioridad'] = out['_priority_score'].map({3: 'Alta', 2: 'Alta', 1: 'Media', 0: 'Baja'})
    out = out.drop(columns=['_priority_score'])
    return out


def _build_gap_context(df):
    cache_key = id(df)
    if cache_key in _GAP_CTX_CACHE:
        return _GAP_CTX_CACHE[cache_key]

    catalog = _prepare_catalog(df)
    students_catalog = catalog[catalog['club_name'] == CLUB_DEFAULT].copy()
    est_norm_set = set(students_catalog['product_norm'].dropna())
    est_norm_list = sorted(est_norm_set)

    competitor_rows = catalog[catalog['club_name'] != CLUB_DEFAULT].copy()
    gap_mask = competitor_rows['product_norm'].apply(
        lambda n: n not in est_norm_set and not _fuzzy_match_exists(n, est_norm_list)
    )
    gap_detail = competitor_rows[gap_mask].copy()
    gap_unique = _dedupe_gap_products(gap_detail)
    gap_unique = _assign_gap_priority(gap_unique)

    clubs_present = sorted(c for c in catalog['club_name'].dropna().unique() if c)
    club_options = [FILTRO_TODOS] + ([CLUB_DEFAULT] if CLUB_DEFAULT in clubs_present else [])
    club_options += [c for c in clubs_present if c != CLUB_DEFAULT]
    club_options = list(dict.fromkeys(club_options))

    ctx = {
        'catalog': catalog,
        'students_catalog': students_catalog,
        'gap_detail': gap_detail,
        'gap_unique': gap_unique,
        'club_options': club_options,
    }
    _GAP_CTX_CACHE[cache_key] = ctx
    return ctx


def _to_table_data(frame):
    extra_cols = [c for c in ['Clubes', 'Prioridad'] if c in frame.columns]
    table_data = frame[_COLS + extra_cols].rename(columns=_ES_RENAME).copy()
    table_data = table_data.fillna('')
    for col in table_data.columns:
        if col != 'Precio':
            table_data[col] = table_data[col].astype(str)
    text_cols = ['Categoría', 'Subcategoría', 'Edad', 'Género', 'Club', 'Colores']
    for col in text_cols:
        if col in table_data.columns:
            table_data[col] = table_data[col].apply(_capitalize_words_for_display)
    return table_data


def _capitalize_words_for_display(value):
    txt = '' if pd.isna(value) else str(value).strip()
    if not txt:
        return txt
    out_tokens = []
    for tok in txt.split(' '):
        if not tok:
            out_tokens.append(tok)
            continue
        # Preserve short all-caps tokens and size-like tokens (XS, XXL, 38/39, etc.).
        if tok.isupper() and (len(tok) <= 4 or any(ch.isdigit() for ch in tok) or '/' in tok):
            out_tokens.append(tok)
        else:
            out_tokens.append(tok[:1].upper() + tok[1:].lower())
    return ' '.join(out_tokens)


def _filter_options(table_data, club_options):
    def _clean_values(values):
        cleaned = []
        for v in values:
            s = str(v).strip()
            if not s:
                continue
            if s.lower() in {'nan', 'none', 'null'}:
                continue
            cleaned.append(s)
        # frequency-aware ordering can make common filters easier to find
        freq = pd.Series(cleaned).value_counts()
        ordered = list(freq.index)
        return ordered

    size_tokens = []
    for raw in table_data['Tallas'].astype(str).tolist():
        size_tokens.extend(_extract_size_tokens(raw))
    unique_sizes = _clean_values(size_tokens)
    return {
        'club': club_options,
        'category': _clean_values(table_data['Categoría'].astype(str).tolist()),
        'subcategory': _clean_values(table_data['Subcategoría'].astype(str).tolist()),
        'sizes': unique_sizes,
        'age': _clean_values(table_data['Edad'].astype(str).tolist()),
        'gender': _clean_values(table_data['Género'].astype(str).tolist()),
        'colours': _clean_values(table_data['Colores'].astype(str).tolist()),
    }


def _create_data_table(table_data, table_id, club_options, is_gap=False):
    filter_options = _filter_options(table_data, club_options)
    price_format = Format(
        scheme=Scheme.fixed,
        precision=0,
        group=True,
        group_delimiter='.',
        decimal_delimiter=',',
        symbol=Symbol.yes,
        symbol_prefix='$',
    )
    dd_style = {'color': '#333', 'backgroundColor': '#fff'}
    def all_option(key, values):
        return [{'label': ALL_LABELS[key], 'value': FILTRO_TODOS}] + [
            {'label': x, 'value': x} for x in values
        ]

    return html.Div([
        dbc.Row([
            dbc.Col([html.H6('Filtros', className='mb-3', style={'color': ACCENT})], width=10),
            dbc.Col([
                dbc.Button('Restablecer', id=f'reset-filters-{table_id}', color='secondary', size='sm', className='mb-3')
            ], width=2),
        ]),
        dbc.Row([
            dbc.Col(
                [
                    dbc.Label('Filas por página:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                    dcc.Dropdown(
                        id=f'page-size-{table_id}',
                        options=[{'label': str(n), 'value': n} for n in PAGE_SIZE_OPTIONS],
                        value=PAGE_SIZE_DEFAULT,
                        clearable=False,
                        className='mb-3',
                        style=dd_style,
                    ),
                ],
                width=2,
            ),
            (
                dbc.Col(
                    [
                        dbc.Label('Vista de brechas:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                        dcc.RadioItems(
                            id='gap-view-mode',
                            options=[
                                {'label': 'Deduplicada', 'value': 'dedup'},
                                {'label': 'Detalle por club', 'value': 'detail'},
                            ],
                            value='dedup',
                            inline=True,
                            style={'color': FONT_COLOR, 'paddingTop': '8px'},
                            labelStyle={'marginRight': '16px'},
                        ),
                    ],
                    width=6,
                )
                if is_gap
                else None
            ),
            dbc.Col(
                [
                    dbc.Label('Exportar:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                    dbc.Button(
                        'Descargar filtrado (CSV)',
                        id=f'export-filtered-{table_id}',
                        color='primary',
                        size='sm',
                        className='mb-3',
                    ),
                    dcc.Download(id=f'download-filtered-{table_id}'),
                ],
                width=4,
            ),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label('Club:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                dcc.Dropdown(
                    id=f'club-filter-{table_id}',
                    options=all_option('club', [x for x in filter_options['club'] if x != FILTRO_TODOS]),
                    value=FILTRO_TODOS if is_gap else (CLUB_DEFAULT if CLUB_DEFAULT in filter_options['club'] else FILTRO_TODOS),
                    clearable=False,
                    className='mb-3',
                    style=dd_style,
                ),
            ], width=2),
            dbc.Col([
                dbc.Label('Categoría:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                dcc.Dropdown(
                    id=f'category-filter-{table_id}',
                    options=all_option('category', filter_options['category']),
                    value=FILTRO_TODOS,
                    clearable=False,
                    className='mb-3',
                    style=dd_style,
                ),
            ], width=2),
            dbc.Col([
                dbc.Label('Subcategoría:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                dcc.Dropdown(
                    id=f'subcategory-filter-{table_id}',
                    options=all_option('subcategory', filter_options['subcategory']),
                    value=FILTRO_TODOS,
                    clearable=False,
                    className='mb-3',
                    style=dd_style,
                ),
            ], width=2),
            dbc.Col([
                dbc.Label('Tallas:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                dcc.Dropdown(
                    id=f'sizes-filter-{table_id}',
                    options=all_option('sizes', filter_options['sizes']),
                    value=FILTRO_TODOS,
                    clearable=False,
                    className='mb-3',
                    style=dd_style,
                ),
            ], width=2),
            dbc.Col([
                dbc.Label('Edad:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                dcc.Dropdown(
                    id=f'age-filter-{table_id}',
                    options=all_option('age', filter_options['age']),
                    value=FILTRO_TODOS,
                    clearable=False,
                    className='mb-3',
                    style=dd_style,
                ),
            ], width=2),
            dbc.Col([
                dbc.Label('Género:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                dcc.Dropdown(
                    id=f'gender-filter-{table_id}',
                    options=all_option('gender', filter_options['gender']),
                    value=FILTRO_TODOS,
                    clearable=False,
                    className='mb-3',
                    style=dd_style,
                ),
            ], width=2),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Label('Colores:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                dcc.Dropdown(
                    id=f'colours-filter-{table_id}',
                    options=all_option('colours', filter_options['colours']),
                    value=FILTRO_TODOS,
                    clearable=False,
                    className='mb-3',
                    style=dd_style,
                ),
            ], width=3),
            dbc.Col([
                dbc.Label('Buscar:', className='form-label fw-bold', style={'color': FONT_COLOR}),
                dcc.Input(
                    id=f'search-filter-{table_id}',
                    placeholder='Buscar por nombre de producto…',
                    type='text',
                    className='mb-3',
                    debounce=True,
                    style={'width': '100%'},
                ),
            ], width=9),
        ]),
        html.Hr(),
        dash_table.DataTable(
            id=f'estudiantes-products-table-{table_id}',
            columns=[
                {'name': 'Producto', 'id': 'Producto', 'presentation': 'markdown'},
                {'name': 'Categoría', 'id': 'Categoría'},
                {'name': 'Subcategoría', 'id': 'Subcategoría'},
                {'name': 'Precio', 'id': 'Precio', 'type': 'numeric', 'format': price_format},
                {'name': 'Tallas', 'id': 'Tallas'},
                {'name': 'Edad', 'id': 'Edad'},
                {'name': 'Género', 'id': 'Género'},
                {'name': 'Temporada', 'id': 'Temporada'},
                {'name': 'Colores', 'id': 'Colores'},
                {'name': 'Club', 'id': 'Club'},
            ] + (
                [
                    {'name': '# Clubes', 'id': 'Clubes', 'type': 'numeric'},
                    {'name': 'Prioridad', 'id': 'Prioridad'},
                ]
                if is_gap
                else []
            ),
            data=table_data.to_dict('records'),
            sort_action='native',
            filter_action='none',
            page_action='native',
            page_current=0,
            page_size=PAGE_SIZE_DEFAULT,
            export_format='xlsx',
            export_headers='display',
            markdown_options={'link_target': '_blank'},
            fixed_rows={'headers': True},
            style_table={'overflowX': 'auto', 'overflowY': 'auto', 'maxHeight': '70vh'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Segoe UI, sans-serif',
                'fontSize': '14px',
                'minWidth': '110px',
                'maxWidth': '340px',
                'whiteSpace': 'normal',
                'height': 'auto',
                'lineHeight': '18px',
                'backgroundColor': PLOT_BG,
                'color': FONT_COLOR,
                'border': '1px solid #333',
            },
            style_header={
                'backgroundColor': CARD_BG,
                'color': ACCENT,
                'fontWeight': 'bold',
                'fontSize': '16px',
                'textAlign': 'center',
                'border': '1px solid #444',
            },
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': PLOT_BG},
                {'if': {'row_index': 'even'}, 'backgroundColor': '#171727'},
            ],
        ),
    ])


def _apply_common_filters(df_in, club_filter, cat_filter, subcat_filter, sizes_filter, age_filter, gender_filter, colours_filter, search_filter):
    out = df_in
    if club_filter != FILTRO_TODOS:
        if 'club_set' in out.columns:
            out = out[out['club_set'].apply(lambda xs: club_filter in (xs or []))]
        else:
            out = out[out['club_name'] == club_filter]
    if cat_filter != FILTRO_TODOS:
        out = out[out['category_tier_1'] == cat_filter]
    if subcat_filter != FILTRO_TODOS:
        out = out[out['category_tier_2'] == subcat_filter]
    if sizes_filter != FILTRO_TODOS:
        if 'sizes_tokens' in out.columns:
            out = out[out['sizes_tokens'].apply(lambda xs: sizes_filter in (xs or []))]
        else:
            out = out[out['sizes_available'].astype(str).str.contains(sizes_filter, na=False, regex=False)]
    if age_filter != FILTRO_TODOS:
        out = out[out['age_group'] == age_filter]
    if gender_filter != FILTRO_TODOS:
        out = out[out['gender'] == gender_filter]
    if colours_filter != FILTRO_TODOS:
        out = out[out['Colores'] == colours_filter]
    if search_filter:
        fields = ['product_name', 'category_tier_1', 'category_tier_2', 'sizes_available', 'age_group', 'gender']
        search_mask = pd.Series(False, index=out.index)
        for col in fields:
            if col in out.columns:
                search_mask = search_mask | out[col].astype(str).str.contains(search_filter, case=False, na=False, regex=False)
        out = out[search_mask]
    return out


def create_simple_gap_analysis_layout(df):
    """Create gap analysis page with tabs for current catalog and deduped gap opportunities."""
    ctx = _build_gap_context(df)
    students_table_data = _to_table_data(ctx['students_catalog'].sort_values('product_name'))
    gap_table_data = _to_table_data(ctx['gap_unique'].sort_values('product_name'))
    clubs = ctx['club_options']

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1('Análisis de brechas', style={'color': FONT_COLOR, 'marginBottom': '14px'}),
                html.P(
                    'Datos actualizados desde master_data.xlsx. '
                    'Brechas calculadas con nombre normalizado + coincidencia difusa y deduplicadas por producto.',
                    style={'color': MUTED, 'marginBottom': '20px', 'fontSize': '14px'},
                ),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Tabs([
                    dcc.Tab(
                        label='Catálogo actual (seleccioná club)',
                        value='estudiantes',
                        style={'color': '#000000'},
                        selected_style={'color': '#000000', 'fontWeight': 'bold'},
                        children=[dbc.Card([
                            dbc.CardHeader([
                                html.H5('Catálogo actual por club', className='mb-0', style={'color': FONT_COLOR}),
                                html.Small(f"Total base: {len(ctx['catalog'])} productos", style={'color': MUTED}),
                                html.Div(
                                    id='rows-shown-estudiantes',
                                    children=f"Mostrando {len(ctx['catalog'])} de {len(ctx['catalog'])}",
                                    style={'color': MUTED, 'fontSize': '14px', 'marginTop': '4px'},
                                ),
                            ], style={'backgroundColor': CARD_BG}),
                            dbc.CardBody(
                                _create_data_table(students_table_data, 'estudiantes', clubs, is_gap=False),
                                style={'backgroundColor': PLOT_BG},
                            ),
                        ], className='mt-3', style={'backgroundColor': PLOT_BG, 'border': '1px solid #333'})],
                    ),
                    dcc.Tab(
                        label='Oportunidades de brecha (deduplicadas)',
                        value='gap',
                        style={'color': '#000000'},
                        selected_style={'color': '#000000', 'fontWeight': 'bold'},
                        children=[dbc.Card([
                            dbc.CardHeader([
                                html.H5('Oportunidades de brecha', className='mb-0', style={'color': FONT_COLOR}),
                                html.Small(f"Total deduplicado: {len(ctx['gap_unique'])} productos", style={'color': MUTED}),
                                html.Span(' ⓘ', id='gap-help-icon', style={'color': ACCENT, 'cursor': 'pointer', 'marginLeft': '8px'}),
                                dbc.Tooltip(
                                    'Brecha = nombre normalizado + control difuso. '
                                    'Vista deduplicada agrupa productos equivalentes entre clubes. '
                                    'Prioridad combina cobertura en clubes y señal de precio.',
                                    target='gap-help-icon',
                                    placement='right',
                                ),
                                html.Div(
                                    id='rows-shown-gap',
                                    children=f"Mostrando {len(ctx['gap_unique'])} de {len(ctx['gap_unique'])}",
                                    style={'color': MUTED, 'fontSize': '14px', 'marginTop': '4px'},
                                ),
                            ], style={'backgroundColor': CARD_BG}),
                            dbc.CardBody(
                                _create_data_table(gap_table_data, 'gap', clubs, is_gap=True),
                                style={'backgroundColor': PLOT_BG},
                            ),
                        ], className='mt-3', style={'backgroundColor': PLOT_BG, 'border': '1px solid #333'})],
                    ),
                ], value='estudiantes', persistence=True, style={'marginBottom': '12px'}),
            ], width=12),
        ]),
        dbc.Row([
            dbc.Col([
                html.P(
                    'Exportá directamente desde la tabla con el botón integrado (XLSX).',
                    className='text-center',
                    style={'fontSize': '14px', 'color': MUTED},
                ),
            ], width=12),
        ]),
    ], fluid=True, style={'backgroundColor': PLOT_BG, 'minHeight': '100vh', 'padding': '16px'})


def register_simple_gap_analysis_callbacks(app, df):
    """Register simple callbacks using cached preprocessing for performance."""
    ctx = _build_gap_context(df)

    @app.callback(
        Output('estudiantes-products-table-estudiantes', 'data'),
        Output('rows-shown-estudiantes', 'children'),
        [
            Input('club-filter-estudiantes', 'value'),
            Input('category-filter-estudiantes', 'value'),
            Input('subcategory-filter-estudiantes', 'value'),
            Input('sizes-filter-estudiantes', 'value'),
            Input('age-filter-estudiantes', 'value'),
            Input('gender-filter-estudiantes', 'value'),
            Input('colours-filter-estudiantes', 'value'),
            Input('search-filter-estudiantes', 'value'),
        ],
    )
    def update_estudiantes_table(club_filter, cat_filter, subcat_filter, sizes_filter, age_filter, gender_filter, colours_filter, search_filter):
        base = ctx['catalog']
        out = _apply_common_filters(
            base, club_filter, cat_filter, subcat_filter, sizes_filter, age_filter, gender_filter, colours_filter, search_filter
        )
        table_data = _to_table_data(out.sort_values('product_name'))
        counter = f"Mostrando {len(table_data)} de {len(base)}"
        return table_data.to_dict('records'), counter

    @app.callback(
        Output('estudiantes-products-table-gap', 'data'),
        Output('rows-shown-gap', 'children'),
        [
            Input('gap-view-mode', 'value'),
            Input('club-filter-gap', 'value'),
            Input('category-filter-gap', 'value'),
            Input('subcategory-filter-gap', 'value'),
            Input('sizes-filter-gap', 'value'),
            Input('age-filter-gap', 'value'),
            Input('gender-filter-gap', 'value'),
            Input('colours-filter-gap', 'value'),
            Input('search-filter-gap', 'value'),
        ],
    )
    def update_gap_table(view_mode, club_filter, cat_filter, subcat_filter, sizes_filter, age_filter, gender_filter, colours_filter, search_filter):
        base = ctx['gap_unique'] if view_mode != 'detail' else ctx['gap_detail']
        out = _apply_common_filters(
            base, club_filter, cat_filter, subcat_filter, sizes_filter, age_filter, gender_filter, colours_filter, search_filter
        )
        table_data = _to_table_data(out.sort_values('product_name'))
        counter = f"Mostrando {len(table_data)} de {len(base)}"
        return table_data.to_dict('records'), counter

    @app.callback(
        Output('estudiantes-products-table-estudiantes', 'page_size'),
        Input('page-size-estudiantes', 'value'),
    )
    def update_page_size_estudiantes(page_size):
        return page_size or PAGE_SIZE_DEFAULT

    @app.callback(
        Output('estudiantes-products-table-gap', 'page_size'),
        Input('page-size-gap', 'value'),
    )
    def update_page_size_gap(page_size):
        return page_size or PAGE_SIZE_DEFAULT

    @app.callback(
        Output('download-filtered-estudiantes', 'data'),
        Input('export-filtered-estudiantes', 'n_clicks'),
        State('club-filter-estudiantes', 'value'),
        State('category-filter-estudiantes', 'value'),
        State('subcategory-filter-estudiantes', 'value'),
        State('sizes-filter-estudiantes', 'value'),
        State('age-filter-estudiantes', 'value'),
        State('gender-filter-estudiantes', 'value'),
        State('colours-filter-estudiantes', 'value'),
        State('search-filter-estudiantes', 'value'),
        prevent_initial_call=True,
    )
    def export_estudiantes_filtered(_, club_filter, cat_filter, subcat_filter, sizes_filter, age_filter, gender_filter, colours_filter, search_filter):
        out = _apply_common_filters(
            ctx['catalog'], club_filter, cat_filter, subcat_filter, sizes_filter, age_filter, gender_filter, colours_filter, search_filter
        )
        table_data = _to_table_data(out.sort_values('product_name'))
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        return dcc.send_data_frame(table_data.to_csv, f'estudiantes_filtrado_{ts}.csv', index=False)

    @app.callback(
        Output('download-filtered-gap', 'data'),
        Input('export-filtered-gap', 'n_clicks'),
        State('gap-view-mode', 'value'),
        State('club-filter-gap', 'value'),
        State('category-filter-gap', 'value'),
        State('subcategory-filter-gap', 'value'),
        State('sizes-filter-gap', 'value'),
        State('age-filter-gap', 'value'),
        State('gender-filter-gap', 'value'),
        State('colours-filter-gap', 'value'),
        State('search-filter-gap', 'value'),
        prevent_initial_call=True,
    )
    def export_gap_filtered(_, view_mode, club_filter, cat_filter, subcat_filter, sizes_filter, age_filter, gender_filter, colours_filter, search_filter):
        base = ctx['gap_unique'] if view_mode != 'detail' else ctx['gap_detail']
        out = _apply_common_filters(
            base, club_filter, cat_filter, subcat_filter, sizes_filter, age_filter, gender_filter, colours_filter, search_filter
        )
        table_data = _to_table_data(out.sort_values('product_name'))
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        return dcc.send_data_frame(table_data.to_csv, f'gap_filtrado_{ts}.csv', index=False)

    @app.callback(
        Output('url', 'search'),
        [
            Input('club-filter-estudiantes', 'value'),
            Input('category-filter-estudiantes', 'value'),
            Input('subcategory-filter-estudiantes', 'value'),
            Input('sizes-filter-estudiantes', 'value'),
            Input('age-filter-estudiantes', 'value'),
            Input('gender-filter-estudiantes', 'value'),
            Input('colours-filter-estudiantes', 'value'),
            Input('search-filter-estudiantes', 'value'),
            Input('page-size-estudiantes', 'value'),
            Input('gap-view-mode', 'value'),
            Input('club-filter-gap', 'value'),
            Input('category-filter-gap', 'value'),
            Input('subcategory-filter-gap', 'value'),
            Input('sizes-filter-gap', 'value'),
            Input('age-filter-gap', 'value'),
            Input('gender-filter-gap', 'value'),
            Input('colours-filter-gap', 'value'),
            Input('search-filter-gap', 'value'),
            Input('page-size-gap', 'value'),
        ],
        prevent_initial_call=True,
    )
    def sync_filters_to_url(
        e_club, e_cat, e_sub, e_sizes, e_age, e_gender, e_col, e_search, e_ps,
        g_view, g_club, g_cat, g_sub, g_sizes, g_age, g_gender, g_col, g_search, g_ps
    ):
        params = {
            'e_club': e_club or '',
            'e_cat': e_cat or '',
            'e_sub': e_sub or '',
            'e_sizes': e_sizes or '',
            'e_age': e_age or '',
            'e_gender': e_gender or '',
            'e_col': e_col or '',
            'e_search': e_search or '',
            'e_ps': e_ps or PAGE_SIZE_DEFAULT,
            'g_view': g_view or 'dedup',
            'g_club': g_club or '',
            'g_cat': g_cat or '',
            'g_sub': g_sub or '',
            'g_sizes': g_sizes or '',
            'g_age': g_age or '',
            'g_gender': g_gender or '',
            'g_col': g_col or '',
            'g_search': g_search or '',
            'g_ps': g_ps or PAGE_SIZE_DEFAULT,
        }
        return '?' + urlencode(params)

    @app.callback(
        [
            Output('club-filter-estudiantes', 'value'),
            Output('category-filter-estudiantes', 'value'),
            Output('subcategory-filter-estudiantes', 'value'),
            Output('sizes-filter-estudiantes', 'value'),
            Output('age-filter-estudiantes', 'value'),
            Output('gender-filter-estudiantes', 'value'),
            Output('colours-filter-estudiantes', 'value'),
            Output('search-filter-estudiantes', 'value'),
        ],
        [Input('reset-filters-estudiantes', 'n_clicks')],
    )
    def reset_estudiantes_filters(_):
        return [CLUB_DEFAULT, FILTRO_TODOS, FILTRO_TODOS, FILTRO_TODOS, FILTRO_TODOS, FILTRO_TODOS, FILTRO_TODOS, '']

    @app.callback(
        [
            Output('club-filter-gap', 'value'),
            Output('category-filter-gap', 'value'),
            Output('subcategory-filter-gap', 'value'),
            Output('sizes-filter-gap', 'value'),
            Output('age-filter-gap', 'value'),
            Output('gender-filter-gap', 'value'),
            Output('colours-filter-gap', 'value'),
            Output('search-filter-gap', 'value'),
        ],
        [Input('reset-filters-gap', 'n_clicks')],
    )
    def reset_gap_filters(_):
        return [FILTRO_TODOS, FILTRO_TODOS, FILTRO_TODOS, FILTRO_TODOS, FILTRO_TODOS, FILTRO_TODOS, FILTRO_TODOS, '']
