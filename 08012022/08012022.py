# %%
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as ticker
import matplotlib.patheffects as path_effects
import matplotlib.patches as patches
from matplotlib import rcParams
from highlight_text import ax_text, fig_text
import pandas as pd

from PIL import Image
import urllib
import os

# --- Use this only if you have already downloaded fonts into your
# --- local directory.

# Add pretty fonts

font_path = r"" #Set the path to where the fonts are located

for x in os.listdir(font_path):
    for y in os.listdir(f"{font_path}/{x}"):
        if y.split(".")[-1] == "ttf":
            fm.fontManager.addfont(f"{font_path}/{x}/{y}")
            try:
                fm.FontProperties(weight=y.split("-")[-1].split(".")[0].lower(), fname=y)
            except Exception as e:
                print(f"Font {y} could not be added.")
                continue

rcParams['font.family'] = 'Karla'

# --- Read and transform the data

df = pd.read_csv("data/08012022_womens_euro.csv", index_col = 0)

# ----------------------------------------------------------------
# -- Declare a function to group the shots into bins

def shot_map_bins(match_id, team_id, grid_x = 6, grid_y = 2, data = df):
    '''
    This function takes a playerId and returns the list of 
    percentages (in order) to map the values into our shot map plot.

    Args:
        grid_x (int): the number of divisions to be made to the goal aross the x-axis. Must be an even number.
        grid_y (int): the number of divisions to be made to the goal aross the y-axis. Must be an even number.
    '''

    data = data.copy()
    width = 24
    height = 8

    if (grid_x % 2 != 0) | (grid_y % 2 != 0):
        raise Exception('grid_x and grid_y must be even integers.')

    increment_x = int(width / grid_x)
    increment_y = int(height / grid_y) 

    # The data's scale is 2 units wide and .666 high.

    data['x'] = [((x*width)/2.1) for x in data['x']]
    data['y'] = [((y*height)/.7) for y in data['y']]

    # Assign intervals
    bins_x = range(0, width + 1, increment_x)
    bins_y = range(0, height + 1, increment_y)

    data['bins_x'] = pd.cut(data['x'], bins_x)
    data['bins_y'] = pd.cut(data['y'], bins_y)

    # -- We add an auxiliary column to help us count the number of shots.
    data['shot_aux'] = 1

    data_bins = (
        data
        .groupby(['bins_x','bins_y','team_id', 'match_id'])
        ['shot_aux'].sum().
        reset_index()
    )

    # -- Count all shots on target.
    total_shots = data.groupby(['team_id', 'match_id'])['shot_aux'].sum().reset_index()
    total_shots.columns = ['team_id', 'match_id', 'total']

    # -- Merge it back & calculate the percentage
    data_bins = pd.merge(data_bins, total_shots, how = 'left', on = ['match_id', 'team_id'])
    data_bins['shot_pct'] = data_bins['shot_aux']/data_bins['total']

    # -- Order data_bins first by x and then by y
    team_bins = data_bins[(data_bins['team_id'] == team_id) & (data_bins['match_id'] == match_id)].reset_index()
    team_bins = team_bins.sort_values(by = ['bins_x', 'bins_y'])
  
    return team_bins['shot_pct'].to_list()

# -------------------------------------------------------------------------
# Declare a function that plots the shotmap

def shot_map_plot(match_id, team_id, ax, grid_x = 6, grid_y = 2, data = df, main_color = '#005377'):
    '''
    This function takes a team, match_id and axes to plot a shot map.

    Args:
    ax (obj): a Matplotlib axes.
    grid_x (int): the number of divisions to be made to the goal aross the x-axis. Must be an even number.
    grid_y (int): the number of divisions to be made to the goal aross the y-axis. Must be an even number.
    main_color (str): a hex color code for the heat-map.
    '''

    scatter_df = data.copy()
    scatter_df = scatter_df[
        (scatter_df["match_id"] == match_id) &
        (scatter_df["team_id"] == team_id)
    ]

    ax.axis('equal')

    # -- The size of the goal
    width = 24
    height = 8

    # -- The left & right post
    ax.plot([0,0],[0,height], color = 'black', lw = 1.25)
    ax.plot([width,width],[0,height], color = 'black', lw = 1.25)

    # -- The top post
    ax.plot([0,width],[height,height], color = 'black', lw = 1.25)

    # -- The data

    data = shot_map_bins(match_id = match_id, team_id = team_id, grid_x = grid_x, grid_y = grid_y, data = data)
    try:
        max_data = max(data)
        scaled_data = [x/max_data for x in data]
        scatter_df['x'] = [((x*width)/2.1) for x in scatter_df['x']]
        scatter_df['y'] = [((y*height)/.7) for y in scatter_df['y']]
        ax.scatter(scatter_df['x'], scatter_df['y'], ec = "black", color = "white", alpha = 0.5, s = 10)
    except:
        scaled_data = [0]*grid_x*grid_y
        data = scaled_data


    # -- The Grid

    increment_x = int(width / grid_x)
    increment_y = int(height / grid_y)

    i = 0 
    x = 0
    while x < width:
        for y in range(0, height, increment_y):
            rect = patches.Rectangle(
                    (x, y),  # bottom left starting position (x,y)
                    increment_x,  # width
                    increment_y,  # height
                    ec= main_color,
                    fc= main_color,
                    alpha = scaled_data[i], # <---- the transparency
                    zorder=-1
                )
            
            ax.add_patch(rect)

            # -- Anotate the counter (i) and choose color depending on value
            if scaled_data[i] < .5:
                color_text = 'black'
                fore_color ='white'
            else:
                color_text = 'white'
                fore_color = 'black'
            label_ = ax.text(
                    x = x + increment_x/2, y = y + increment_y/2,
                    s = f'{data[i]:.0%}', # <----- the data label
                    color = color_text,
                    va = 'center',
                    ha = 'center',
                    size = 7
                    )
            # Set path effects to ensure readability
            label_.set_path_effects(
                [path_effects.Stroke(linewidth=1, foreground=fore_color), 
                path_effects.Normal()]
            )

            i += 1
        # -- Once we've placed the top & bottom rectangles we move right.
        x = x + increment_x

    # -- Set axes limits and remove ticks
    ax.set_xlim(-.5,width + .5)
    ax.set_ylim(-.5,height + 1)
    ax.set_axis_off()


    # -- Draw the lower border
    ax.plot([-2,width + 2],[0,0], color = 'black', marker = 'None', lw = 1.25, zorder = 3)

    return ax

# ----------------------------------------------------------------
# The final visual
# ----------------------------------------------------------------

# ----------------------------------------------------------------
# --- Define the grid we'll be using to plot all of the matches.
# %%
layout = [
    ["q1logo_h", ".", "q1logo_a", ".", ".", "q2logo_h", ".", "q2logo_a", "."],
    ["q1goal_h", "q1goal_h", "q1goal_a", "q1goal_a", ".", "q2goal_h", "q2goal_h", "q2goal_a", "q2goal_a"],
    ["."] * 9,
    [".", ".", "s1logo_h", ".", ".", "s1logo_a", ".", ".", "."],
    [".", ".", "s1goal_h", "s1goal_h", ".", "s1goal_a", "s1goal_a", ".", "."],
    ["."] * 9,
    [".", ".", "flogo_h", ".", ".", "flogo_a", ".", ".", "."],
    [".", ".", "fgoal_h", "fgoal_h", ".", "fgoal_a", "fgoal_a", ".", "."],
    ["."] * 9,
    [".", ".", "s2logo_h", ".", ".", "s2logo_a", ".", ".", "."],
    [".", ".", "s2goal_h", "s2goal_h", ".", "s2goal_a", "s2goal_a", ".", "."],
    ["."] * 9,
    ["q3logo_h", ".", "q3logo_a", ".", ".", "q4logo_h", ".", "q4logo_a", "."],
    ["q3goal_h", "q3goal_h", "q3goal_a", "q3goal_a", ".", "q4goal_h", "q4goal_h", "q4goal_a", "q4goal_a"],
]

# -- Fotmob url for logos
fotmob_url = "https://images.fotmob.com/image_resources/logo/teamlogo/"

# Hieght ratios (logo, shotmap, space)
h_ratios = [.35, 1., .25] * 4 + [.35, 1.]

fig = plt.figure(figsize=(12, 8), dpi = 200)
axs = fig.subplot_mosaic(
    layout,
    gridspec_kw = {
        "height_ratios" : h_ratios,
        "width_ratios" : [1]*4 + [0.25] + [1]*4
    }
)


# --- This could have been a function, but was already too invested to change it :(
# --- Sorry for being lazy...

# -------------------- Quarter Finals
# --------------
# England vs. Spain
shot_map_plot(3552651, 5811, axs["q1goal_h"], main_color = "#6fa3e6")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{5811:.0f}.png"))
axs["q1logo_h"].imshow(club_icon)
x_ = axs["q1logo_h"].get_xlim()[1]
y_ = axs["q1logo_h"].get_ylim()[0]
axs["q1logo_h"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "England (2)",
    ha = "left",
    va = "bottom",
    weight = "bold"
)
axs["q1logo_h"].axis("off")
# --
shot_map_plot(3552651, 244165, axs["q1goal_a"], main_color = "#cd4201")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{244165:.0f}.png"))
axs["q1logo_a"].imshow(club_icon)
x_ = axs["q1logo_a"].get_xlim()[1]
y_ = axs["q1logo_a"].get_ylim()[0]
axs["q1logo_a"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "Spain (1)",
    ha = "left",
    va = "bottom"
)
axs["q1logo_a"].axis("off")

# --------------
# Sweden vs. Belgium
shot_map_plot(3552653, 5814, axs["q2goal_h"], main_color = "#3060a8")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{5814:.0f}.png"))
axs["q2logo_h"].imshow(club_icon)
x_ = axs["q2logo_h"].get_xlim()[1]
y_ = axs["q2logo_h"].get_ylim()[0]
axs["q2logo_h"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "Sweden (1)",
    ha = "left",
    va = "bottom",
    weight = "bold"
)
axs["q2logo_h"].axis("off")
# --
shot_map_plot(3552653, 394233, axs["q2goal_a"], main_color = "#333333")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{394233:.0f}.png"))
axs["q2logo_a"].imshow(club_icon)
x_ = axs["q2logo_a"].get_xlim()[1]
y_ = axs["q2logo_a"].get_ylim()[0]
axs["q2logo_a"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "Belgium (0)",
    ha = "left",
    va = "bottom"
)
axs["q2logo_a"].axis("off")

# --------------
# France vs. Netherlands
shot_map_plot(3552654, 6325, axs["q3goal_h"], main_color = "#284898")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{6325:.0f}.png"))
axs["q3logo_h"].imshow(club_icon)
x_ = axs["q3logo_h"].get_xlim()[1]
y_ = axs["q3logo_h"].get_ylim()[0]
axs["q3logo_h"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "France (1)",
    ha = "left",
    va = "bottom",
    weight = "bold"
)
axs["q3logo_h"].axis("off")
# --
shot_map_plot(3552654, 159980, axs["q3goal_a"], main_color = "#ff6d41")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{159980:.0f}.png"))
axs["q3logo_a"].imshow(club_icon)
x_ = axs["q3logo_a"].get_xlim()[1]
y_ = axs["q3logo_a"].get_ylim()[0]
axs["q3logo_a"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "Netherlands (0)",
    ha = "left",
    va = "bottom"
)
axs["q3logo_a"].axis("off")

# --------------
# Germany vs. Austria
shot_map_plot(3552652, 5812, axs["q4goal_h"], main_color = "#000000")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{5812:.0f}.png"))
axs["q4logo_h"].imshow(club_icon)
x_ = axs["q4logo_h"].get_xlim()[1]
y_ = axs["q4logo_h"].get_ylim()[0]
axs["q4logo_h"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "Germany (2)",
    ha = "left",
    va = "bottom",
    weight = "bold"
)
axs["q4logo_h"].axis("off")
# --
shot_map_plot(3552652, 394231, axs["q4goal_a"], main_color = "#EF3340")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{394231:.0f}.png"))
axs["q4logo_a"].imshow(club_icon)
x_ = axs["q4logo_a"].get_xlim()[1]
y_ = axs["q4logo_a"].get_ylim()[0]
axs["q4logo_a"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "Austria (0)",
    ha = "left",
    va = "bottom"
)
axs["q4logo_a"].axis("off")

# -------------------- Semi Finals
# --------------
# England vs. Sweden
shot_map_plot(3552655, 5811, axs["s1goal_h"], main_color = "#6fa3e6")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{5811:.0f}.png"))
axs["s1logo_h"].imshow(club_icon)
x_ = axs["s1logo_h"].get_xlim()[1]
y_ = axs["s1logo_h"].get_ylim()[0]
axs["s1logo_h"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "England (4)",
    ha = "left",
    va = "bottom",
    weight = "bold"
)
axs["s1logo_h"].axis("off")
# --
shot_map_plot(3552655, 5814, axs["s1goal_a"], main_color = "#3060a8")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{5814:.0f}.png"))
axs["s1logo_a"].imshow(club_icon)
x_ = axs["s1logo_a"].get_xlim()[1]
y_ = axs["s1logo_a"].get_ylim()[0]
axs["s1logo_a"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "Sweden (1)",
    ha = "left",
    va = "bottom"
)
axs["s1logo_a"].axis("off")

# --------------
# France vs. Germany
shot_map_plot(3552656, 6325, axs["s2goal_h"], main_color = "#284898")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{6325:.0f}.png"))
axs["s2logo_h"].imshow(club_icon)
x_ = axs["s2logo_h"].get_xlim()[1]
y_ = axs["s2logo_h"].get_ylim()[0]
axs["s2logo_h"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "France (1)",
    ha = "left",
    va = "bottom"
)
axs["s2logo_h"].axis("off")
# -- 
shot_map_plot(3552656, 5812, axs["s2goal_a"], main_color = "#000000")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{5812:.0f}.png"))
axs["s2logo_a"].imshow(club_icon)
x_ = axs["s2logo_a"].get_xlim()[1]
y_ = axs["s2logo_a"].get_ylim()[0]
axs["s2logo_a"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "Germany (2)",
    ha = "left",
    va = "bottom",
    weight = "bold"
)
axs["s2logo_a"].axis("off")

# ----------- THE FINAL
# England vs. Germany
shot_map_plot(3552657, 5811, axs["fgoal_h"], main_color = "#6fa3e6")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{5811:.0f}.png"))
axs["flogo_h"].imshow(club_icon)
x_ = axs["flogo_h"].get_xlim()[1]
y_ = axs["flogo_h"].get_ylim()[0]
axs["flogo_h"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "England (2)",
    ha = "left",
    va = "bottom",
    weight = "bold"
)
axs["flogo_h"].axis("off")
# -- 
shot_map_plot(3552657, 5812, axs["fgoal_a"], main_color = "#000000")
club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{5812:.0f}.png"))
axs["flogo_a"].imshow(club_icon)
x_ = axs["flogo_a"].get_xlim()[1]
y_ = axs["flogo_a"].get_ylim()[0]
axs["flogo_a"].annotate(
    xy = (x_,y_),
    xytext = (5, 0),
    textcoords = "offset points",
    text = "Germany (1)",
    ha = "left",
    va = "bottom"
)
axs["flogo_a"].axis("off")


trophy_ax = fig.add_axes([0.22, 0.46, 0.06, 0.06])
trophy_icon = Image.open(urllib.request.urlopen(f"https://cdn-icons-png.flaticon.com/512/3112/3112946.png"))
trophy_ax.imshow(trophy_icon)
trophy_ax.axis("off")


fig_text(
    x = 0.15, y = .95, 
    s = "Shotmap of the Euro's Knockout Stage",
    va = "bottom", ha = "left",
    fontsize = 16, color = "black", font = "DM Sans", weight = "bold"
)
fig_text(
	x = 0.15, y = .92, 
    s = "<Shot-on-target> locations for each match in the <Euro's knockout stage> | 2022 | Viz by @sonofacorner",
    highlight_textprops=[{"weight": "bold", "color": "black"}, {"weight": "bold", "color": "black"}],
	va = "bottom", ha = "left",
	fontsize = 12, color = "#4E616C", font = "Karla"
)

plt.savefig(
	"figures/08012022_womens_euro.png",
	dpi = 600,
	facecolor = "#EFE9E6",
	bbox_inches="tight",
    edgecolor="none",
	transparent = False
)

plt.savefig(
	"figures/08012022_womens_euro_tr.png",
	dpi = 600,
	facecolor = "none",
	bbox_inches="tight",
    edgecolor="none",
	transparent = True
)