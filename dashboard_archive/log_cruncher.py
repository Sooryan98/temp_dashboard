import re
# # Define the input and output file paths

# input_file_path = '/home/soorya/dashboard__logs/FMS_2025-04-18.log'  # Replace with your actual file path
# output_file_path = 'crunched.log'  # Output file to store filtered lines

# # Open the input file for reading and output file for writing
# with open(input_file_path, 'r') as infile, open(output_file_path, 'w') as outfile:
#     # Iterate over each line in the input file
#     for line in infile:
#         # Write the line to the output file only if it does not contain "travelled 0 m"
#         if 'travelled 0 m' not in line:
#             outfile.write(line)

# print(f"Filtered log saved to {output_file_path}")

# # Define the input and output file paths
input_file_path = '/home/soorya/dashboard__logs/FMS_2025-04-18.log'  # Replace with your actual file path
output_file_path = '21utow.log'  # Output file to store filtered lines
latest_logs = {}
# Dictionary to store the latest log for each robot
non_distance_logs = []

# Open the input file for reading
with open(input_file_path, 'r') as infile:
    # Iterate over each line in the input file
    for line in infile:
        # Check if the line is related to the distance traveled
        if 'travelled' in line and 'm' in line:
            # Use regex to capture the robot name and distance traveled
            match = re.search(r'Robot (\S+) has travelled ([\d\.]+) m', line)
            
            if match:
                robot_name = match.group(1)
                distance = float(match.group(2))  # Convert distance to float
                
                # Update the latest log for each robot with the latest distance
                if distance > 0:
                 latest_logs[robot_name] = line
        else:
            # Keep non-distance logs
            non_distance_logs.append(line)

# Write the non-distance logs and the latest distance logs to the output file
with open(output_file_path, 'w') as outfile:
    # Write non-distance logs first
    for log in non_distance_logs:
        outfile.write(log)
    
    # Write the latest log for each robot
    for log in latest_logs.values():
        outfile.write(log)

print(f"Filtered log with the last entry for each robot saved to {output_file_path}")
