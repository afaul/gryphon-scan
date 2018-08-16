# -*- coding: utf-8 -*-
# This file is part of the Horus Project

__author__ = 'Jesús Arroyo Torrens <jesus.arroyo@bq.com>'
__copyright__ = 'Copyright (C) 2014-2016 Mundo Reader S.L.'
__license__ = 'GNU General Public License v2 http://www.gnu.org/licenses/gpl2.html'

import time
from horus.engine.calibration.calibration import Calibration

from horus.util import profile

class MovingCalibration(Calibration):

    """Moving calibration:

            - Move motor sequence
            - Call _capture at each position
            - Call _calibrate at the end
    """

    def __init__(self):
        Calibration.__init__(self)
        self.motor_step = 0
        self.motor_speed = 0
        self.motor_acceleration = 0
        self.angle_offset = 0
        self.final_move = "Return"

    def _initialize(self):
        raise NotImplementedError

    def read_profile(self):
        self.motor_step = profile.settings['motor_step_calibration']
        self.motor_speed = profile.settings['motor_speed_calibration']
        self.motor_acceleration = profile.settings['motor_acceleration_calibration']
        self.final_move = profile.settings['after_calibration_position']

    def _capture(self, angle):
        raise NotImplementedError

    def _calibrate(self):
        raise NotImplementedError

    def _start(self):
        if self.driver.is_connected:

            angle = 0.0

            self._initialize()

            # Setup scanner
            self.driver.board.lasers_off()
            self.driver.board.motor_enable()
            self.driver.board.motor_reset_origin()
            self.driver.board.motor_speed(self.motor_speed)
            self.driver.board.motor_acceleration(self.motor_acceleration)

            # Move to starting position
            self.driver.board.motor_move(-90-self.angle_offset)

            if self._progress_callback is not None:
                self._progress_callback(0)

            while self._is_calibrating and abs(angle) < 180:

                if self._progress_callback is not None:
                    self._progress_callback(100 * abs(angle) / 180.)

                self._capture(angle)

                angle += self.motor_step
                self.driver.board.motor_move(self.motor_step)
                time.sleep(0.5)

            if self.final_move == 'Return':
                # Move to origin
                self.driver.board.motor_move(90 + self.angle_offset - angle)
            else:
                if self.final_move == 'Perpendicular':
                    # Move to origin
                    self.driver.board.motor_move(90 - angle)

            self.driver.board.lasers_off()
            self.driver.board.motor_disable()
            self.angle_offset = 0 # cleanup

            # Compute calibration
            response = self._calibrate()

            if self._after_callback is not None:
                self._after_callback(response)
