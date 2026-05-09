"""
Gap Analysis Page for Marketing Team
=====================================

This module contains a comprehensive gap analysis table for the marketing team
to view all products and competitive opportunities.
"""

import dash
from dash import dcc, html, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime

def create_gap_analysis_layout(df):
    """Create comprehensive gap analysis table layout."""
    
    print(f"🔍 DEBUG: Creating Gap Analysis layout with {len(df)} total records")
    
    # Clean data - fill missing product names instead of dropping them
    df_clean = df.copy()
    df_clean['product_name'] = df_clean['product_name'].fillna('Producto sin nombre')
    df_clean = df_clean.fillna({'category_tier_1': 'Sin categoría', 'price': 0})
    
    # Calculate gap analysis
    estudiantes_products = df_clean[df_clean['club_name'] == 'Estudiantes']
    other_clubs_df = df_clean[df_clean['club_name'] != 'Estudiantes']
    
    print(f"🎯 DEBUG: Layout creation - Estudiantes products: {len(estudiantes_products)}")
    
    # Use all product names (including duplicates) for gap analysis
    # Exclude the placeholder "Producto sin nombre" from gap analysis
    estudiantes_product_names = set(estudiantes_products[estudiantes_products['product_name'] != 'Producto sin nombre']['product_name'].str.lower())
    other_product_names = set(other_clubs_df[other_clubs_df['product_name'] != 'Producto sin nombre']['product_name'].str.lower())
    gap_products = other_product_names - estudiantes_product_names
    gap_df = other_clubs_df[other_clubs_df['product_name'].str.lower().isin(gap_products)]
    
    print(f"🔍 DEBUG: Layout creation - Gap opportunities: {len(gap_df)}")
    
    # Create comprehensive analysis table
    analysis_df = create_comprehensive_analysis_table(df_clean, estudiantes_products, gap_df)
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Gap Analysis Dashboard", 
                       style={"color": "#2c3e50", "marginBottom": "30px"}),
                html.P("Comprehensive analysis of Estudiantes product catalog vs competitors for marketing strategy development.",
                       style={"color": "#6c757d", "marginBottom": "40px"})
            ])
        ]),
        
        # Executive Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{len(estudiantes_products)}", className="text-primary"),
                        html.P("Estudiantes Products", className="card-text"),
                        html.Small("Current product catalog", className="text-muted")
                    ])
                ], color="light", outline=True)
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{len(gap_df)}", className="text-danger"),
                        html.P("Gap Opportunities", className="card-text"),
                        html.Small("Products competitors sell", className="text-muted")
                    ])
                ], color="light", outline=True)
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{len(df_clean)}", className="text-info"),
                        html.P("Total Market", className="card-text"),
                        html.Small("All competitor products", className="text-muted")
                    ])
                ], color="light", outline=True)
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{len(gap_products)/len(other_product_names)*100:.1f}%", className="text-success"),
                        html.P("Market Gap", className="card-text"),
                        html.Small("Percentage of missing products", className="text-muted")
                    ])
                ], color="light", outline=True)
            ], md=3)
        ], style={"marginBottom": "30px"}),
        
        # Filters and Controls
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🔍 Analysis Filters"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("View Mode:", className="form-label"),
                                dcc.Dropdown(
                                    id='gap-analysis-view-mode',
                                    options=[
                                        {'label': 'All Products (Comprehensive)', 'value': 'all'},
                                        {'label': 'Gap Products Only', 'value': 'gap'},
                                        {'label': 'Estudiantes Products Only', 'value': 'estudiantes'},
                                        {'label': 'High Priority Opportunities', 'value': 'priority'}
                                    ],
                                    value='gap',
                                    className="mb-3"
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Category Filter:", className="form-label"),
                                dcc.Dropdown(
                                    id='gap-analysis-category-filter',
                                    options=[
                                        {'label': 'All Categories', 'value': 'all'}
                                    ] + [{'label': cat if cat else 'Uncategorized', 'value': cat} for cat in sorted([str(cat) for cat in df_clean['category_tier_1'].unique() if pd.notna(cat)])],
                                    value='all',
                                    className="mb-3"
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Competitor Filter:", className="form-label"),
                                dcc.Dropdown(
                                    id='gap-analysis-competitor-filter',
                                    options=[
                                        {'label': 'All Competitors', 'value': 'all'}
                                    ] + [{'label': club, 'value': club} for club in sorted(other_clubs_df['club_name'].unique())],
                                    value='all',
                                    className="mb-3"
                                )
                            ], md=3),
                            dbc.Col([
                                html.Label("Sort by:", className="form-label"),
                                dcc.Dropdown(
                                    id='gap-analysis-sort-filter',
                                    options=[
                                        {'label': 'Product Name (A-Z)', 'value': 'name_asc'},
                                        {'label': 'Product Name (Z-A)', 'value': 'name_desc'},
                                        {'label': 'Price (Low to High)', 'value': 'price_asc'},
                                        {'label': 'Price (High to Low)', 'value': 'price_desc'},
                                        {'label': 'Priority Score', 'value': 'priority'},
                                        {'label': 'Market Demand', 'value': 'demand'}
                                    ],
                                    value='priority',
                                    className="mb-3"
                                )
                            ], md=3)
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Search Products:", className="form-label"),
                                dbc.Input(
                                    id='gap-analysis-search',
                                    type='text',
                                    placeholder='Search by product name...',
                                    className="mb-3"
                                )
                            ], md=6),
                            dbc.Col([
                                html.Label("Price Range:", className="form-label"),
                                dcc.RangeSlider(
                                    id='gap-analysis-price-range',
                                    min=0,
                                    max=100000,
                                    step=1000,
                                    marks={
                                        0: '$0',
                                        25000: '$25K',
                                        50000: '$50K',
                                        75000: '$75K',
                                        100000: '$100K+'
                                    },
                                    value=[0, 100000],
                                    className="mb-3"
                                )
                            ], md=6)
                        ])
                    ])
                ], style={"marginBottom": "20px"})
            ], md=12)
        ]),
        
        # Main Analysis Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.Div([
                            html.H5("📊 Gap Analysis Table", className="mb-0"),
                            html.Small("Comprehensive product analysis for marketing strategy", className="text-muted")
                        ])
                    ]),
                    dbc.CardBody([
                        html.Div(id='gap-analysis-table-container')
                    ])
                ], style={"marginBottom": "20px"})
            ], md=12)
        ]),
        
        # Export Options
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📤 Export Options"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Export Format:", className="form-label"),
                                dcc.Dropdown(
                                    id='export-format',
                                    options=[
                                        {'label': 'Excel (.xlsx)', 'value': 'excel'},
                                        {'label': 'CSV (.csv)', 'value': 'csv'},
                                        {'label': 'PDF Report', 'value': 'pdf'}
                                    ],
                                    value='excel',
                                    className="mb-3"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Include Columns:", className="form-label"),
                                dcc.Checklist(
                                    id='export-columns',
                                    options=[
                                        {'label': 'Product Details', 'value': 'product'},
                                        {'label': 'Competitive Analysis', 'value': 'competitive'},
                                        {'label': 'Marketing Insights', 'value': 'marketing'},
                                        {'label': 'Strategic Recommendations', 'value': 'strategic'}
                                    ],
                                    value=['product', 'competitive', 'marketing'],
                                    className="mb-3"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label(" ", className="form-label"),
                                dbc.Button(
                                    "📥 Export Analysis",
                                    id='export-button',
                                    color="primary",
                                    className="w-100"
                                )
                            ], md=4)
                        ])
                    ])
                ], style={"marginBottom": "20px"})
            ], md=12)
        ]),
        
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def create_comprehensive_analysis_table(df, estudiantes_products, gap_df):
    """Create comprehensive analysis table with all product information."""
    
    # Combine all products for comprehensive analysis
    all_products = []
    
    # Add Estudiantes products
    for _, product in estudiantes_products.iterrows():
        all_products.append({
            'Product Name': product['product_name'],
            'Category': product.get('category_tier_1', 'Sin categoría'),
            'Price': product['price'] if pd.notna(product['price']) else 0,
            'Club': 'Estudiantes',
            'Status': 'Current',
            'Competitors': 'N/A',
            'Market Demand': calculate_market_demand(df, product['product_name']),
            'Priority Score': 0,
            'Marketing Insight': 'Current product - monitor performance',
            'Strategic Action': 'Maintain and optimize',
            'Revenue Potential': 0,
            'Launch Priority': 'N/A'
        })
    
    # Add gap products
    for _, product in gap_df.iterrows():
        priority_score = calculate_priority_score(df, product)
        revenue_potential = calculate_revenue_potential(df, product)
        
        all_products.append({
            'Product Name': product['product_name'],
            'Category': product.get('category_tier_1', 'Sin categoría'),
            'Price': product['price'] if pd.notna(product['price']) else 0,
            'Club': product['club_name'],
            'Status': 'Gap Opportunity',
            'Competitors': get_competitors_selling_product(df, product['product_name'], 'Estudiantes'),
            'Market Demand': calculate_market_demand(df, product['product_name']),
            'Priority Score': priority_score,
            'Marketing Insight': generate_marketing_insight(product, gap_df),
            'Strategic Action': generate_strategic_action(product, priority_score),
            'Revenue Potential': revenue_potential,
            'Launch Priority': get_launch_priority(priority_score)
        })
    
    return pd.DataFrame(all_products)

def calculate_market_demand(df, product_name):
    """Calculate market demand based on number of competitors selling the product."""
    if pd.isna(product_name) or not isinstance(product_name, str):
        return "Low"
    
    competitors = df[df['product_name'].str.lower() == product_name.lower()]['club_name'].nunique()
    if competitors >= 4:
        return "Very High"
    elif competitors >= 3:
        return "High"
    elif competitors >= 2:
        return "Medium"
    else:
        return "Low"

def calculate_priority_score(df, product):
    """Calculate priority score for gap products."""
    # Factors: price, market demand, category popularity
    price_score = min(product['price'] / 1000, 50) if pd.notna(product['price']) else 0
    
    product_name = product.get('product_name', '')
    if pd.isna(product_name) or not isinstance(product_name, str):
        demand_score = 0
    else:
        demand_score = len(df[df['product_name'].str.lower() == product_name.lower()]) * 10
    
    category = product.get('category_tier_1', '')
    if pd.isna(category) or not isinstance(category, str):
        category_score = 0
    else:
        category_score = len(df[df['category_tier_1'] == category]) / 10
    
    return min(price_score + demand_score + category_score, 100)

def calculate_revenue_potential(df, product):
    """Calculate revenue potential for gap products."""
    avg_sales_per_product = 10  # Estimated monthly sales
    price = product['price'] if pd.notna(product['price']) else 25000
    monthly_revenue = price * avg_sales_per_product
    return monthly_revenue * 12  # Annual potential

def get_competitors_selling_product(df, product_name, exclude_club):
    """Get list of competitors selling a specific product."""
    if pd.isna(product_name) or not isinstance(product_name, str):
        return "N/A"
    
    competitors = df[df['product_name'].str.lower() == product_name.lower()]
    competitors = competitors[competitors['club_name'] != exclude_club]['club_name'].unique()
    return ', '.join(sorted(competitors)) if len(competitors) > 0 else "N/A"

def generate_marketing_insight(product, gap_df):
    """Generate marketing insight for gap products."""
    price = product['price'] if pd.notna(product['price']) else 0
    category = product.get('category_tier_1', '')
    
    if price > 50000:
        return "Premium pricing opportunity - target high-value customers"
    elif category == 'Indumentaria':
        return "Core apparel category - high demand across all segments"
    elif category == 'Accesorios':
        return "Accessory category - impulse purchase potential"
    else:
        return "Niche category - target specific customer segments"

def generate_strategic_action(product, priority_score):
    """Generate strategic action recommendation."""
    if priority_score >= 80:
        return "Immediate launch - high priority opportunity"
    elif priority_score >= 60:
        return "Q1 launch - medium priority opportunity"
    elif priority_score >= 40:
        return "Q2 launch - consider for expansion"
    else:
        return "Long-term consideration - monitor market trends"

def get_launch_priority(priority_score):
    """Get launch priority category."""
    if priority_score >= 80:
        return "🔴 Critical"
    elif priority_score >= 60:
        return "🟡 High"
    elif priority_score >= 40:
        return "🟢 Medium"
    else:
        return "⚪ Low"

# Callbacks for gap analysis page
def register_gap_analysis_callbacks(app, df):
    """Register gap analysis callbacks with the app."""
    
    @app.callback(
        Output('gap-analysis-table-container', 'children'),
        [Input('gap-analysis-view-mode', 'value'),
         Input('gap-analysis-category-filter', 'value'),
         Input('gap-analysis-competitor-filter', 'value'),
         Input('gap-analysis-sort-filter', 'value'),
         Input('gap-analysis-search', 'value'),
         Input('gap-analysis-price-range', 'value')]
    )
    def update_gap_analysis_table(view_mode, category_filter, competitor_filter, sort_filter, search_term, price_range):
        """Update gap analysis table based on filters."""
        
        print(f"🔍 DEBUG: Gap Analysis callback triggered!")
        print(f"   view_mode: {view_mode}")
        print(f"   category_filter: {category_filter}")
        
        print(f"📊 DEBUG: Total records in df: {len(df)}")
        
        # Clean data - fill missing product names instead of dropping them
        df_clean = df.copy()
        df_clean['product_name'] = df_clean['product_name'].fillna('Producto sin nombre')
        df_clean = df_clean.fillna({'category_tier_1': 'Sin categoría', 'price': 0})
        
        # Calculate gap analysis
        estudiantes_products = df_clean[df_clean['club_name'] == 'Estudiantes']
        other_clubs_df = df_clean[df_clean['club_name'] != 'Estudiantes']
        
        print(f"🎯 DEBUG: Estudiantes products: {len(estudiantes_products)}")
        print(f"🔍 DEBUG: Other clubs products: {len(other_clubs_df)}")
        
        # Exclude the placeholder "Producto sin nombre" from gap analysis
        estudiantes_product_names = set(estudiantes_products[estudiantes_products['product_name'] != 'Producto sin nombre']['product_name'].str.lower())
        other_product_names = set(other_clubs_df[other_clubs_df['product_name'] != 'Producto sin nombre']['product_name'].str.lower())
        gap_products = other_product_names - estudiantes_product_names
        gap_df = other_clubs_df[other_clubs_df['product_name'].str.lower().isin(gap_products)]
        
        print(f"🔍 DEBUG: Gap opportunities: {len(gap_df)}")
        
        # Create comprehensive analysis table
        all_products = []
        
        # Add Estudiantes products
        for _, product in estudiantes_products.iterrows():
            all_products.append({
                'Product Name': product['product_name'],
                'Category': product.get('category_tier_1', 'Sin categoría'),
                'Sub-Category': product.get('category_tier_2', 'N/A'),
                'Price': product['price'] if pd.notna(product['price']) else 0,
                'Sizes Available': product.get('sizes_available', 'N/A'),
                'Age Group': product.get('age_group', 'N/A'),
                'Gender': product.get('gender', 'N/A'),
                'Club': 'Estudiantes',
                'Status': 'Current'
            })
        
        # Add gap products
        for _, product in gap_df.iterrows():
            all_products.append({
                'Product Name': product['product_name'],
                'Category': product.get('category_tier_1', 'Sin categoría'),
                'Sub-Category': product.get('category_tier_2', 'N/A'),
                'Price': product['price'] if pd.notna(product['price']) else 0,
                'Sizes Available': product.get('sizes_available', 'N/A'),
                'Age Group': product.get('age_group', 'N/A'),
                'Gender': product.get('gender', 'N/A'),
                'Club': product['club_name'],
                'Status': 'Gap Opportunity'
            })
        
        df_table = pd.DataFrame(all_products)
        
        # Apply filters
        if view_mode == 'gap':
            df_table = df_table[df_table['Status'] == 'Gap Opportunity']
        elif view_mode == 'estudiantes':
            df_table = df_table[df_table['Status'] == 'Current']
        elif view_mode == 'priority':
            # Priority mode not applicable with new structure
            pass
        
        if category_filter != 'all':
            df_table = df_table[df_table['Category'] == category_filter]
        
        if competitor_filter != 'all':
            df_table = df_table[df_table['Club'] == competitor_filter]
        
        if search_term:
            df_table = df_table[df_table['Product Name'].str.contains(search_term, case=False, na=False)]
        
        if price_range:
            df_table = df_table[(df_table['Price'] >= price_range[0]) & (df_table['Price'] <= price_range[1])]
        
        # Apply sorting
        if sort_filter == 'name_asc':
            df_table = df_table.sort_values('Product Name', ascending=True)
        elif sort_filter == 'name_desc':
            df_table = df_table.sort_values('Product Name', ascending=False)
        elif sort_filter == 'price_asc':
            df_table = df_table.sort_values('Price', ascending=True)
        elif sort_filter == 'price_desc':
            df_table = df_table.sort_values('Price', ascending=False)
        elif sort_filter == 'priority':
            # Default to price sorting since Priority Score column doesn't exist
            df_table = df_table.sort_values('Price', ascending=False)
        elif sort_filter == 'demand':
            # Default to category sorting since Market Demand column doesn't exist
            df_table = df_table.sort_values('Category', ascending=True)
        
        table = dash_table.DataTable(
            id='gap-analysis-table',
            columns=[
                {'name': 'Product Name', 'id': 'Product Name', 'editable': False},
                {'name': 'Category', 'id': 'Category', 'editable': False},
                {'name': 'Sub-Category', 'id': 'Sub-Category', 'editable': False},
                {'name': 'Price', 'id': 'Price', 'type': 'numeric', 'format': {'specifier': '$,.0f'}, 'editable': False},
                {'name': 'Sizes Available', 'id': 'Sizes Available', 'editable': False},
                {'name': 'Age Group', 'id': 'Age Group', 'editable': False},
                {'name': 'Gender', 'id': 'Gender', 'editable': False},
                {'name': 'Club', 'id': 'Club', 'editable': False},
                {'name': 'Status', 'id': 'Status', 'editable': False}
            ],
            data=df_table.to_dict('records'),
            sort_action='native',
            filter_action='native',
            page_size=50,
            export_format='xlsx',
            export_headers='display',
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontFamily': 'Arial, sans-serif',
                'fontSize': '12px',
                'minWidth': '100px',
                'maxWidth': '300px',
                'whiteSpace': 'normal'
            },
            style_header={
                'backgroundColor': '#CC0000',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center',
                'border': '1px solid white'
            },
            style_data={
                'border': '1px solid #ddd'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{Status} = Current'},
                    'backgroundColor': '#e8f5e9',
                    'color': '#2e7d32',
                },
                {
                    'if': {'filter_query': '{Status} = Gap Opportunity'},
                    'backgroundColor': '#ffebee',
                    'color': '#c62828',
                }
            ]
        )
        
        return table

@callback(
    Output('export-button', 'children'),
    [Input('export-button', 'n_clicks')],
    prevent_initial_call=True
)
def handle_export(n_clicks):
    """Handle export button click."""
    if n_clicks:
        return "✅ Export Started..."
    return "📥 Export Analysis"
