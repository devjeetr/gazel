import argparse
import math
from typing import NamedTuple

from gazel.fixation_filters.fixation_data import Fixation, RawGaze


### OLSSON STEP 1 ###
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


### OLSSON STEP 2 ###
# Calculate difference vector from the raw gaze data vector ###
def calculateDifferenceVector(raw_gaze_vector, window_size):
    difference_vector = list()

    # Start at the window size and iterate until no additional windows
    #   of size window_size can be found.
    #   NOTE: The +1 here is required as the range function would cut
    #   off the sliding windows by one iteration.
    for i in range(window_size, (len(raw_gaze_vector) + 1) - window_size):
        # Simple arrays for points (0 = x, 1 = y)
        #   Could make a point class for clarity later
        #   DO NOT USE TUPLES THEY ARE IMMUTABLE
        before_window = [0, 0]
        after_window = [0, 0]

        for j in range(window_size):
            # Sum of Before X and Y (sums backward from index)
            before_window[0] += raw_gaze_vector[i - (j + 1)].x
            before_window[1] += raw_gaze_vector[i - (j + 1)].y
            # Sum od After X and Y (sums forward from index)
            after_window[0] += raw_gaze_vector[i + j].x
            after_window[1] += raw_gaze_vector[i + j].y

        # Average of before and after X and Y values
        before_window[0] /= window_size
        before_window[1] /= window_size
        after_window[0] /= window_size
        after_window[1] /= window_size

        # Distance between average gaze points in windows
        difference_vector.append(
            math.sqrt(
                pow((after_window[0] - before_window[0]), 2)
                + pow((after_window[1] - before_window[1]), 2)
            )
        )

    return difference_vector


### OLSSON STEP 3-5 ###
# Calculate peak indices ###
def calculatePeakIndices(difference_vector, window_size, peak_threshold):
    peaks = [0.0] * len(difference_vector)

    # Find Peaks in difference vector [OLSSON STEP 3]
    # According to the algorithm, first and last  elements
    #   in the difference vector cannot be peaks
    for i in range(1, (len(difference_vector) - 1)):
        if (difference_vector[i] > difference_vector[i - 1]) and (
            difference_vector[i] > difference_vector[i + 1]
        ):
            peaks[i] = difference_vector[i]

    # Find highest peak in window [OLSSON STEP 4]
    #   The algorithm write-up provides a more complex approach to this
    #   but the gist seems to be that no two peaks can be within window_size
    #   of one another. For simplicity one sliding window should provide the
    #   same effect as Step 4 in Olsson while avoiding redundant inner for loop.
    for i in range(window_size - 1, len(peaks)):
        start_index = i - (window_size - 1)  # 0, 1, 2, etc...
        end_index = i
        while start_index != end_index:
            if peaks[start_index] >= peaks[end_index]:
                peaks[end_index] = 0.0
                end_index -= 1
            else:
                peaks[start_index] = 0.0
                start_index += 1

    # Produce Peak Indicies [OLSSON STEP 5]
    peak_indicies = list()
    for i in range(len(peaks)):
        if peaks[i] >= peak_threshold:
            peak_indicies.append(i)

    return peak_indicies


def calculateSpatialFixations(raw_gazes, peak_indicies, window_size, radius):
    shortest_distance = 0
    fixations = list()
    while shortest_distance < radius:

        # Delete content of fixations list
        del fixations[:]

        # While the paper algorithm starts at index 1, it stands  to reason that
        #   gazes before the peak could also make up a fixation (since they
        #   were used in the distance calculation). This code assumes
        #   that fixation estimates are delimited by peaks.
        start_peak_index = 0
        for index in peak_indicies:
            # peak_indicies holds index in distance vector. Mapping to the raw
            #   data requires the index be added to window size
            # Slice the array to capture raw data between peaks
            fixations.append(computeFixationEstimate(raw_gazes[start_peak_index:index]))
            start_peak_index = index

        # Get the last fixation estimate between the last peek and the end of the list
        fixations.append(computeFixationEstimate(raw_gazes[start_peak_index:]))

        # Reset shortest distance
        shortest_distance = float("inf")

        # This is the (n-1) fixation
        previous_estimate = None

        # The first loop iteration will always be a pass through
        #   So the first actual distance computation and peak index
        #   in question will be first one at index 0
        peak_index = -1

        # This will be set to the peak that will be removed
        #   for subsequent iterations
        peak_removal_index = -1

        for current_estimate in fixations:
            if previous_estimate:
                distance = math.sqrt(
                    pow((current_estimate.x - previous_estimate.x), 2)
                    + pow((current_estimate.y - previous_estimate.y), 2)
                )

                if distance < shortest_distance:
                    shortest_distance = distance
                    peak_removal_index = peak_index

            previous_estimate = current_estimate
            peak_removal_index += 1

        if shortest_distance < radius:
            peak_indicies.pop(peak_removal_index)

    return fixations


# Helper function to build a fixation estimate
def computeFixationEstimate(raw_gaze_slice):

    # Construct a fixation
    fixation = Fixation()

    # Calculate median for all fields
    #   Previous filter calculated mean for pupil diameter
    x_positions = list()
    y_positions = list()

    # This could be done in place, but the windows should be relatively
    #   small, and this is more obvious

    for gaze in raw_gaze_slice:
        x_positions.append(gaze.x)
        y_positions.append(gaze.y)
        fixation.gaze_set.add(gaze)

    # Sort data for median calculation
    x_positions.sort()
    y_positions.sort()

    median_index = int(len(x_positions) / 2)

    if len(x_positions) % 2 == 0:
        fixation.x = (x_positions[median_index - 1] + x_positions[median_index]) / 2
        fixation.y = (y_positions[median_index - 1] + y_positions[median_index]) / 2
    else:
        fixation.x = x_positions[median_index]
        fixation.y = y_positions[median_index]

    return fixation


# This is a step that is in the Java version but not apart of the Olsson
#   algorithm. The question here becomes what is the duration threshold?
#   In the java version it looked like 60, but 60 what? Milliseconds, Nano, etc.
def removeShortGazeDurations():
    pass


def identifyFixations(raw_gaze_data, window_size, radius_length, peak_height):

    raw_gaze_vector = buildRawGazeVector(raw_gaze_data)

    difference_vector = calculateDifferenceVector(raw_gaze_vector, window_size)

    peak_indicies = calculatePeakIndices(difference_vector, window_size, peak_height)

    fixations = calculateSpatialFixations(
        raw_gaze_vector, peak_indicies, window_size, radius_length
    )

    return fixations


default_args = {
    "window": 4,
    "peak": None,
    "duration": 60,
    "radius": 35,
}


class BasicConfig(NamedTuple):
    peak: float = float("-inf")
    window: float = 4
    duration: float = 60
    radius: float = 35


def run_filters(gazes, config: BasicConfig):
    if config.peak == float("-inf"):
        # Not sure what 16.6 is for...
        #   This constant was used in the Java version
        peak = config.radius / (16.6 * config.window)
        config = BasicConfig(
            window=config.window,
            duration=config.duration,
            radius=config.radius,
            peak=peak,
        )

    raw_gaze_vector = buildRawGazeVector(gazes)
    difference_vector = calculateDifferenceVector(raw_gaze_vector, config.window)
    peak_indicies = calculatePeakIndices(difference_vector, config.window, config.peak)
    fixations = calculateSpatialFixations(
        raw_gaze_vector, peak_indicies, config.window, config.radius
    )

    return fixations
