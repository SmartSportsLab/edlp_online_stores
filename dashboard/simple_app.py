#!/usr/bin/env python3
"""
Simple Club Store Dashboard
Works with data/master_categorized_corrected.csv (same layout as the main app).
"""

import os
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Load data (same source as main app: Submission/master_data.xlsx when present)
_DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
_CLUB_STORES_ROOT = os.path.normpath(os.path.join(_DASHBOARD_DIR, '..'))
_PFM_PARENT = os.path.normpath(os.path.join(_DASHBOARD_DIR, '..', '..'))


def _default_master_xlsx_path():
    candidates = [
        os.path.join(_PFM_PARENT, 'Submission', 'master_data.xlsx'),
        os.path.join(_CLUB_STORES_ROOT, 'Submission', 'master_data.xlsx'),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return candidates[-1]


MASTER_DATA_XLSX = os.environ.get('CLUB_STORES_MASTER_DATA') or _default_master_xlsx_path()
DATA_CSV_FALLBACK = os.path.normpath(os.path.join(_DASHBOARD_DIR, '..', 'data', 'master_categorized_corrected.csv'))
if os.path.isfile(MASTER_DATA_XLSX):
    df = pd.read_excel(MASTER_DATA_XLSX, sheet_name=0, engine='openpyxl')
else:
    df = pd.read_csv(DATA_CSV_FALLBACK)
df.columns = [str(c).strip() for c in df.columns]

# Clean data
df = df.dropna(subset=['price'])
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df = df.dropna(subset=['price'])

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Club Store Intelligence Dashboard"

# Define layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Club Store Intelligence Dashboard", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            html.H3("Market Overview"),
            html.P(f"Total Products: {len(df)}"),
            html.P(f"Clubs Analyzed: {df['club_name'].nunique()}"),
            html.P(f"Categories: {df['category_tier_1'].nunique()}")
        ], width=3),
        
        dbc.Col([
            dcc.Graph(id='product-count-chart')
        ], width=9)
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='category-distribution-chart')
        ], width=6),
        
        dbc.Col([
            dcc.Graph(id='pricing-analysis-chart')
        ], width=6)
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='gender-distribution-chart')
        ], width=6),
        
        dbc.Col([
            dcc.Graph(id='women-market-analysis')
        ], width=6)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.H3("Club Details"),
            dcc.Dropdown(
                id='club-dropdown',
                options=[{'label': club, 'value': club} for club in df['club_name'].unique()],
                value=df['club_name'].unique()[0],
                clearable=False
            ),
            html.Div(id='club-details')
        ], width=12)
    ])
], fluid=True)

# Callbacks
@app.callback(
    Output('product-count-chart', 'figure'),
    Input('club-dropdown', 'value')
)
def update_product_count(selected_club):
    club_counts = df['club_name'].value_counts().sort_values(ascending=False)
    
    fig = go.Figure(data=[
        go.Bar(x=club_counts.index, y=club_counts.values)
    ])
    
    fig.update_layout(
        title="Product Count by Club",
        xaxis_title="Club",
        yaxis_title="Number of Products",
        height=400
    )
    
    return fig

@app.callback(
    Output('category-distribution-chart', 'figure'),
    Input('club-dropdown', 'value')
)
def update_category_distribution(selected_club):
    if selected_club:
        filtered_df = df[df['club_name'] == selected_club]
        title = f"Category Distribution - {selected_club}"
    else:
        filtered_df = df
        title = "Category Distribution - All Clubs"
    
    category_counts = filtered_df['category_tier_1'].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(labels=category_counts.index, values=category_counts.values)
    ])
    
    fig.update_layout(
        title=title,
        height=400
    )
    
    return fig

@app.callback(
    Output('pricing-analysis-chart', 'figure'),
    Input('club-dropdown', 'value')
)
def update_pricing_analysis(selected_club):
    if selected_club:
        filtered_df = df[df['club_name'] == selected_club]
        title = f"Price Distribution - {selected_club}"
    else:
        filtered_df = df
        title = "Price Distribution - All Clubs"
    
    fig = go.Figure(data=[
        go.Histogram(x=filtered_df['price'], nbinsx=30)
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Price (ARS)",
        yaxis_title="Number of Products",
        height=400
    )
    
    return fig

@app.callback(
    Output('gender-distribution-chart', 'figure'),
    Input('club-dropdown', 'value')
)
def update_gender_distribution(selected_club):
    if selected_club:
        filtered_df = df[df['club_name'] == selected_club]
        title = f"Gender Distribution - {selected_club}"
    else:
        filtered_df = df
        title = "Gender Distribution - All Clubs"
    
    gender_counts = filtered_df['gender'].value_counts()
    
    fig = go.Figure(data=[
        go.Bar(x=gender_counts.index, y=gender_counts.values)
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="Gender",
        yaxis_title="Number of Products",
        height=400
    )
    
    return fig

@app.callback(
    Output('women-market-analysis', 'figure'),
    Input('club-dropdown', 'value')
)
def update_women_market_analysis(selected_club):
    # Women's market analysis
    womens_df = df[df['gender'] == 'mujer']
    club_womens = womens_df['club_name'].value_counts()
    club_total = df['club_name'].value_counts()
    
    womens_percentages = []
    for club in club_total.index:
        womens_count = club_womens.get(club, 0)
        total_count = club_total[club]
        percentage = (womens_count / total_count) * 100
        womens_percentages.append(percentage)
    
    fig = go.Figure(data=[
        go.Bar(x=club_total.index, y=womens_percentages)
    ])
    
    fig.update_layout(
        title="Women's Market Penetration by Club",
        xaxis_title="Club",
        yaxis_title="Women's Products (%)",
        height=400
    )
    
    # Add industry target line
    fig.add_hline(y=15, line_dash="dash", line_color="red", annotation_text="Industry Target (15%)")
    
    return fig

@app.callback(
    Output('club-details', 'children'),
    Input('club-dropdown', 'value')
)
def update_club_details(selected_club):
    if not selected_club:
        return html.Div("Select a club to see details")
    
    club_df = df[df['club_name'] == selected_club]
    
    # Calculate metrics
    total_products = len(club_df)
    avg_price = club_df['price'].mean()
    womens_products = len(club_df[club_df['gender'] == 'mujer'])
    womens_percentage = (womens_products / total_products) * 100
    
    # Top categories
    top_categories = club_df['category_tier_1'].value_counts().head(3)
    
    details = [
        html.H4(f"{selected_club} Details"),
        html.P(f"Total Products: {total_products}"),
        html.P(f"Average Price: ${avg_price:,.0f}"),
        html.P(f"Women's Products: {womens_products} ({womens_percentage:.1f}%)"),
        html.H5("Top Categories:"),
        html.Ul([html.Li(f"{cat}: {count} products") for cat, count in top_categories.items()])
    ]
    
    return details

if __name__ == '__main__':
    app.run(debug=True, port=8051)
