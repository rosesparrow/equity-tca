"""
Equity TCA Dashboard
Streamlit app for post-trade execution quality analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Page configuration
st.set_page_config(
    page_title="TCA Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 10px;
        border-bottom: 3px solid #1f77b4;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title("Equity Trading Cost Analysis")
st.markdown("Post-trade execution quality analysis with IS and interval VWAP benchmarking.")

# Sidebar
st.sidebar.header("Controls")

# File upload
uploaded_file = st.sidebar.file_uploader(
    "Upload Trade Data (CSV)",
    type=['csv'],
    help="Upload simulated_trades.csv or simulated_trades_with_analysis.csv"
)

# Load data
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        try:
            df = pd.read_csv('simulated_trades.csv')
        except FileNotFoundError:
            st.error("No trade data found. Please upload a CSV or run the simulation notebook.")
            return None
    
    # Convert datetime columns
    for col in ['ArrivalTime', 'ExecStartTime', 'ExecEndTime', 'Date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    return df

trades = load_data(uploaded_file)

if trades is None:
    st.stop()

# Sidebar filters
st.sidebar.markdown("---")
st.sidebar.header("Filters")

# Date range
min_date = trades['Date'].min().date()
max_date = trades['Date'].max().date()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Strategy filter
strategies = ['All'] + sorted(trades['Strategy'].unique().tolist())
selected_strategies = st.sidebar.multiselect(
    "Execution Strategy",
    options=strategies,
    default=['All']
)

# Ticker filter
tickers = ['All'] + sorted(trades['Ticker'].unique().tolist())
selected_tickers = st.sidebar.multiselect(
    "Tickers",
    options=tickers,
    default=['All']
)

# Side filter
sides = ['All', 'Buy', 'Sell']
selected_side = st.sidebar.selectbox("Trade Side", sides)

# Apply filters
filtered_trades = trades.copy()

if len(date_range) == 2:
    filtered_trades = filtered_trades[
        (filtered_trades['Date'].dt.date >= date_range[0]) &
        (filtered_trades['Date'].dt.date <= date_range[1])
    ]

if 'All' not in selected_strategies and len(selected_strategies) > 0:
    filtered_trades = filtered_trades[filtered_trades['Strategy'].isin(selected_strategies)]

if 'All' not in selected_tickers and len(selected_tickers) > 0:
    filtered_trades = filtered_trades[filtered_trades['Ticker'].isin(selected_tickers)]

if selected_side != 'All':
    filtered_trades = filtered_trades[filtered_trades['Side'] == selected_side]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Showing {len(filtered_trades)} of {len(trades)} orders**")

if len(filtered_trades) == 0:
    st.warning("⚠️ No orders match the selected filters.")
    st.stop()

# Key metrics
st.header("Executive Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_is = filtered_trades['IS_Bps'].mean()
    st.metric(
        "Avg Implementation Shortfall",
        f"{avg_is:.2f} bps",
        delta=f"{avg_is - 5.0:.2f} vs target",
        delta_color="inverse"
    )

with col2:
    total_cost = filtered_trades['TotalCost_Dollars'].sum()
    st.metric(
        "Total Transaction Cost",
        f"${total_cost:,.0f}"
    )

with col3:
    beat_vwap = (filtered_trades['VsIntervalVWAP_Bps'] < 0).sum()
    beat_pct = (beat_vwap / len(filtered_trades)) * 100
    st.metric(
        "Orders Beat Interval VWAP",
        f"{beat_pct:.1f}%",
        delta=f"{beat_pct - 50:.1f}% vs benchmark"
    )

with col4:
    avg_duration = filtered_trades['ExecDurationMins'].mean()
    st.metric(
        "Avg Execution Duration",
        f"{avg_duration:.0f} mins"
    )

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Strategy Analysis",
    "Timing Analysis",
    "Venue Analysis",
    "Order Size Impact"
])

# Tab 1: Overview
with tab1:
    st.header("Portfolio Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # IS Distribution
        fig_is = px.histogram(
            filtered_trades,
            x='IS_Bps',
            nbins=30,
            title='Implementation Shortfall Distribution',
            labels={'IS_Bps': 'Implementation Shortfall (bps)'},
            color_discrete_sequence=['#1f77b4']
        )
        fig_is.add_vline(x=5, line_dash="dash", line_color="red",
                        annotation_text="Target (5 bps)")
        fig_is.add_vline(x=0, line_dash="dash", line_color="green",
                        annotation_text="Zero cost")
        fig_is.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_is, use_container_width=True)
    
    with col2:
        # Strategy Distribution
        strategy_dist = filtered_trades['Strategy'].value_counts()
        fig_strat = px.pie(
            values=strategy_dist.values,
            names=strategy_dist.index,
            title='Order Distribution by Strategy',
            color=strategy_dist.index,
            color_discrete_map={
                'Immediate': '#e74c3c',
                'VWAP': '#3498db',
                'VWAP-Dark': '#2ecc71',
                'Careful': '#9b59b6'
            }
        )
        fig_strat.update_layout(height=400)
        st.plotly_chart(fig_strat, use_container_width=True)
    
    # Execution characteristics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### Execution Stats")
        st.metric("Total Orders", f"{len(filtered_trades):,}")
        st.metric("Total Notional", f"${filtered_trades['NotionalValue'].sum():,.0f}")
        st.metric("Avg Order Size", f"{filtered_trades['Quantity'].mean():,.0f} shares")
    
    with col2:
        st.markdown("### Duration Stats")
        st.metric("Avg Duration", f"{filtered_trades['ExecDurationMins'].mean():.0f} mins")
        st.metric("Avg Fills per Order", f"{filtered_trades['NumFills'].mean():.1f}")
        st.metric("Max Duration", f"{filtered_trades['ExecDurationMins'].max():.0f} mins")
    
    with col3:
        st.markdown("### Performance")
        st.metric("Median IS", f"{filtered_trades['IS_Bps'].median():.2f} bps")
        st.metric("Std Dev IS", f"{filtered_trades['IS_Bps'].std():.2f} bps")
        st.metric("Best Execution", f"{filtered_trades['IS_Bps'].min():.2f} bps")

# Tab 2: Strategy Analysis
with tab2:
    st.header("Execution Strategy Performance")
    
    # Strategy comparison
    strategy_stats = filtered_trades.groupby('Strategy').agg({
        'OrderID': 'count',
        'IS_Bps': ['mean', 'median', 'std'],
        'VsIntervalVWAP_Bps': 'mean',
        'ExecDurationMins': 'mean',
        'NumFills': 'mean',
        'DarkPct': 'mean'
    }).round(2)
    
    strategy_stats.columns = ['Orders', 'Avg_IS', 'Median_IS', 'StdDev_IS',
                              'Avg_vs_VWAP', 'Avg_Duration', 'Avg_Fills', 'Avg_Dark_Pct']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Bar chart
        fig_strat_cost = go.Figure()
        
        colors = {'Immediate': '#e74c3c', 'VWAP': '#3498db', 
                 'VWAP-Dark': '#2ecc71', 'Careful': '#9b59b6'}
        
        for strategy in strategy_stats.index:
            fig_strat_cost.add_trace(go.Bar(
                x=[strategy],
                y=[strategy_stats.loc[strategy, 'Avg_IS']],
                name=strategy,
                marker_color=colors.get(strategy, '#95a5a6'),
                text=[f"{strategy_stats.loc[strategy, 'Avg_IS']:.2f}"],
                textposition='outside'
            ))
        
        fig_strat_cost.add_hline(y=5, line_dash="dash", line_color="red",
                                annotation_text="Target")
        fig_strat_cost.add_hline(y=0, line_dash="dash", line_color="green",
                                annotation_text="Zero cost")
        
        fig_strat_cost.update_layout(
            title='Average Implementation Shortfall by Strategy',
            yaxis_title='Implementation Shortfall (bps)',
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig_strat_cost, use_container_width=True)
    
    with col2:
        st.markdown("### Key Insights")
        best_strat = strategy_stats['Avg_IS'].idxmin()
        worst_strat = strategy_stats['Avg_IS'].idxmax()
        
        st.success(f"**Best:** {best_strat}")
        st.info(f"{strategy_stats.loc[best_strat, 'Avg_IS']:.2f} bps avg")
        
        st.error(f"**Worst:** {worst_strat}")
        st.info(f"{strategy_stats.loc[worst_strat, 'Avg_IS']:.2f} bps avg")
        
        savings = strategy_stats.loc[worst_strat, 'Avg_IS'] - strategy_stats.loc[best_strat, 'Avg_IS']
        st.warning(f"**Savings:** {savings:.2f} bps")
    
    # Detailed table
    st.markdown("### Strategy Statistics")
    st.dataframe(
        strategy_stats.style.background_gradient(cmap='RdYlGn_r', subset=['Avg_IS']),
        use_container_width=True
    )
    
    # Duration vs IS by strategy
    fig_dur = px.scatter(
        filtered_trades,
        x='ExecDurationMins',
        y='IS_Bps',
        color='Strategy',
        size='Quantity',
        hover_data=['Ticker', 'NumFills'],
        title='Execution Duration vs Cost (by Strategy)',
        color_discrete_map=colors
    )
    fig_dur.update_layout(height=450)
    st.plotly_chart(fig_dur, use_container_width=True)

# Tab 3: Timing Analysis
with tab3:
    st.header("Arrival Time Impact")
    
    # Session analysis
    session_stats = filtered_trades.groupby('ArrivalSession').agg({
        'OrderID': 'count',
        'IS_Bps': ['mean', 'median'],
        'VsIntervalVWAP_Bps': 'mean',
        'ExecDurationMins': 'mean'
    }).round(2)
    
    session_stats.columns = ['Orders', 'Avg_IS', 'Median_IS', 'Avg_vs_VWAP', 'Avg_Duration']
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Session performance
        session_order = ['Market Open', 'Mid-Day', 'Market Close']
        session_colors = {'Market Open': '#ff6b6b', 'Mid-Day': '#4ecdc4', 'Market Close': '#ffe66d'}
        
        plot_data = session_stats.reindex([s for s in session_order if s in session_stats.index])
        
        fig_session = go.Figure()
        for session in plot_data.index:
            fig_session.add_trace(go.Bar(
                x=[session],
                y=[plot_data.loc[session, 'Avg_IS']],
                marker_color=session_colors[session],
                text=[f"{plot_data.loc[session, 'Avg_IS']:.2f}"],
                textposition='outside'
            ))
        
        fig_session.add_hline(y=5, line_dash="dash", line_color="red")
        fig_session.update_layout(
            title='Execution Cost by Arrival Session',
            yaxis_title='Avg Implementation Shortfall (bps)',
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig_session, use_container_width=True)
    
    with col2:
        st.markdown("### Timing Insights")
        if len(session_stats) > 0:
            best_time = session_stats['Avg_IS'].idxmin()
            worst_time = session_stats['Avg_IS'].idxmax()
            
            st.success(f"**Best:** {best_time}")
            st.info(f"{session_stats.loc[best_time, 'Avg_IS']:.2f} bps")
            
            st.error(f"**Worst:** {worst_time}")
            st.info(f"{session_stats.loc[worst_time, 'Avg_IS']:.2f} bps")
            
            time_savings = session_stats.loc[worst_time, 'Avg_IS'] - session_stats.loc[best_time, 'Avg_IS']
            st.warning(f"**Opportunity:** {time_savings:.2f} bps")
    
    # Box plot by session
    fig_box = px.box(
        filtered_trades,
        x='ArrivalSession',
        y='IS_Bps',
        color='ArrivalSession',
        title='IS Distribution by Arrival Session',
        color_discrete_map=session_colors
    )
    fig_box.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_box, use_container_width=True)

# Tab 4: Venue Analysis
with tab4:
    st.header("Lit vs Dark Pool Performance")
    
    # Venue categories
    filtered_trades['VenueCategory'] = pd.cut(
        filtered_trades['DarkPct'],
        bins=[-1, 10, 30, 100],
        labels=['Mostly Lit (0-10%)', 'Mixed (10-30%)', 'Heavy Dark (>30%)']
    )
    
    venue_stats = filtered_trades.groupby('VenueCategory').agg({
        'OrderID': 'count',
        'IS_Bps': ['mean', 'std'],
        'PctOfADV': 'mean',
        'DarkPct': 'mean'
    }).round(2)
    
    venue_stats.columns = ['Orders', 'Avg_IS', 'StdDev_IS', 'Avg_Size_Pct', 'Avg_Dark_Pct']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Venue performance
        fig_venue = px.bar(
            venue_stats.reset_index(),
            x='VenueCategory',
            y='Avg_IS',
            title='Execution Cost by Venue Mix',
            color='Avg_IS',
            color_continuous_scale='RdYlGn_r'
        )
        fig_venue.add_hline(y=5, line_dash="dash", line_color="red")
        fig_venue.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_venue, use_container_width=True)
    
    with col2:
        # Dark % by strategy
        dark_by_strat = filtered_trades.groupby('Strategy')['DarkPct'].mean().sort_values()
        fig_dark = px.bar(
            x=dark_by_strat.values,
            y=dark_by_strat.index,
            orientation='h',
            title='Average Dark Pool Usage by Strategy',
            labels={'x': 'Dark Pool %', 'y': 'Strategy'},
            color=dark_by_strat.values,
            color_continuous_scale='Greens'
        )
        fig_dark.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_dark, use_container_width=True)
    
    # Venue stats table
    st.markdown("### Venue Statistics")
    st.dataframe(venue_stats, use_container_width=True)
    
    # Dark % vs Order Size
    fig_dark_size = px.scatter(
        filtered_trades,
        x='PctOfADV',
        y='DarkPct',
        color='IS_Bps',
        size='Quantity',
        hover_data=['Ticker', 'Strategy'],
        title='Dark Pool Usage vs Order Size',
        color_continuous_scale='RdYlGn_r'
    )
    fig_dark_size.update_layout(height=400)
    st.plotly_chart(fig_dark_size, use_container_width=True)

# Tab 5: Order Size Impact
with tab5:
    st.header("Order Size vs Execution Quality")
    
    # Size buckets
    filtered_trades['SizeBucket'] = pd.cut(
        filtered_trades['PctOfADV'],
        bins=[0, 0.005, 0.02, 0.05, 100],
        labels=['Small (<0.5bp)', 'Medium (0.5-2bp)', 'Large (2-5bp)', 'Very Large (>5bp)']
    )
    
    size_stats = filtered_trades.groupby('SizeBucket').agg({
        'OrderID': 'count',
        'IS_Bps': ['mean', 'median'],
        'ExecDurationMins': 'mean',
        'DarkPct': 'mean'
    }).round(2)
    
    size_stats.columns = ['Orders', 'Avg_IS', 'Median_IS', 'Avg_Duration', 'Avg_Dark_Pct']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Size vs cost
        fig_size = px.bar(
            size_stats.reset_index(),
            x='SizeBucket',
            y='Avg_IS',
            title='Execution Cost by Order Size',
            color='Avg_IS',
            color_continuous_scale='RdYlGn_r',
            text='Avg_IS'
        )
        fig_size.add_hline(y=5, line_dash="dash", line_color="red")
        fig_size.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_size.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_size, use_container_width=True)
    
    with col2:
        # Duration by size
        fig_dur_size = px.bar(
            size_stats.reset_index(),
            x='SizeBucket',
            y='Avg_Duration',
            title='Execution Duration by Order Size',
            color='Avg_Duration',
            color_continuous_scale='Blues',
            text='Avg_Duration'
        )
        fig_dur_size.update_traces(texttemplate='%{text:.0f} min', textposition='outside')
        fig_dur_size.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_dur_size, use_container_width=True)
    
    # Scatter: Size vs IS
    fig_scatter = px.scatter(
        filtered_trades,
        x='PctOfADV',
        y='IS_Bps',
        color='Strategy',
        size='Quantity',
        hover_data=['Ticker', 'ExecDurationMins'],
        title='Order Size vs Implementation Shortfall',
        labels={'PctOfADV': 'Order Size (% of ADV)', 'IS_Bps': 'Implementation Shortfall (bps)'}
    )
    
    # Trend line
    z = np.polyfit(filtered_trades['PctOfADV'], filtered_trades['IS_Bps'], 1)
    p = np.poly1d(z)
    x_trend = np.linspace(0, filtered_trades['PctOfADV'].max(), 100)
    fig_scatter.add_trace(go.Scatter(
        x=x_trend,
        y=p(x_trend),
        mode='lines',
        name=f'Trend: +{z[0]:.2f} bps per 1% ADV',
        line=dict(color='red', dash='dash')
    ))
    
    fig_scatter.update_layout(height=450)
    st.plotly_chart(fig_scatter, use_container_width=True)

# Footer - Export
st.markdown("---")
st.header("Export Data")

col1, col2 = st.columns(2)

with col1:
    csv = filtered_trades.to_csv(index=False)
    st.download_button(
        label="Download Filtered Orders (CSV)",
        data=csv,
        file_name=f"filtered_orders_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

with col2:
    # Summary report
    report = f"""
TCA SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total Orders: {len(filtered_trades):,}
Avg Implementation Shortfall: {filtered_trades['IS_Bps'].mean():.2f} bps
Total Cost: ${filtered_trades['TotalCost_Dollars'].sum():,.2f}
Orders Beat Interval VWAP: {(filtered_trades['VsIntervalVWAP_Bps'] < 0).sum() / len(filtered_trades) * 100:.1f}%

Best Strategy: {strategy_stats['Avg_IS'].idxmin()} ({strategy_stats['Avg_IS'].min():.2f} bps)
Best Arrival Time: {session_stats['Avg_IS'].idxmin() if len(session_stats) > 0 else 'N/A'}
Avg Execution Duration: {filtered_trades['ExecDurationMins'].mean():.0f} minutes
Avg Dark Pool Usage: {filtered_trades['DarkPct'].mean():.1f}%
"""
    
    st.download_button(
        label="Download Summary Report (TXT)",
        data=report,
        file_name=f"execution_summary_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain"
    )

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.markdown("Built with Streamlit and Plotly")
