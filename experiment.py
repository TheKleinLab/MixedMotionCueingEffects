__author__ = "jon mulle"

from math import sqrt, pi, cos, sin
from sdl2 import SDLK_SPACE

import klibs
from klibs.KLExceptions import TrialException
from klibs import P
from klibs.KLConstants import CIRCLE_BOUNDARY, EL_RIGHT_EYE, EL_LEFT_EYE, EL_BOTH_EYES, EL_SACCADE_END, NA, RC_KEYPRESS
from klibs.KLUtilities import deg_to_px, flush, iterable, smart_sleep, boolean_to_logical
from klibs.KLUtilities import line_segment_len as lsl
from klibs.KLCommunication import any_key, ui_request, message
from klibs.KLGraphics import fill, flip, blit, clear
from klibs.KLGraphics.KLDraw import Rectangle, Circle, Line, Asterisk2, Triangle, Arrow, FixationCross
from klibs.KLGraphics.KLAnimate import Animation
from klibs.KLKeyMap import KeyMap

TOP = "top"
BOTTOM = "bottom"
LEFT = "left"
RIGHT = "right"
V_START_AXIS = "vertical"
H_START_AXIS = "horizontal"
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
RED = (255, 0, 0, 255)
ROT_CW = "clockwise"
ROT_CCW = "counterclockwise"
BOX_1 = "top_or_left"
BOX_2 = "bottom_or_right"
SACC_INSIDE = "inside"
SACC_OUTSIDE = "outside"

class MixedMotionCueingEffects(klibs.Experiment):
	# general description of graphical elements'  sizes and position
	feedback_size_deg = 3      # size of the feedback text in degrees of visual angle
	feedback_size = None       # size of the feedback text in px
	cue_size_deg = .5          # size of the cue circle (diameter) in degrees of visual angle
	cue_size = None		       # size of the cue circle (diameter) in px
	target_width_deg = 0.5     # width of the target arrows in degrees of visual angle
	target_width = None        # width of the target arrows in px
	box_size_deg = 0.8		   # box size in degrees of visual angle
	box_size = None			   # box size in px
	fixation_boundary_deg = 3  # radius of the fixation boundary in degrees of visual angle
	fixation_boundary = None   # radius of the fixation boundary in px
	offset_size_deg = 7        # box/target/cue offsets from center in degrees of visual angle
	offset_size = None         # box/target/cue offsets from center in px
	target_locs = None

	frame_count = 15
	animation_duration = 300       # ms
	frame_duration = None		    # ms
	box_v_to_h_locations = []
	frames = {V_START_AXIS: {ROT_CW:[], ROT_CCW:[]},
			  H_START_AXIS: {ROT_CW:[], ROT_CCW:[]}}
	rotation_increment = None
	current_frame = 0

	#below are proportional to the sizes specified above
	fixation_thickness = .1
	target_thickness = .15 #specify the size of the arrow stem
	target_height = .5 #specify the height of arrow head
	target_head = 1 / 3.0 #specify the width of the arrow head

	# graphical objects
	box = None
	circle = None
	cross_w = None
	cross_r = None
	asterisk = None
	rotation_frames_v = None
	rotation_frames_h = None

	# trial data
	saccades = []
	target_acquired = False

	def __init__(self, *args, **kwargs):
		super(MixedMotionCueingEffects, self).__init__(*args, **kwargs)

	def setup(self):
		self.txtm.add_style("feedback", 20, WHITE, "Helvetica")
		# convert degree measurements to pixels now that the screen is loaded
		self.target_width = deg_to_px(self.target_width_deg)
		self.cue_size = deg_to_px(self.cue_size_deg)
		self.offset_size = deg_to_px(self.offset_size_deg if not P.development_mode else P.offset_size)
		self.box_size = deg_to_px(self.box_size_deg)
		self.fixation_boundary = deg_to_px(self.fixation_boundary_deg)
		self.target_locs = {
							 TOP: (P.screen_c[0], P.screen_c[1] - self.offset_size),
							 RIGHT: (P.screen_c[0] + self.offset_size, P.screen_c[1]),
							 BOTTOM: (P.screen_c[0], P.screen_c[1] + self.offset_size),
							 LEFT: (P.screen_c[0] - self.offset_size, P.screen_c[1])
		}

		self.asterisk = Asterisk2(deg_to_px(0.5), WHITE, 1).render()
		self.cross_w = FixationCross(deg_to_px(0.5), 2, fill=WHITE).render()
		self.cross_r = FixationCross(deg_to_px(0.5), 2, fill=RED).render()
		self.circle = Circle(self.target_width, fill=WHITE).render()
		self.box =  Rectangle(self.box_size, stroke=(1, WHITE)).render()
		self.frame_duration =  self.animation_duration / self.frame_count
		self.rotation_increment = (pi / 2) / self.frame_count

		# prepare all animation locations for both rotation directions and starting axes
		cx, cy = P.screen_c
		for i in range(0, self.frame_count):
			l_x_cw = -self.offset_size * cos(i * self.rotation_increment)
			l_y_cw = self.offset_size * sin(i * self.rotation_increment)
			l_x_ccw = self.offset_size * cos(i * self.rotation_increment)
			l_y_ccw = -self.offset_size * sin(i * self.rotation_increment)
			cw_locs = [(cx + l_x_cw, cy + l_y_cw), (cx - l_x_cw, cy - l_y_cw)]
			ccw_locs = [(cx + l_x_ccw, cy - l_y_ccw), (cx - l_x_ccw, cy + l_y_ccw)]
			self.frames[H_START_AXIS][ROT_CW].append(ccw_locs)
			self.frames[H_START_AXIS][ROT_CCW].append(cw_locs)
			self.frames[V_START_AXIS][ROT_CW].insert(0, cw_locs)
			self.frames[V_START_AXIS][ROT_CCW].insert(0, ccw_locs)

		self.el.add_boundary("drift correct", [P.screen_c, self.fixation_boundary], CIRCLE_BOUNDARY)

	def block(self):
		pass

	def setup_response_collector(self):
		# this next bit would normally be done in trial_prep() but this method gets called first. we're inferring the
		# cue location based on starting axis (ie. left and top boxes are 'box 1', bottom and right are 'box 2'
		if self.cue_location ==  BOX_1:
			self.cue_location = LEFT if self.start_axis is H_START_AXIS else TOP
		else:
			self.cue_location = RIGHT if self.start_axis is H_START_AXIS else BOTTOM

		self.rc.uses(RC_KEYPRESS)
		self.rc.end_collection_event = "task end"
		self.rc.keypress_listener.interrupts = True
		self.rc.display_callback = self.display_refresh
		self.rc.keypress_listener.key_map = KeyMap("speeded response", ["spacebar"], ["spacebar"], [SDLK_SPACE])
		self.rc.display_args = [self.box_axis_during_target(), self.circle, None, self.target_location]
		self.rc.flip = False

	def trial_prep(self):
		self.el.drift_correct(fill_color=BLACK, target_img=self.cross_r)
		self.evm.register_tickets([("cross fix end", 300),
								   ("circle fix end", 1100),
								   ("cue end", 1400),
								   ("circle box end", 1600),
								   ("animation end", 1900),
								   ("asterisk end", 2060),
								   ("task end", 10560)
		])
		self.display_refresh(self.start_axis, self.circle)

	def trial(self):
		flush()
		while self.evm.before("cross fix end"):
			self.jc_wait_time()
			self.display_refresh(self.start_axis, self.cross_w)
			ui_request()

		while self.evm.before("circle fix end"):
			self.jc_wait_time()
			self.display_refresh(self.start_axis, self.circle)
			ui_request()

		while self.evm.before("cue end"):
			self.jc_wait_time()
			self.display_refresh(self.start_axis, self.circle, cue=self.cue_location)
			ui_request()

		while self.evm.before("circle box end"):
			self.jc_wait_time()
			self.display_refresh(self.start_axis, self.circle)
			ui_request()

		while self.evm.before("animation end"):
			self.jc_wait_time()
			if self.animation_trial:
				if self.evm.trial_time_ms - 1600 > self.current_frame * self.frame_duration and self.current_frame < 15:
					self.display_refresh(self.frames[self.start_axis][self.rotation_dir][self.current_frame], self.asterisk)
					self.current_frame += 1
			else:
				self.display_refresh(self.start_axis, self.asterisk)
			ui_request()


		while self.evm.before("asterisk end"):
			self.display_refresh(self.box_axis_during_target(), self.circle)
			self.jc_wait_time()
			ui_request()

		flush()
		self.display_refresh(self.box_axis_during_target(), self.circle, target=self.target_location)

		if P.saccade_response_cond:
			self.jc_saccade_data()
			keypress_rt = NA
		if P.keypress_response_cond:
			onset = self.evm.trial_time_ms
			self.rc.collect()
			keypress_rt = self.rc.keypress_listener.responses[0][1] - onset
			fill()
		clear()
		smart_sleep(1000)
		return {
			"block_num": P.block_number,
			"trial_num": P.trial_number,
			"cue_location": self.cue_location,
			"target_location": self.target_location,
			"start_axis": self.start_axis,
			"box_rotation": self.rotation_dir if self.animation_trial else NA,
			"animation_trial": boolean_to_logical(self.animation_trial),
			"target_acquired": boolean_to_logical(self.target_acquired) if P.saccade_response_cond else NA,
			"keypress_rt": keypress_rt
		}

	def trial_clean_up(self):
		if P.trial_id and P.saccade_response_cond:  # won't exist if trial recycled
			print self.saccades
			print "/n/n"
			for s in self.saccades:
				s['trial_id'] = P.trial_id
				s['participant_id'] = P.participant_id
				self.db.init_entry('saccades', 't_{0}_saccade_{1}'.format(P.trial_number, self.saccades.index(s)))
				for f in s:
					if f == "end_time":
						continue
					self.db.log(f, s[f])
				self.db.insert()
			self.saccades = []
			self.target_acquired = False
		self.current_frame = 0

	def clean_up(self):
		pass

	def display_refresh(self, boxes=None, fixation=None, cue=None, target=None):
		if P.keypress_response_cond and self.evm.between("asterisk end", "task end"):
			self.jc_wait_time()
		fill()
		if boxes is not None:
			if iterable(boxes):
				box_l = boxes
			if boxes == V_START_AXIS:
				box_l =  [self.target_locs[TOP], self.target_locs[BOTTOM]]
			if boxes == H_START_AXIS:
				box_l =  [self.target_locs[LEFT], self.target_locs[RIGHT]]

			for l in box_l:
				blit(self.box, 5, l)

		if fixation is not None:
			blit(fixation, 5, P.screen_c)

		if cue:
			blit(self.circle, 5, self.target_locs[cue])

		if target:
			blit(self.circle, 5, self.target_locs[target])

		flip()

	def jc_wait_time(self):
		if lsl(self.el.gaze(), P.screen_c) > self.fixation_boundary:
			fill()
			message("MOVED YOUR EYES, IDIOT", registration=5, location=P.screen_c, flip_screen=True)
			any_key()
			raise TrialException("Left fixation early.")

	def jc_saccade_data(self):
		# following code is tidied up but otherwise borrowed from John Christie's original code
		target_onset = self.el.now()
		self.el.write("TARGETON%d" % target_onset)
		if self.el.eye == EL_RIGHT_EYE:
			self.el.write("EYE_USED 1 RIGHT")
		elif self.el.eye in [EL_LEFT_EYE, EL_BOTH_EYES]:
			self.el.write("EYE_USED 0 LEFT")
		else:
			raise TrialException("No eye available")
		while self.el.now() - target_onset < 2500:
			if self.el.getNextData() == EL_SACCADE_END:
				saccade = self.el.getFloatData()
				if saccade:
					if self.el.eye == saccade.getEye():
						gaze = saccade.getEndGaze()
						if lsl(gaze, P.screen_c) > self.fixation_boundary:
							dist_from_target = lsl(gaze, self.target_locs[self.target_location])
							accuracy = SACC_OUTSIDE if dist_from_target > self.fixation_boundary else SACC_INSIDE
							if len(self.saccades):
								duration = saccade.getStartTime() + 4 - self.saccades[-1]['end_time']
							else:
								duration = saccade.getStartTime() + 4 - target_onset
							if len(self.saccades) < 3:
								self.saccades.append({"rt": saccade.getStartTime() - target_onset,
													  "accuracy": accuracy,
													  "dist_from_target": dist_from_target,
													  "start_x": saccade.getStartGaze()[0],
													  "start_y": saccade.getStartGaze()[1],
													  "end_x": saccade.getEndGaze()[0],
													  "end_y": saccade.getEndGaze()[1],
													  "end_time": saccade.getEndTime(),
													  "duration": duration})

							if dist_from_target <= self.fixation_boundary:
								self.target_acquired = True
								break

	def box_axis_during_target(self):
		if self.animation_trial:
			if self.start_axis == V_START_AXIS:
				return H_START_AXIS
			if self.start_axis == H_START_AXIS:
				return V_START_AXIS
		else:
			return self.start_axis