import streamlit as st
import pandas as pd
import altair as alt
import re
import os
from collections import defaultdict
from datetime import datetime


# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DESTRO_PATH = os.path.join(BASE_DIR, "yusen", "logs", "inputlog", "yusen_2025-04-10.log")
# FMS_PATH = os.path.join(BASE_DIR, "yusen", "logs", "inputlog", "FMS_2025-04-10.log")
# DESTRO_PATH = "log_bank/1_1/1 Jul_2025/yusen_2025-07-01.log"
# FMS_PATH = "log_bank/1_1/1 Jul_2025/FMS_2025-07-01.log"
DESTRO_PATH = "log_bank/1_1/2 Jul_2025/yusen_2025-07-01.log"
FMS_PATH = "log_bank/1_1/2 Jul_2025/FMS_2025-07-01.log"


st.set_page_config(page_title="destro", layout="wide")


# ---------------- Data Structures ----------------dashboard_time=0

robot_count=2
cart_count=6
start_time=0
end_time=0
ptrack=0

robot_destro_data = defaultdict(lambda: defaultdict(dict))
progress_track={"0.0":0}
progress=defaultdict(int)
task_id_tracker=[]
uph_tracker={}
log_data = {"total_cases": 0}
robot_fms_data = {f"Robot {i+1}": 0 for i in range(2)}
robot_total_cases={f"Robot {i+1}" : 0 for i in range(2)}
robot_dwell={f"Robot {i+1}" : 0 for i in range(2)}
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
# robot_destro_data = defaultdict(lambda: defaultdict(lambda: {"loaded_cases": 0, "total_cases": 0}))

# ---------------- DESTRO Log Parser ----------------

def download_log(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text.splitlines()
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

# robot_dwell_df=pd.DataFrame(list(robot_distance_dict))
# robot_dwell_df=pd.DataFrame(list(robot_dwell.items()),columns=['Robot','Time (sec)'])
# robot_dwell_df["Time (hrs)"] = robot_dwell_df["Time (sec)"] / 3600


fmt = "%Y-%m-%d %H:%M:%S,%f"
# 2025-06-17 14:29:59,162
# 2025-06-18 15:40:40,196

# start_time='2025-06-24 08:34:28,000000'
end_time='2025-07-02 02:01:51,000000'
start_time = datetime.strptime(start_time, fmt)
end_time= datetime.strptime(end_time, fmt)
dashboard_time=end_time-start_time
dhrs, rem =divmod(dashboard_time.total_seconds(),3600)
dmins,dsec =divmod(rem,60)
total_sec=dashboard_time.total_seconds()
avg_uph = sum(int(v) for v in uph_tracker.values()) / len(uph_tracker)
# ---------------- Display Dashboard ----------------
st.markdown(
    """
    <style>
    body {
        background-color: #e6f2ff;  /* Light blue background */
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.image("destro_logo_black.png", width=400)
col1,col2=st.columns(2)
with col1:
    st.metric(label="Time", value=f"{int(dhrs)} : {int(dmins)} : {int(dsec)}")
    
    total_time=dhrs+dmins/60
    st.metric(label="Total Cases Picked", value=code_101)
    st.metric(label="UPH", value=f"{int(code_101/total_time)}")
with col2:
    st.metric(label="Total Robots in Sim", value=f"{robot_count}")
    st.metric(label="Total Carts in Sim", value=f"{cart_count}")


robot_distance_dict = dict(zip(robot_dist_df["Robot"], total_sec-(robot_dist_df["Distance"]/1.5)))
# print(robot_distance_dict)


#  robot_dwell_df=pd.DataFrame(list(robot_distance_dict))



# chart_cases = alt.Chart(robot_cases_df).mark_bar().encode(
#     x=alt.X('Robot:N', sort='ascending'),
#     y='Case Num:Q'
# ).properties(width=2000, height=400, title="Robot vs Cases Unloaded in this Trip")

# chart_dist = alt.Chart(robot_dist_df).mark_bar().encode(
#     x=alt.X('Robot:N', sort='ascending'),
#     y='Distance:Q'
# ).properties(width=2000, height=400, title="Robot vs  Distance Travelled")
# chart_botuph = alt.Chart(robot_total_cases_df).mark_bar().encode(
#     x=alt.X('Robot:N', sort='ascending'),
#     y='Total Cases:Q'
# ).properties(width=2000, height=400, title="Robot vs Total Cases")
chart_dist = alt.Chart(robot_dist_df).mark_bar(size=150).encode(
    x=alt.X('Robot:N',sort=robot_dist_df["Robot"].tolist()),  # Ensure robots are in ascending order
    y='Distance:Q'
).properties(width=2000,height=400,
    title="Robot vs Distance [m]")

chart_botuph = alt.Chart(robot_total_cases_df).mark_bar(size=150).encode(
    x=alt.X('Cart:N'),
    y='Total Cases:Q'
).properties(width=2000, height=400, title="Cart vs Total Cases")



# Bar chart using Altair
chart_trips = alt.Chart(robot_trips_df).mark_bar(size=150).encode(
    x='Robot:N',
    y='Trips:Q',
    tooltip=['Robot', 'Trips']
).properties(
    width=2000,
    height=400 , title= 'Robot vs Trips Made'
)
chart_full_idle = alt.Chart(cart_full_idle_df).mark_bar(size=150).encode(
    x='Cart:N',
    y='Dwell Time:Q',
    tooltip=['Cart', 'Dwell Time']
).properties(
    width=2000,
    height=400 ,title='Cart vs Dwell Time [min]'
)
chart_empty_idle = alt.Chart(cart_empty_idle_df).mark_bar(size=150).encode(
    x='Cart:N',
    y='Dwell Time:Q',
    tooltip=['Cart', 'Dwell Time']
).properties(
    width=2000,
    height=400 ,title='Cart vs Dwell Time [min]'
)

chart_robot_idle = alt.Chart(robot_dwell_df).mark_bar(size=150).encode(
    x='Robot:N',
    y='Dwell Time:Q',
    tooltip=['Robot', 'Dwell Time']
).properties(
    width=2000,
    height=400 ,title='Robot vs Dwell Time [min]'
)

chart_inbound_idle = alt.Chart(indoor_idle_df).mark_bar(size=150).encode(
    x='Inbound ID:N',
    y='Dwell Time:Q',
    tooltip=['Inbound ID', 'Dwell Time']
).properties(
    width=2000,
    height=400 ,title='Inbound ID vs Dwell Time [min]'
)


chart_outbound_idle = alt.Chart(outdoor_idle_df).mark_bar(size=100).encode(
    x='Outbound ID:N',
    y='Dwell Time:Q',
    tooltip=['Outbound ID', 'Dwell Time']
).properties(
    width=2000,
    height=400 ,title='Outbound ID vs Dwell Time [min]'
)




# st.altair_chart(chart_cases, use_container_width=False)
st.altair_chart(chart_dist, use_container_width=False)
st.title("CART Unloading Cases per Hour")
st.dataframe(cases_ph_df , use_container_width=True)
st.altair_chart(chart_botuph, use_container_width=False)
st.metric(label="Total Full Cart Dwell Time", value=)
st.title("Full Cart Dwell Time")
st.altair_chart(chart_full_idle,use_container_width=False)
st.title("Empty Cart Dwell Time")
st.altair_chart(chart_empty_idle,use_container_width=False)
st.title("Robot Dwell Time")
st.altair_chart(chart_robot_idle,use_container_width=False)
st.title("Inbound Door Dwell Time")
st.altair_chart(chart_inbound_idle,use_container_width=False)
st.title("Outbound Door Dwell Time")
st.altair_chart(chart_outbound_idle,use_container_width=False)


st.title("Robot Trips")
st.altair_chart(chart_trips,use_container_width=True)
st.write("### CART Unloading Status")
st.dataframe(df, use_container_width=True)
# st.write("### Progress over time")
# st.dataframe(progress_df, use_container_width=True)
st.write("### UPH break down")
st.dataframe(uph_tracker_df, use_container_width=True)


