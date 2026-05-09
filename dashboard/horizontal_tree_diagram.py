"""
Horizontal Tree Diagram - Estudiantes Navigation Structure
Left-to-right tree diagram as shown in user's drawing
"""

import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import os

def load_navigation_data():
    """Load and prepare navigation data"""
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', 'club_navigation_categories.csv'))
    df = df.fillna('')
    return df

def create_horizontal_tree_diagram(club_name='Estudiantes', tier_filter='all'):
    """Create VERTICAL tree diagram for specified club with optional tier filtering"""
    df = load_navigation_data()
    
    # Filter for selected club
    club_data = df[df['club_name'] == club_name].copy()
    
    # Apply tier filtering if specified
    if tier_filter != 'all':
        tier_num = int(tier_filter)
        if tier_num == 1:
            # Only show Level 1 categories
            club_data = club_data[club_data['nav_level_1'] != '']
        elif tier_num == 2:
            # Only show paths that have Level 2
            club_data = club_data[(club_data['nav_level_1'] != '') & (club_data['nav_level_2'] != '')]
        elif tier_num == 3:
            # Only show paths that have Level 3
            club_data = club_data[(club_data['nav_level_1'] != '') & (club_data['nav_level_2'] != '') & (club_data['nav_level_3'] != '')]
        elif tier_num == 4:
            # Only show paths that have Level 4
            club_data = club_data[(club_data['nav_level_1'] != '') & (club_data['nav_level_2'] != '') & (club_data['nav_level_3'] != '') & (club_data['nav_level_4'] != '')]
    
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
            height=600,
            xaxis={'visible': False},
            yaxis={'visible': False}
        )
        return fig
    
    # Build VERTICAL tree structure
    nodes = []
    edges_x = []
    edges_y = []
    
    # Start with club name as root (top center)
    nodes.append((0, 18, club_name, 25, '#2c3e50'))  # x, y, label, size, color - increased Y and size
    
    # Process each navigation path
    x_positions = {}
    current_x = 0
    x_spacing = 18.0  # Significantly increased for better horizontal spacing
    
    # Get unique level 1 categories
    level_1_categories = club_data[club_data['nav_level_1'] != '']['nav_level_1'].unique()
    
    for i, level_1 in enumerate(level_1_categories):
        if pd.notna(level_1) and level_1.strip():
            # Level 1 node - spread horizontally at y=14
            level_1_x = i * x_spacing - (len(level_1_categories) * x_spacing) / 2
            nodes.append((level_1_x, 14, level_1.upper(), 18, get_category_color(level_1)))
            
            # Edge from club to level 1
            edges_x.extend([0, level_1_x, None])
            edges_y.extend([18, 14, None])
            
            # Get level 2 categories for this level 1
            level_2_data = club_data[club_data['nav_level_1'] == level_1]
            level_2_categories = level_2_data[level_2_data['nav_level_2'] != '']['nav_level_2'].unique()
            
            for j, level_2 in enumerate(level_2_categories):
                if pd.notna(level_2) and level_2.strip():
                    # Level 2 node - increased spacing to 8.0
                    level_2_x = level_1_x + (j - len(level_2_categories)/2) * 8.0
                    nodes.append((level_2_x, 10, level_2, 15, get_category_color(level_1, 0.8)))
                    
                    # Edge from level 1 to level 2
                    edges_x.extend([level_1_x, level_2_x, None])
                    edges_y.extend([14, 10, None])
                    
                    # Get level 3 categories for this level 2
                    level_3_data = level_2_data[level_2_data['nav_level_2'] == level_2]
                    level_3_categories = level_3_data[level_3_data['nav_level_3'] != '']['nav_level_3'].unique()
                    
                    for k, level_3 in enumerate(level_3_categories):
                        if pd.notna(level_3) and level_3.strip():
                            # Level 3 node - increased spacing to 5.5
                            level_3_x = level_2_x + (k - len(level_3_categories)/2) * 5.5
                            nodes.append((level_3_x, 6, level_3, 12, get_category_color(level_1, 0.6)))
                            
                            # Edge from level 2 to level 3
                            edges_x.extend([level_2_x, level_3_x, None])
                            edges_y.extend([10, 6, None])
                            
                            # Get level 4 categories for this level 3
                            level_4_data = level_3_data[level_3_data['nav_level_3'] == level_3]
                            level_4_categories = level_4_data[level_4_data['nav_level_4'] != '']['nav_level_4'].unique()
                            
                            for l, level_4 in enumerate(level_4_categories):
                                if pd.notna(level_4) and level_4.strip():
                                    # Level 4 node - increased spacing to 4.0
                                    level_4_x = level_3_x + (l - len(level_4_categories)/2) * 4.0
                                    nodes.append((level_4_x, 2, level_4, 10, get_category_color(level_1, 0.4)))
                                    
                                    # Edge from level 3 to level 4
                                    edges_x.extend([level_3_x, level_4_x, None])
                                    edges_y.extend([6, 2, None])
    
    # Create the figure
    fig = go.Figure()
    
    # Add edges (lines)
    if edges_x:
        fig.add_trace(go.Scatter(
            x=edges_x,
            y=edges_y,
            mode='lines',
            line=dict(width=2, color='#cbd5e0'),
            hoverinfo='none',
            showlegend=False
        ))
    
    # Add nodes
    if nodes:
        node_x = [node[0] for node in nodes]
        node_y = [node[1] for node in nodes]
        node_text = [node[2] for node in nodes]
        node_sizes = [node[3] for node in nodes]
        node_colors = [node[4] for node in nodes]
        
        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            text=node_text,
            textposition='top center',
            textfont=dict(color='black', size=10, family='Arial Black, sans-serif', weight='bold'),
            hovertemplate='<b>%{text}</b><extra></extra>',
            showlegend=False
        ))
    
    # Update layout for VERTICAL orientation
    fig.update_layout(
        title=f'{club_name} Navigation Structure - Vertical Tree Diagram',
        height=900,  # Increased height to fill more space
        showlegend=False,
        xaxis=dict(
            visible=False,
            range=[-90, 90]  # Significantly increased for wider spacing
        ),
        yaxis=dict(
            visible=False,
            range=[0, 20]  # Increased vertical range to fill height
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=50, l=20, r=20, b=20)  # Reduced margins to maximize space
    )
    
    return fig

def get_category_color(category_name, opacity=1.0):
    """Get color for category"""
    color_map = {
        'RUGE': '#CC0000',
        'JUGADOR': '#45B7D1', 
        'LA UTILERÍA': '#FF6B6B',
        'MERCHANDISING': '#4ECDC4',
        'Tienda Oficial': '#2c3e50',
        'Indumentaria': '#28a745',
        'Accesorios': '#ffc107',
        'Calzado': '#6f42c1',
        'Hogar': '#fd7e14'
    }
    
    base_color = color_map.get(category_name, '#6c757d')
    
    # Convert hex to rgba with opacity
    if opacity < 1.0:
        hex_color = base_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f'rgba({r}, {g}, {b}, {opacity})'
    
    return base_color

def create_horizontal_tree_layout():
    """Create layout for horizontal tree diagram page"""
    
    # Get available clubs
    df = load_navigation_data()
    available_clubs = sorted(df['club_name'].unique())
    
    # Create initial tree diagram (Estudiantes as default)
    initial_fig = create_horizontal_tree_diagram('Estudiantes', tier_filter='all')
    
    layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("🌳 Horizontal Navigation Tree", 
                       className="text-center mb-4",
                       style={'color': '#2c3e50'}),
                
                html.P("Left-to-right tree diagram showing navigation hierarchy structure",
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
                                    id='horizontal-tree-club-selector',
                                    options=[{'label': club, 'value': club} for club in available_clubs],
                                    value='Estudiantes',  # Default to Estudiantes
                                    clearable=False,
                                    className="mb-3",
                                    style={'width': '300px', 'color': '#333', 'backgroundColor': '#fff', 'borderRadius': '6px'}
                                )
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Navigation Stats:", className="form-label fw-bold"),
                                html.Div(id='horizontal-tree-stats', className="mb-3")
                            ], width=8)
                        ])
                    ])
                ], color="light")
            ], width=12)
        ], className="mb-4"),
        
        # Main tree diagram
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(
                            figure=initial_fig,
                            id='horizontal-tree-diagram',
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                                'toImageButtonOptions': {
                                    'format': 'png',
                                    'filename': 'horizontal_navigation_tree',
                                    'height': 600,  # Updated to match new height
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
                        html.H5("🌳 Tree Diagram Features", className="card-title"),
                        html.P("Horizontal tree visualization with:"),
                        html.Ul([
                            html.Li("📐 Left-to-right flow (as requested)"),
                            html.Li("🔗 Connected branches showing hierarchy"),
                            html.Li("🎨 Color-coded by category"),
                            html.Li("📏 Spaced for clarity"),
                            html.Li("👆 Interactive hover information")
                        ])
                    ])
                ], color="info", outline=True)
            ], width=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("📊 Navigation Insights", className="card-title"),
                        html.P("Clear visualization of:"),
                        html.Ul([
                            html.Li("🏷️ Category relationships"),
                            html.Li("🔀 Navigation paths"),
                            html.Li("📐 Structure complexity"),
                            html.Li("🎯 Category organization")
                        ])
                    ])
                ], color="success", outline=True)
            ], width=6)
        ], className="mb-4"),
        
    ], fluid=True)
    
    return layout

# Register callbacks
@callback(
    [Output('horizontal-tree-diagram', 'figure'),
     Output('horizontal-tree-stats', 'children')],
    [Input('horizontal-tree-club-selector', 'value')]
)
def update_horizontal_tree(selected_club):
    """Update horizontal tree diagram when club is selected"""
    
    # Create new tree diagram
    fig = create_horizontal_tree_diagram(selected_club)
    
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
    # Test the tree diagram creation
    fig = create_horizontal_tree_diagram('Estudiantes', tier_filter='all')
    fig.show()
