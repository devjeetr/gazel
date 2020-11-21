# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%

# %% [markdown]
# # gazel: Supporting Source Code Edits in Eye-Tracking Studies
#
#

# %%

from gazel import Tracker, fixation_filters, pprint
from gazel.fixation_filters.ivt import IVTConfig
import json
import os


# %%
base = "./notebooks/demo-data/"

core_file = os.path.join(base, "core.xml")
plugin_file = os.path.join(base, "plugin.xml")
change_log_file = os.path.join(base, "changelog.json")
source_file = os.path.join(base, "Sample-Data.cpp")


# %%
def load_file(filepath):
    with open(filepath) as f:
        return f.read()


changelog = json.loads(load_file(change_log_file))["log"][:-1]

source = load_file(source_file)
gazes = fixation_filters.core.ivt(core_file, plugin_file, changelog, IVTConfig(50, 80))

tracker = Tracker(source, gazes, changelog, "cpp", 500)


# %%


# %%


# %%

for snapshot in tracker.snapshots:
    for change in snapshot.changes:
        if change.type == "edited":
            print("Edited")

print("Hello")
# %%

