# created with help of Claude.ai

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from matplotlib.lines import Line2D

# Load data from the JSON file
with open('results.json', 'r') as f:
    data = json.load(f)

# Convert data to pandas DataFrame
df = pd.DataFrame(data)

# Convert string values to numeric
df['freq'] = df['freq'].astype(float)
df['beta'] = df['beta'].astype(float)
df['pen_betaCV'] = df['pen_betaCV'].astype(float)
df['pen_r2CV'] = df['pen_r2CV'].astype(float)
df['pen_betaCA'] = df['pen_betaCA'].astype(float)
df['pen_r2CA'] = df['pen_r2CA'].astype(float)

# Create new columns for point size based on pen_r2CV and pen_r2CA
df['point_size_CV'] = np.where(df['pen_r2CV'] >= 0.75, 40, 10)
df['point_size_CA'] = np.where(df['pen_r2CA'] >= 0.75, 40, 10)


plt.rcParams.update({'font.family': 'sans-serif'})

# Set up the figure with two subplots
fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)

# Create jitter for x positions
unique_freqs = sorted(df['freq'].unique())
freq_to_position = {freq: i for i, freq in enumerate(unique_freqs)}

# Function to create a violin plot with scatter points
def create_violin_plot(ax, y_col, size_col, title, ylabel):
    # Create the violin plot
    sns.violinplot(x='freq', y=y_col, data=df, inner=None, color='lightgray', ax=ax)
    
    # Add points with jitter, color based on beta, and size based on r2 value
    for _, row in df.iterrows():
        # Map frequency to position
        x_pos = freq_to_position[row['freq']]
        
        # Add jitter to x position
        jitter = np.random.uniform(-0.2, 0.2)
        
        # Determine color based on beta value
        if row['beta'] == 0.0:
            color = 'red'
        elif row['beta'] == -0.333:
            color = 'blue'
        elif row['beta'] == -0.667:
            color = 'green'
        else:
            color = 'gray'  # Fallback color
        
        ax.scatter(
            x=x_pos + jitter, 
            y=row[y_col], 
            s=row[size_col],
            color=color,
            alpha=0.7,
            edgecolor='black',
            linewidth=0.5
        )
    
        if y_col=='pen_betaCV':
            ax.plot([-0.5, 4.5], [row['beta'], row['beta']], "--", color=color, alpha=0.5)
        else:
            ax.plot([-0.5, 4.5], [1+row['beta'], 1+row['beta']], "--", color=color, alpha=0.5)
    

    # Customize the plot
    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Target frequency (Hz)', fontsize=14)
    ax.set_ylabel(ylabel, fontsize=14)
    
    # Update x-tick labels to show actual frequency values
    ax.set_xticks(range(len(unique_freqs)))
    ax.set_xticklabels(unique_freqs)

# Create first violin plot for CV data
create_violin_plot(
    ax=axes[1],
    y_col='pen_betaCV',
    size_col='point_size_CV',
    title='Speed and Curvature (VC)\nPower law in pen trajectories',
    ylabel=r"Power law exponent $\beta$"
)

# Create second violin plot for CA data
create_violin_plot(
    ax=axes[0],
    y_col='pen_betaCA',
    size_col='point_size_CA',
    title='Angular Speed and Curvature (AC)\nPower law in pen trajectories',
    ylabel=r"Power law exponent $\beta$"
)

axes[0].set_ylim(0.3, 1.1)
axes[1].set_ylim(-0.7, 0.1)

# Create a custom legend for beta values
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markersize=10, label=r'target $\beta$ = 0'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label=r'target $\beta$ = -1/3'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markersize=10, label=r'target $\beta$ = -2/3')
]

# Add another part to the legend for point sizes
legend_elements.extend([
    Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=6, label=r'$r^2$ < 0.75'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label=r'$r^2$ ≥ 0.75')
])

# Add the legend to the figure
fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0), 
           ncol=5, frameon=True, framealpha=0.7)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(bottom=0.15)  # Make room for the legend at the bottom

# Save the figure
plt.savefig('../figures/AC_VC_comparison.eps', format="eps", dpi=300, bbox_inches='tight')
plt.savefig('AC_VC_comparison.png', dpi=300, bbox_inches='tight')

#plt.show()