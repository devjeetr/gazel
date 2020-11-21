# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from typing import Dict, List, Callable
import xml.etree.ElementTree as ET
import pandas as pd
from gazel.fixation_filters import ivt as IVT
from gazel.fixation_filters import idt as IDT
from gazel.fixation_filters import basic as BASIC
from gazel.fixation_filters.fixation_data import Fixation


def load_gazes_from_xml(filepath: str) -> pd.DataFrame:
    """loads data from the gaze XML file output by itrace.
        Returns the responses as a pandas DataFrame

    Parameters
    ----------
    filepath : str
        path to XML

    Returns
    -------
    pd.DataFrame
        Gazes contained in the xml file
    """
    root = ET.parse(filepath)
    return pd.DataFrame(list(map(lambda e: e.attrib, root.findall("./gazes/response"))))


def get_raw_gaze_time(gaze: tuple) -> float:
    return float(gaze[3])


def create_gazes_for_fixation_filters(
    plugin_data: pd.DataFrame, core_data: pd.DataFrame
) -> List[tuple]:
    common_cols = list(plugin_data.columns.intersection(core_data.columns))
    combined = pd.merge(plugin_data, core_data, on=common_cols, how="inner")

    columns = [
        "event_id",
        "x",
        "y",
        "plugin_time",  # don't know what this is..
        "left_pupil_diameter",
        "right_pupil_diameter",
        "left_validation",
        "right_validation",
        "gaze_target",
        "gaze_target_type",
        "source_file_line",
        "source_file_col",
        "source_token",
        "source_token_xpath",
        "source_token_syntactic_context",
    ]

    combined["source_token"] = "token"
    combined["source_token_xpath"] = "path"
    combined["source_token_syntactic_context"] = "path"

    combined = combined[columns].copy()

    entries = combined.to_dict("record")

    gazes = []
    for entry in entries:
        gazes.append(tuple([entry[col] for col in columns]))

    return gazes


def _partition_gazes(
    raw_gazes: List[tuple], changelog: List[Dict]
) -> List[List[tuple]]:

    if len(changelog) == 0:
        return [raw_gazes]

    next_partition = 0
    current_partition = []
    partitions = []

    for gaze in raw_gazes:
        gaze_time = get_raw_gaze_time(gaze)
        if gaze_time < changelog[next_partition]["timestamp"]:
            current_partition.append(gaze)
        else:
            partitions.append(current_partition)
            current_partition = []
            if next_partition + 1 < len(changelog):
                next_partition = next_partition + 1

    return partitions


def _fixation_to_dict(fixation: Fixation) -> Dict:
    fixation.calculateDatebaseFields()
    fixation_fields = fixation.__dict__.copy()
    del fixation_fields["gaze_set"]

    return fixation_fields


def _run_fixation_filter(
    fn: Callable[[List[tuple]], List[Fixation]],
    core_file: str,
    plugin_file: str,
    changelog: List[Dict],
) -> pd.DataFrame:
    core_data, plugin_data = map(load_gazes_from_xml, [core_file, plugin_file])

    raw_gazes = create_gazes_for_fixation_filters(plugin_data, core_data)
    partitioned_gazes = _partition_gazes(raw_gazes, changelog)
    all_fixations: List[Dict] = []

    for partition in partitioned_gazes:
        fixations = fn(partition)
        all_fixations.extend(_fixation_to_dict(fixation) for fixation in fixations)
        # fixations.append()

    return pd.DataFrame(all_fixations)


def ivt(
    core_file: str, plugin_file: str, changelog: List[Dict], config: IVT.IVTConfig
) -> pd.DataFrame:
    def partial(gazes):
        return IVT.identifyFixations(
            gazes, config.velocity_threshold, config.duration_threshold
        )

    return _run_fixation_filter(partial, core_file, plugin_file, changelog)


def idt(
    core_file: str, plugin_file: str, changelog: List[Dict], config: IDT.IDTConfig
) -> pd.DataFrame:
    def partial(gazes):
        return IDT.identifyFixations(
            gazes, config.dispersion_threshold, config.duration_window
        )

    return _run_fixation_filter(partial, core_file, plugin_file, changelog)


def basic(
    core_file: str, plugin_file: str, changelog: List[Dict], config: BASIC.BasicConfig
) -> pd.DataFrame:
    def partial(gazes):
        return BASIC.run_filters(gazes, config)

    return _run_fixation_filter(partial, core_file, plugin_file, changelog)
