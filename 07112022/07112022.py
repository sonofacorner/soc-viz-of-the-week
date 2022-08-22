# %%
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as ticker
import matplotlib.gridspec as gridspec
import matplotlib.patheffects as path_effects
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


# --- Reading the data

df = pd.read_csv("data/538_probs_07112022.csv", encoding = "utf-8")
df["date"] = pd.to_datetime(df["date"])

# -- Compute the Brier Score for each match

df["home_win"] = [
    1 if x > y else 0 for x,y in zip(df["score_home"], df["score_away"])
]

df["tie"] = [
    1 if x == y else 0 for x,y in zip(df["score_home"], df["score_away"])
]

df["away_win"] = [
    1 if x < y else 0 for x,y in zip(df["score_home"], df["score_away"])
]

df = df.assign(
    brier_score = lambda x: 
    1/3*(
        (x.prob_home - x.home_win)**2 + 
        (x.prob_tie - x.tie)**2 +
        (x.prob_away - x.away_win)**2
    )
)

# %%
# -- Compute cumulative average of Brier Score

teams = df[["home_team_id"]].drop_duplicates()

plot_df = pd.DataFrame()

for team in teams["home_team_id"]:
    aux_df = df[(df["home_team_id"] == team) | (df["away_team_id"] == team)].copy()
    # compute cumulative average
    cum_mean = (
        aux_df["brier_score"].expanding().mean()
    )

    new_df = pd.DataFrame()
    new_df["cum_mean"] = cum_mean
    new_df["team_id"] = team

    plot_df = plot_df.append(new_df)

plot_df = pd.merge(
    plot_df, 
    df[["home_team_id", "home_team_name"]].drop_duplicates(),
    how = "left",
    left_on = "team_id",
    right_on = "home_team_id",
).rename(columns = {"home_team_name":"team_name"})

# %%
# Assign team colors

team_colors = pd.read_csv("data/team_colors.csv")
plot_df = pd.merge(plot_df, team_colors, how = "left")

# %%

def plot_team_brier_score(ax, team_id, data, label_y = True, label_x = True):
    '''
    Plots the cumulative Brier Score for a given side
    with all the other teams in the backgorund in a lighter
    color.
    '''

    df = data.copy()

    team_df = df[df["team_id"] == team_id].reset_index(drop = True)
    color = team_df["color"].iloc[0]

    ax.plot(
        team_df.index,
        team_df["cum_mean"],
        color = color,
        lw = 1.75,
        zorder = 3,
        marker = "o",
        markevery = [-1],
        markeredgecolor = "#EFE9E6"
    )

    ax.annotate(
        xy = (team_df.index[-1], team_df["cum_mean"].iloc[-1]),
        xytext = (15, 0),
        text = f'{team_df["cum_mean"].iloc[-1]:.3f}',
        textcoords = "offset points",
        ha = "center",
        va = "center",
        color = color,
        weight = "bold",
        size = 8
    )

    for x in df["team_id"].unique():
        if x == team_id:
            continue
        aux_df = df[df["team_id"] == x].reset_index(drop = True)

        ax.plot(
            aux_df.index,
            aux_df["cum_mean"],
            color = "gray",
            alpha = 0.15,
            lw = 1.25,
            zorder = 2
        )

    ax.grid(ls = ":", color = "lightgrey")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.05))

    if label_y:
        ax.set_ylabel("Brier score")
    else:
        ax.set_yticklabels([])
    if label_x:
        ax.set_xlabel("Match day")
    else:
        ax.set_xticklabels([])

    return ax


order_teams = (
    plot_df.groupby(["team_id"])
    ["cum_mean"]
    .last()
    .reset_index()
    .sort_values(by = "cum_mean")
)

fig = plt.figure(figsize=(14, 14), dpi = 200)
nrows = 10
ncols = 4
gspec = gridspec.GridSpec(
    ncols=ncols, nrows=nrows, figure=fig, 
    height_ratios = [(1/nrows)*2. if x % 2 != 0 else (1/nrows)/2. for x in range(nrows)], hspace = 0.3
)

plot_counter = 0
logo_counter = 0
for row in range(nrows):
    for col in range(ncols):
        if row % 2 != 0:
            ax = plt.subplot(
                gspec[row, col],
                facecolor = "#EFE9E6"
            )

            teamId = order_teams["team_id"].iloc[plot_counter]

            if col == 0:
                labels_y = True
            else:
                labels_y = False
            
            if row == nrows - 1:
                labels_x = True
            else:
                labels_x = False
            
            plot_team_brier_score(ax, teamId, plot_df, labels_y, labels_x)           

            plot_counter += 1

        else:

            teamId = order_teams["team_id"].iloc[logo_counter]
            teamName = plot_df[plot_df["team_id"] == teamId]["team_name"].iloc[0]

            fotmob_url = "https://images.fotmob.com/image_resources/logo/teamlogo/"
            logo_ax = plt.subplot(
                gspec[row,col],
                anchor = "NW", facecolor = "#EFE9E6"
            )
            club_icon = Image.open(urllib.request.urlopen(f"{fotmob_url}{teamId:.0f}.png")).convert("LA")
            logo_ax.imshow(club_icon)
            logo_ax.axis("off")

            if teamName == "Wolverhampton Wanderers":
                teamName = "Wolverhampton"

            # # Add the team name
            ax_text(
                x = 1.1, 
                y = 0.7,
                s = f"{teamName}",
                ax = logo_ax, 
                weight = "bold", 
                font = "Karla", 
                ha = "left", 
                size = 13, 
                annotationbbox_kw = {"xycoords":"axes fraction"}
            )

            logo_counter += 1

fig_text(
    x = 0.11, y = .96, 
    s = "Which Premier League teams are the most predictable?",
    va = "bottom", ha = "left",
    fontsize = 25, color = "black", font = "DM Sans", weight = "bold"
)
fig_text(
	x = 0.11, y = .9, 
    s = "Cumulative average Brier Score of 538's Premier League match predictions | Season 2021/2022 | viz by @sonofacorner\n<Brier Score> is a proper score function that measures the accuracy of probabilistic predictions.\nThe higher the Brier Score, the less accurate the prediction.",
    highlight_textprops=[{"weight": "bold", "color": "black"}],
	va = "bottom", ha = "left",
	fontsize = 13, color = "#4E616C", font = "Karla"
)


plt.savefig(
	"figures/07112022_epl_predictable.png",
	dpi = 600,
	facecolor = "#EFE9E6",
	bbox_inches="tight",
    edgecolor="none",
	transparent = False
)

plt.savefig(
	"figures/07112022_epl_predictable_tr.png",
	dpi = 600,
	facecolor = "none",
	bbox_inches="tight",
    edgecolor="none",
	transparent = True
)