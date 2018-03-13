### Klibs Parameter overrides ###

from klibs import P

#########################################
# Runtime Settings
#########################################
collect_demographics = True
manual_demographics_collection = False
manual_trial_generation = False
run_practice_blocks = True
multi_user = False
view_distance = 57 # in centimeters, 57cm = 1 deg of visual angle per cm of screen
slack_messaging = True

#########################################
# PROJECT-SPECIFIC VARS
#########################################
saccade_response_cond = P.condition == 'saccade' # defaults to 'keypress' unless specified
keypress_response_cond = (saccade_response_cond == False)
dm_offset_size = 5 # box offset for devmode, useful for testing on smaller screens

#########################################
# Available Hardware
#########################################
eye_tracker_available = True
eye_tracking = True
labjack_available = False
labjacking = False

#########################################
# Environment Aesthetic Defaults
#########################################
default_fill_color = (0, 0, 0, 255)
default_color = (255, 255, 255, 255)
default_font_size = 28
default_font_name = 'Frutiger'

#########################################
# EyeLink Settings
#########################################
manual_eyelink_setup = False
manual_eyelink_recording = False
show_gaze_dot = False

saccadic_velocity_threshold = 20
saccadic_acceleration_threshold = 5000
saccadic_motion_threshold = 0.15

#########################################
# Experiment Structure
#########################################
multi_session_project = False
if saccade_response_cond:
	trials_per_block = 64 
	blocks_per_experiment = 5
else:
	trials_per_block = 80
	blocks_per_experiment = 4
trials_per_participant = 0
conditions = ['saccade', 'keypress']
table_defaults = {}

#########################################
# Development Mode Settings
#########################################
dm_auto_threshold = True
dm_trial_show_mouse = True
dm_ignore_local_overrides = False
dm_show_gaze_dot = True

#########################################
# Data Export Settings
#########################################
primary_table = "trials"
unique_identifier = "userhash"
default_participant_fields = [[unique_identifier, "participant"], "sex", "age", "handedness"]
default_participant_fields_sf = [[unique_identifier, "participant"], "random_seed", "sex", "age", "handedness"]
