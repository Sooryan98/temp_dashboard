import streamlit as st
import pandas as pd
import altair as alt
import re
import os
from collections import defaultdict
from datetime import datetime
from collections import Counter

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DESTRO_PATH = os.path.join(BASE_DIR, "yusen", "logs", "inputlog", "yusen_2025-04-10.log")
# FMS_PATH = os.path.join(BASE_DIR, "yusen", "logs", "inputlog", "FMS_2025-04-10.log")
# DESTRO_PATH = "log_bank/1_1/1 Jul_2025/yusen_2025-07-01.log"
# FMS_PATH = "log_bank/1_1/1 Jul_2025/FMS_2025-07-01.log"

DESTRO_PATH = "log_bank/1_Many/DEMO-20x/15R60C/yusen_2025-07-27.log"
FMS_PATH = "log_bank/1_Many/DEMO-20x/15R60C/FMS_2025-07-27.log"

st.set_page_config(page_title="destro", layout="wide")


# ---------------- Data Structures ----------------dashboard_time=0
sim_speed=20
robot_count=15
cart_count=60
start_time=0
end_time=0
ptrack=0
inbound_count = 15
outbound_count = 42

robot_destro_data = defaultdict(lambda: defaultdict(dict))
progress_track={"0.0":0}
progress=defaultdict(int)
task_id_tracker=[]
uph_tracker={}
log_data = {"total_cases": 0}
robot_fms_data = {f"Robot {i+1}": 0 for i in range(15)}
robot_total_cases={f"Robot {i+1}" : 0 for i in range(15)}
robot_dwell={f"Robot {i+1}" : 0 for i in range(15)}
cases_per_hour = defaultdict(lambda: defaultdict(int))
log_time_format = "%Y-%m-%d %H:%M:%S,%f"
robot_destro_data = defaultdict(lambda: defaultdict(dict))
robot_total_cases = defaultdict(int)
cases_per_hour = defaultdict(lambda: defaultdict(int))
trips_robot={}
cart_empty_idle={}
cart_full_idle={}
indoor_idle={}
outdoor_idle={}

outbound_counter = Counter()
# robot_destro_data = defaultdict(lambda: defaultdict(lambda: {"loaded_cases": 0, "total_cases": 0}))

# ---------------- DESTRO Log Parser ----------------
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
outbound_destinations={v:k for k,v in destination_mapping.items()}

import base64

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def download_log(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text.splitlines()

def outbound_density(log_path):

    with open(log_path, "r") as f:
        lines = f.readlines()



    pattern = re.compile(r"route:\s*(\[[^\]]*\])")

    for line in lines:
        if "[Coordination] Starting coordination for cart" in line:
            match = pattern.search(line)
            if match:
                route_list = eval(match.group(1))  
                outbound_counter.update(route_list)


    # for outbound, count in outbound_counter.items():
    #     print(f"{outbound}: {count}")



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

                        # Round down to the hour
                        log_hour_str = log_time.strftime("%Y-%m-%d %H:00")
                # pattern = re.compile(
                #     r"CODE 201 \[Batch (\d+)] Robot (\d+) unloading case (\d+) of (\d+) for item (\d+)"
                # )
                # match = pattern.search(line)
                # if match:
                 
                #     batch, robot_id, case_num, total_cases, item_id = match.groups()
                #     robot_key = f"Robot {int(robot_id)+1}"
                #     robot_destro_data[robot_key][item_id] = {
                #         "batch": int(batch),
                #         "case_num": int(case_num),
                #         "total_cases": int(total_cases),
                #     }
                #     # if  item_id not in task_id_tracker:
                #     #     task_id_tracker.append(item_id)
                #     robot_total_cases[f'Robot {int(robot_id)+1}'] +=1
                #     cases_per_hour[robot_key][log_hour_str] += 1
         

                pattern = re.compile(r"CODE 201 \[Cart CART_(\d+)] Loading case (\d+) of (\d+) from cart \w+ for item (\d+)")

                match = pattern.search(line)
                if match:
                    cart_id, current_case, total_cases, item_id = match.groups()
                    current_case = int(current_case)
                    total_cases = int(total_cases)
                    
                    robot_destro_data[f"Cart {int(cart_id)}"][item_id] = {
                        # "loaded_cases": current_case,
                        "total_cases": total_cases
                    }
                    # robot_destro_data[cart_id][item_id]["loaded_cases"] += 1
                    # robot_destro_data[cart_id][item_id]["total_cases"] = int(total_cases)
                    robot_total_cases[cart_id] += 1

                    cases_per_hour[cart_id][log_hour_str] += 1

            elif "CODE 101" in line:
                pattern = re.compile(r"CODE 101 --------------- (\d+)")
                match = pattern.search(line)
                if match:
                    cases = match.groups()
                    log_data["total_cases"] = int(cases[0])
            elif "[IDLE] CODE 701 " in line:
                # pattern=  re.compile(r"[IDLE] Cart CART_(\d+) total idle time: ([\d.]+) seconds")
                pattern = re.compile(r"\[IDLE\] CODE 701 Cart CART_(\d+) total idle time: ([\d.]+) seconds")

                match=pattern.search(line)
                if match:
                    cart_id,idle_time=match.groups()
                    idle_time=float(idle_time)/60
                    cart_full_idle[f"Cart {cart_id}"]=idle_time
            elif "[IDLE] CODE 601 " in line:
                # pattern=  re.compile(r"[IDLE] Cart CART_(\d+) total idle time: ([\d.]+) seconds")
                pattern = re.compile(r"\[IDLE\] CODE 601 Cart CART_(\d+) total idle time: ([\d.]+) seconds")

                match=pattern.search(line)
                if match:
                    cart_id,idle_time=match.groups()
                    idle_time=float(idle_time)/60
                    cart_empty_idle[f"Cart {cart_id}"]=idle_time
            elif "CODE 501" in line:
                
                pattern= re.compile(r"CODE 501 Trips taken by Robot_(\d+) is (\d+)")
                match=pattern.search(line)
                if match:
                    robot_id,trips=match.groups()
                    trips_robot[f"Robot {int(robot_id)+1}"]=trips
            elif "[DOOR DWELL] CODE 801 Inbound" in line:
                pattern=re.compile(r"\[DOOR DWELL\] CODE 801 Inbound dock Inbound_(\d+) total dwell time : ([\d.]+)")
                match=pattern.search(line)
                if match:
                    indoor_id, dtime=match.groups()
                    dtime =float(dtime)/60
                    indoor_idle[f"Inbound {indoor_id}"]=dtime
            elif "[DOOR DWELL] CODE 801 Outbound" in line:
                pattern=re.compile(r"\[DOOR DWELL\] CODE 801 Outbound dock Outbound_(\d+) total dwell time : ([\d.]+)")
                match=pattern.search(line)
                if match:
                    outdoor_id, dtime=match.groups()
                    dtime =float(dtime)/60
                    outdoor_idle[f"Outbound {outdoor_id}"]=dtime

# ---------------- FMS Log Parser ----------------
def parse_fms_log(path):
    global ptrack, start_time, end_time,dashboard_time
    if not os.path.exists(path):
        return

    with open(path, "r") as file:
        # file=download_log(FMS_URL)
        
        for line in file:
            line = re.sub(r'\x1b\[[0-9;]*m', '', line)

            if "CODE F01" in line:
                # timestamp_match = re.match(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+)', line)
                # if timestamp_match:
                #         log_time_str = timestamp_match.group(1)
                #         log_time = datetime.strptime(log_time_str, log_time_format)
                #         log_hr=log_time.hour
                #         # Round down to the hour
                #         log_hour_str = log_time.strftime("%Y-%m-%d %H:00")
                pattern = re.compile(r"CODE F01 at (\d+\.\d+) number of cases finished is (\d+)")
                match = pattern.search(line)
                if match:
                    hour, cases = match.groups()
                    cases_until_now= sum(progress_track.values())
                    progress_track[hour]=int(cases)   
                    
                    progress_track[hour]=progress_track[hour]-cases_until_now
                    progress[hour]=progress_track[hour]
                    if progress[hour]!=ptrack:
                        ptrack=progress[hour]
                        match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                        if match:
                            timestamp = match.group(1)
                            end_time=timestamp
                        
                    # if log_hr!=0:
                    #     uph_track[log_hr]=progress[hour]*60/log_hr
                
            elif "CODE F02" in line:
                    print(line)
                    pattern =re.compile(
                            r"CODE F02 at (\d+\.\d+) UPH is (\d+)"

)
                    match=pattern.search(line)
                    # print(match)
                    if match:
                        hour,uph=match.groups()
                        uph_tracker[hour]=uph
            elif "CODE 000" in line :
                match = re.search(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                if match:
                    timestamp = match.group(1)
                    start_time=timestamp
            elif "has dwelled" in line:
                pattern = re.compile(r"Robot robot_(\d+) has dwelled for ([\d.]+) sec")
                match=pattern.search(line)
                if match:
                    robot_id,dwell_time=match.groups()
                    dwell_time=round(float(dwell_time),2)/60
                    robot_key = f"Robot {int(robot_id)+1}"
                    if dwell_time!=0:
                        robot_dwell[robot_key]=dwell_time
            else:
                pattern = re.compile(r"Robot robot_(\d+)\s+has travelled\s+([\d\.]+)\s+m")
                match = pattern.search(line)
                if match:
                    robot_id, dist = match.groups()
                    if int(robot_id)<25:

                        robot_key = f"Robot {int(robot_id)+1}"
                        robot_fms_data[robot_key] = float(dist)

# ---------------- Run Parsers ----------------
parse_destro_log(DESTRO_PATH)

parse_fms_log(FMS_PATH)
print(f"{start_time} ------- {type(start_time)}")
print(f"{end_time} ------- {type(end_time)}")
outbound_density(DESTRO_PATH)



out_density={}
for k,v in outbound_counter.items():
    if k in outbound_destinations:
        out_density[outbound_destinations[k]]=v




print(cases_per_hour)
# ---------------- Prepare DataFrames ----------------
rows = []
code_101=0
for cart, items in robot_destro_data.items():
    for item_id, data in items.items():
        
        rows.append({
            "CART": cart,
            "Item ID": item_id,
            
            # "Case Num": data["loaded_cases"],
            "Total Cases": data["total_cases"]
        })

df = pd.DataFrame(rows)
print(df)
# robot_cases_df = (
#     df.groupby("Robot")["Case Num"].max().reset_index().sort_values(by="Robot")
# )
cases_ph_df = pd.DataFrame(cases_per_hour).T.fillna(0).astype(int)

cases_ph_df= cases_ph_df.reindex(sorted(cases_ph_df.columns), axis=1)

cases_ph_df["Total cases overall"] = cases_ph_df.sum(axis=1)
code_101=cases_ph_df['Total cases overall'].sum()
cases_ph_df.loc["Total per hour"] = cases_ph_df.sum(axis=0)
# robot_dist_df = pd.DataFrame(list(robot_fms_data.items()), columns=["Robot", "Distance"]).sort_values(by="Robot")
robot_dist_df = pd.DataFrame(list(robot_fms_data.items()), columns=["Robot", "Distance"])

robot_dist_df["Robot_Num"] = robot_dist_df["Robot"].str.extract(r'(\d+)').astype(int)
robot_dist_df = robot_dist_df.sort_values(by="Robot_Num")

progress_df=pd.DataFrame(list(progress.items()), columns=["Hour", "Cases"])
uph_tracker_df=pd.DataFrame(list(uph_tracker.items()), columns=["Hour", "UPH"])

robot_total_cases_df=pd.DataFrame(list(robot_total_cases.items()), columns=["Cart", "Total Cases"])
# robot_total_cases_df["Robot_Num"] = robot_total_cases_df["Robot"].str.extract(r'(\d+)').astype(int)
# robot_total_cases_df = robot_total_cases_df.sort_values(by="Robot_Num")
robot_trips_df=pd.DataFrame(list(trips_robot.items()),columns=['Robot','Trips'])
cart_full_idle_df=pd.DataFrame(list(cart_full_idle.items()),columns=['Cart','Dwell Time'])
cart_empty_idle_df=pd.DataFrame(list(cart_empty_idle.items()),columns=['Cart','Dwell Time'])
robot_dwell_df=pd.DataFrame(list(robot_dwell.items()),columns=['Robot','Dwell Time'])
indoor_idle_df=pd.DataFrame(list(indoor_idle.items()),columns=['Inbound ID','Dwell Time'])
outdoor_idle_df=pd.DataFrame(list(outdoor_idle.items()),columns=['Outbound ID','Dwell Time'])
out_density_df=pd.DataFrame(list(out_density.items()),columns=['Outbound Destination','Density'])
# robot_dwell_df=pd.DataFrame(list(robot_distance_dict))
# robot_dwell_df=pd.DataFrame(list(robot_dwell.items()),columns=['Robot','Time (sec)'])
# robot_dwell_df["Time (hrs)"] = robot_dwell_df["Time (sec)"] / 3600


fmt = "%Y-%m-%d %H:%M:%S,%f"
# 2025-06-17 14:29:59,162
# 2025-06-18 15:40:40,196

# start_time='2025-06-24 08:34:28,000000'
end_time='2025-07-27 21:29:22,000000'
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

# Enhanced CSS with animations and modern styling
def get_image_base64(image_path):
    import base64
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None
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
    
    .page-nav-button {
        background: linear-gradient(145deg, #374151, #4b5563) !important;
        color: #d1d5db !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 16px 24px !important;
        margin: 0 8px 24px 0 !important;
        font-weight: 500 !important;
        font-size: 15px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    .page-nav-button:hover {
        background: linear-gradient(145deg, #4b5563, #6b7280) !important;
        color: #ffffff !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4) !important;
    }
    
    .page-nav-button.active {
        background: linear-gradient(145deg, #3b82f6, #2563eb) !important;
        color: #ffffff !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4) !important;
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
        animation: fadeIn 10s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for page navigation
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Overview'

# Enhanced Page Navigation with custom styling
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

with col1:
    if st.button(" Overview", key="overview_btn", use_container_width=True):
        st.session_state.current_page = 'Overview'

with col2:
    if st.button("Dock Analytics", key="door_btn", use_container_width=True):
        st.session_state.current_page = 'Inbound and Outbound Docks'

with col3:
    if st.button("Cart Analytics", key="cart_btn", use_container_width=True):
        st.session_state.current_page = 'Cart Analytics'

with col4:
    if st.button("Robot Analytics", key="robot_btn", use_container_width=True):
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
    header_content += '''
                <div class="time-info">
                    <div>Current Time</div>
                    <div>6:44 PM</div>
                    <div>Tuesday, 22 April 2025</div>
                </div>
            </div>
            <div class="status-info">
                <div>Simulation Status</div>
                <div class="status-active">Static</div>
            </div>
        </div>
    '''
    
    st.markdown(header_content, unsafe_allow_html=True)

# Enhanced Page Content with better color schemes
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
                <div class="metric-value">{int(dhrs):02d}:{int(dmins):02d}:{int(dsec):02d}</div>
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
        total_inbound_dwell = sum(indoor_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Inbound Dwell</div>
                <div class="metric-value">{int(total_inbound_dwell)} min</div>
                <div class="metric-subtitle">Total idle time</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        total_outbound_dwell = sum(outdoor_idle.values())
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
        total_cart_empty = sum(cart_empty_idle.values())
        st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-title">Empty Cart Dwell</div>
                <div class="metric-value">{int(total_cart_empty)} min</div>
                <div class="metric-subtitle">Total idle time</div>
            </div>
        """, unsafe_allow_html=True)
       
    with col3:
        total_cart_full = sum(cart_full_idle.values())
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
        trip_sum = sum(int(v) for v in trips_robot.values()) if trips_robot else 0
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