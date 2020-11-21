import math
from fixation_filters.fixation_data import RawGaze
from fixation_filters.fixation_data import Fixation
from typing import NamedTuple

### IVT STEP 1 ###
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


### IVT STEP 2 ###
# Calculate velocity between each point in raw_gaze_vector ###
def gaze_velocity(x1, y1, x2, y2):
    vx = x1 - x2
    vy = y1 - y2
    v = math.sqrt(vx * vx + vy * vy)
    return v


def calculateVelocityVector(raw_gaze_vector):
    velocity_vector = list()

    # Default value for first entry
    velocity_vector.append(0)

    for i in range(1, len(raw_gaze_vector)):
        # Calculate velocity between the current gaze and the following gaze
        velocity = gaze_velocity(
            raw_gaze_vector[i - 1].x,
            raw_gaze_vector[i - 1].y,
            raw_gaze_vector[i].x,
            raw_gaze_vector[i].y,
        )
        # Record the velocity from the previous point to the current point
        velocity_vector.append(velocity)

    return velocity_vector


### IVT STEP 3 ###
# Calculate fixation groupings ###
def calculateFixationGroups(velocity_vector, raw_gaze_vector, velocity_threshold):
    fixation_groups = list()
    fix_number = 1
    on_saccade = False

    # Assign all gazes under the velocity threshold a fixation number, increment
    #   fixation number when encountering a saccade point after 1 or more fixation points,
    # 	gather fixation points into the fixation_groups list
    for i in range(0, len(raw_gaze_vector)):
        if velocity_vector[i] <= velocity_threshold:
            raw_gaze_vector[i].group_id = fix_number
            fixation_groups.append(raw_gaze_vector[i])
            on_saccade = False
        elif on_saccade == False:
            on_saccade = True
            fix_number += 1
    return fixation_groups


### IVT STEP 4 ###
# Filter fixation groupings ###
def filterFixationGroups(fixation_groups, duration):
    fixations = list()
    tmp = list()

    for i in range(1, len(fixation_groups) - 1):
        # While the paper algorithm starts at index 1, it stands  to reason that
        #   gazes before the peak could also make up a fixation (since they

        if fixation_groups[i].group_id == fixation_groups[i + 1].group_id:
            # Gather consecutive fixaction points int a tmp list for processing
            tmp.append(fixation_groups[i])
        elif fixation_groups[i].group_id == fixation_groups[i - 1].group_id:
            tmp.append(fixation_groups[i])
            fix = computeFixationEstimate(tmp, duration)
            if fix.x > -1:
                fixations.append(fix)
            del tmp[:]
        else:
            fix = computeFixationEstimate(tmp, duration)
            if fix.x > -1:
                fixations.append(fix)
            del tmp[:]

    return fixations


# Helper function to build a fixation estimate
def computeFixationEstimate(fixation_points, duration):
    # Use a RawGaze object to construct a fixation
    fixation = Fixation()

    # Calculate mean for all fields
    x_total = 0
    y_total = 0

    # This could be done in place, but the windows should be relatively
    #   small, and this is more obvious
    for point in fixation_points:
        x_total += point.x
        y_total += point.y
        fixation.gaze_set.add(point)

    if len(fixation_points) <= 1:
        fixation.x = -1
        fixation.y = -1
        return fixation

    # Time units are in milliseconds (including duration)
    if (
        fixation_points[len(fixation_points) - 1].system_time_milliseconds
        - fixation_points[0].system_time_milliseconds
    ) >= duration:
        fixation.x = x_total / len(fixation_points)
        fixation.y = y_total / len(fixation_points)
    else:
        fixation.x = -1
        fixation.y = -1

    return fixation


def identifyFixations(raw_gaze_data, velocity_threshold, duration_threshold):
    print("Building Gaze Vector...")
    raw_gaze_vector = buildRawGazeVector(raw_gaze_data)

    print("Calculate Velocity Vector...")
    velocity_vector = calculateVelocityVector(raw_gaze_vector)

    print("Identify Fixation Groups...")
    fixation_groups = calculateFixationGroups(
        velocity_vector, raw_gaze_vector, velocity_threshold
    )

    print("Filter Fixation Groups...")
    fixations = filterFixationGroups(fixation_groups, duration_threshold)

    return fixations


class IVTConfig(NamedTuple):
    velocity_threshold: float
    duration_threshold: float


def run_filters(gazes, config: IVTConfig):
    return identifyFixations(
        gazes, config.velocity_threshold, config.duration_threshold
    )

