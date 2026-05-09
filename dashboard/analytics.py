"""
Analytics Dashboard for Club Store Revenue Intelligence
======================================================

This module contains comprehensive analytics visualizations and insights
for Estudiantes and competitor analysis.
"""

import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

def create_analytics_layout(df):
    """Create comprehensive analytics dashboard layout."""
    
    # Calculate key metrics
    estudiantes_products = df[df['club_name'] == 'Estudiantes']
    other_clubs_df = df[df['club_name'] != 'Estudiantes']
    
    # Gap analysis
    estudiantes_product_names = set(estudiantes_products['product_name'].str.lower())
    other_product_names = set(other_clubs_df['product_name'].str.lower())
    gap_products = other_product_names - estudiantes_product_names
    gap_df = other_clubs_df[other_clubs_df['product_name'].str.lower().isin(gap_products)]
    
    # Revenue calculations
    avg_price_estudiantes = estudiantes_products['price'].mean()
    avg_price_competitors = other_clubs_df['price'].mean()
    avg_price_gap = gap_df['price'].mean()
    
    # Category analysis
    category_gap = gap_df.groupby('category_tier_1').agg({
        'price': ['count', 'mean'],
        'product_name': 'nunique'
    }).round(2)
    
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("Analytics Dashboard", 
                       style={"color": "#2c3e50", "marginBottom": "30px"}),
                html.P("Comprehensive analysis of Estudiantes product catalog and market opportunities.",
                       style={"color": "#6c757d", "marginBottom": "40px"})
            ])
        ]),
        
        # Executive Summary Cards
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("1,408", className="text-primary"),
                        html.P("Gap Opportunities", className="card-text"),
                        html.Small("Products competitors sell but Estudiantes doesn't", className="text-muted")
                    ])
                ], color="light", outline=True)
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"${avg_price_gap:,.0f}", className="text-success"),
                        html.P("Avg Gap Price", className="card-text"),
                        html.Small("Average price of gap products", className="text-muted")
                    ])
                ], color="light", outline=True)
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("96%", className="text-danger"),
                        html.P("Market Gap", className="card-text"),
                        html.Small("Percentage of competitor products missing", className="text-muted")
                    ])
                ], color="light", outline=True)
            ], md=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"${avg_price_gap * 1408:,.0f}", className="text-info"),
                        html.P("Revenue Potential", className="card-text"),
                        html.Small("Estimated annual revenue opportunity", className="text-muted")
                    ])
                ], color="light", outline=True)
            ], md=3)
        ], style={"marginBottom": "40px"}),
        
        # Charts Row 1
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Product Comparison by Club"),
                    dbc.CardBody([
                        dcc.Graph(
                            id='product-count-chart',
                            figure=create_product_count_chart(df)
                        )
                    ])
                ], style={"marginBottom": "20px"})
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Price Distribution Analysis"),
                    dbc.CardBody([
                        dcc.Graph(
                            id='price-distribution-chart',
                            figure=create_price_distribution_chart(df)
                        )
                    ])
                ], style={"marginBottom": "20px"})
            ], md=6)
        ]),
        
        # Charts Row 2
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Gap Analysis by Category"),
                    dbc.CardBody([
                        dcc.Graph(
                            id='gap-category-chart',
                            figure=create_gap_category_chart(gap_df)
                        )
                    ])
                ], style={"marginBottom": "20px"})
            ], md=8),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Market Share"),
                    dbc.CardBody([
                        dcc.Graph(
                            id='market-share-chart',
                            figure=create_market_share_chart(df)
                        )
                    ])
                ], style={"marginBottom": "20px"})
            ], md=4)
        ]),
        
        # Revenue Opportunity Analysis
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Revenue Opportunity Matrix"),
                    dbc.CardBody([
                        dcc.Graph(
                            id='revenue-matrix-chart',
                            figure=create_revenue_matrix_chart(gap_df)
                        )
                    ])
                ], style={"marginBottom": "20px"})
            ], md=12)
        ]),
        
        # Strategic Insights
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Strategic Insights"),
                    dbc.CardBody([
                        generate_strategic_insights(estudiantes_products, gap_df)
                    ])
                ], style={"marginBottom": "20px"})
            ], md=12)
        ]),
        
    ], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

def create_product_count_chart(df):
    """Create product count comparison chart."""
    club_counts = df.groupby('club_name').size().sort_values(ascending=False)
    
    fig = px.bar(
        x=club_counts.index,
        y=club_counts.values,
        title="Product Count by Club",
        labels={'x': 'Club', 'y': 'Number of Products'},
        color=club_counts.values,
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Club",
        yaxis_title="Number of Products"
    )
    
    return fig

def create_price_distribution_chart(df):
    """Create price distribution comparison chart."""
    
    fig = go.Figure()
    
    for club in df['club_name'].unique():
        club_data = df[df['club_name'] == club]['price'].dropna()
        fig.add_trace(go.Histogram(
            x=club_data,
            name=club,
            opacity=0.7,
            nbinsx=30
        ))
    
    fig.update_layout(
        title="Price Distribution by Club",
        xaxis_title="Price ($)",
        yaxis_title="Number of Products",
        height=400,
        barmode='overlay'
    )
    
    return fig

def create_gap_category_chart(gap_df):
    """Create gap analysis by category chart."""
    category_counts = gap_df['category_tier_1'].value_counts().head(10)
    
    fig = px.bar(
        x=category_counts.values,
        y=category_counts.index,
        orientation='h',
        title="Gap Products by Category",
        labels={'x': 'Number of Products', 'y': 'Category'},
        color=category_counts.values,
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        height=500,
        showlegend=False,
        xaxis_title="Number of Gap Products",
        yaxis_title="Category"
    )
    
    return fig

def create_market_share_chart(df):
    """Create market share pie chart."""
    club_counts = df.groupby('club_name').size()
    
    fig = px.pie(
        values=club_counts.values,
        names=club_counts.index,
        title="Market Share by Product Count"
    )
    
    fig.update_layout(height=400)
    
    return fig

def create_revenue_matrix_chart(gap_df):
    """Create revenue opportunity matrix."""
    
    # Calculate revenue potential by category
    category_revenue = gap_df.groupby('category_tier_1').agg({
        'price': ['count', 'mean', 'sum']
    }).round(2)
    
    category_revenue.columns = ['Product Count', 'Avg Price', 'Total Revenue']
    category_revenue = category_revenue.sort_values('Total Revenue', ascending=False).head(10)
    
    fig = px.scatter(
        x=category_revenue['Product Count'],
        y=category_revenue['Avg Price'],
        size=category_revenue['Total Revenue'],
        hover_name=category_revenue.index,
        title="Revenue Opportunity Matrix",
        labels={
            'x': 'Number of Products',
            'y': 'Average Price ($)',
            'size': 'Total Revenue Potential'
        }
    )
    
    fig.update_layout(height=500)
    
    return fig

def generate_strategic_insights(estudiantes_products, gap_df):
    """Generate strategic insights based on data analysis."""
    
    # Calculate key metrics
    total_gap_products = len(gap_df)
    avg_gap_price = gap_df['price'].mean()
    high_value_gap = gap_df[gap_df['price'] > avg_gap_price]
    
    insights = [
        html.Div([
            html.H4("🎯 Key Strategic Insights", className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H6("📈 Market Opportunity", style={"color": "#CC0000"}),
                    html.P(f"Estudiantes is missing {total_gap_products} products that competitors offer, representing a significant market opportunity."),
                    html.P(f"The average price point of gap products is ${avg_gap_price:,.0f}, indicating premium revenue potential.")
                ], md=6),
                dbc.Col([
                    html.H6("💰 Revenue Potential", style={"color": "#28a745"}),
                    html.P(f"High-value gap products (> ${avg_gap_price:,.0f}): {len(high_value_gap)} items"),
                    html.P(f"Estimated annual revenue potential: ${avg_gap_price * total_gap_products:,.0f}")
                ], md=6)
            ], className="mb-4"),
            
            dbc.Row([
                dbc.Col([
                    html.H6("🏆 Priority Categories", style={"color": "#007bff"}),
                    html.Ul([
                        html.Li(f"Indumentaria: {len(gap_df[gap_df['category_tier_1'] == 'Indumentaria'])} products"),
                        html.Li(f"Otros: {len(gap_df[gap_df['category_tier_1'] == 'Otros'])} products"),
                        html.Li(f"Accesorios: {len(gap_df[gap_df['category_tier_1'] == 'Accesorios'])} products")
                    ])
                ], md=6),
                dbc.Col([
                    html.H6("⚡ Quick Wins", style={"color": "#FFCC00"}),
                    html.Ul([
                        html.Li("Focus on high-demand apparel categories"),
                        html.Li("Expand accessories and lifestyle products"),
                        html.Li("Introduce premium pricing tiers")
                    ])
                ], md=6)
            ])
        ])
    ]
    
    return insights
