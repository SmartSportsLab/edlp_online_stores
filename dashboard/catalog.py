"""
Product Catalog Page for Club Store Dashboard
============================================

This module contains the Product Catalog page focused on Estudiantes products
and unique products from other clubs.
"""

import dash
from dash import dcc, html, dash_table, Input, Output, State, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

# Define constants locally to avoid circular import
PLOT_BG = '#1e1e2f'
CHART_LAYOUT = {
    'template': 'plotly_dark',
    'paper_bgcolor': PLOT_BG,
    'plot_bgcolor': PLOT_BG,
    'font': {'color': '#ffffff'},
    'margin': {'t': 50, 'b': 50, 'l': 50, 'r': 50}
}
CLUB_ORDER = ['Boca Juniors', 'River Plate', 'Independiente', 'San Lorenzo', 'Estudiantes', 'Racing Club']

# Load image database
def load_image_database():
    """Load the image database for product images."""
    try:
        db_path = Path("../images/image_database.json")
        if db_path.exists():
            with open(db_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading image database: {e}")
    return {}

# Global image database
image_db = load_image_database()

def get_product_image(product_id, club, image_index=1):
    """Get local image path for a product from image database."""
    if not image_db:
        return None
    
    # Find product in database
    for item in image_db:
        if item['product_id'] == product_id and item['club'] == club:
            if item['local_image_paths'] and len(item['local_image_paths']) >= image_index:
                return f"../{item['local_image_paths'][image_index-1]}"
    
    return None

def create_product_card(product, show_club=False, highlight_opportunity=False):
    """Create a product card component."""
    
    # Extract product information
    product_name = product['product_name'] if pd.notna(product['product_name']) else 'Sin nombre'
    price = product['price'] if pd.notna(product['price']) else 0
    club = product['club_name'] if pd.notna(product['club_name']) else 'Desconocido'
    category = product.get('category_tier_1', 'Sin categoría') if pd.notna(product.get('category_tier_1')) else 'Sin categoría'
    in_stock = product.get('in_stock', False)
    image_url = product.get('image_urls', '')
    
    # Format price
    price_formatted = f"${price:,.0f}" if price > 0 else "Precio no disponible"
    
    # Stock status
    stock_status = "✅ En stock" if in_stock else "❌ Sin stock"
    stock_color = "success" if in_stock else "danger"
    
    # Card styling
    card_style = {
        "border": "1px solid #dee2e6",
        "borderRadius": "8px",
        "padding": "15px",
        "margin": "10px",
        "backgroundColor": "#f8f9fa",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "transition": "all 0.3s ease",
        "cursor": "pointer",
        "minHeight": "280px"
    }
    
    if highlight_opportunity:
        card_style["borderColor"] = "#28a745"
        card_style["borderWidth"] = "2px"
    
    # Image placeholder or actual image
    if pd.notna(image_url) and image_url:
        image_component = html.Img(
            src=image_url,
            style={
                "width": "100%",
                "height": "150px",
                "objectFit": "cover",
                "borderRadius": "4px",
                "marginBottom": "10px"
            },
            onError="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2Y4ZjlmOSIvPjx0ZXh0IHg9IjUwIiB5PSI1NSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEyIiBmaWxsPSIjNmM3NTdkIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5JbWFnZW4gbm8gZGlzcG9uaWJsZTwvdGV4dD48L3N2Zz4='"
        )
    else:
        image_component = html.Div(
            style={
                "width": "100%",
                "height": "150px",
                "backgroundColor": "#f8f9fa",
                "borderRadius": "4px",
                "marginBottom": "10px",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "border": "1px dashed #dee2e6"
            },
            children=html.Div([
                html.I(className="fas fa-image", style={"fontSize": "24px", "color": "#6c757d"}),
                html.P("Sin imagen", style={"margin": "5px 0 0 0", "fontSize": "12px", "color": "#6c757d"})
            ])
        )
    
    return dbc.Card([
        image_component,
        html.H6(
            product_name[:50] + "..." if len(product_name) > 50 else product_name,
            style={"fontSize": "14px", "fontWeight": "bold", "marginBottom": "8px", "color": "#2c3e50"}
        ),
        html.P(
            f"Precio: {price_formatted}",
            style={"fontSize": "16px", "fontWeight": "bold", "color": "#007bff", "marginBottom": "5px"}
        ),
        html.P(
            f"Categoría: {category}",
            style={"fontSize": "12px", "color": "#6c757d", "marginBottom": "5px"}
        ),
        html.P(
            stock_status,
            style={"fontSize": "12px", "color": "#28a745" if in_stock else "#dc3545", "marginBottom": "8px"}
        ),
        html.Div([
            dbc.Badge(
                club if show_club else "Estudiantes",
                color="primary" if not show_club else "secondary",
                style={"fontSize": "10px"}
            ),
            " " if highlight_opportunity else "",
            dbc.Badge(
                "Oportunidad",
                color="success" if highlight_opportunity else "light",
                style={"fontSize": "10px"} if highlight_opportunity else {"display": "none"}
            )
        ]),
        html.Div(
            id=f"product-details-{hash(product_name)}",
            style={"display": "none"}
        )
    ], style=card_style)

def create_catalog_layout(df):
    """Create the catalog page layout."""
    
    # Filter data for Estudiantes
    estudiantes_df = df[df['club_name'] == 'Estudiantes'].copy()
    
    # Find products unique to other clubs
    other_clubs_df = df[df['club_name'] != 'Estudiantes'].copy()
    estudiantes_products = set(estudiantes_df['product_name'].str.lower())
    other_products = set(other_clubs_df['product_name'].str.lower())
    unique_to_others = other_products - estudiantes_products
    unique_products_df = other_clubs_df[other_clubs_df['product_name'].str.lower().isin(unique_to_others)].copy()
    
    # Store initial data
    initial_data = {
        'estudiantes': estudiantes_df.to_dict('records'),
        'unique': unique_products_df.to_dict('records')
    }
    
    # Get categories for dropdown
    categories = sorted(df['category_tier_1'].dropna().unique())
    
    return dbc.Container([
        # Header with dropdown and layout toggle
        dbc.Row([
            dbc.Col([
                html.H1("Catálogo de Productos", 
                       style={"color": "#2c3e50", "marginBottom": "10px"}),
                html.P("Explora el catálogo completo de productos de todos los clubes.",
                       style={"color": "#6c757d", "marginBottom": "20px"})
            ], md=8),
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dcc.Dropdown(
                            id='catalog-club-filter-simple',
                            options=[
                                {'label': 'Todos los Clubes', 'value': 'Todos los Clubes'},
                                {'label': 'Estudiantes de La Plata', 'value': 'Estudiantes'},
                                {'label': 'Boca Juniors', 'value': 'Boca Juniors'},
                                {'label': 'River Plate', 'value': 'River Plate'},
                                {'label': 'Racing Club', 'value': 'Racing Club'},
                                {'label': 'Independiente', 'value': 'Independiente'},
                                {'label': 'San Lorenzo', 'value': 'San Lorenzo'}
                            ],
                            value='Todos los Clubes',
                            clearable=False,
                            style={'width': '200px', 'color': '#333', 'backgroundColor': '#f8f9fa', 'borderRadius': '6px'}
                        ),
                    ], width='auto'),
                    dbc.Col([
                        html.Div([
                            html.Label("View Mode:", style={"marginRight": "10px", "marginTop": "8px", "fontSize": "14px", "fontWeight": "bold", "color": "#000000"}),
                            dcc.Dropdown(
                                id='catalog-layout-toggle',
                                options=[
                                    {'label': 'Grid View', 'value': False},
                                    {'label': 'List View', 'value': True}
                                ],
                                value=False,
                                clearable=False,
                                style={'width': '120px'}
                            )
                        ], style={"display": "flex", "alignItems": "center"})
                    ], width='auto')
                ])
            ], width='auto'),
        ]),
        
        # Filters and Controls
        dbc.Row([
            dbc.Col([
                html.H5("Filtros Adicionales", style={"marginBottom": "20px"}),
                
                # Sort dropdown
                html.Label("Ordenar por:"),
                dcc.Dropdown(
                    id='catalog-sort-filter-simple',
                    options=[
                        {'label': 'Precio (menor a mayor)', 'value': 'price_asc'},
                        {'label': 'Precio (mayor a menor)', 'value': 'price_desc'},
                        {'label': 'Nombre (A-Z)', 'value': 'name_asc'},
                        {'label': 'Nombre (Z-A)', 'value': 'name_desc'}
                    ],
                    value='price_asc',
                    clearable=False,
                    style={'marginBottom': '15px', 'backgroundColor': '#f8f9fa', 'color': '#333', 'borderRadius': '6px'}
                ),
                
                # Category filter
                html.Label("Categoría:"),
                dcc.Dropdown(
                    id='catalog-category-filter-simple',
                    options=[
                        {'label': 'Todas las categorías', 'value': 'all'}
                    ] + [
                        {'label': cat, 'value': cat} 
                        for cat in categories
                    ],
                    value='all',
                    clearable=False,
                    style={'marginBottom': '15px', 'backgroundColor': '#f8f9fa', 'color': '#333', 'borderRadius': '6px'}
                ),
                
                # Search
                html.Label("Buscar productos:"),
                dbc.Input(
                    id='catalog-search-simple',
                    type='text',
                    placeholder='Buscar por nombre de producto...',
                    style={'marginBottom': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '6px'}
                ),
                
                # Stats
                html.Div(id='catalog-stats-simple')
            ], md=3),
            
            # Main content area
            dbc.Col([
                # Product catalog container - single tab or tabs for Estudiantes
                html.Div(id='catalog-layout-container-simple'),
                
                # Product details modal
                dbc.Modal(
                    [
                        dbc.ModalHeader("Detalles del Producto"),
                        dbc.ModalBody(id='product-modal-content-simple'),
                        dbc.ModalFooter(
                            dbc.Button("Cerrar", id="close-product-modal-simple", className="ml-auto")
                        ),
                    ],
                    id="product-modal-simple",
                    size="lg",
                    is_open=False,
                ),
                
            ], md=9)
        ])
        
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def create_catalog_callbacks(df, app):
    """Create simple, working callbacks for the catalog page."""
    
    print("🔍 DEBUG: Creating catalog callbacks...")
    
    # Main catalog callback - handles layout and products
    @app.callback(
        Output('catalog-layout-container-simple', 'children'),
        [Input('catalog-club-filter-simple', 'value'),
         Input('catalog-sort-filter-simple', 'value'),
         Input('catalog-category-filter-simple', 'value'),
         Input('catalog-search-simple', 'value'),
         Input('catalog-layout-toggle', 'value')]
    )
    def update_catalog_layout_simple(selected_club, sort_by, category_filter, search_term, is_list_layout):
        """Update catalog layout and products based on selected club."""
        
        print(f"🔍 DEBUG: update_catalog_layout_simple called with:")
        print(f"   selected_club: {selected_club}")
        print(f"   sort_by: {sort_by}")
        print(f"   category_filter: {category_filter}")
        print(f"   search_term: {search_term}")
        print(f"   is_list_layout: {is_list_layout}")
        
        if selected_club == 'Estudiantes':
            print("   ✅ Creating Estudiantes tabs")
            # Show tabs for Estudiantes: Current Products and Gap Analysis
            return dbc.Container([
                dcc.Tabs([
                    dcc.Tab(
                        label='Current Products',
                        value='current',
                        children=[
                            html.Div(id='estudiantes-current-products-simple')
                        ]
                    ),
                    dcc.Tab(
                        label='Gap Analysis',
                        value='gap',
                        children=[
                            # Gap Analysis specific filters
                            dbc.Row([
                                dbc.Col([
                                    html.H6("Gap Analysis Filters", style={"marginBottom": "15px", "color": "#2c3e50"}),
                                    html.Label("Filter by Category:", style={"fontSize": "14px", "fontWeight": "bold"}),
                                    dcc.Dropdown(
                                        id='gap-category-filter',
                                        options=[{'label': 'All Categories', 'value': 'all'}] + 
                                               [{'label': cat if cat else 'Uncategorized', 'value': cat} for cat in sorted(df['category_tier_1'].unique())],
                                        value='all',
                                        clearable=False,
                                        style={'width': '250px', 'marginBottom': '20px'}
                                    ),
                                    html.P("Filter gap products by category to focus on specific opportunities.", 
                                          style={"fontSize": "12px", "color": "#6c757d", "marginBottom": "20px"})
                                ], width=12)
                            ]),
                            html.Div(id='estudiantes-gap-products-simple')
                        ]
                    )
                ], style={'marginBottom': '20px'})
            ], fluid=True)
        else:
            print(f"   ✅ Creating single view for {selected_club}")
            # Show single product view for other clubs
            return html.Div(id='other-clubs-products-simple')
    
    # Callback for Estudiantes current products
    @app.callback(
        Output('estudiantes-current-products-simple', 'children'),
        [Input('catalog-club-filter-simple', 'value'),
         Input('catalog-sort-filter-simple', 'value'),
         Input('catalog-category-filter-simple', 'value'),
         Input('catalog-search-simple', 'value'),
         Input('catalog-layout-toggle', 'value')]
    )
    def update_estudiantes_current_products(selected_club, sort_by, category_filter, search_term, is_list_layout):
        """Update Estudiantes current products display."""
        
        print(f"🔍 DEBUG: update_estudiantes_current_products called with:")
        print(f"   selected_club: {selected_club}")
        print(f"   sort_by: {sort_by}")
        print(f"   category_filter: {category_filter}")
        print(f"   search_term: {search_term}")
        print(f"   is_list_layout: {is_list_layout}")
        
        if selected_club != 'Estudiantes':
            print("   ❌ Returning early - not Estudiantes")
            return html.Div("Select Estudiantes to view current products")
        
        # Filter Estudiantes products only
        filtered_df = df[df['club_name'] == 'Estudiantes'].copy()
        print(f"   Estudiantes Current: {len(filtered_df)} products")
        
        # Clean data - remove rows with missing essential data
        filtered_df = filtered_df.dropna(subset=['product_name'])
        filtered_df = filtered_df.fillna({'category_tier_1': 'Sin categoría', 'price': 0})
        print(f"   After data cleaning: {len(filtered_df)} products")
        
        # Apply filters
        if category_filter != 'all':
            before_filter = len(filtered_df)
            filtered_df = filtered_df[filtered_df['category_tier_1'] == category_filter]
            after_filter = len(filtered_df)
            print(f"   After category filter ({category_filter}): {after_filter} products (was {before_filter})")
        
        if search_term:
            before_search = len(filtered_df)
            filtered_df = filtered_df[
                filtered_df['product_name'].str.lower().str.contains(search_term.lower(), na=False)
            ]
            after_search = len(filtered_df)
            print(f"   After search filter: {after_search} products (was {before_search})")
        
        # Sort
        if sort_by == 'price_asc':
            filtered_df = filtered_df.sort_values('price', ascending=True)
        elif sort_by == 'price_desc':
            filtered_df = filtered_df.sort_values('price', ascending=False)
        elif sort_by == 'name_asc':
            filtered_df = filtered_df.sort_values('product_name', ascending=True)
        elif sort_by == 'name_desc':
            filtered_df = filtered_df.sort_values('product_name', ascending=False)
        
        print(f"   Final Estudiantes products: {len(filtered_df)}")
        
        # Create layout
        if is_list_layout:
            return create_list_layout(filtered_df, show_club=False, highlight_opportunity=False)
        else:
            product_cards = []
            for _, product in filtered_df.iterrows():
                card = create_simple_product_card(product, show_club=False, highlight_opportunity=False)
                product_cards.append(card)
            
            if product_cards:
                return dbc.Row([
                    dbc.Col(card, md=4, lg=3) for card in product_cards
                ])
            else:
                return html.Div([
                    html.H4("No se encontraron productos", style={"textAlign": "center", "color": "#6c757d"}),
                    html.P("Estudiantes no tiene productos en esta categoría.", style={"textAlign": "center", "color": "#6c757d"})
                ], style={"padding": "50px"})
    
    # Callback for Estudiantes gap analysis
    @app.callback(
        Output('estudiantes-gap-products-simple', 'children'),
        [Input('catalog-club-filter-simple', 'value'),
         Input('catalog-sort-filter-simple', 'value'),
         Input('catalog-category-filter-simple', 'value'),
         Input('gap-category-filter', 'value'),
         Input('catalog-search-simple', 'value'),
         Input('catalog-layout-toggle', 'value')]
    )
    def update_estudiantes_gap_analysis(selected_club, sort_by, main_category_filter, gap_category_filter, search_term, is_list_layout):
        """Update Estudiantes gap analysis display."""
        
        print(f"🔍 DEBUG: update_estudiantes_gap_analysis called with:")
        print(f"   selected_club: {selected_club}")
        print(f"   sort_by: {sort_by}")
        print(f"   main_category_filter: {main_category_filter}")
        print(f"   gap_category_filter: {gap_category_filter}")
        print(f"   search_term: {search_term}")
        print(f"   is_list_layout: {is_list_layout}")
        
        if selected_club != 'Estudiantes':
            print("   ❌ Returning early - not Estudiantes")
            return html.Div("Select Estudiantes to view gap analysis")
        
        # Use the gap-specific category filter if on gap tab, otherwise use main filter
        category_filter = gap_category_filter if gap_category_filter != 'all' else main_category_filter
        
        # Calculate gap products
        estudiantes_products = set(df[df['club_name'] == 'Estudiantes']['product_name'].str.lower())
        other_clubs_df = df[df['club_name'] != 'Estudiantes'].copy()
        other_products = set(other_clubs_df['product_name'].str.lower())
        gap_products = other_products - estudiantes_products
        
        # Filter to show only gap products
        filtered_df = other_clubs_df[other_clubs_df['product_name'].str.lower().isin(gap_products)].copy()
        print(f"   Estudiantes Gap Analysis: {len(filtered_df)} products")
        
        # Apply category filter (using gap-specific filter)
        print(f"   Applying category filter: '{category_filter}'")
        if category_filter != 'all':
            before_filter = len(filtered_df)
            filtered_df = filtered_df[filtered_df['category_tier_1'] == category_filter]
            after_filter = len(filtered_df)
            print(f"   After category filter ({category_filter}): {after_filter} products (was {before_filter})")
            
            # Show available categories for debugging
            available_categories = filtered_df['category_tier_1'].unique()
            print(f"   Available categories in filtered data: {list(available_categories)}")
        else:
            print(f"   No category filter applied, showing all {len(filtered_df)} products")
        
        # Apply search filter
        if search_term:
            filtered_df = filtered_df[
                filtered_df['product_name'].str.lower().str.contains(search_term.lower(), na=False)
            ]
            print(f"   After search filter: {len(filtered_df)} products")
        
        # Sort
        if sort_by == 'price_asc':
            filtered_df = filtered_df.sort_values('price', ascending=True)
        elif sort_by == 'price_desc':
            filtered_df = filtered_df.sort_values('price', ascending=False)
        elif sort_by == 'name_asc':
            filtered_df = filtered_df.sort_values('product_name', ascending=True)
        elif sort_by == 'name_desc':
            filtered_df = filtered_df.sort_values('product_name', ascending=False)
        
        print(f"   Final gap products: {len(filtered_df)}")
        
        # Create layout
        if is_list_layout:
            return create_list_layout(filtered_df, show_club=True, highlight_opportunity=True)
        else:
            product_cards = []
            for _, product in filtered_df.iterrows():
                card = create_simple_product_card(product, show_club=True, highlight_opportunity=True)
                product_cards.append(card)
            
            if product_cards:
                return dbc.Row([
                    dbc.Col(card, md=4, lg=3) for card in product_cards
                ])
            else:
                return html.Div([
                    html.H4("No se encontraron productos gap", style={"textAlign": "center", "color": "#6c757d"}),
                    html.P("No hay productos gap en esta categoría. Intenta seleccionar otra categoría.", style={"textAlign": "center", "color": "#6c757d"})
                ], style={"padding": "50px"})
    
    # Callback for other clubs products
    @app.callback(
        Output('other-clubs-products-simple', 'children'),
        [Input('catalog-club-filter-simple', 'value'),
         Input('catalog-sort-filter-simple', 'value'),
         Input('catalog-category-filter-simple', 'value'),
         Input('catalog-search-simple', 'value'),
         Input('catalog-layout-toggle', 'value')]
    )
    def update_other_clubs_products(selected_club, sort_by, category_filter, search_term, is_list_layout):
        """Update other clubs products display."""
        
        if selected_club == 'Estudiantes':
            return html.Div("Select a club other than Estudiantes")
        
        # Filter data by selected club
        if selected_club == 'Todos los Clubes':
            filtered_df = df.copy()
            print(f"   Todos los Clubes: {len(filtered_df)} products")
        else:
            filtered_df = df[df['club_name'] == selected_club].copy()
            print(f"   {selected_club}: {len(filtered_df)} products")
        
        # Apply filters
        if category_filter != 'all':
            filtered_df = filtered_df[filtered_df['category_tier_1'] == category_filter]
        
        if search_term:
            filtered_df = filtered_df[
                filtered_df['product_name'].str.lower().str.contains(search_term.lower(), na=False)
            ]
        
        # Sort
        if sort_by == 'price_asc':
            filtered_df = filtered_df.sort_values('price', ascending=True)
        elif sort_by == 'price_desc':
            filtered_df = filtered_df.sort_values('price', ascending=False)
        elif sort_by == 'name_asc':
            filtered_df = filtered_df.sort_values('product_name', ascending=True)
        elif sort_by == 'name_desc':
            filtered_df = filtered_df.sort_values('product_name', ascending=False)
        
        print(f"   Final products to display: {len(filtered_df)}")
        
        # Create layout
        if is_list_layout:
            return create_list_layout(filtered_df, show_club=True, highlight_opportunity=False)
        else:
            product_cards = []
            for _, product in filtered_df.iterrows():
                card = create_simple_product_card(product, show_club=True, highlight_opportunity=False)
                product_cards.append(card)
            
            if product_cards:
                return dbc.Row([
                    dbc.Col(card, md=4, lg=3) for card in product_cards
                ])
            else:
                return html.Div([
                    html.H4("No se encontraron productos", style={"textAlign": "center", "color": "#6c757d"}),
                    html.P("Intenta ajustar los filtros para ver más resultados.", style={"textAlign": "center", "color": "#6c757d"})
                ], style={"padding": "50px"})
    
    # Stats callback
    @app.callback(
        Output('catalog-stats-simple', 'children'),
        [Input('catalog-club-filter-simple', 'value')]
    )
    def update_catalog_stats_simple(selected_club):
        """Update catalog statistics."""
        print(f"🔍 STATS: Club selected: {selected_club}")
        
        if selected_club == 'Todos los Clubes':
            total_count = len(df)
            club_count = len(df['club_name'].unique())
            stats_text = f"Total: {total_count} productos | {club_count} clubes"
        elif selected_club == 'Estudiantes':
            # Calculate Estudiantes stats
            estudiantes_count = len(df[df['club_name'] == 'Estudiantes'])
            estudiantes_products = set(df[df['club_name'] == 'Estudiantes']['product_name'].str.lower())
            other_clubs_df = df[df['club_name'] != 'Estudiantes'].copy()
            other_products = set(other_clubs_df['product_name'].str.lower())
            gap_products = other_products - estudiantes_products
            gap_count = len(gap_products)
            stats_text = f"Estudiantes: {estudiantes_count} productos | Gap: {gap_count} oportunidades"
        else:
            club_count = len(df[df['club_name'] == selected_club])
            stats_text = f"{selected_club}: {club_count} productos"
        
        return dbc.Card([
            dbc.CardBody([
                html.H6("Estadísticas del Catálogo", className="card-title"),
                html.P(stats_text, className="card-text")
            ])
        ], color="info", outline=True)
    
    @app.callback(
        Output("product-modal-simple", "is_open"),
        [Input("close-product-modal-simple", "n_clicks")],
        [State("product-modal-simple", "is_open")],
    )
    def toggle_product_modal_simple(n_clicks, is_open):
        """Toggle product details modal."""
        if n_clicks:
            return not is_open
        return is_open

def create_list_layout(filtered_df, show_club=False, highlight_opportunity=False):
    """Create a compact list layout without images."""
    
    if len(filtered_df) == 0:
        return html.Div([
            html.H4("No se encontraron productos", style={"textAlign": "center", "color": "#6c757d"}),
            html.P("Intenta ajustar los filtros para ver más resultados.", style={"textAlign": "center", "color": "#6c757d"})
        ], style={"padding": "50px"})
    
    # Create list items
    list_items = []
    for _, product in filtered_df.iterrows():
        # Extract product information
        product_name = product['product_name'] if pd.notna(product['product_name']) else 'Sin nombre'
        price = product['price'] if pd.notna(product['price']) else 0
        club = product['club_name'] if pd.notna(product['club_name']) else 'Desconocido'
        category = product.get('category_tier_1', 'Sin categoría') if pd.notna(product.get('category_tier_1')) else 'Sin categoría'
        in_stock = product.get('in_stock', False)
        
        # Format price
        price_formatted = f"${price:,.0f}" if price > 0 else "Precio no disponible"
        
        # Create list item
        list_item = dbc.ListGroupItem([
            dbc.Row([
                dbc.Col([
                    html.H6(
                        product_name,
                        style={"fontSize": "14px", "fontWeight": "bold", "marginBottom": "5px", "color": "#2c3e50"}
                    ),
                    html.P(
                        f"Categoría: {category}",
                        style={"fontSize": "12px", "color": "#6c757d", "marginBottom": "3px"}
                    ),
                ], md=6),
                dbc.Col([
                    html.P(
                        price_formatted,
                        style={"fontSize": "16px", "fontWeight": "bold", "color": "#007bff", "marginBottom": "0px", "textAlign": "right"}
                    ),
                ], md=2),
                dbc.Col([
                    html.P(
                        "✅ En stock" if in_stock else "❌ Sin stock",
                        style={"fontSize": "11px", "color": "#28a745" if in_stock else "#dc3545", "marginBottom": "0px", "textAlign": "center"}
                    ),
                ], md=2),
                dbc.Col([
                    html.Div([
                        dbc.Badge(
                            club if show_club else "Estudiantes",
                            color="primary" if not show_club else "secondary",
                            style={"fontSize": "10px"}
                        ),
                        " " if highlight_opportunity else "",
                        dbc.Badge(
                            "Oportunidad",
                            color="success" if highlight_opportunity else "light",
                            style={"fontSize": "10px"} if highlight_opportunity else {"display": "none"}
                        )
                    ], style={"textAlign": "right"})
                ], md=2),
            ])
        ], style={
            "borderLeft": "3px solid #28a745" if highlight_opportunity else "none",
            "backgroundColor": "#f8f9fa",
            "border": "1px solid #dee2e6",
            "marginBottom": "2px"
        })
        
        list_items.append(list_item)
    
    # Create the list
    return dbc.ListGroup(
        list_items, 
        flush=True, 
        style={
            "maxHeight": "600px", 
            "overflowY": "auto", 
            "backgroundColor": "#f8f9fa",
            "border": "none"
        }
    )

def create_simple_product_card(product, show_club=False, highlight_opportunity=False):
    """Create a simple product card component with real images."""
    
    # Extract product information
    product_name = product['product_name'] if pd.notna(product['product_name']) else 'Sin nombre'
    price = product['price'] if pd.notna(product['price']) else 0
    club = product['club_name'] if pd.notna(product['club_name']) else 'Desconocido'
    category = product.get('category_tier_1', 'Sin categoría') if pd.notna(product.get('category_tier_1')) else 'Sin categoría'
    in_stock = product.get('in_stock', False)
    
    # Extract product ID for image lookup
    image_path = None
    if 'product_id' in product and pd.notna(product['product_id']):
        club_folder = product['club_name'].lower().replace(' ', '_')
        image_filename = f"{product['product_id']}_1.jpg"
        image_path = f"../images/{club_folder}/{image_filename}"
    
    # Card styling with opportunity highlighting
    card_style = {
        "border": "2px solid #e9ecef",
        "borderRadius": "8px",
        "padding": "15px",
        "marginBottom": "20px",
        "backgroundColor": "#ffffff",
        "transition": "all 0.3s ease",
        "cursor": "pointer",
        "height": "100%"
    }
    
    if highlight_opportunity:
        card_style["borderColor"] = "#28a745"
        card_style["boxShadow"] = "0 4px 8px rgba(40, 167, 69, 0.2)"
    
    # Price formatting
    price_str = f"${int(product['price']):,}" if pd.notna(product['price']) else "Precio N/A"
    
    # Create card with click handler
    card = dbc.Card(
        id=f"product-card-{product.get('product_id', 'unknown')}",
        style=card_style,
        className="product-card-hover",
        n_clicks=0,
        children=[
            # Image component - real image or placeholder
            html.Div(
                style={
                    "width": "100%",
                    "height": "150px",
                    "backgroundColor": "#f8f9fa",
                    "borderRadius": "4px",
                    "marginBottom": "10px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "overflow": "hidden"
                },
                children=[
                    html.Img(
                        src=image_path if image_path and Path(image_path).exists() else "/assets/images/placeholder.png",
                        style={
                            "width": "100%",
                            "height": "100%",
                            "objectFit": "cover"
                        },
                        onError="this.src='/assets/images/placeholder.png'"
                    ) if image_path and Path(image_path).exists() else
                    html.Div([
                        html.H4("📷", style={"margin": "0", "fontSize": "24px", "color": "#6c757d"}),
                        html.P("Imagen no disponible", style={"margin": "5px 0 0 0", "fontSize": "12px", "color": "#6c757d"})
                    ], style={"textAlign": "center"})
                ]
            ),
            
            # Product info
            dbc.CardBody([
                # Club name (if showing club info)
                html.H6(
                    product['club_name'] if show_club else "",
                    style={"color": "#007bff", "fontSize": "12px", "marginBottom": "5px", "textTransform": "uppercase"}
                ) if show_club else html.Div(),
                
                # Product name
                html.H5(
                    product['product_name'][:40] + "..." if len(product['product_name']) > 40 else product['product_name'],
                    style={"fontSize": "14px", "fontWeight": "bold", "marginBottom": "8px", "color": "#2c3e50", "lineHeight": "1.2"}
                ),
                
                # Category
                html.P(
                    product.get('category_tier_1', 'Sin categoría'),
                    style={"fontSize": "11px", "color": "#6c757d", "marginBottom": "8px", "textTransform": "capitalize"}
                ),
                
                # Price
                html.H4(
                    price_str,
                    style={"color": "#28a745", "fontSize": "16px", "fontWeight": "bold", "margin": "0"}
                ),
                
                # Opportunity badge
                html.Div(
                    "🎯 OPORTUNIDAD",
                    style={
                        "backgroundColor": "#28a745",
                        "color": "white",
                        "padding": "4px 8px",
                        "borderRadius": "4px",
                        "fontSize": "10px",
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "marginTop": "8px"
                    }
                ) if highlight_opportunity else html.Div()
            ], style={"padding": "10px"})
        ]
    )
    
    return card

# Add Estudiantes brand colors and improved styling
def add_estudiantes_branding(app):
    """Add Estudiantes brand colors and CSS styling to the app."""
    
    app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Estudiantes brand colors */
            :root {
                --estudiantes-red: #CC0000;
                --estudiantes-dark-red: #990000;
                --estudiantes-light-red: #FF3333;
                --estudiantes-yellow: #FFCC00;
                --estudiantes-gray: #333333;
            }
            
            /* Product card hover effects */
            .product-card-hover {
                transition: all 0.3s ease;
                cursor: pointer;
            }
            
            .product-card-hover:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                border-color: var(--estudiantes-red) !important;
            }
            
            /* Tab styling */
            .nav-tabs .nav-link.active {
                background-color: var(--estudiantes-red) !important;
                border-color: var(--estudiantes-red) !important;
                color: white !important;
            }
            
            .nav-tabs .nav-link:hover {
                border-color: var(--estudiantes-light-red) !important;
                color: var(--estudiantes-red) !important;
            }
            
            /* Dropdown styling */
            .form-control:focus {
                border-color: var(--estudiantes-red) !important;
                box-shadow: 0 0 0 0.2rem rgba(204, 0, 0, 0.25) !important;
            }
            
            /* Button styling */
            .btn-primary {
                background-color: var(--estudiantes-red) !important;
                border-color: var(--estudiantes-red) !important;
            }
            
            .btn-primary:hover {
                background-color: var(--estudiantes-dark-red) !important;
                border-color: var(--estudiantes-dark-red) !important;
            }
            
            /* Opportunity badge animation */
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            
            .opportunity-badge {
                animation: pulse 2s infinite;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
    '''
