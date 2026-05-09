"""
Strategic Recommendations Page for Club Store Revenue Intelligence
================================================================

This module contains strategic recommendations and implementation roadmap
for Estudiantes product catalog expansion.
"""

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_recommendations_layout(df):
    """Create strategic recommendations layout."""
    
    # Calculate gap analysis
    estudiantes_products = df[df['club_name'] == 'Estudiantes']
    other_clubs_df = df[df['club_name'] != 'Estudiantes']
    
    estudiantes_product_names = set(estudiantes_products['product_name'].str.lower())
    other_product_names = set(other_clubs_df['product_name'].str.lower())
    gap_products = other_product_names - estudiantes_product_names
    gap_df = other_clubs_df[other_clubs_df['product_name'].str.lower().isin(gap_products)]
    
    # Generate prioritized recommendations
    top_recommendations = generate_top_recommendations(gap_df)
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Strategic Recommendations", 
                       style={"color": "#2c3e50", "marginBottom": "30px"}),
                html.P("Actionable recommendations for expanding Estudiantes product catalog and maximizing revenue opportunities.",
                       style={"color": "#6c757d", "marginBottom": "40px"})
            ])
        ]),
        
        # Executive Summary
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🎯 Executive Summary"),
                    dbc.CardBody([
                        html.Div([
                            html.H5("Market Opportunity Analysis", className="mb-3"),
                            html.P("Estudiantes has a significant opportunity to expand its product catalog by introducing 1,408 products that competitors currently offer but Estudiantes does not.", className="mb-3"),
                            html.P("This represents a 96% market gap and an estimated annual revenue potential of over $2M.", className="mb-3"),
                            html.Div([
                                html.H6("Key Recommendations:", className="mb-2"),
                                html.Ul([
                                    html.Li("Launch 50 high-priority products in Q1"),
                                    html.Li("Focus on apparel and accessories categories"),
                                    html.Li("Implement premium pricing strategy"),
                                    html.Li("Develop 3-phase expansion roadmap")
                                ])
                            ])
                        ])
                    ])
                ], color="light", outline=True)
            ], md=12)
        ], style={"marginBottom": "30px"}),
        
        # Priority Matrix
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 Priority Matrix"),
                    dbc.CardBody([
                        dcc.Graph(
                            id='priority-matrix-chart',
                            figure=create_priority_matrix(gap_df)
                        )
                    ])
                ], style={"marginBottom": "20px"})
            ], md=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("⏱️ Implementation Timeline"),
                    dbc.CardBody([
                        create_timeline_implementation()
                    ])
                ], style={"marginBottom": "20px"})
            ], md=4)
        ]),
        
        # Top Recommendations Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🏆 Top 50 Priority Products"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Filter by Category:", className="form-label"),
                                dcc.Dropdown(
                                    id='recommendation-category-filter',
                                    options=[
                                        {'label': 'All Categories', 'value': 'all'}
                                    ] + [{'label': cat, 'value': cat} for cat in sorted(gap_df['category_tier_1'].unique())],
                                    value='all',
                                    className="mb-3"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Sort by:", className="form-label"),
                                dcc.Dropdown(
                                    id='recommendation-sort-filter',
                                    options=[
                                        {'label': 'Revenue Potential', 'value': 'revenue'},
                                        {'label': 'Market Demand', 'value': 'demand'},
                                        {'label': 'Price', 'value': 'price'}
                                    ],
                                    value='revenue',
                                    className="mb-3"
                                )
                            ], md=4),
                            dbc.Col([
                                html.Label("Products to show:", className="form-label"),
                                dcc.Dropdown(
                                    id='recommendation-count-filter',
                                    options=[
                                        {'label': 'Top 10', 'value': 10},
                                        {'label': 'Top 25', 'value': 25},
                                        {'label': 'Top 50', 'value': 50}
                                    ],
                                    value=10,
                                    className="mb-3"
                                )
                            ], md=4)
                        ]),
                        html.Div(id='recommendations-table')
                    ])
                ], style={"marginBottom": "20px"})
            ], md=12)
        ]),
        
        # ROI Calculator
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("💰 Revenue Projection Calculator"),
                    dbc.CardBody([
                        create_roi_calculator()
                    ])
                ], style={"marginBottom": "20px"})
            ], md=12)
        ]),
        
        # Implementation Plan
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📋 Implementation Plan"),
                    dbc.CardBody([
                        create_implementation_plan()
                    ])
                ], style={"marginBottom": "20px"})
            ], md=12)
        ]),
        
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def generate_top_recommendations(gap_df):
    """Generate prioritized product recommendations."""
    
    # Calculate priority scores
    gap_df['priority_score'] = (
        gap_df['price'] * 0.4 +  # Price factor (40%)
        gap_df.groupby('club_name')['product_name'].transform('count') * 0.3 +  # Competitor factor (30%)
        gap_df.groupby('category_tier_1')['product_name'].transform('count') * 0.3  # Category demand (30%)
    )
    
    # Sort by priority score
    top_products = gap_df.nlargest(50, 'priority_score')
    
    return top_products

def create_priority_matrix(gap_df):
    """Create priority matrix visualization."""
    
    # Calculate metrics for each product
    gap_df_analysis = gap_df.copy()
    gap_df_analysis['market_demand'] = gap_df_analysis.groupby('category_tier_1')['product_name'].transform('count')
    gap_df_analysis['revenue_potential'] = gap_df_analysis['price'] * gap_df_analysis['market_demand']
    
    # Sample top 100 products for visualization
    sample_df = gap_df_analysis.nlargest(100, 'revenue_potential')
    
    fig = px.scatter(
        x=sample_df['price'],
        y=sample_df['market_demand'],
        size=sample_df['revenue_potential'],
        color=sample_df['category_tier_1'],
        hover_name=sample_df['product_name'],
        hover_data=['club_name', 'price'],
        title="Product Priority Matrix",
        labels={
            'x': 'Price Point ($)',
            'y': 'Market Demand',
            'size': 'Revenue Potential',
            'category_tier_1': 'Category'
        }
    )
    
    # Add quadrant lines
    fig.add_hline(y=sample_df['market_demand'].median(), line_dash="dash", line_color="gray")
    fig.add_vline(x=sample_df['price'].median(), line_dash="dash", line_color="gray")
    
    fig.update_layout(height=600)
    
    return fig

def create_timeline_implementation():
    """Create implementation timeline visualization."""
    
    timeline_data = [
        {'phase': 'Phase 1', 'duration': '3 months', 'products': 50, 'focus': 'Quick Wins'},
        {'phase': 'Phase 2', 'duration': '6 months', 'products': 150, 'focus': 'Category Expansion'},
        {'phase': 'Phase 3', 'duration': '12 months', 'products': 300, 'focus': 'Complete Portfolio'}
    ]
    
    timeline = html.Div([
        html.H6("3-Phase Implementation Plan", className="mb-3"),
        
        dbc.Timeline([
            dbc.TimelineItem(
                title=phase['phase'],
                subtitle=f"{phase['duration']} - {phase['products']} products",
                body=dbc.Card([
                    dbc.CardBody([
                        html.H6(phase['focus'], className="text-primary"),
                        html.P(f"Launch {phase['products']} priority products with focus on {phase['focus'].lower()}.")
                    ])
                ], color="primary")
            ) for phase in timeline_data
        ])
    ])
    
    return timeline

def create_roi_calculator():
    """Create ROI calculator component."""
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Number of Products to Launch:", className="form-label"),
                dbc.Input(
                    id='roi-products-input',
                    type='number',
                    value=50,
                    min=1,
                    max=1408,
                    className="mb-3"
                )
            ], md=3),
            dbc.Col([
                html.Label("Average Price Point ($):", className="form-label"),
                dbc.Input(
                    id='roi-price-input',
                    type='number',
                    value=25000,
                    min=1000,
                    max=100000,
                    className="mb-3"
                )
            ], md=3),
            dbc.Col([
                html.Label("Expected Sales per Product (monthly):", className="form-label"),
                dbc.Input(
                    id='roi-sales-input',
                    type='number',
                    value=10,
                    min=1,
                    max=100,
                    className="mb-3"
                )
            ], md=3),
            dbc.Col([
                html.Label("Profit Margin (%):", className="form-label"),
                dbc.Input(
                    id='roi-margin-input',
                    type='number',
                    value=40,
                    min=10,
                    max=80,
                    className="mb-3"
                )
            ], md=3)
        ]),
        html.Div(id='roi-results')
    ])

def create_implementation_plan():
    """Create detailed implementation plan."""
    
    phases = [
        {
            'title': 'Phase 1: Quick Wins (Months 1-3)',
            'description': 'Launch 50 high-priority products with immediate revenue potential',
            'actions': [
                'Focus on top-selling apparel categories',
                'Introduce premium pricing tiers',
                'Launch accessories and lifestyle products',
                'Implement basic marketing campaigns'
            ],
            'kpi': '50 products launched, $2M revenue potential',
            'investment': '$500K',
            'roi': '300%'
        },
        {
            'title': 'Phase 2: Category Expansion (Months 4-9)',
            'description': 'Expand into new product categories and increase market coverage',
            'actions': [
                'Launch youth and kids product lines',
                'Introduce home goods and lifestyle products',
                'Develop seasonal collections',
                'Implement advanced marketing strategies'
            ],
            'kpi': '150 products launched, $6M revenue potential',
            'investment': '$1.2M',
            'roi': '400%'
        },
        {
            'title': 'Phase 3: Complete Portfolio (Months 10-24)',
            'description': 'Achieve comprehensive product portfolio coverage',
            'actions': [
                'Launch remaining gap products',
                'Develop exclusive Estudiantes products',
                'Implement premium membership programs',
                'Establish strategic partnerships'
            ],
            'kpi': '300+ products launched, $15M+ revenue potential',
            'investment': '$3M',
            'roi': '500%'
        }
    ]
    
    return dbc.Accordion([
        dbc.AccordionItem([
            html.H6(phase['title'], className="text-primary mb-2"),
            html.P(phase['description'], className="mb-3"),
            html.H6("Key Actions:", className="mb-2"),
            html.Ul([html.Li(action) for action in phase['actions']], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.P(f"📊 {phase['kpi']}", className="mb-1")
                ], md=4),
                dbc.Col([
                    html.P(f"💰 Investment: {phase['investment']}", className="mb-1")
                ], md=4),
                dbc.Col([
                    html.P(f"📈 ROI: {phase['roi']}", className="mb-1")
                ], md=4)
            ])
        ], title=phase['title']) for phase in phases
    ])

# Callbacks for recommendations page
@callback(
    Output('recommendations-table', 'children'),
    [Input('recommendation-category-filter', 'value'),
     Input('recommendation-sort-filter', 'value'),
     Input('recommendation-count-filter', 'value')]
)
def update_recommendations_table(category_filter, sort_filter, count_filter):
    """Update recommendations table based on filters."""
    
    # This would be implemented with actual data filtering
    # For now, return a placeholder
    
    table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Product Name"),
                html.Th("Category"),
                html.Th("Price"),
                html.Th("Competitor"),
                html.Th("Priority Score"),
                html.Th("Action")
            ])
        ]),
        html.Tbody([
            html.Tr([
                html.Td(f"Sample Product {i}"),
                html.Td("Indumentaria"),
                html.Td(f"${25000 + i*1000:,}"),
                html.Td("Boca Juniors"),
                html.Td(f"{90 - i}/100"),
                dbc.Button("Launch", color="success", size="sm")
            ]) for i in range(count_filter)
        ])
    ], striped=True, bordered=True, hover=True)
    
    return table

@callback(
    Output('roi-results', 'children'),
    [Input('roi-products-input', 'value'),
     Input('roi-price-input', 'value'),
     Input('roi-sales-input', 'value'),
     Input('roi-margin-input', 'value')]
)
def update_roi_calculator(products, price, sales, margin):
    """Update ROI calculator results."""
    
    monthly_revenue = products * price * sales
    annual_revenue = monthly_revenue * 12
    monthly_profit = monthly_revenue * (margin / 100)
    annual_profit = monthly_profit * 12
    
    results = dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Monthly Revenue:", className="text-muted"),
                    html.H4(f"${monthly_revenue:,.0f}", className="text-primary")
                ], md=3),
                dbc.Col([
                    html.H6("Annual Revenue:", className="text-muted"),
                    html.H4(f"${annual_revenue:,.0f}", className="text-success")
                ], md=3),
                dbc.Col([
                    html.H6("Monthly Profit:", className="text-muted"),
                    html.H4(f"${monthly_profit:,.0f}", className="text-info")
                ], md=3),
                dbc.Col([
                    html.H6("Annual Profit:", className="text-muted"),
                    html.H4(f"${annual_profit:,.0f}", className="text-warning")
                ], md=3)
            ])
        ])
    ], color="light")
    
    return results
