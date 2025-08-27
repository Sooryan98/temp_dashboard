import streamlit as st
import time
import pandas as pd
import natsort
import altair as alt 
from collections import defaultdict
from LiveDashProcessor import (
    log_data, robot_destro_data, lock, start_destro_thread, start_fms_thread,
    robot_fms_data, progress, cases_per_hour, robot_total_cases, progress_track,
    uph_tracker, flag_event, current_elapsed_time, simulation_started, start_timing_thread
)
from datetime import datetime
from collections import Counter
import re
import os

# Constants
DESTRO_PATH = "/home/soorya/destro_core/cross-docking/logs/yusen_2025-08-11.log"
FMS_PATH="/home/soorya/destro_FMS/destro_fms/yusen_charlestone/logs/FMS_2025-08-11.log"

# Page config - set once
st.set_page_config(page_title="destro", layout="wide")

# Initialize threads and data structures once
if 'dashboard_initialized' not in st.session_state:
    st.session_state.dashboard_initialized = True
    st.session_state.current_page = 'Overview'
    
    # Start threads once
    start_destro_thread(DESTRO_PATH)
    start_fms_thread(FMS_PATH)
    start_timing_thread()  # Start the timing thread

# Initialize constants
sim_speed = 20
robot_count = 10
cart_count = 30
inbound_count = 15
outbound_count = 42

# Destination mapping
destination_mapping = {
    # ── Group 1 ── (positions 1, 5, 9, … in the sorted list)
    "0555 - Woodland":           "Outbound_11",
    "0588 - Phoenix":            "Outbound_10",
    "3803 - Topeka":             "Outbound_9",
    "0600 - Lacey":              "Outbound_8",
    "0590 - Cedarfalls":         "Outbound_7",
    "3811 - Newton":             "Outbound_6",
    "0579 - New York":           "Outbound_5",
    "0556 - Tifton":             "Outbound_4",
    "3680 - NFI CHICAGO":        "Outbound_3",
    "Dest - Destroy":            "Outbound_2",
    "3681 - NFI Mount Pocono":   "Outbound_1",

    # ── Group 2 ── (positions 2, 6, 10, …)
    "0578 - Texas DC":           "Outbound_12",
    "0593 - Shaffer":            "Outbound_13",
    "0587 - Galesburg":          "Outbound_14",
    "3801 - Midlothian":         "Outbound_15",
    "3842 - DeKalb":             "Outbound_16",
    "0594 - Lugoff DC":          "Outbound_17",
    "3804 - West Jefferson":     "Outbound_18",
    "3865 - Chicago":            "Outbound_19",
    "3868 - Hampton":            "Outbound_20",
    "9156 - Burlington":         "Outbound_21",
    "9253 - Joliet":             "Outbound_22",

    # ── Group 3 ── (positions 3, 7, 11, …)
    "3806 - Rialto":             "Outbound_23",
    "3841 - Suffolk":            "Outbound_24",
    "0554 - Pueblo":             "Outbound_25",
    "0559 - Indianapolis":       "Outbound_26",
    "0551 - Minneapolis":        "Outbound_27",
    "3808 - Midway":             "Outbound_28",
    "0560 - Stuart's Draft VA":  "Outbound_29",
    "0580 - Alabama":            "Outbound_30",
    "OVERAGE":                   "Outbound_31",
    "9417 Savannah":             "Outbound_32",
    "9479 Ontario":              "Outbound_33",

    # ── Group 4 ── (positions 4, 8, 12, …)
    "0558 - Albany OR":          "Outbound_34",
    "0553 - Los Angeles":        "Outbound_35",
    "0557 - Oconomowoc":         "Outbound_36",
    "3840 - Rialto":             "Outbound_37",
    "3802 - Amsterdam":          "Outbound_38",
    "0589 - Chambersburg":       "Outbound_39",
    "3856 - Riverside":          "Outbound_40",
    "3857 - Logan Township":     "Outbound_41",
    "Salvage- Longbeach":        "Outbound_42",
}

outbound_destinations = {v: k for k, v in destination_mapping.items()}

# Helper functions
def clock_formating(elapsed_seconds):
    """Format elapsed seconds into HH:MM:SS format"""
    hrs = elapsed_seconds // 3600
    mins = (elapsed_seconds % 3600) // 60
    sec = elapsed_seconds % 60
    return f"{int(hrs):02d}:{int(mins):02d}:{int(sec):02d}"

def get_image_base64(image_path):
    import base64
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# Get current data from shared variables
try:
    with lock:
        # Copy all shared data to avoid conflicts
        current_robot_destro_data = dict(robot_destro_data) if robot_destro_data else {}
        current_cases_per_hour = dict(cases_per_hour) if cases_per_hour else {}
        current_progress = dict(progress) if progress else {}
        current_uph_tracker = dict(uph_tracker) if uph_tracker else {}
        current_robot_total_cases = dict(robot_total_cases) if robot_total_cases else {}
        current_robot_fms_data = dict(robot_fms_data) if robot_fms_data else {}
        current_log_data = dict(log_data) if log_data else {'total_cases': 0}
        current_flag_event = flag_event.is_set() if flag_event else False
        
        # Get the persistent timing data
        current_elapsed_time = current_elapsed_time
        current_simulation_started = simulation_started
        
        # Get additional data if available
        try:
            from LiveDashProcessor import trips_robot, cart_empty_idle, cart_full_idle, indoor_idle, outdoor_idle, robot_dwell
            # Try to import outbound_counter separately as it might not exist
            try:
                from LiveDashProcessor import outbound_counter
                current_outbound_counter = dict(outbound_counter) if outbound_counter else {}
            except ImportError:
                current_outbound_counter = {}
            
            current_trips_robot = dict(trips_robot) if trips_robot else {}
            current_cart_empty_idle = dict(cart_empty_idle) if cart_empty_idle else {}
            current_cart_full_idle = dict(cart_full_idle) if cart_full_idle else {}
            current_indoor_idle = dict(indoor_idle) if indoor_idle else {}
            current_outdoor_idle = dict(outdoor_idle) if outdoor_idle else {}
            current_robot_dwell = dict(robot_dwell) if robot_dwell else {}
        except ImportError:
            current_trips_robot = {}
            current_cart_empty_idle = {}
            current_cart_full_idle = {}
            current_indoor_idle = {}
            current_outdoor_idle = {}
            current_outbound_counter = {}
            current_robot_dwell = {}

except Exception as e:
    # Fallback to empty data if lock fails
    current_robot_destro_data = {}
    current_cases_per_hour = {}
    current_progress = {}
    current_uph_tracker = {}
    current_robot_total_cases = {}
    current_robot_fms_data = {}
    current_log_data = {'total_cases': 0}
    current_flag_event = False
    current_elapsed_time = 0
    current_simulation_started = False
    current_trips_robot = {}
    current_cart_empty_idle = {}
    current_cart_full_idle = {}
    current_indoor_idle = {}
    current_outdoor_idle = {}
    current_outbound_counter = {}
    current_robot_dwell = {}

# Process timing data using persistent timing from LiveDashProcessor
if current_flag_event and current_simulation_started:
    elapsed_time = current_elapsed_time*sim_speed
    dhrs, rem = divmod(elapsed_time, 3600)
    dmins, dsec = divmod(rem, 60)
    ctime = clock_formating(elapsed_time)
    
    # Calculate UPH using persistent elapsed time
    uph = int(current_log_data['total_cases']) / (elapsed_time / 3600) if elapsed_time > 0 else 0
    total_time = elapsed_time*sim_speed / 3600  # Convert to hours for calculations
else:
    uph = 0
    elapsed_time = 0
    dhrs, dmins, dsec = 0, 0, 0
    ctime = "00:00:00"
    total_time = 1  # Prevent division by zero

# Process data for dashboard
out_density = {}
for k, v in current_outbound_counter.items():
    if k in outbound_destinations:
        out_density[outbound_destinations[k]] = v

# Prepare DataFrames
rows = []
for cart, items in current_robot_destro_data.items():
    for item_id, data in items.items():
        rows.append({
            "CART": cart,
            "Item ID": item_id,
            "Total Cases": data.get("total_cases", 0)
        })

df = pd.DataFrame(rows)

# Cases per hour DataFrame
cases_ph_df = pd.DataFrame(current_cases_per_hour).T.fillna(0).astype(int)
if not cases_ph_df.empty:
    cases_ph_df = cases_ph_df.reindex(sorted(cases_ph_df.columns), axis=1)
    cases_ph_df["Total cases overall"] = cases_ph_df.sum(axis=1)
    code_101 = cases_ph_df['Total cases overall'].sum()
    cases_ph_df.loc["Total per hour"] = cases_ph_df.sum(axis=0)
else:
    code_101 = 0

# Robot distance DataFrame
robot_dist_df = pd.DataFrame(list(current_robot_fms_data.items()), columns=["Robot", "Distance"])
if not robot_dist_df.empty:
    robot_dist_df["Robot_Num"] = robot_dist_df["Robot"].str.extract(r'(\d+)').astype(int)
    robot_dist_df = robot_dist_df.sort_values(by="Robot_Num")

# Other DataFrames
progress_df = pd.DataFrame(list(current_progress.items()), columns=["Hour", "Cases"])
uph_tracker_df = pd.DataFrame(list(current_uph_tracker.items()), columns=["Hour", "UPH"])
robot_total_cases_df = pd.DataFrame(list(current_robot_total_cases.items()), columns=["Cart", "Total Cases"])
robot_trips_df = pd.DataFrame(list(current_trips_robot.items()), columns=['Robot', 'Trips'])
cart_full_idle_df = pd.DataFrame(list(current_cart_full_idle.items()), columns=['Cart', 'Dwell Time'])
cart_empty_idle_df = pd.DataFrame(list(current_cart_empty_idle.items()), columns=['Cart', 'Dwell Time'])
robot_dwell_df = pd.DataFrame(list(current_robot_dwell.items()), columns=['Robot', 'Dwell Time'])
indoor_idle_df = pd.DataFrame(list(current_indoor_idle.items()), columns=['Inbound ID', 'Dwell Time'])
outdoor_idle_df = pd.DataFrame(list(current_outdoor_idle.items()), columns=['Outbound ID', 'Dwell Time'])
out_density_df = pd.DataFrame(list(out_density.items()), columns=['Outbound Destination', 'Density'])

# Enhanced CSS with animations and modern styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main {
        background: linear-gradient(135deg, #0c1426 0%, #1a202c 100%);
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0c1426 0%, #1a202c 100%);
    }
    
    .metric-tile {
        background: linear-gradient(145deg, #1e293b, #334155);
        color: #ffffff;
        border-radius: 20px;
        padding: 28px;
        text-align: center;
        box-shadow: 
            0 10px 30px rgba(0,0,0,0.4),
            inset 0 1px 0 rgba(255,255,255,0.1);
        border: 1px solid rgba(148, 163, 184, 0.1);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .metric-tile::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
        transition: left 0.6s;
    }
    
    .metric-tile:hover::before {
        left: 100%;
    }
    
    .metric-tile:hover {
        transform: translateY(-8px);
        box-shadow: 
            0 20px 50px rgba(0,0,0,0.6),
            inset 0 1px 0 rgba(255,255,255,0.2);
    }
    
    .metric-title {
        font-size: 16px;
        color: #94a3b8;
        font-weight: 500;
        margin-bottom: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-value {
        font-size: 42px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 8px;
        background: linear-gradient(135deg, #ffffff, #e2e8f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .metric-subtitle {
        font-size: 13px;
        color: #64748b;
        font-weight: 400;
    }
    
    .chart-container {
        background: linear-gradient(145deg, #1e293b, #334155);
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 32px;
        border: 1px solid rgba(148, 163, 184, 0.1);
        box-shadow: 
            0 10px 30px rgba(0,0,0,0.4),
            inset 0 1px 0 rgba(255,255,255,0.1);
    }
    
    .chart-title {
        font-size: 22px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 24px;
        text-align: center;
        position: relative;
    }
    
    .chart-title::after {
        content: '';
        position: absolute;
        bottom: -8px;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        border-radius: 2px;
    }
    
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 40px;
        padding: 32px;
        background: linear-gradient(145deg, #1e293b, #334155);
        border-radius: 24px;
        border: 1px solid rgba(148, 163, 184, 0.1);
        box-shadow: 
            0 10px 30px rgba(0,0,0,0.4),
            inset 0 1px 0 rgba(255,255,255,0.1);
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 24px;
    }
    
    .logo {
        height: 60px;
        width: auto;
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    
    .logo:hover {
        transform: scale(1.05);
    }
    
    .time-info {
        color: #94a3b8;
        font-size: 15px;
        line-height: 1.6;
    }
    
    .time-info div:nth-child(2) {
        font-size: 20px;
        font-weight: 600;
        color: #ffffff;
        margin: 4px 0;
    }
    
    .status-info {
        text-align: right;
        color: #94a3b8;
        font-size: 15px;
    }
    
    .status-active {
        color: #10b981;
        font-weight: 600;
        font-size: 18px;
        position: relative;
    }
    
    .status-active::before {
        content: '●';
        color: #10b981;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .section-header {
        font-size: 36px;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 32px;
        text-align: center;
        background: linear-gradient(135deg, #ffffff, #e2e8f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        position: relative;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -12px;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
        border-radius: 2px;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e293b;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #3b82f6, #8b5cf6);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #2563eb, #7c3aed);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Animation for page transitions */
    .main > div {
        animation: fadeIn 0.5s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

# Navigation - Create unique keys for each button
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button(" Overview", key="nav_overview_btn", use_container_width=True):
        st.session_state.current_page = 'Overview'

with col2:
    if st.button("Dock Analytics", key="nav_dock_analytics_btn", use_container_width=True):
        st.session_state.current_page = 'Inbound and Outbound Docks'

with col3:
    if st.button("Cart Analytics", key="nav_cart_analytics_btn", use_container_width=True):
        st.session_state.current_page = 'Cart Analytics'

with col4:
    if st.button("Robot Analytics", key="nav_robot_analytics_btn", use_container_width=True):
        st.session_state.current_page = 'Robot Analytics'

# Enhanced Header with better logo handling
logo_base64 = get_image_base64("destro_logo.jpg")
yusen_base64 = get_image_base64("yusen_logo.png")

if logo_base64 or yusen_base64:
    header_content = '''
        <div class="header-container">
            <div class="logo-section">
    '''
    
    if yusen_base64:
        header_content += f'<img src="data:image/png;base64,{yusen_base64}" class="logo" alt="Yusen Logo" style="height: 80px; width: auto;">'
    if logo_base64:
        header_content += f'<img src="data:image/png;base64,{logo_base64}" class="logo" alt="Destro Logo" style="height: 50px; width: auto;">'
    header_content += f'''
                <div class="time-info">
                    <div>Simulation Runtime</div>
                    <div>{ctime}</div>
                    <div>Persistent Timer</div>
                </div>
            </div>
            <div class="status-info">
                <div>Simulation Status</div>
                <div class="status-active">{"Active" if current_flag_event else "Inactive"}</div>
                <div style="margin-top: 8px; font-size: 12px;">
                    {"Started" if current_simulation_started else "Not Started"}
                </div>
            </div>
        </div>
    '''
    
    st.markdown(header_content, unsafe_allow_html=True)

# Page Content
if st.session_state.current_page == 'Overview':
    st.markdown('<div class="section-header">System Performance Overview</div>', unsafe_allow_html=True)
    
    # Main Metrics with enhanced styling
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        uph_value = int(code_101 / total_time) if total_time > 0 else 0
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Units Per Hour</div>
                <div class="metric-value">{uph_value}</div>
                <div class="metric-subtitle">Current throughput</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Total Cases</div>
                <div class="metric-value">{code_101:,}</div>
                <div class="metric-subtitle">Units processed</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Runtime</div>
                <div class="metric-value">{ctime}</div>
                <div class="metric-subtitle">HH:MM:SS</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Active Robots</div>
                <div class="metric-value">{robot_count}</div>
                <div class="metric-subtitle">Fleet status</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Active Carts</div>
                <div class="metric-value">{cart_count}</div>
                <div class="metric-subtitle">In operation</div>
            </div>
        """, unsafe_allow_html=True)

    # Enhanced Charts with better color schemes
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">UPH Progression</div>', unsafe_allow_html=True)
        if not uph_tracker_df.empty:
            chart_uph = alt.Chart(uph_tracker_df).mark_bar(
                size=25,
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='#3b82f6', offset=0),
                        alt.GradientStop(color='#8b5cf6', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Hour:N', 
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=False,
                        domain=False
                    )
                ),
                y=alt.Y('UPH:Q',
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=True,
                        gridColor='rgba(148, 163, 184, 0.1)',
                        domain=False
                    )
                ),
                tooltip=[
                    alt.Tooltip('Hour:N', title='Hour'),
                    alt.Tooltip('UPH:Q', title='Units Per Hour')
                ]
            ).properties(height=400).configure_view(
                strokeWidth=0,
                fill='transparent'
            ).configure(
                background='transparent'
            )
            st.altair_chart(chart_uph, use_container_width=True)
        else:
            st.write("No UPH data available")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Outbound Destination Density</div>', unsafe_allow_html=True)
        if not out_density_df.empty:
            chart_density = alt.Chart(out_density_df).mark_bar(
                size=15,
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='#ec4899', offset=0),
                        alt.GradientStop(color='#f59e0b', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Outbound Destination:N', 
                    sort='-y',
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        labelAngle=-90,
                        grid=False,
                        domain=False
                    )
                ),
                y=alt.Y('Density:Q',
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=True,
                        gridColor='rgba(148, 163, 184, 0.1)',
                        domain=False
                    )
                ),
                tooltip=[
                    alt.Tooltip('Outbound Destination:N', title='Destination'),
                    alt.Tooltip('Density:Q', title='Package Count')
                ]
            ).properties(height=400).configure_view(
                strokeWidth=0,
                fill='transparent'
            ).configure(
                background='transparent'
            )
            st.altair_chart(chart_density, use_container_width=True)
        else:
            st.write("No density data available")
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == 'Inbound and Outbound Docks':
    st.markdown('<div class="section-header">Dock Analytics Dashboard</div>', unsafe_allow_html=True)
    
    # Door Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Inbound Docks</div>
                <div class="metric-value">{inbound_count}</div>
                <div class="metric-subtitle">Active doors</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Outbound Docks</div>
                <div class="metric-value">{outbound_count}</div>
                <div class="metric-subtitle">Active doors</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        total_inbound_dwell = sum(current_indoor_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Inbound Dwell</div>
                <div class="metric-value">{int(total_inbound_dwell)} min</div>
                <div class="metric-subtitle">Total idle time</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        total_outbound_dwell = sum(current_outdoor_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Outbound Dwell</div>
                <div class="metric-value">{int(total_outbound_dwell)} min</div>
                <div class="metric-subtitle">Total idle time</div>
            </div>
        """, unsafe_allow_html=True)

    # Door Charts
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Inbound Dock Dwell Time</div>', unsafe_allow_html=True)
        if not indoor_idle_df.empty:
            chart_inbound = alt.Chart(indoor_idle_df).mark_bar(
                size=20,
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='#10b981', offset=0),
                        alt.GradientStop(color='#3b82f6', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Inbound ID:N', 
                    sort=[f'Inbound {i}' for i in range(1,16)],
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=False,
                        domain=False
                    )
                ),
                y=alt.Y('Dwell Time:Q',
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=True,
                        gridColor='rgba(148, 163, 184, 0.1)',
                        domain=False
                    )
                ),
                tooltip=[
                    alt.Tooltip('Inbound ID:N', title='Door'),
                    alt.Tooltip('Dwell Time:Q', title='Dwell Time (min)')
                ]
            ).properties(height=450).configure_view(
                strokeWidth=0,
                fill='transparent'
            ).configure(
                background='transparent'
            )
            st.altair_chart(chart_inbound, use_container_width=True)
        else:
            st.write("No inbound door data available")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Outbound Dock Dwell Time</div>', unsafe_allow_html=True)
        if not outdoor_idle_df.empty:
            chart_outbound = alt.Chart(outdoor_idle_df).mark_bar(
                size=15,
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='#f59e0b', offset=0),
                        alt.GradientStop(color='#ec4899', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Outbound ID:N', 
                    sort=[f'Outbound {i}' for i in range(1,43)],
                    axis=alt.Axis(
                        labelFontSize=10, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        labelAngle=-90,
                        grid=False,
                        domain=False
                    )
                ),
                y=alt.Y('Dwell Time:Q',
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=True,
                        gridColor='rgba(148, 163, 184, 0.1)',
                        domain=False
                    )
                ),
                tooltip=[
                    alt.Tooltip('Outbound ID:N', title='Door'),
                    alt.Tooltip('Dwell Time:Q', title='Dwell Time (min)')
                ]
            ).properties(height=450).configure_view(
                strokeWidth=0,
                fill='transparent'
            ).configure(
                background='transparent'
            )
            st.altair_chart(chart_outbound, use_container_width=True)
        else:
            st.write("No outbound door data available")
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == 'Cart Analytics':
    st.markdown('<div class="section-header">Cart Performance Analytics</div>', unsafe_allow_html=True)
    
    # Cart overview chart
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Cases Unloaded per Cart</div>', unsafe_allow_html=True)
    if not robot_total_cases_df.empty:
        chart_cart_cases = alt.Chart(robot_total_cases_df).mark_bar(
            size=8,
            color=alt.Gradient(
                gradient='linear',
                stops=[
                    alt.GradientStop(color='#8b5cf6', offset=0),
                    alt.GradientStop(color='#3b82f6', offset=1)
                ],
                x1=1, x2=1, y1=1, y2=0
            ),
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3
        ).encode(
            x=alt.X('Cart:N', 
                sort=[f'{i}' for i in range(1,cart_count)],
                axis=alt.Axis(
                    labelFontSize=10, 
                    titleFontSize=14,
                    labelColor='#ffffff', 
                    titleColor='#ffffff',
                    labelExpr="'Cart ' + datum.value",
                    grid=False,
                    domain=False
                )
            ),
            y=alt.Y('Total Cases:Q',
                axis=alt.Axis(
                    labelFontSize=12, 
                    titleFontSize=14,
                    labelColor='#ffffff', 
                    titleColor='#ffffff',
                    grid=True,
                    gridColor='rgba(148, 163, 184, 0.1)',
                    domain=False
                )
            ),
            tooltip=[
                alt.Tooltip('Cart:N', title='Cart ID'),
                alt.Tooltip('Total Cases:Q', title='Cases Unloaded')
            ]
        ).properties(height=400).configure_view(
            strokeWidth=0,
            fill='transparent'
        ).configure(
            background='transparent'
        )
        st.altair_chart(chart_cart_cases, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Cart Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Active Carts</div>
                <div class="metric-value">{cart_count}</div>
                <div class="metric-subtitle">In circulation</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        total_cart_empty = sum(current_cart_empty_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Empty Cart Dwell</div>
                <div class="metric-value">{int(total_cart_empty)} min</div>
                <div class="metric-subtitle">Total idle time</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_cart_full = sum(current_cart_full_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Full Cart Dwell</div>
                <div class="metric-value">{int(total_cart_full)} min</div>
                <div class="metric-subtitle">Total idle time</div>
            </div>
        """, unsafe_allow_html=True)

    # Cart Dwell Charts
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Empty Cart Dwell Time</div>', unsafe_allow_html=True)
        if not cart_empty_idle_df.empty:
            chart_empty = alt.Chart(cart_empty_idle_df).mark_bar(
                size=10,
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='#10b981', offset=0),
                        alt.GradientStop(color='#06b6d4', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Cart:N', 
                    sort=[f'Cart {i}' for i in range(1,cart_count)],
                    axis=alt.Axis(
                        labelFontSize=10, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=False,
                        domain=False
                    )
                ),
                y=alt.Y('Dwell Time:Q',
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=True,
                        gridColor='rgba(148, 163, 184, 0.1)',
                        domain=False
                    )
                ),
                tooltip=[
                    alt.Tooltip('Cart:N', title='Cart'),
                    alt.Tooltip('Dwell Time:Q', title='Dwell Time (min)')
                ]
            ).properties(height=400).configure_view(
                strokeWidth=0,
                fill='transparent'
            ).configure(
                background='transparent'
            )
            st.altair_chart(chart_empty, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Full Cart Dwell Time</div>', unsafe_allow_html=True)
        if not cart_full_idle_df.empty:
            chart_full = alt.Chart(cart_full_idle_df).mark_bar(
                size=10,
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='#f59e0b', offset=0),
                        alt.GradientStop(color='#ef4444', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Cart:N', 
                    sort=[f'Cart {i}' for i in range(1,cart_count)],
                    axis=alt.Axis(
                        labelFontSize=10, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=False,
                        domain=False
                    )
                ),
                y=alt.Y('Dwell Time:Q',
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=True,
                        gridColor='rgba(148, 163, 184, 0.1)',
                        domain=False
                    )
                ),
                tooltip=[
                    alt.Tooltip('Cart:N', title='Cart'),
                    alt.Tooltip('Dwell Time:Q', title='Dwell Time (min)')
                ]
            ).properties(height=400).configure_view(
                strokeWidth=0,
                fill='transparent'
            ).configure(
                background='transparent'
            )
            st.altair_chart(chart_full, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.current_page == 'Robot Analytics':
    st.markdown('<div class="section-header">Robot Fleet Analytics</div>', unsafe_allow_html=True)
    
    # Robot Performance Summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Active Robots</div>
                <div class="metric-value">{robot_count}</div>
                <div class="metric-subtitle">Fleet size</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg_robot_distance = robot_dist_df['Distance'].mean() if not robot_dist_df.empty else 0
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Avg Distance</div>
                <div class="metric-value">{avg_robot_distance:.1f}m</div>
                <div class="metric-subtitle">Per robot</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        trip_sum = sum(int(v) for v in current_trips_robot.values()) if current_trips_robot else 0
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Total Trips</div>
                <div class="metric-value">{trip_sum}</div>
                <div class="metric-subtitle">Fleet total</div>
            </div>
        """, unsafe_allow_html=True)

    # Robot Performance Charts
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Distance Travelled by Robots</div>', unsafe_allow_html=True)
        if not robot_dist_df.empty:
            chart_dist = alt.Chart(robot_dist_df).mark_bar(
                size=15,
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='#8b5cf6', offset=0),
                        alt.GradientStop(color='#ec4899', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Robot:N', 
                    sort=robot_dist_df["Robot"].tolist(),
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=False,
                        domain=False
                    )
                ),
                y=alt.Y('Distance:Q',
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=True,
                        gridColor='rgba(148, 163, 184, 0.1)',
                        domain=False
                    )
                ),
                tooltip=[
                    alt.Tooltip('Robot:N', title='Robot'),
                    alt.Tooltip('Distance:Q', title='Distance (m)')
                ]
            ).properties(height=400).configure_view(
                strokeWidth=0,
                fill='transparent'
            ).configure(
                background='transparent'
            )
            st.altair_chart(chart_dist, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Trips Made by Robots</div>', unsafe_allow_html=True)
        if not robot_trips_df.empty:
            chart_trips = alt.Chart(robot_trips_df).mark_bar(
                size=15,
                color=alt.Gradient(
                    gradient='linear',
                    stops=[
                        alt.GradientStop(color='#06b6d4', offset=0),
                        alt.GradientStop(color='#3b82f6', offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                ),
                cornerRadiusTopLeft=4,
                cornerRadiusTopRight=4
            ).encode(
                x=alt.X('Robot:N', 
                    sort=[f'Robot {i}' for i in range(1,robot_count+1)],
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=False,
                        domain=False
                    )
                ),
                y=alt.Y('Trips:Q',
                    axis=alt.Axis(
                        labelFontSize=12, 
                        titleFontSize=14,
                        labelColor='#ffffff', 
                        titleColor='#ffffff',
                        grid=True,
                        gridColor='rgba(148, 163, 184, 0.1)',
                        domain=False
                    )
                ),
                tooltip=[
                    alt.Tooltip('Robot:N', title='Robot'),
                    alt.Tooltip('Trips:Q', title='Number of Trips')
                ]
            ).properties(height=400).configure_view(
                strokeWidth=0,
                fill='transparent'
            ).configure(
                background='transparent'
            )
            st.altair_chart(chart_trips, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Robot Dwell Time Chart
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Robot Dwell Time Analysis</div>', unsafe_allow_html=True)
    if not robot_dwell_df.empty:
        chart_robot_dwell = alt.Chart(robot_dwell_df).mark_bar(
            size=20,
            color=alt.Gradient(
                gradient='linear',
                stops=[
                    alt.GradientStop(color='#f59e0b', offset=0),
                    alt.GradientStop(color='#ef4444', offset=1)
                ],
                x1=1, x2=1, y1=1, y2=0
            ),
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4
        ).encode(
            x=alt.X('Robot:N', 
                sort=[f'Robot {i}' for i in range(1,robot_count+1)],
                axis=alt.Axis(
                    labelFontSize=12, 
                    titleFontSize=14,
                    labelColor='#ffffff', 
                    titleColor='#ffffff',
                    grid=False,
                    domain=False
                )
            ),
            y=alt.Y('Dwell Time:Q',
                axis=alt.Axis(
                    labelFontSize=12, 
                    titleFontSize=14,
                    labelColor='#ffffff', 
                    titleColor='#ffffff',
                    grid=True,
                    gridColor='rgba(148, 163, 184, 0.1)',
                    domain=False
                )
            ),
            tooltip=[
                alt.Tooltip('Robot:N', title='Robot'),
                alt.Tooltip('Dwell Time:Q', title='Dwell Time (min)')
            ]
        ).properties(height=400).configure_view(
            strokeWidth=0,
            fill='transparent'
        ).configure(
            background='transparent'
        )
        st.altair_chart(chart_robot_dwell, use_container_width=True)
    else:
        st.write("No robot dwell data available")
    st.markdown('</div>', unsafe_allow_html=True)

# Auto-refresh the dashboard
time.sleep(0.1)  # Adjust this to control refresh rate (1 second here)
st.rerun()