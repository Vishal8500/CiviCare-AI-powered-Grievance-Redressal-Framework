# ==========================================
# Civic Grievance Collector Dashboard (Enhanced with Notify All Departments + Popup)
# ==========================================

import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection, DB_NAME, update_grievance_status, notify_department
from issue_config import ISSUE_CONFIG  # <-- ADDED
import base64
import asyncio
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime, timedelta
import io

# --- Page Config ---
st.set_page_config(page_title="Civic Grievance Collector Dashboard", layout="wide")

# --- Department Mapping (Issue → Department) ---
DEPARTMENT_MAP = {
    "Fire Hazards": "Fire Department",
    "Crime / Anti-Social Activity": "Police Department",
    "Roads & Traffic": "Public Works Department",
    "Water Supply": "Water Board",
    "Electricity / Power": "Electricity Board",
    "Sewage & Drainage": "Municipal Corporation",
    "Garbage & Waste Management": "Sanitation Department",
    "Pollution & Noise": "Pollution Control Board",
    "Green Spaces": "Parks & Horticulture",
    "Public Transport": "Transport Authority",
    "Community Facilities": "Civic Amenities",
    "Healthcare & Hospitals": "Health Department",
    "Animal-Related Issues": "Animal Welfare",
    "Street Safety": "Traffic Police",
    "Documentation / Permits": "Municipal Office",
    "Billing / Taxes / Fines": "Revenue Department",
    "Corruption / Malpractice": "Anti-Corruption Bureau",
    "App / Portal Issues": "IT Department",
    "Noise Complaints": "Local Administration",
    "Other Civic Complaints": "General Administration",
}

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
        position: relative;
    }
    .grievance-card:hover {
        border-color: #f59e0b;
        background-color: #111827;
    }
    img:hover { transform: scale(1.05); transition: transform 0.2s; }
    .notify-btn {
        background-color: #dc2626 !important;
        color: white !important;
    }
    .notified-btn {
        background-color: #16a34a !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Database Fetch ---
@st.cache_data(ttl=60)
def get_all_grievances():
    conn = get_connection(DB_NAME)
    if conn is None:
        st.error("Database connection failed.")
        return pd.DataFrame()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT *, (notified_to_dept = TRUE) AS notified_to_dept FROM grievances ORDER BY created_at DESC")
    data = cursor.fetchall()
    conn.close()
    return pd.DataFrame(data)

# --- Data Preparation ---
def prepare_data(df):
    if df.empty:
        return df
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['Date'] = df['created_at'].dt.strftime('%Y-%m-%d %H:%M')
    df['Photo Status'] = df['photo'].apply(lambda x: 'Yes' if x not in [None, b'', ''] else 'No')
    df['Extra Data'] = df['additional_data'].fillna('N/A')
    df.rename(columns={'issue': 'Issue Type', 'location': 'Location', 'status': 'Status'}, inplace=True)
    for col in ['priority_index', 'sentiment_score', 'keyword_severity', 'frequency_score', 'notified_to_dept']:
        if col in df.columns:
            df[col] = df[col].fillna(0.0 if col != 'notified_to_dept' else False)
        else:
            df[col] = 0.0 if col != 'notified_to_dept' else False
    return df

# --- Generate PDF Report ---
def generate_pdf_report(df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("Civic Grievance Report (Last 30 Days)", styles['Title'])
    elements.append(title)
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}", styles['Normal']))
    elements.append(Paragraph(f"Total Grievances: {len(df)}", styles['Normal']))
    elements.append(Paragraph("\n", styles['Normal']))

    table_data = [['ID', 'Issue Type', 'Location', 'Status', 'Priority Index', 'Complaint', 'Date', 'Notified']]
    for _, row in df.iterrows():
        table_data.append([
            str(row['id']),
            row['Issue Type'],
            row['Location'],
            row['Status'],
            f"{row['priority_index']:.2f}",
            row['grievance'][:100] + "..." if len(row['grievance']) > 100 else row['grievance'],
            row['Date'],
            "Yes" if row['notified_to_dept'] else "No"
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- Load Data ---
df = get_all_grievances()
if df.empty:
    st.warning("No grievance data available.")
    st.stop()

df = prepare_data(df)

# --- Title ---
st.markdown('<div class="big-title">Civic Grievance Collector Dashboard</div>', unsafe_allow_html=True)
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
st.sidebar.header("Filters")
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

# --- Charts & Analytics (unchanged) ---
# ... [Your existing charts code here – unchanged] ...
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

# --- Map Visualization ---
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
st.subheader("Recent Grievances")

# Initialize session state for popup
if 'show_popup' not in st.session_state:
    st.session_state.show_popup = False
if 'popup_message' not in st.session_state:
    st.session_state.popup_message = ""

for _, row in filtered_df.head(10).iterrows():
    with st.container():
        current_status = row['Status']
        button_text = "Mark Completed" if current_status == 'Pending' else "Mark Pending"
        new_status = 'Completed' if current_status == 'Pending' else 'Pending'

        with st.form(key=f"form_{row['id']}"):
            st.markdown(f"""
            <div class='grievance-card'>
                <h4>ID #{row['id']} — {row['Issue Type']}</h4>
                <b>Location:</b> {row['Location']}  
                <b>User:</b> {row['username']}  
                <b>Date:</b> {row['Date']}  
                <b>Status:</b> <span style='color:#facc15'>{row['Status']}</span><br>
                <b>Priority Index:</b> {row['priority_index']:.2f}<br><br>
                <b>Complaint:</b> {row['grievance']}<br>
                <b>AI Reply:</b> {row['ai_reply'] or 'No AI response'}<br>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 1])

            with col1:
                submitted = st.form_submit_button(
                    label=button_text,
                    help=f"Toggle status to {new_status}",
                    type="primary"
                )
                if submitted:
                    with st.spinner("Updating status..."):
                        success = asyncio.run(update_grievance_status(row['id'], new_status))
                        if success:
                            st.success(f"Grievance #{row['id']} marked as {new_status}")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("Failed to update status")

            with col2:
                # --- NOTIFY BUTTON FOR ALL ISSUE TYPES ---
                dept_name = DEPARTMENT_MAP.get(row['Issue Type'], "Relevant Department")
                notify_label = f"Notify {dept_name.split()[0]} Dept"

                if row['notified_to_dept']:
                    st.form_submit_button(
                        label="Notified",
                        disabled=True,
                        help=f"Already notified to {dept_name}"
                    )
                else:
                    notify_submitted = st.form_submit_button(
                        label=notify_label,
                        help=f"Notify {dept_name}",
                        type="secondary"
                    )
                    if notify_submitted:
                        with st.spinner(f"Notifying {dept_name}..."):
                            success = asyncio.run(notify_department(row['id']))
                            if success:
                                st.session_state.show_popup = True
                                st.session_state.popup_message = f"Grievance #{row['id']} ({row['Issue Type']}) has been successfully notified to the **{dept_name}**."
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Failed to notify department")

        # --- Zoomable Image ---
        blob_data = row.get('photo')
        if blob_data:
            base64_str = base64.b64encode(blob_data).decode('utf-8')
            image_html = f"""
            <div style="text-align:center; margin: 10px 0;">
                <img src="data:image/jpeg;base64,{base64_str}" width="150"
                    style="border-radius:10px; cursor:pointer;" onclick="openPopup{row['id']}()">
            </div>
            <div id="popup-{row['id']}" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); justify-content:center; align-items:center; z-index:9999;">
                <img id="popup-img-{row['id']}" src="data:image/jpeg;base64,{base64_str}"
                    style="max-width:90%; max-height:90%; border-radius:12px; box-shadow:0 0 25px #000;">
            </div>
            <script>
            const popup{row['id']} = document.getElementById("popup-{row['id']}");
            function openPopup{row['id']}() {{ popup{row['id']}.style.display = "flex"; }}
            popup{row['id']}.onclick = (e) => {{ if (e.target === popup{row['id']}) popup{row['id']}.style.display = "none"; }};
            </script>
            """
            st.markdown(image_html, unsafe_allow_html=True)
        else:
            st.markdown("<span style='color:#888'>No image available</span>", unsafe_allow_html=True)

# --- Popup Modal (Dynamic Department) ---
if st.session_state.show_popup:
    st.markdown(f"""
    <div style="
        position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8);
        display: flex; justify-content: center; align-items: center; z-index: 10000; padding: 20px;
    ">
        <div style="
            background: #1f2937; padding: 30px; border-radius: 16px; max-width: 500px; text-align: center;
            border: 2px solid #dc2626; box-shadow: 0 0 20px rgba(220,38,38,0.5);
        ">
            <h3 style="color: #facc15; margin-bottom: 15px;">Department Notified</h3>
            <p style="color: #e5e7eb; font-size: 16px; margin-bottom: 20px;">
                {st.session_state.popup_message}
            </p>
            <button onclick="window.location.reload()" style="
                background: #dc2626; color: white; border: none; padding: 10px 20px;
                border-radius: 8px; cursor: pointer; font-weight: bold;
            ">Close</button>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.show_popup = False

# --- PDF Download Section ---
st.subheader("Download Report")
last_month = datetime.now() - timedelta(days=30)
recent_df = df[df['created_at'] >= last_month]

if not recent_df.empty:
    pdf_buffer = generate_pdf_report(recent_df)
    st.download_button(
        label="Download Last 30 Days Report as PDF",
        data=pdf_buffer,
        file_name=f"grievance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf"
    )
else:
    st.warning("No grievances recorded in the last 30 days.")