"""
Tree Map Navigation Page - Plotly Implementation
Shows club navigation structures as interactive tree maps
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

# Load navigation data
def load_navigation_data():
    """Load and prepare navigation data"""
    df = pd.read_csv('../club_navigation_categories.csv')
    df = df.fillna('')
    return df

# Color schemes for each club
CLUB_COLORS = {
    'Estudiantes': {
        'RUGE': '#CC0000',
        'JUGADOR': '#45B7D1', 
        'LA UTILERÍA': '#FF6B6B',
        'MERCHANDISING': '#4ECDC4'
    },
    'River Plate': {
        'Tienda Oficial': '#FFFFFF',
        'Indumentaria': '#DC143C',
        'Accesorios': '#FFD700',
        'Hogar': '#FF6347',
        'Calzado': '#000000'
    },
    'Boca Juniors': {
        'Tienda Oficial': '#0047AB',
        'Indumentaria': '#FFD700',
        'Accesorios': '#FFD700',
        'Hogar': '#0047AB',
        'Calzado': '#000000'
    },
    'Racing Club': {
        'Tienda Oficial': '#0033A0',
        'INDUMENTARIA': '#0033A0',
        'ACCESORIOS': '#FFFFFF',
        'HOGAR': '#FFD700',
        'CALZADO': '#000000'
    },
    'Independiente': {
        'Tienda Oficial': '#FF0000',
        'colección': '#FF0000',
        'puma': '#FF0000'
    },
    'San Lorenzo': {
        'Tienda Oficial': '#0047AB',
        'accesorios': '#0047AB',
        'atomik': '#0047AB',
        'bazar': '#0047AB',
        'bebés': '#0047AB',
        'escolar': '#0047AB',
        'hogar y blanco': '#0047AB',
        'hombre': '#0047AB',
        'juvenil': '#0047AB',
        'marroquinería': '#0047AB',
        'mujer': '#0047AB',
        'niños': '#0047AB',
        'regalería': '#0047AB'
    }
}

def create_club_treemap(club_name):
    """Create tree map for specific club"""
    df = load_navigation_data()
    
    # Filter for selected club
    club_data = df[df['club_name'] == club_name].copy()
    
    if club_data.empty:
        # Create empty figure if no data
        fig = go.Figure()
        fig.add_annotation(
            text=f"No navigation data available for {club_name}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            title=f'{club_name} Navigation Structure',
            height=600
        )
        return fig
    
    # Prepare data for tree map
    tree_data = []
    
    # First, build the hierarchy structure
    hierarchy = {}
    
    for _, row in club_data.iterrows():
        # Build the hierarchy path
        path = []
        
        if row['nav_level_1'] and row['nav_level_1'].strip():
            path.append(row['nav_level_1'])
        if row['nav_level_2'] and row['nav_level_2'].strip():
            path.append(row['nav_level_2'])
        if row['nav_level_3'] and row['nav_level_3'].strip():
            path.append(row['nav_level_3'])
        if row['nav_level_4'] and row['nav_level_4'].strip():
            path.append(row['nav_level_4'])
        
        if len(path) > 0:  # Must have at least one level
            # Add to hierarchy
            current_level = hierarchy
            for i, level in enumerate(path):
                if level not in current_level:
                    current_level[level] = {} if i < len(path) - 1 else 1  # Leaf node gets value 1
                if i < len(path) - 1:
                    current_level = current_level[level]
    
    # Convert hierarchy to tree map data
    def flatten_hierarchy(hierarchy, parent_path=None):
        items = []
        for key, value in hierarchy.items():
            current_path = [parent_path] if parent_path else []
            current_path.append(key)
            
            if isinstance(value, dict):
                # This is a parent node, add it and recurse
                items.extend(flatten_hierarchy(value, key))
            else:
                # This is a leaf node
                data_row = {'value': value}
                for i, level in enumerate(current_path):
                    data_row[f'path_{i}'] = level
                data_row['level_1'] = current_path[0] if len(current_path) > 0 else ''
                items.append(data_row)
        return items
    
    tree_data = flatten_hierarchy(hierarchy)
    
    if not tree_data:
        # Create empty figure if no valid data
        fig = go.Figure()
        fig.add_annotation(
            text=f"No valid navigation structure for {club_name}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(
            title=f'{club_name} Navigation Structure',
            height=600
        )
        return fig
    
    # Convert to DataFrame
    tree_df = pd.DataFrame(tree_data)
    
    # Determine the path columns
    path_columns = [col for col in tree_df.columns if col.startswith('path_')]
    
    # Get color scheme for this club
    color_scheme = CLUB_COLORS.get(club_name, {})
    
    # Create tree map
    fig = px.treemap(
        tree_df,
        path=path_columns,
        values='value',
        title=f'{club_name} Navigation Structure',
        color='level_1',
        color_discrete_map=color_scheme
    )
    
    # Update hover template
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Navigation category<extra></extra>"
    )
    
    # Update layout
    fig.update_layout(
        height=500,  # Reduced from 600
        font=dict(size=12, color='black'),  # Changed to black
        title_font=dict(size=20, color='black'),  # Changed to black
        margin=dict(t=40, l=20, r=20, b=20),  # Reduced margins
        showlegend=False
    )
    
    return fig

def create_treemap_layout():
    """Create layout for tree map page"""
    
    # Get available clubs
    df = load_navigation_data()
    available_clubs = sorted(df['club_name'].unique())
    
    # Create initial tree map (Estudiantes as default)
    initial_fig = create_club_treemap('Estudiantes')
    
    layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("🌳 Club Navigation Tree Maps", 
                       className="text-center mb-4",
                       style={'color': '#2c3e50'}),
                
                html.P("Interactive visualization of each club's website navigation structure",
                       className="text-center text-muted mb-4"),
                
            ])
        ]),
        
        # Controls
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Select Club:", className="form-label fw-bold"),
                                dcc.Dropdown(
                                    id='club-selector-dropdown',
                                    options=[{'label': club, 'value': club} for club in available_clubs],
                                    value='Estudiantes',  # Default to Estudiantes
                                    clearable=False,
                                    className="mb-3",
                                    style={'width': '300px', 'color': '#333', 'backgroundColor': '#fff', 'borderRadius': '6px'}
                                )
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Navigation Stats:", className="form-label fw-bold"),
                                html.Div(id='navigation-stats', className="mb-3")
                            ], width=8)
                        ])
                    ])
                ], color="light")
            ], width=12)
        ], className="mb-4"),
        
        # Main tree map
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            figure=initial_fig,
                            id='club-treemap',
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
                                'toImageButtonOptions': {
                                    'format': 'png',
                                    'filename': 'club_navigation_treemap',
                                    'height': 500,  # Reduced from 600
                                    'width': 1200,
                                    'scale': 2
                                }
                            }
                        )
                    ])
                ], color="light")
            ], width=12)
        ], className="mb-3"),  # Reduced from mb-4
        
        # Info section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📊 Tree Map Features", className="card-title"),
                        html.P("Interactive navigation visualization with:"),
                        html.Ul([
                            html.Li("🖱️ Click on any section to zoom in"),
                            html.Li("👆 Right-click to zoom out"),
                            html.Li("🎨 Color-coded by category type"),
                            html.Li("💡 Hover for descriptions and examples"),
                            html.Li("📱 Responsive design for all devices")
                        ])
                    ])
                ], color="info", outline=True)
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("🔍 Navigation Insights", className="card-title"),
                        html.P("Compare how different clubs organize their products:"),
                        html.Ul([
                            html.Li("📊 Category complexity varies by club"),
                            html.Li("🏷️ Different naming conventions"),
                            html.Li("🎯 Unique category structures"),
                            html.Li("📈 Navigation depth analysis")
                        ])
                    ])
                ], color="success", outline=True)
            ], width=6)
        ], className="mb-4"),
        
        # Technical details
        dbc.Accordion([
            dbc.AccordionItem([
                html.H6("About Tree Maps"),
                html.P("Tree maps are hierarchical visualizations that show nested data as rectangles. The size represents the quantity, and colors represent different categories."),
                html.P("In this visualization:"),
                html.Ul([
                    html.Li("Each rectangle represents a navigation category"),
                    html.Li("Size shows the number of subcategories"),
                    html.Li("Colors indicate different category types"),
                    html.Li("Hierarchy shows the navigation structure")
                ])
            ], title="📚 Understanding Tree Maps"),
            
            dbc.AccordionItem([
                html.H6("Data Source"),
                html.P("Navigation data extracted from each club's official website store:"),
                html.Ul([
                    html.Li("Manual navigation structure analysis"),
                    html.Li("Category hierarchy mapping"),
                    html.Li("Product categorization alignment"),
                    html.Li("Cross-club comparison data")
                ])
            ], title="📋 Data Information")
        ], className="mt-4"),
        
    ], fluid=True)
    
    return layout

# Register callbacks
@callback(
    [Output('club-treemap', 'figure'),
     Output('navigation-stats', 'children')],
    [Input('club-selector-dropdown', 'value')]
)
def update_treemap(selected_club):
    """Update tree map when club is selected"""
    
    # Create new tree map
    fig = create_club_treemap(selected_club)
    
    # Calculate navigation stats
    df = load_navigation_data()
    club_data = df[df['club_name'] == selected_club]
    
    if not club_data.empty:
        # Calculate statistics
        total_paths = len(club_data)
        unique_level_1 = club_data['nav_level_1'].nunique()
        unique_level_2 = club_data['nav_level_2'].nunique()
        unique_level_3 = club_data['nav_level_3'].nunique()
        
        # Calculate average depth
        depths = []
        for _, row in club_data.iterrows():
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
        
        stats = html.Div([
            html.Span(f"📊 {total_paths} paths", className="badge bg-primary me-2"),
            html.Span(f"🏷️ {unique_level_1} top categories", className="badge bg-success me-2"),
            html.Span(f"📏 {avg_depth:.1f} avg depth", className="badge bg-info me-2"),
            html.Span(f"🔗 {unique_level_2 + unique_level_3} subcategories", className="badge bg-warning")
        ])
    else:
        stats = html.Span("No data available", className="badge bg-secondary")
    
    return fig, stats

if __name__ == "__main__":
    # Test the tree map creation
    fig = create_club_treemap('Estudiantes')
    fig.show()
