import math
import uuid

# RAW GAZES USE TO COMPUTE FIXATIONS
class RawGaze:
    def __init__(self, gaze_data=None):
        # Gaze_data is tuple with fields:
        #   (event_time, x, y, system_time,
        #    left_pupil_diameter, right_pupil_diameter,
        #    left_validation, right_validation,
        #    gaze_target, gaze_target_type,
        #    source_file_line, source_file_col,
        #    source_token, source_token_xpath,
        #    source_token_syntactic_context)

        # Core Data
        self.x = None
        self.y = None
        self.event_time = None
        self.system_time_milliseconds = None
        self.left_pupil_diameter = None
        self.right_pupil_diameter = None
        self.left_validation = None
        self.right_validation = None

        # Plugin Data
        self.gaze_target = None
        self.gaze_target_type = None
        self.source_file_line = None
        self.source_file_col = None
        self.source_token = None
        self.source_token_xpath = None
        self.source_token_syntactic_context = None

        # Used for initial grouping in IVT filter ONLY
        self.group_id = None

        if not gaze_data is None:
            # Core Data
            self.event_time = int(gaze_data[0]) if gaze_data[0] != None else None
            self.x = float(gaze_data[1]) if gaze_data[1] != None else None
            self.y = float(gaze_data[2]) if gaze_data[2] != None else None
            self.system_time_milliseconds = int(gaze_data[3])
            self.left_pupil_diameter = (
                float(gaze_data[4]) if gaze_data[4] != None else 0
            )
            self.right_pupil_diameter = (
                float(gaze_data[5]) if gaze_data[5] != None else 0
            )
            self.left_validation = int(gaze_data[6]) if gaze_data[6] != None else 0
            self.right_validation = int(gaze_data[7]) if gaze_data[7] != None else 0

            # Plugin Data
            self.gaze_target = (
                gaze_data[8] if gaze_data[8] != "" and gaze_data[8] != None else None
            )
            self.gaze_target_type = (
                gaze_data[9] if gaze_data[9] != "" and gaze_data[9] != None else None
            )
            self.source_file_line = (
                int(gaze_data[10]) if gaze_data[10] != None else None
            )
            self.source_file_col = int(gaze_data[11]) if gaze_data[11] != None else None
            self.source_token = self.gaze_target_type = (
                gaze_data[12] if gaze_data[12] != "" and gaze_data[12] != None else None
            )
            self.source_token_xpath = self.gaze_target_type = (
                gaze_data[13] if gaze_data[13] != "" and gaze_data[13] != None else None
            )
            self.source_token_syntactic_context = self.gaze_target_type = (
                gaze_data[14] if gaze_data[14] != "" and gaze_data[14] != None else None
            )

    # Determines if the data is valid from the x and y.
    #   (This can be altered later to be more robust)
    def isValid(self):
        if self.x == None or self.x < 0 or math.isnan(self.x):
            return False
        if self.y == None or self.y < 0 or math.isnan(self.y):
            return False
        if self.left_validation == 0 and self.right_validation == 0:
            return False
        return True


# FIXATION TO CONTAIN CALCULATED DATA AND REFERENCE TO RAWGAZES
class Fixation:
    def __init__(self):
        # Determined by Fixation Filter Algorithm
        self.x = None
        self.y = None

        # Since data stored here is determined by the Fixation
        #   Filter Algorithm, this could contain duplicates due
        #   to data interpolation. Normally a set is unique, but
        #   without a hash function implemented for the raw_gaze
        #   object it will take any objects that are not the same
        #   instance. If we want to remove duplicates we can implement
        #   that function.
        self.gaze_set = set()

        # Calculated fields based on the gaze_set collection
        self.target = None
        self.source_file_line = None
        self.source_file_col = None
        self.syntactic_category = None
        self.xpath = None
        self.left_pupil_diameter = 0
        self.right_pupil_diameter = 0
        self.duration = 0
        self.token = None
        self.fixation_event_time = 0

    def calculateDatebaseFields(self):
        start_time = None
        end_time = None
        candidate_targets = {}
        gaze_count = 0

        for gaze in self.gaze_set:
            if not gaze.isValid():
                continue

            if (
                self.fixation_event_time == 0
                or self.fixation_event_time > gaze.event_time
            ):
                self.fixation_event_time = gaze.event_time

            # In the event that some points end up not being valid.
            #   If every point in gaze_set is valid, len() could be
            #   used instead.
            gaze_count += 1

            # Find the start and end time of the fixation for duration
            if start_time == None or start_time > gaze.system_time_milliseconds:
                start_time = gaze.system_time_milliseconds
            if end_time == None or end_time < gaze.system_time_milliseconds:
                end_time = gaze.system_time_milliseconds

            self.left_pupil_diameter += (
                gaze.left_pupil_diameter
                if not math.isnan(gaze.left_pupil_diameter)
                else 0
            )
            self.right_pupil_diameter += (
                gaze.right_pupil_diameter
                if not math.isnan(gaze.right_pupil_diameter)
                else 0
            )

            # Build up a unique candidate key made up of all the token information and including the target
            candidate_key = str(gaze.gaze_target) if gaze.gaze_target != None else ""
            candidate_key += "\t"
            candidate_key += (
                str(gaze.source_file_line) if gaze.source_file_line != None else ""
            )
            candidate_key += "\t"
            candidate_key += (
                str(gaze.source_file_col) if gaze.source_file_col != None else ""
            )
            candidate_key += "\t"
            candidate_key += str(gaze.source_token) if gaze.source_token != None else ""
            candidate_key += "\t"
            candidate_key += (
                str(gaze.source_token_syntactic_context)
                if gaze.source_token_syntactic_context != None
                else ""
            )
            candidate_key += "\t"
            candidate_key += (
                str(gaze.source_token_xpath) if gaze.source_token_xpath != None else ""
            )

            # Count the occurances to later select the most common occurance as the
            #   token of the fixation
            if not candidate_key in candidate_targets:
                candidate_targets[candidate_key] = 1
            else:
                candidate_targets[candidate_key] += 1

        # Assign Values
        most_frequent_target = None
        for candidate in candidate_targets.keys():
            if most_frequent_target == None:
                most_frequent_target = candidate
            elif candidate_targets[candidate] > candidate_targets[most_frequent_target]:
                most_frequent_target = candidate

        # Break up the candidate key into the respective database fields
        fields = most_frequent_target.split("\t")

        self.target = fields[0] if fields[0] != "" else None
        self.source_file_line = int(fields[1]) if fields[1] != "" else None
        self.source_file_col = int(fields[2]) if fields[2] != "" else None

        # Simple calculations on the non-token information
        self.left_pupil_diameter = self.left_pupil_diameter / gaze_count
        self.right_pupil_diameter = self.right_pupil_diameter / gaze_count
        self.duration = end_time - start_time
        self.system_time = start_time
