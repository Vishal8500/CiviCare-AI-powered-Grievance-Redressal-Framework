# ==========================================
# 🏛️ Civic Grievance Collector Dashboard (Enhanced with Priority Analytics)
# ==========================================
import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection, DB_NAME

# --- Page Config ---
st.set_page_config(
    page_title="Civic Grievance Collector Dashboard",
    layout="wide",
)

# --- CSS Styling ---
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

import base64

def convert_blob_to_image_html(blob_data):
    if not blob_data:
        return "❌ No Image"
    base64_str = base64.b64encode(blob_data).decode('utf-8')
    return f"<img src='data:image/jpeg;base64,{base64_str}' width='150' style='border-radius:10px'/>"


# --- Data Preparation ---
def prepare_data(df):
    if df.empty:
        return df
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['Date'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M')

    # ✅ Detect whether photo exists in BLOB
    df['Photo Status'] = df['photo'].apply(lambda x: 'Yes' if x not in [None, b'', ''] else 'No')

    df['Extra Data'] = df['additional_data'].fillna('N/A')
    df.rename(columns={'issue': 'Issue Type', 'location': 'Location', 'status': 'Status'}, inplace=True)

    # Fill missing priority-related values for display
    for col in ['priority_index', 'sentiment_score', 'keyword_severity', 'frequency_score']:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)
        else:
            df[col] = 0.0

    return df


# --- Load Data ---
df = get_all_grievances()
if df.empty:
    st.warning("No grievance data available.")
    st.stop()

df = prepare_data(df)

# --- Title ---
st.markdown('<div class="big-title">🏛️ Civic Grievance Collector Dashboard</div>', unsafe_allow_html=True)
st.markdown("#### Empowering smarter governance through AI-based prioritization and citizen feedback")

# --- Summary Metrics ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.markdown(f"<div class='metric-box'><div class='metric-label'>Total Grievances</div><div class='metric-value'>{len(df)}</div></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='metric-box'><div class='metric-label'>Pending Issues</div><div class='metric-value'>{df['Status'].eq('Pending').sum()}</div></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='metric-box'><div class='metric-label'>With Photos</div><div class='metric-value'>{df['Photo Status'].eq('Yes').sum()}</div></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='metric-box'><div class='metric-label'>Unique Locations</div><div class='metric-value'>{df['Location'].nunique()}</div></div>", unsafe_allow_html=True)
col5.markdown(f"<div class='metric-box'><div class='metric-label'>Avg Priority Index</div><div class='metric-value'>{df['priority_index'].mean():.2f}</div></div>", unsafe_allow_html=True)

st.divider()

# --- Sidebar Filters ---
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
st.subheader("📊 Issue, Location & Priority Analytics")

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

# --- Priority Index Analytics ---
st.subheader("🔥 High Priority Issues Overview")

if 'priority_index' in filtered_df.columns and filtered_df['priority_index'].sum() != 0:
    high_priority_df = filtered_df.sort_values(by='priority_index', ascending=False).head(10)

    priority_chart = px.bar(
        high_priority_df,
        x='priority_index',
        y='Issue Type',
        color='priority_index',
        orientation='h',
        title="Top 10 High Priority Complaints",
        color_continuous_scale='Reds',
        hover_data=['Location', 'username', 'Status', 'priority_index']
    )
    priority_chart.update_layout(height=400, xaxis_title='Priority Index', yaxis_title=None)
    st.plotly_chart(priority_chart, use_container_width=True)

    st.dataframe(
        high_priority_df[['id', 'Issue Type', 'Location', 'Status', 'priority_index', 'sentiment_score', 'keyword_severity', 'frequency_score']],
        use_container_width=True
    )
else:
    st.info("Priority index values not available yet. Run the bot to generate data.")

# --- Map Visualization (if coordinates exist) ---
if {'latitude', 'longitude'}.issubset(df.columns):
    st.subheader("🗺️ Issue Heatmap by Location (Weighted by Priority)")
    map_fig = px.density_mapbox(
        df, lat='latitude', lon='longitude', z='priority_index',
        hover_name='Issue Type', hover_data=['Location', 'Status', 'priority_index'],
        radius=20, center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
        mapbox_style='carto-darkmatter', zoom=10, color_continuous_scale="Inferno"
    )
    st.plotly_chart(map_fig, use_container_width=True)

# --- Interactive Grievance List ---
st.subheader("🧾 Recent Grievances")
st.subheader("🧾 Recent Grievances")
for _, row in filtered_df.head(10).iterrows():
    with st.container():
        st.markdown(f"""
        <div class='grievance-card'>
            <h4>🆔 #{row['id']} — {row['Issue Type']}</h4>
            <b>📍 Location:</b> {row['Location']}  
            <b>👤 User:</b> {row['username']}  
            <b>📅 Date:</b> {row['Date']}  
            <b>📦 Status:</b> <span style='color:#facc15'>{row['Status']}</span><br>
            <b>🔥 Priority Index:</b> {row['priority_index']:.2f}<br><br>
            <b>🗣️ Complaint:</b> {row['grievance']}<br>
            <b>🧠 AI Reply:</b> {row['ai_reply'] or 'No AI response'}<br>
        </div>
        """, unsafe_allow_html=True)

        # ✅ Add this snippet BELOW the st.markdown() call
        image_html = convert_blob_to_image_html(row.get('photo'))
        st.markdown(image_html, unsafe_allow_html=True)
