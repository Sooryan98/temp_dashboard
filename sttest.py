

import streamlit as st
import pandas as pd
import altair as alt
import re
import os
from collections import defaultdict
from datetime import datetime
from collections import Counter
import base64

# Your existing configuration and data structures
DESTRO_PATH = "log_bank/1_Many/DEMO-5x/60C/yusen_2025-07-15.log"
FMS_PATH = "log_bank/1_Many/DEMO-5x/60C/FMS_2025-07-15.log"

st.set_page_config(page_title="Destro Dashboard", layout="wide")

# All your existing variables and data structures
dashboard_time = 0
sim_speed = 5
robot_count = 15
cart_count = 60
inbound_count=15
outbound_count=42
start_time = 0
end_time = 0
ptrack = 0

robot_destro_data = defaultdict(lambda: defaultdict(dict))
progress_track = {"0.0": 0}
progress = defaultdict(int)
task_id_tracker = []
uph_tracker = {}
log_data = {"total_cases": 0}
robot_fms_data = {f"Robot {i+1}": 0 for i in range(15)}
robot_total_cases = {f"Robot {i+1}": 0 for i in range(15)}
robot_dwell = {f"Robot {i+1}": 0 for i in range(15)}
cases_per_hour = defaultdict(lambda: defaultdict(int))
log_time_format = "%Y-%m-%d %H:%M:%S,%f"
trips_robot = {}
cart_empty_idle = {}
cart_full_idle = {}
indoor_idle = {}
outdoor_idle = {}
outbound_counter = Counter()
robot_total_cases = defaultdict(int)

# Your existing destination mapping
destination_mapping = {
    "0555 - Woodland": "Outbound_11",
    "0588 - Phoenix": "Outbound_10",
    "3803 - Topeka": "Outbound_9",
    "0600 - Lacey": "Outbound_8",
    "0590 - Cedarfalls": "Outbound_7",
    "3811 - Newton": "Outbound_6",
    "0579 - New York": "Outbound_5",
    "0556 - Tifton": "Outbound_4",
    "3680 - NFI CHICAGO": "Outbound_3",
    "Dest - Destroy": "Outbound_2",
    "3681 - NFI Mount Pocono": "Outbound_1",
    "0578 - Texas DC": "Outbound_12",
    "0593 - Shaffer": "Outbound_13",
    "0587 - Galesburg": "Outbound_14",
    "3801 - Midlothian": "Outbound_15",
    "3842 - DeKalb": "Outbound_16",
    "0594 - Lugoff DC": "Outbound_17",
    "3804 - West Jefferson": "Outbound_18",
    "3865 - Chicago": "Outbound_19",
    "3868 - Hampton": "Outbound_20",
    "9156 - Burlington": "Outbound_21",
    "9253 - Joliet": "Outbound_22",
    "3806 - Rialto": "Outbound_23",
    "3841 - Suffolk": "Outbound_24",
    "0554 - Pueblo": "Outbound_25",
    "0559 - Indianapolis": "Outbound_26",
    "0551 - Minneapolis": "Outbound_27",
    "3808 - Midway": "Outbound_28",
    "0560 - Stuart's Draft VA": "Outbound_29",
    "0580 - Alabama": "Outbound_30",
    "OVERAGE": "Outbound_31",
    "9417 Savannah": "Outbound_32",
    "9479 Ontario": "Outbound_33",
    "0558 - Albany OR": "Outbound_34",
    "0553 - Los Angeles": "Outbound_35",
    "0557 - Oconomowoc": "Outbound_36",
    "3840 - Rialto": "Outbound_37",
    "3802 - Amsterdam": "Outbound_38",
    "0589 - Chambersburg": "Outbound_39",
    "3856 - Riverside": "Outbound_40",
    "3857 - Logan Township": "Outbound_41",
    "Salvage- Longbeach": "Outbound_42",
}
outbound_destinations = {v: k for k, v in destination_mapping.items()}

# Your existing functions (keeping them as they are)
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def outbound_density(log_path):
    if not os.path.exists(log_path):
        return
    
    with open(log_path, "r") as f:
        lines = f.readlines()
    
    pattern = re.compile(r"route:\s*(\[[^\]]*\])")
    
    for line in lines:
        if "[Coordination] Starting coordination for cart" in line:
            match = pattern.search(line)
            if match:
                route_list = eval(match.group(1))
                outbound_counter.update(route_list)

def parse_destro_log(path):
    if not os.path.exists(path):
        return

    with open(path, "r") as file:
        for line in file:
            line = re.sub(r'\x1b\[[0-9;]*m', '', line)
            
            if "CODE 201" in line:
                timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)', line)
                if timestamp_match:
                    log_time_str = timestamp_match.group(1)
                    log_time = datetime.strptime(log_time_str, log_time_format)
                    log_hour_str = log_time.strftime("%Y-%m-%d %H:00")

                pattern = re.compile(r"CODE 201 \[Cart CART_(\d+)] Loading case (\d+) of (\d+) from cart \w+ for item (\d+)")
                match = pattern.search(line)
                if match:
                    cart_id, current_case, total_cases, item_id = match.groups()
                    current_case = int(current_case)
                    total_cases = int(total_cases)
                    
                    robot_destro_data[f"Cart {int(cart_id)}"][item_id] = {
                        "total_cases": total_cases
                    }
                    robot_total_cases[ cart_id] += 1
                    cases_per_hour[cart_id][log_hour_str] += 1

            elif "CODE 101" in line:
                pattern = re.compile(r"CODE 101 --------------- (\d+)")
                match = pattern.search(line)
                if match:
                    cases = match.groups()
                    log_data["total_cases"] = int(cases[0])
                    
            elif "[IDLE] CODE 701 " in line:
                pattern = re.compile(r"\[IDLE\] CODE 701 Cart CART_(\d+) total idle time: ([\d.]+) seconds")
                match = pattern.search(line)
                if match:
                    cart_id, idle_time = match.groups()
                    idle_time = float(idle_time) / 60
                    cart_full_idle[f"Cart {cart_id}"] = idle_time
                    
            elif "[IDLE] CODE 601 " in line:
                pattern = re.compile(r"\[IDLE\] CODE 601 Cart CART_(\d+) total idle time: ([\d.]+) seconds")
                match = pattern.search(line)
                if match:
                    cart_id, idle_time = match.groups()
                    idle_time = float(idle_time) / 60
                    cart_empty_idle[f"Cart {cart_id}"] = idle_time
                    
            elif "CODE 501" in line:
                pattern = re.compile(r"CODE 501 Trips taken by Robot_(\d+) is (\d+)")
                match = pattern.search(line)
                if match:
                    robot_id, trips = match.groups()
                    trips_robot[f"Robot {int(robot_id)+1}"] = trips
                    
            elif "[DOOR DWELL] CODE 801 Inbound" in line:
                pattern = re.compile(r"\[DOOR DWELL\] CODE 801 Inbound dock Inbound_(\d+) total dwell time : ([\d.]+)")
                match = pattern.search(line)
                if match:
                    indoor_id, dtime = match.groups()
                    dtime = float(dtime) / 60
                    indoor_idle[f"Inbound {indoor_id}"] = dtime
                    
            elif "[DOOR DWELL] CODE 801 Outbound" in line:
                pattern = re.compile(r"\[DOOR DWELL\] CODE 801 Outbound dock Outbound_(\d+) total dwell time : ([\d.]+)")
                match = pattern.search(line)
                if match:
                    outdoor_id, dtime = match.groups()
                    dtime = float(dtime) / 60
                    outdoor_idle[f"Outbound {outdoor_id}"] = dtime

def parse_fms_log(path):
    global ptrack, start_time, end_time, dashboard_time
    if not os.path.exists(path):
        return

    with open(path, "r") as file:
        for line in file:
            line = re.sub(r'\x1b\[[0-9;]*m', '', line)

            if "CODE F01" in line:
                pattern = re.compile(r"CODE F01 at (\d+\.\d+) number of cases finished is (\d+)")
                match = pattern.search(line)
                if match:
                    hour, cases = match.groups()
                    cases_until_now = sum(progress_track.values())
                    progress_track[hour] = int(cases)
                    progress_track[hour] = progress_track[hour] - cases_until_now
                    progress[hour] = progress_track[hour]
                    if progress[hour] != ptrack:
                        ptrack = progress[hour]
                        match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                        if match:
                            timestamp = match.group(1)
                            end_time = timestamp
                            
            elif "CODE F02" in line:
                pattern = re.compile(r"CODE F02 at (\d+\.\d+) UPH is (\d+)")
                match = pattern.search(line)
                if match:
                    hour, uph = match.groups()
                    uph_tracker[hour] = uph
                    
            elif "CODE 000" in line:
                match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                if match:
                    timestamp = match.group(1)
                    start_time = timestamp
                    
            elif "has dwelled" in line:
                pattern = re.compile(r"Robot robot_(\d+) has dwelled for ([\d.]+) sec")
                match = pattern.search(line)
                if match:
                    robot_id, dwell_time = match.groups()
                    dwell_time = round(float(dwell_time), 2) / 60
                    robot_key = f"Robot {int(robot_id)+1}"
                    if dwell_time != 0:
                        robot_dwell[robot_key] = dwell_time
                        
            else:
                pattern = re.compile(r"Robot robot_(\d+)\s+has travelled\s+([\d\.]+)\s+m")
                match = pattern.search(line)
                if match:
                    robot_id, dist = match.groups()
                    if int(robot_id) < 25:
                        robot_key = f"Robot {int(robot_id)+1}"
                        robot_fms_data[robot_key] = float(dist)

# Run parsers
parse_destro_log(DESTRO_PATH)
parse_fms_log(FMS_PATH)
outbound_density(DESTRO_PATH)

# Process data
out_density = {}
for k, v in outbound_counter.items():
    if k in outbound_destinations:
        out_density[outbound_destinations[k]] = v

# Create DataFrames
rows = []
for cart, items in robot_destro_data.items():
    for item_id, data in items.items():
        rows.append({
            "CART": cart,
            "Item ID": item_id,
            "Total Cases": data["total_cases"]
        })

df = pd.DataFrame(rows)
cases_ph_df = pd.DataFrame(cases_per_hour).T.fillna(0).astype(int)
cases_ph_df = cases_ph_df.reindex(sorted(cases_ph_df.columns), axis=1)
cases_ph_df["Total cases overall"] = cases_ph_df.sum(axis=1)
code_101 = cases_ph_df['Total cases overall'].sum()

robot_dist_df = pd.DataFrame(list(robot_fms_data.items()), columns=["Robot", "Distance"])
robot_dist_df["Robot_Num"] = robot_dist_df["Robot"].str.extract(r'(\d+)').astype(int)
robot_dist_df = robot_dist_df.sort_values(by="Robot_Num")

robot_total_cases_df = pd.DataFrame(list(robot_total_cases.items()), columns=["Cart", "Total Cases"])
robot_trips_df = pd.DataFrame(list(trips_robot.items()), columns=['Robot', 'Trips'])
cart_full_idle_df = pd.DataFrame(list(cart_full_idle.items()), columns=['Cart', 'Dwell Time'])
cart_empty_idle_df = pd.DataFrame(list(cart_empty_idle.items()), columns=['Cart', 'Dwell Time'])
robot_dwell_df = pd.DataFrame(list(robot_dwell.items()), columns=['Robot', 'Dwell Time'])
indoor_idle_df = pd.DataFrame(list(indoor_idle.items()), columns=['Inbound ID', 'Dwell Time'])
outdoor_idle_df = pd.DataFrame(list(outdoor_idle.items()), columns=['Outbound ID', 'Dwell Time'])
out_density_df = pd.DataFrame(list(out_density.items()), columns=['Outbound Destination', 'Density'])
uph_tracker_df=pd.DataFrame(list(uph_tracker.items()), columns=["Hour", "UPH"])

# Calculate time metrics
fmt = "%Y-%m-%d %H:%M:%S,%f"
if start_time != 0 and end_time != 0:
    start_time_dt = datetime.strptime(start_time, fmt)
    end_time_dt = datetime.strptime(end_time, fmt)
    dashboard_time = (end_time_dt - start_time_dt) * sim_speed
    dhrs, rem = divmod(dashboard_time.total_seconds(), 3600)
    dmins, dsec = divmod(rem, 60)
    total_time = dhrs + dmins / 60
else:
    dhrs, dmins, dsec = 0, 0, 0
    total_time = 1  # Prevent division by zero



st.markdown("""
    <style>
    .main {
        background-color: #1f2937;
        color: #ffffff;
    }
    
    .metric-tile {
        background-color: #1f2937;
        color: #ffffff;
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border: 1px solid #374151;
        margin-bottom: 16px;
    }
    
    .metric-title {
        font-size: 24px;
        color: #9ca3af;
        font-weight: 500;
        margin-bottom: 8px;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 4px;
    }
    
    .metric-subtitle {
        font-size: 12px;
        color: #6b7280;
    }
    
    .chart-container {
        background-color: #1f2937;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid #374151;
    }
    
    .chart-title {
        font-size: 18px;
        font-weight: 600;
        color: #1f2937;  /* Changed from #1f2937 to #ffffff for visibility */
        margin-bottom: 16px;
    }
    
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 32px;
        padding: 24px;
        background-color: #1f2937;
        border-radius: 16px;
        border: 1px solid #374151;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    
    .logo {
        height: 40px;  /* Set desired height */
        width: auto;   /* Maintain aspect ratio */
        border-radius: 8px;
    }
    
    .time-info {
        color: #9ca3af;
        font-size: 14px;
    }
    
    .status-info {
        text-align: right;
        color: #9ca3af;
        font-size: 14px;
    }
    
    .status-active {
        color: #10b981;
        font-weight: 600;
        font-size: 16px;
    }
    
    .page-nav {
        background-color: #374151;
        border-radius: 12px;
        padding: 8px;
        margin-bottom: 24px;
        display: flex;
        gap: 8px;
    }
    
    .page-nav button {
        background-color: transparent;
        color: #9ca3af;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .page-nav button:hover {
        background-color: #4b5563;
        color: #ffffff;
    }
    
    .page-nav button.active {
        background-color: #3b82f6;
        color: #ffffff;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background-color: #374151;
        border-radius: 8px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #9ca3af;
        border-radius: 6px;
        padding: 12px 24px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)
# ===== PAGE NAVIGATION =====
# Initialize session state for page navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Overview'

# Page navigation
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button("📊 Overview", key="overview_btn", use_container_width=True):
        st.session_state.current_page = 'Overview'

with col2:
    if st.button("🔧 Inbound and Outbound Doors", key="door_btn", use_container_width=True):
        st.session_state.current_page = 'Inbound and Outbound Doors'

with col3:
    if st.button("📈 Cart Analytics", key="cart_btn", use_container_width=True):
        st.session_state.current_page = 'Cart Analytics'
with col4:
    if st.button("📈 Robot Analytics", key="robot_btn", use_container_width=True):
        st.session_state.current_page = 'Robot Analytics'

# ===== SHARED HEADER (appears on all pages) =====
# st.markdown("""
#     <div class="header-container">
#         <div class="logo-section">
#             <div class="logo">destro</div>
#             <div class="time-info">
#                 <div>Current</div>
#                 <div style="font-size: 16px; font-weight: 600; color: #ffffff;">6:44 PM</div>
#                 <div>Wednesday, 16 July 2025</div>
#             </div>
#         </div>
#         <div class="status-info">
#             <div>Simulation Status</div>
#             <div class="status-active">Active</div>
#         </div>
#     </div>
# """, unsafe_allow_html=True)
# Method 1: Using base64 encoded image (if you have a local file)
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# Load your logo
logo_base64 = get_image_base64("destro_logo.jpg")  # Update with your logo path
yusen_base64=get_image_base64("yusen_logo.png")
if logo_base64:
    st.markdown(f"""
        <div class="header-container">
            <div class="logo-section">
                <img src="data:image/png;base64,{logo_base64}" class="logo" alt="Destro Logo"
                  style="height: 50px; width: auto; border-radius: 8px;" 
                     alt="Yusen Logo">
                <img src="data:image/png;base64,{yusen_base64}" class="logo" alt="Destro Logo"
                  style="height: 80px; width: auto; border-radius: 8px;" 
                     alt="Yusen Logo">
                <div class="time-info">
                    <div>Current</div>
                    <div style="font-size: 16px; font-weight: 600; color: #ffffff;">6:44 PM</div>
                    <div>Tuesday, 22 April 2025</div>
                </div>
            </div>
            <div class="status-info">
                <div>Simulation Status</div>
                <div class="status-active">Static</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ===== PAGE CONTENT =====
if st.session_state.current_page == 'Overview':
    st.markdown("# 📊 System Analytics")
    
    # Main Metrics
    col1, col2, col3, col4, col5= st.columns(5)
    with col1:
        uph_value = int(code_101 / total_time) if total_time > 0 else 0
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">UPH</div>
                <div class="metric-value">{uph_value}</div>
                <div class="metric-subtitle">Units per hour</div>
            </div>
    """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Total Cases Picked</div>
                <div class="metric-value">{code_101:,}</div>
                <div class="metric-subtitle">Units processed</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Total Runtime</div>
                <div class="metric-value">{int(dhrs):02d}:{int(dmins):02d}:{int(dsec):02d}</div>
                <div class="metric-subtitle">HH:MM:SS</div>
            </div>
        """, unsafe_allow_html=True)

    

   
    with col4:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Active Robots</div>
                <div class="metric-value">{robot_count}</div>
                <div class="metric-subtitle">Currently operational</div>
            </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Active Carts</div>
                <div class="metric-value">{cart_count}</div>
                <div class="metric-subtitle">In circulation</div>
            </div>
        """, unsafe_allow_html=True)


    # Performance Charts
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
 
    with col1:
        st.markdown('<div class="chart-title">UPH Progression </div>', unsafe_allow_html=True)
        if not out_density_df.empty:  # You might want to change this condition to check uph_tracker_df
            chart_uph_break = alt.Chart(uph_tracker_df).mark_bar(size=20, color='#1f2937').encode(
                x=alt.X('Hour:N', sort='-y',
                    axis=alt.Axis(labelFontSize=24, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
                y=alt.Y('UPH:Q',
                    axis=alt.Axis(labelFontSize=24, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
                tooltip=['Hour', 'UPH']
            ).properties(height=500)  # Changed from height=00 to height=600
            st.altair_chart(chart_uph_break, use_container_width=True)
        else:
            st.write("No UPH data available")  # Updated message

    with col2:
        st.markdown('<div class="chart-title">Outbound Destination Density</div>', unsafe_allow_html=True)
        if not out_density_df.empty:
            chart_density = alt.Chart(out_density_df).mark_bar(size=20, color='#1f2937').encode(
                x=alt.X('Outbound Destination:N', sort='-y',
                    axis=alt.Axis(labelFontSize=15, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
                y=alt.Y('Density:Q',
                    axis=alt.Axis(labelFontSize=24, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
                tooltip=['Outbound Destination', 'Density']
            ).properties(height=600)  # Keep height=600
            st.altair_chart(chart_density, use_container_width=True)
        else:
            st.write("No density data available")

elif st.session_state.current_page == 'Inbound and Outbound Doors':
    st.markdown("# 🔧 Inbound - Outbound Data")
    
    # Dwell Time Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Active Inbound Doors</div>
                <div class="metric-value">{inbound_count}</div>
                <div class="metric-subtitle">Doors Available for Use</div>
               
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Active Outbound Doors</div>
                <div class="metric-value">{outbound_count}</div>
                <div class="metric-subtitle">Doors Available for Use</div>
             
            </div>
        """, unsafe_allow_html=True)

    with col3:
        total_inbound_dwell = sum(indoor_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Total Inbound Door Dwell Time</div>
                <div class="metric-value">{int(total_inbound_dwell)} min</div>
                <div class="metric-subtitle">Total idle time</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        total_inbound_dwell = sum(outdoor_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Total Outbound Door Dwell Time</div>
                <div class="metric-value">{int(total_inbound_dwell)} min</div>
                <div class="metric-subtitle">Total idle time</div>
            </div>
        """, unsafe_allow_html=True)

    # Operations Charts
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        if not indoor_idle_df.empty:
            st.markdown('<div class="chart-title">Inbound Dwell Time</div>', unsafe_allow_html=True)

            chart_inbound_idle = alt.Chart(indoor_idle_df).mark_bar(size=20,color='#1f2937').encode(
            x=alt.X('Inbound ID:N', sort=[f'Inbound {i}' for i in range(1,16)],
            axis=alt.Axis(labelFontSize=15, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
            y=alt.Y('Dwell Time:Q',axis=alt.Axis(labelFontSize=24, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
            tooltip=['Inbound ID', 'Dwell Time']
        ).properties(
            height=700 ,title='Inbound ID vs Dwell Time [min]'
        )
            st.altair_chart(chart_inbound_idle,use_container_width=True)
        else:
             st.write("No Inbound Door Data available")
    with col2:
        if not outdoor_idle_df.empty:
            st.markdown('<div class="chart-title">Inbound Dwell Time</div>', unsafe_allow_html=True)

            chart_inbound_idle = alt.Chart(outdoor_idle_df).mark_bar(size=20,color='#1f2937').encode(
            x=alt.X('Outbound ID:N', sort=[f'Outbound {i}' for i in range(1,42)],
            axis=alt.Axis(labelFontSize=15, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
            y=alt.Y('Dwell Time:Q',axis=alt.Axis(labelFontSize=24, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
            tooltip=['Outbound ID', 'Dwell Time']
        ).properties(
            height=700 ,title='Outbound ID vs Dwell Time [min]'
        )
            st.altair_chart(chart_inbound_idle,use_container_width=True)
        else:
             st.write("No Inbound Door Data available")
        # st.markdown('<div class="chart-title">Robot Trips</div>', unsafe_allow_html=True)
        # if not robot_trips_df.empty:
        #     chart_trips = alt.Chart(robot_trips_df).mark_bar(size=20, color='#f59e0b').encode(
        #         x=alt.X('Robot:N',
        #                axis=alt.Axis(labelFontSize=24, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
        #         y=alt.Y('Trips:Q',
        #                axis=alt.Axis(labelFontSize=24, titleFontSize=24 ,labelColor='#1f2937', titleColor='#1f2937')),
        #         tooltip=['Robot', 'Trips']
        #     ).properties(height=300)
        #     st.altair_chart(chart_trips, use_container_width=True)
        # else:
        #     st.write("No trip data available")


elif st.session_state.current_page == 'Cart Analytics':
    st.markdown("# 📈  Cart Analytics Dashboard")
    
    

    # col1=st.columns(1)
    # with col1:
    st.markdown('<div class="chart-title">Cart Cases Unloaded</div>', unsafe_allow_html=True)
    if not robot_total_cases_df.empty:
        chart_botuph = alt.Chart(robot_total_cases_df).mark_bar(size=10,color="#1f2937").encode(
    x=alt.X('Cart:N', sort=[f'{i}' for i in range(1,cart_count)],
    axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937',labelExpr="'Cart ' + datum.value")),
    y=alt.Y('Total Cases:Q',axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
).properties(width=2000, height=400, title="Cart vs Total Cases")
    st.altair_chart(chart_botuph,use_container_width=True)

    # with col2 :
    #     st.dataframe(cases_ph_df , use_container_width=True)
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
        total_cart_empty=sum(cart_empty_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Cart Empty Dwell Time</div>
                <div class="metric-value">{int(total_cart_empty)} mins</div>
                <div class="metric-subtitle">Total time empty carts stayed without being moved</div>
            </div>
        """, unsafe_allow_html=True)
       
    
    with col3:
        total_cart_full=sum(cart_full_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Cart Full Dwell Time</div>
                <div class="metric-value">{int(total_cart_full)} mins</div>
                <div class="metric-subtitle">Total time full carts stayed without being moved</div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-title">Cart Empty Dwell Time</div>', unsafe_allow_html=True)
        if not cart_empty_idle_df.empty:
            chart_empty_idle = alt.Chart(cart_empty_idle_df).mark_bar(size=10,color="#1f2937").encode(
            x=alt.X('Cart:N', sort=[f'Cart {i}' for i in range(1,cart_count)],
            axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
            y=alt.Y('Dwell Time:Q',axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
            tooltip=['Cart', 'Dwell Time']
        ).properties(
            
            height=400 ,title='Cart vs Dwell Time [min]'
        )
        st.altair_chart(chart_empty_idle,use_container_width=True)

       

    
    with col2:
        st.markdown('<div class="chart-title">Cart Full Dwell Time</div>', unsafe_allow_html=True)
        if not cart_full_idle_df.empty:
            chart_full_idle = alt.Chart(cart_full_idle_df).mark_bar(size=10,color="#1f2937").encode(
            x=alt.X('Cart:N', sort=[f'Cart {i}' for i in range(1,cart_count)],
            axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
            y=alt.Y('Dwell Time:Q',axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
            tooltip=['Cart', 'Dwell Time']
        ).properties(
            
            height=400 ,title='Cart vs Dwell Time [min]'
        )
        st.altair_chart(chart_full_idle,use_container_width=True)
            
    # Additional Analytics Section


elif st.session_state.current_page == 'Robot Analytics':
    st.markdown("# 📈  Robot Analytics Dashboard")
    
    
    # Performance Summary Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Active Robots</div>
                <div class="metric-value">{robot_count}</div>
                <div class="metric-subtitle">Fleet Size</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        avg_robot_distance = robot_dist_df['Distance'].mean() if not robot_dist_df.empty else 0
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Avg Robot Distance</div>
                <div class="metric-value">{avg_robot_distance:.1f} m</div>
                <div class="metric-subtitle">Per robot average</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        trip_sum = sum(int(v) for v in trips_robot.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Total Trips Across Fleet</div>
                <div class="metric-value">{trip_sum} </div>
                <div class="metric-subtitle">Trips Across Fleet</div>
            </div>
        """, unsafe_allow_html=True)
    # Data Tables Section
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 =st.columns(2)
    with col1:
        st.markdown('<div class="chart-title">Distance Travlled by Robots</div>', unsafe_allow_html=True)
        if not robot_dist_df.empty:
            chart_dist = alt.Chart(robot_dist_df).mark_bar(size=10,color="#1f2937").encode(
            x=alt.X('Robot:N', sort=robot_dist_df["Robot"].tolist(),
            axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
            y=alt.Y('Distance:Q',axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
            tooltip=['Robot', 'Distance']
        ).properties(
            
            height=400 ,title='Robot vs Distance [m]'
        )
        st.altair_chart(chart_dist,use_container_width=True)

   

    
    with col2:
        st.markdown('<div class="chart-title">Trips Made by Robots</div>', unsafe_allow_html=True)
        if not robot_trips_df.empty:
            chart_trips = alt.Chart(robot_trips_df).mark_bar(size=10,color="#1f2937").encode(
            x=alt.X('Robot:N', sort=[f'Robot {i}' for i in range(1,cart_count)],
            axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
            y=alt.Y('Trips:Q',axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
            tooltip=['Robot', 'Trips']
        ).properties(
            
            height=400 ,title='Robot vs Trips '
        )
        st.altair_chart(chart_trips,use_container_width=True)



    st.markdown('<div class="chart-title">Robot Dwell Time</div>', unsafe_allow_html=True)
    if not robot_dwell_df.empty:
        chart_trips = alt.Chart(robot_dwell_df).mark_bar(size=20,color="#1f2937").encode(
        x=alt.X('Robot:N', sort=[f'Robot {i}' for i in range(1,cart_count)],
        axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
        y=alt.Y('Dwell Time:Q',axis=alt.Axis(labelFontSize=12, titleFontSize=12 ,labelColor='#1f2937', titleColor='#1f2937')),
        tooltip=['Robot', 'Dwell Time']
    ).properties(
        
        height=400 ,title='Robot vs Dwell Time [min] '
    )   
        st.altair_chart(chart_trips,use_container_width=True)


