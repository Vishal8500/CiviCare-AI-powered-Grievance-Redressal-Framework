# dashboard_interactive.py
import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from database import get_connection, DB_NAME
import requests

# --- Page Config ---
st.set_page_config(
    page_title="Civic Grievance Collector Dashboard",
    layout="wide",
)

st.markdown("""
    <style>
    .big-title { font-size: 36px; font-weight: 800; color: #e0e0e0; }
    .metric-box { background: #111827; padding: 15px; border-radius: 10px; text-align: center; }
    .metric-label { color: #9ca3af; font-size: 14px; }
    .metric-value { color: #facc15; font-size: 28px; font-weight: 700; }
    .grievance-card {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
    }
    .grievance-card:hover {
        border-color: #f59e0b;
        background-color: #111827;
    }
    </style>
""", unsafe_allow_html=True)

# --- Database Fetch ---
def get_all_grievances():
    conn = get_connection(DB_NAME)
    if conn is None:
        st.error("❌ Database connection failed.")
        return pd.DataFrame()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM grievances ORDER BY created_at DESC")
    data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(data)

# --- Format Data ---
def prepare_data(df):
    if df.empty:
        return df
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['Date'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    df['Photo Status'] = df['photo_file_id'].apply(lambda x: 'Yes' if x not in [None, '', 'skipped'] else 'No')
    df['Extra Data'] = df['additional_data'].fillna('N/A')
    df.rename(columns={'issue': 'Issue Type', 'location': 'Location', 'status': 'Status'}, inplace=True)
    return df

# --- Load Data ---
df = get_all_grievances()
if df.empty:
    st.warning("No grievance data available.")
    st.stop()

df = prepare_data(df)

# --- Title ---
st.markdown('<div class="big-title">🏛️ Civic Grievance Collector Dashboard</div>', unsafe_allow_html=True)
st.markdown("#### Empowering smarter governance through citizen feedback")

# --- Summary Metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"<div class='metric-box'><div class='metric-label'>Total Grievances</div><div class='metric-value'>{len(df)}</div></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-box'><div class='metric-label'>Pending Issues</div><div class='metric-value'>{df['Status'].eq('Pending').sum()}</div></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-box'><div class='metric-label'>With Photos</div><div class='metric-value'>{df['Photo Status'].eq('Yes').sum()}</div></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='metric-box'><div class='metric-label'>Unique Locations</div><div class='metric-value'>{df['Location'].nunique()}</div></div>", unsafe_allow_html=True)

st.divider()

# --- Interactive Filters ---
st.sidebar.header("🔍 Filters")
selected_issue = st.sidebar.multiselect("Issue Type", sorted(df['Issue Type'].unique()))
selected_status = st.sidebar.multiselect("Status", sorted(df['Status'].unique()))
selected_location = st.sidebar.multiselect("Location", sorted(df['Location'].unique()))

filtered_df = df.copy()
if selected_issue:
    filtered_df = filtered_df[filtered_df['Issue Type'].isin(selected_issue)]
if selected_status:
    filtered_df = filtered_df[filtered_df['Status'].isin(selected_status)]
if selected_location:
    filtered_df = filtered_df[filtered_df['Location'].isin(selected_location)]

# --- Charts Section ---
st.subheader("📊 Issue & Location Analytics")

chart_col1, chart_col2 = st.columns([2, 2])

with chart_col1:
    issue_chart = px.bar(
        filtered_df.groupby('Issue Type').size().reset_index(name='Count'),
        y='Issue Type', x='Count', orientation='h',
        title="Grievances by Issue Type", color='Count', color_continuous_scale='Blues'
    )
    issue_chart.update_layout(height=350, xaxis_title='Count', yaxis_title=None)
    st.plotly_chart(issue_chart, use_container_width=True)

with chart_col2:
    loc_chart = px.bar(
        filtered_df.groupby('Location').size().reset_index(name='Count').sort_values('Count', ascending=False).head(10),
        y='Location', x='Count', orientation='h',
        title="Top 10 Reported Locations", color='Count', color_continuous_scale='Oranges'
    )
    loc_chart.update_layout(height=350, xaxis_title='Count', yaxis_title=None)
    st.plotly_chart(loc_chart, use_container_width=True)

# --- Map Visualization (if coordinates exist) ---
if {'latitude', 'longitude'}.issubset(df.columns):
    st.subheader("🗺️ Issue Heatmap by Location")
    map_fig = px.density_mapbox(
        df, lat='latitude', lon='longitude', z=None,
        hover_name='Issue Type', hover_data=['Location', 'Status'],
        radius=20, center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
        mapbox_style='carto-darkmatter', zoom=10, color_continuous_scale="Inferno"
    )
    st.plotly_chart(map_fig, use_container_width=True)

# --- Interactive Grievance List ---
st.subheader("🧾 Recent Grievances")
for _, row in filtered_df.head(10).iterrows():
    with st.container():
        st.markdown(f"""
        <div class='grievance-card'>
            <h4>🆔 #{row['id']} — {row['Issue Type']}</h4>
            <b>📍 Location:</b> {row['Location']}  
            <b>👤 User:</b> {row['username']}  
            <b>📅 Date:</b> {row['Date']}  
            <b>📦 Status:</b> <span style='color:#facc15'>{row['Status']}</span><br><br>
            <b>🗣️ Complaint:</b> {row['grievance']}<br>
            <b>🧠 AI Reply:</b> {row['ai_reply'] or 'No AI response'}<br>
        </div>
        """, unsafe_allow_html=True)
