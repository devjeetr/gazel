import math
from gazel.fixation_filters.fixation_data import RawGaze
from gazel.fixation_filters.fixation_data import Fixation
from typing import List, Union, NamedTuple

### IDT STEP 1 ###
# Build gaze vector and interpolate from input XML ###
def buildRawGazeVector(file_gazes):
    raw_gaze_pos_vector = list()

    # Keep track of the last known valid data
    #   Start empty...first gazes could be invalid
    last_valid_gaze = RawGaze()

    for gaze in file_gazes:
        # Get the data point
        data_point = RawGaze(gaze)

        # Check if the data point is valid
        if data_point.isValid():
            raw_gaze_pos_vector.append(data_point)
            last_valid_gaze = data_point
        else:
            # If the data point isn't valid and no valid
            #  data has been seen, ignore the point
            #  This approach will ignore grouping invalid data
            #  points, but will still interpolate the missing data.
            if last_valid_gaze.isValid():
                raw_gaze_pos_vector.append(last_valid_gaze)

    return raw_gaze_pos_vector


### IDT STEP 2 ###
# Calculate velocity between each point in raw_gaze_vector ###
def calculateFixationVector(raw_gaze_vector, dispersion_threshold, duration_window):
    fixation_vector = list()
    window = list()
    i = 0

    while i < duration_window and i < len(raw_gaze_vector):
        window.append(raw_gaze_vector[i])
        i += 1
    # window has raw gaze vectors
    while i < len(raw_gaze_vector):

        # if the max(gazeXDelta + gazeYdelta < threshold
        #         & len(window) >= duration_window
        if (
            max(window, key=lambda g: g.x).x
            - min(window, key=lambda g: g.x).x
            + max(window, key=lambda g: g.y).y
            - min(window, key=lambda g: g.y).y
        ) <= dispersion_threshold and len(window) >= duration_window:
            while (
                max(window, key=lambda g: g.x).x
                - min(window, key=lambda g: g.x).x
                + max(window, key=lambda g: g.y).y
                - min(window, key=lambda g: g.y).y
            ) <= dispersion_threshold:
                if i < len(raw_gaze_vector) - 1:
                    window.append(raw_gaze_vector[i])
                    i += 1
                else:
                    break
            fixation_vector.append(computeFixationEstimate(window))
            del window[:]
            window.append(raw_gaze_vector[i])
            i += 1
        elif len(window) < duration_window:
            window.append(raw_gaze_vector[i])
            i += 1
        else:
            del window[0]
            if len(window) < duration_window:
                window.append(raw_gaze_vector[i])
                i += 1

    return fixation_vector


# Helper function to build a fixation estimate
def computeFixationEstimate(fixation_points):
    # Construct a fixation
    fixation = Fixation()

    # Calculate mean for all fields
    x_total = 0
    y_total = 0

    for point in fixation_points:
        x_total += point.x
        y_total += point.y
        fixation.gaze_set.add(point)

    fixation.x = x_total / len(fixation_points)
    fixation.y = y_total / len(fixation_points)

    return fixation


def identifyFixations(raw_gaze_data, dispersion_threshold, duration_window):
    raw_gaze_vector = buildRawGazeVector(raw_gaze_data)

    fixations = calculateFixationVector(
        raw_gaze_vector, dispersion_threshold, duration_window
    )

    return fixations


class IDTConfig(NamedTuple):
    dispersion_threshold: float
    duration_window: float


def run_filters(gazes, config: IDTConfig):

    return identifyFixations(gazes, config.dispersion_threshold, config.duration_window)
