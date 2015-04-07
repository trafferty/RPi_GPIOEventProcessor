#!/usr/bin/env python

import signal
import json
import argparse
import time
from threading import Timer
import subprocess

from gpioEventMonitor import GPIOEventMonitor
from gpioEventProcessor import GPIOEventProcessor

try:
    import RPi.GPIO as io
    io.setmode(io.BCM)
    sim_mode = False
except ImportError:
    print " --------- Running in RPi Simulation mode (input values are random, outputs are skipped) ----------"
    from random import randint
    sim_mode = True

(S_UNKNOWN, S_OPEN, S_CLOSED) = range(3)
(S_OFF, S_ON) = range(2)

class GarageEventProcessor(GPIOEventProcessor):
    """ garage Event Processor object"""

    def __init__(self, gpio_settings, sim_mode, log_file, data_log_uri):
        super(GarageEventProcessor, self).__init__(gpio_settings, sim_mode, log_file, data_log_uri)
        self.garageDoor_state = S_UNKNOWN
        self.lastOpenedTime = 0
        self.lastClosedTime = 0
        self.MotionCtr = 0
        self.heartbeat_state = 0
        self.lights_state = S_OFF
        self.setLights(self.lights_state)
        self.opened_threshold_1 = 60 * 180   # if garage door opened > 180m
        self.opened_threshold_2 = 60 * 240  # if garage door opened > 240m
        self.reset_limit = 60 * 60
        self.reset_timestamp = time.time() - self.reset_limit
        self.alert_active = False
        self.alert_time = 0
        self.alert_duration = 60 * 5   # 5m max alert duration
        self.garage_light_on_duration = 60 * 5   # 5m max 
        self.TurnGarageLightOn_cmd = "heyu fon e2"
        self.TurnGarageLightOff_cmd = "heyu foff e2"
        self.garageLights_state = S_OFF
        
    def eventCB(self, event):
        if event == 'heartbeat':
            self.heartbeat()
        elif event == 'reset_button_pressed':
            self.reset_button_pressed()
        elif event == 'Garage_closed':
            self.garage_close_event()
        elif event == 'motion_detected':
            self.motion_detected()
        elif event == 'motion_detected_alert':
            self.motion_detected_alert()
        elif time.time() - self.reset_timestamp > self.reset_limit:
            if event == 'Garage_open_normal':
                self.garage_open_normal_event()
            elif event == 'Garage_open_alert':
                self.garage_open_alert_event()
            else:
                self.doLog('Unhandled event: %s' % (event))
        if self.alert_active:
            if time.time() - self.alert_time > self.alert_duration:
                self.doLog("Cancelling alert: duration exceded")
                self.alert_active = False
                self.horn_on(False)
                self.setLights(S_OFF)

    def reset_button_pressed(self):
        self.reset_timestamp = time.time()
        self.doLog("Reset button pressed...")
        self.buzzer(1)

    def motion_detected_alert(self):
        if not self.alert_active:
            self.alert_time = time.time()
            self.alert_active = True
            self.horn_on(True)
            self.setLights(S_ON)
        self.doLog("Intruder alert!")
        self.log_motion()

    def motion_detected(self):
        self.log_motion()

    def garage_open_normal_event(self):
        current_ts = time.time()
        if self.garageDoor_state == S_OPEN:
            how_long_opened = current_ts - self.lastOpenedTime
            if how_long_opened > self.opened_threshold_2:
                self.setLights(S_OFF)
                self.buzzer(1)
                self.setLights(S_ON)
                self.lights_state = S_ON
            elif how_long_opened > self.opened_threshold_1:
                self.setLights(S_OFF)
                time.sleep(0.5)
                self.setLights(S_ON)
                self.lights_state = S_ON
            else:
                print("Opened for %ds" % (how_long_opened))
        else:
            self.doLog("Processing garage_open_event...")
            self.dataLog(self.build_data_log_entry(S_OPEN, False))
            if self.garageDoor_state == S_CLOSED or self.garageDoor_state == S_UNKNOWN:
                self.garageDoor_state = S_OPEN
                self.lastOpenedTime = current_ts
                self.lights_state = S_ON
                self.setLights(self.lights_state)
                self.buzzer(2)
        if self.garageLights_state == S_OFF:
            self.toggleGarageLight(S_ON)

    def garage_open_alert_event(self):
        self.doLog("Processing garage_open_alert_event...")
        if self.garageDoor_state == S_CLOSED or self.garageDoor_state == S_UNKNOWN:
            self.garageDoor_state = S_OPEN
            self.lastOpenedTime = time.time()
            self.dataLog(self.build_data_log_entry(S_OPEN, False))
        self.setLights(S_OFF)
        self.buzzer(2)
        self.setLights(S_ON)
        self.buzzer(2)
        self.setLights(S_OFF)
        self.buzzer(2)
        self.setLights(S_ON)
        self.lights_state = S_ON
        if self.garageLights_state == S_OFF:
            self.toggleGarageLight(S_ON)

    def garage_close_event(self):
        if self.garageDoor_state != S_CLOSED:
            if self.garageDoor_state == S_OPEN:
                amount_time_opened = time.time() - self.lastOpenedTime
                self.doLog("Processing garage_close_event...was open for %ds" % (amount_time_opened))
                self.dataLog(self.build_data_log_entry(S_CLOSED, False))
            else:
                self.doLog("Processing garage_close_event")
            self.garageDoor_state = S_CLOSED
            self.lastOpenedTime = 0
            self.lights_state = S_OFF
            self.setLights(self.lights_state)
            self.buzzer(3)
        if self.garageLights_state == S_OFF:
            self.toggleGarageLight(S_ON)

    def heartbeat(self):
        # flip the state...
        self.heartbeat_state = self.heartbeat_state^1
        if not sim_mode:
            heartbeat_led = self.gpio_settings['outputs']['heartbeat_led']
            if self.heartbeat_state == 0:
                io.output(heartbeat_led, io.LOW)
            else:
                io.output(heartbeat_led, io.HIGH)
        else:
            self.doLog("Heartbeat signal received. State = %d" % self.heartbeat_state)
        if self.garageLights_state == S_ON:
            if time.time() - self.garageLightOnTime > self.garage_light_on_duration:
                toggleGarageLight(S_OFF)

    def setLights(self, on):
        if not sim_mode:
            lights_relay = self.gpio_settings['outputs']['lights_relay']
            if on:
                io.output(lights_relay, io.LOW)
            else:
                io.output(lights_relay, io.HIGH)
        else:
            self.doLog("Lights turned %s" % ("on" if on else "off"))

    def buzzer(self, num_of_times):
        for idx in range(num_of_times):
            if not sim_mode:
                buzzer_pin = self.gpio_settings['outputs']['buzzer']
                io.output(buzzer_pin, io.HIGH)
                time.sleep(0.4)
                io.output(buzzer_pin, io.LOW)
                time.sleep(0.4)
            else:
                self.doLog("Buzzer: %d of %d..." % (idx+1, num_of_times))

    def horn_on(self, on):
        if not sim_mode:
            horn_pin = self.gpio_settings['outputs']['horn_relay']
            if on:
                io.output(horn_pin, io.HIGH)
            else:
                io.output(horn_pin, io.LOW)
        else:
            self.doLog("Horn: %s" % ("on" if on else "off"))

    def log_motion(self):
        if self.MotionCtr == 0:
            self.motion_log_timer = Timer(10, self.process_cumulative_motion)
            self.motion_log_timer.start()
        self.MotionCtr += 1
        self.doLog(">>>>>>>>>>> Motion detected: %d" % (self.MotionCtr))

    def process_cumulative_motion(self):
        self.motion_log_timer.cancel()
        self.dataLog(self.build_data_log_entry(self.garageDoor_state, True))
        self.dataLog(self.build_data_log_entry(self.garageDoor_state, False))
        self.MotionCtr = 0
        self.doLog(">>>>>>>>> logging motion")

    def build_data_log_entry(self, door_state, motion_detected):
        garageDoor_open = 1 if door_state == S_OPEN else 0
        return "&door_status=%d&motion_detected=%d" % (garageDoor_open, motion_detected)

    def toggleGarageLight(garageLightState):
        if garageLightState == S_ON:
            self.garageLights_state = S_ON
            process = subprocess.Popen(TurnGarageLightOn_cmd.split(), stdout=subprocess.PIPE)
            self.garageLightOnTime = time.time()
        else:
            self.garageLights_state = S_OFF
            process = subprocess.Popen(TurnGarageLightOff_cmd.split(), stdout=subprocess.PIPE)

if __name__ == '__main__':

    def sigint_handler(signal, frame):
        print "Caught Ctrl-c..."
        eventMonitor.stop()
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(description='Event monitor system for Raspberry Pi')
    parser.add_argument('-g', '--gpio_setup', type=str, help='JSON file defining GPIO setup', required=True)
    parser.add_argument('-e', '--events', type=str, help='JSON file defining the events to monitor', required=True)
    parser.add_argument('-l', '--log_file', type=str, default='', help='log file path for processor (optional)', required=False)
    parser.add_argument('-u', '--data_log_uri', type=str, default='', help='uri for logging data to data.sparkfun.com (optional)', required=False)
    parser.add_argument('-s', '--sleep_time', type=float, default=1.0, help='sleep time for event loop, in secs')
    args = parser.parse_args()

    gpio_settings = json.load(open(args.gpio_setup, 'r'))
    event_triggers = json.load(open(args.events, 'r'))

    eventMonitor = GPIOEventMonitor(gpio_settings, event_triggers, sim_mode, args.sleep_time)
    eventProcessor = GarageEventProcessor(gpio_settings, sim_mode, args.log_file, args.data_log_uri)

    eventMonitor.addCallback(eventProcessor.eventCB)
    eventMonitor.start()
    signal.pause()
    eventMonitor.join()

