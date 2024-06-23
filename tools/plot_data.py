"""
import matplotlib.pyplot as plt
import pandas as pd
import argparse

# Create the parser
parser = argparse.ArgumentParser(description='Create a power usage plot from a CSV file.')

# Add the filename argument
parser.add_argument('filename', type=str, help='The name of the CSV file.')

# Parse the arguments
args = parser.parse_args()

# Read the data into a pandas DataFrame
data = pd.read_csv(args.filename, names=['time', 'device', 'power_usage', 'action'])

# Convert the time column to datetime
data['time'] = pd.to_datetime(data['time'], unit='s')

# Get unique devices and actions
devices = data['device'].unique()
actions = data['action'].unique()

# Create a figure and a set of subplots
fig, ax = plt.subplots()

# Loop over devices and actions and plot
for device in devices:
    for action in actions:
        device_action_data = data[(data['device'] == device) & (data['action'] == action)]
        ax.plot(device_action_data['time'], device_action_data['power_usage'], label=f'Device {device}, Action {action}')

# Set a title and labels
ax.set_title('Power Usage over Time')
ax.set_xlabel('Time')
ax.set_ylabel('Power Usage')

# Show the legend
ax.legend()

# Show the plot
plt.show()
"""

"""
import matplotlib.pyplot as plt
import pandas as pd
import argparse

# Create the parser
parser = argparse.ArgumentParser(description='Create a power usage plot from a CSV file.')

# Add the filename argument
parser.add_argument('filename', type=str, help='The name of the CSV file.')

# Parse the arguments
args = parser.parse_args()

# Read the data into a pandas DataFrame
data = pd.read_csv(args.filename, names=['time', 'device', 'power_usage', 'action'])

# The rest of the script is the same as before

# Get unique devices
devices = data['device'].unique()

# Create a figure and a set of subplots
fig, ax = plt.subplots()

# Loop over devices and plot
for device in devices:
    device_data = data[data['device'] == device]
    ax.plot(device_data['time'], device_data['power_usage'], label=f'Device {device}')
    ax.step(device_data['time'], device_data['action'], where='post', label=f'Device {device}')

# Set a title and labels
ax.set_title('Power Usage over Time')
ax.set_xlabel('Time')
ax.set_ylabel('Power Usage')

# Show the legend
ax.legend()

# Show the plot
plt.show()
"""








"""
import matplotlib.pyplot as plt
import pandas as pd
import argparse

# Create the parser
parser = argparse.ArgumentParser(description='Create a power usage plot from a CSV file.')

# Add the filename argument
parser.add_argument('filename', type=str, help='The name of the CSV file.')

# Parse the arguments
args = parser.parse_args()

# Read the data into a pandas DataFrame
data = pd.read_csv(args.filename, names=['time', 'device', 'power_usage', 'action', 'state'])

# The rest of the script is the same as before

# Get unique devices
devices = data['device'].unique()

# Create a figure and a set of subplots
fig, ax1 = plt.subplots()   # power usage
fig, ax2 = plt.subplots()   # action
fig, ax3 = plt.subplots()   # action

# Loop over devices and plot
for device in devices:
    device_data = data[data['device'] == device]
    ax1.plot(device_data['time'], device_data['power_usage'], label=f'Device {device} power usage')

# Set the labels for the first y-axis
ax1.set_xlabel('Time')
ax1.set_ylabel('Power Usage')
ax1.tick_params(axis='y', labelcolor='tab:red')

# Create a secondary y-axis
ax2 = ax1.twinx()

# Loop over devices and plot
for device in devices:
    device_data = data[data['device'] == device]
    ax2.step(device_data['time'], device_data['action'], where='post', color='red', label=f'Device {device} action')

# Set the labels for the second y-axis
ax2.set_ylabel('Action')
ax2.tick_params(axis='y', labelcolor='tab:blue')

# Create a third y-axis
ax3 = ax1.twinx()

# Loop over devices and plot
for device in devices:
    device_data = data[data['device'] == device]
    ax3.step(device_data['time'], device_data['state'], where='post', color='green', label=f'Device {device} state')

# Set the labels for the third y-axis
ax3.set_ylabel('State')
ax3.tick_params(axis='y', labelcolor='tab:blue')

# Set a title and show the legend
fig.tight_layout()
ax1.set_title('Power Usage and Action over Time')
fig.legend(loc='upper right')

# Show the plot
plt.show()
"""




import matplotlib.pyplot as plt
import pandas as pd
import argparse

# Create the parser
parser = argparse.ArgumentParser(description='Create a power usage plot from a CSV file.')

# Add the filename argument
parser.add_argument('filename', type=str, help='The name of the CSV file.')

# Parse the arguments
args = parser.parse_args()

# Read the data into a pandas DataFrame
data = pd.read_csv(args.filename, names=['time', 'device', 'power_usage', 'action', 'state'])

# Convert the time column to datetime
#data['time'] = pd.to_datetime(data['time'], unit='s')

# Get unique devices
devices = data['device'].unique()

# Create a figure and a set of subplots
fig, ax1 = plt.subplots()

# Loop over devices and plot power usage
for device in devices:
    device_data = data[data['device'] == device]
    ax1.plot(device_data['time'], device_data['power_usage'], label=f'Device {device} power usage')

# Set the labels for the first y-axis
ax1.set_xlabel('Time')
ax1.set_ylabel('Power Usage')
ax1.tick_params(axis='y', labelcolor='tab:red')

# Create a secondary y-axis for action
ax2 = ax1.twinx()

# Loop over devices and plot action
for device in devices:
    device_data = data[data['device'] == device]
    ax2.step(device_data['time'], device_data['action'], where='post', color='red', label=f'Device {device} action')

# Set the labels for the second y-axis
ax2.set_ylabel('Action')
ax2.tick_params(axis='y', labelcolor='tab:blue')

# Create a third y-axis for state
ax3 = ax1.twinx()

# Offset the third y-axis
ax3.spines['right'].set_position(('outward', 60))

# Loop over devices and plot state
for device in devices:
    device_data = data[data['device'] == device]
    ax3.step(device_data['time'], device_data['state'], where='post', color='green', label=f'Device {device} state')

# Set the labels for the third y-axis
ax3.set_ylabel('State')
ax3.tick_params(axis='y', labelcolor='tab:blue')

# Set a title and show the legend
fig.tight_layout()
ax1.set_title('Power Usage, Action, and State over Time')
fig.legend(loc='upper right')

# Show the plot
plt.show()