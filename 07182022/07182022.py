# %%
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.ticker as ticker
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

df = pd.read_csv("data/fouls_epl_07182022.csv", encoding = "utf-8", index_col = 0)


# -- Highlighted players.

players = [
    30893, # Cristiano Ronaldo
    207236, # Granit Xhaka
    127130, # Jonjo Shelvey
    724306, # Yves Bissouma
    422685, # Bruno Fernandes
    654908, # Richarlison
    856685, # Frank Onyeka
    248453, # Paul Pogba
    535936, # Joelinton
    72518, # Juraj Kucka
    843099, # Scott McTominay
    295067, # Will Hughes
    939542, # Dwight McNeill
    599353, # Che Adams
    169193, # Lacazette
    201664 # Redmond
]

df_main = df[~df["playerId"].isin(players)].reset_index(drop = True)
df_highlight = df[df["playerId"].isin(players)].reset_index(drop = True)

# %%

# -- Plot the chart

fig = plt.figure(figsize = (7,5), dpi = 300)
ax = plt.subplot(facecolor = "#EFE9E6")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.scatter(
    df_main["cards_per_fouls"], 
    df_main["fouls_per_90"], 
    s = 40, 
    alpha = 0.75, 
    color = "#264653",
    zorder = 3
)

ax.scatter(
    df_highlight["cards_per_fouls"], 
    df_highlight["fouls_per_90"], 
    s = 40, 
    alpha = 0.95, 
    color = "#F64740",
    zorder = 3,
    ec = "#000000",
)

ax.plot(
    [df["cards_per_fouls"].median(), df["cards_per_fouls"].median()],
    [ax.get_ylim()[0], ax.get_ylim()[1]], 
    ls = ":",
    color = "gray",
    zorder = 2
)

ax.plot(
    [ax.get_xlim()[0], ax.get_xlim()[1]],
    [df["fouls_per_90"].median(), df["fouls_per_90"].median()], 
    ls = ":",
    color = "gray",
    zorder = 2
)

ax.grid(True, ls = ":", color = "lightgray")

for index, name in enumerate(df_highlight["playerName"]):
    X = df_highlight["cards_per_fouls"].iloc[index]
    Y = df_highlight["fouls_per_90"].iloc[index]
    if name in [" Joelinton", " Richarlison", "Alexandre Lacazette"]:
        y_pos = 9
    else:
        y_pos = -9
    if name in ["Scott McTominay"]:
        x_pos = 20
    else:
        x_pos = 0
    text_ = ax.annotate(
        xy = (X, Y),
        text = name.split(" ")[1],
        ha = "center",
        va = "center",
        xytext = (x_pos, y_pos),
        textcoords = "offset points",
        weight = "bold"
    )

    text_.set_path_effects(
                [path_effects.Stroke(linewidth=2.5, foreground="white"), 
                path_effects.Normal()]
            )


ax.set_xlabel("Cards per foul committed")
ax.set_ylabel("Fouls per 90")

# # ---- The Naught Boys Image
league_icon = Image.open("figures/naughty.png")
league_ax = fig.add_axes([0.095, 0.89, 0.25, 0.25], zorder=1)
league_ax.imshow(league_icon)
league_ax.axis("off")


fig_text(
    x = 0.73, y = 1.03, 
    s = "Who are the Premier League's\n<naughtiest> players?",
    highlight_textprops=[{"color":"#F64740", "style":"italic"}],
    va = "bottom", ha = "right",
    fontsize = 12, color = "black", font = "Karla", weight = "bold"
)

fig_text(
	x = 0.87, y = .94, 
    s = "Fouls per 90 & cards received per foul committed | Season 2021/2022\nPlayers with more than 1,000 minutes and at least 16 fouls are considered.\nViz by @sonofacorner.",
	va = "bottom", ha = "right",
	fontsize = 7, color = "#4E616C", font = "Karla"
)


plt.savefig(
	"figures/07182022_the_naughty_boys.png",
	dpi = 600,
	facecolor = "#EFE9E6",
	bbox_inches="tight",
    edgecolor="none",
	transparent = False
)

plt.savefig(
	"figures/07182022_the_naughty_boys_tr.png",
	dpi = 600,
	facecolor = "none",
	bbox_inches="tight",
    edgecolor="none",
	transparent = True
)