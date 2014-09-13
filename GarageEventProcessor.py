import signal
import json
import argparse
import time

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

class GarageDoorEventProcessor(GPIOEventProcessor):
    """ garage Door Event Processor object"""

    def __init__(self, gpio_settings, sim_mode, log_file):
        super(GarageDoorEventProcessor, self).__init__(gpio_settings, sim_mode, log_file)
        self.garageDoor_state = S_UNKNOWN
        self.lastOpenedTime = 0
        self.lastClosedTime = 0
        self.heartbeat_state = 0
        self.lights_state = S_OFF
        self.setLights(self.lights_state)
        self.opened_threshold_1 = 60 * 10
        self.opened_threshold_2 = 60 * 60

    def eventCB(self, event):
        if event == 'heartbeat':
            self.heartbeat()
        elif event == 'Garage_open_normal':
            self.garage_open_normal_event()
        elif event == 'Garage_open_alert':
            self.garage_open_alert_event()
        elif event == 'Garage_closed':
            self.garage_close_event()
        else:
            self.doLog('Unhandled event: %s' % (event))

    def garage_open_normal_event(self):
        current_ts = time.time()
        if self.garageDoor_state == S_OPEN:
            how_long_opened = current_ts - self.lastOpenedTime
            if how_long_opened > self.opened_threshold_2:
                self.setLights(S_OFF)
                self.buzzer(2)
                self.setLights(S_ON)
                self.lights_state = S_ON
            elif how_long_opened > self.opened_threshold_1:
                self.setLights(S_OFF)
                time.sleep(1)
                self.setLights(S_ON)
                self.lights_state = S_ON
            else:
                print("Opened for %ds" % (how_long_opened))
        else:
            self.doLog("Processing garage_open_event...")
            if self.garageDoor_state == S_CLOSED or self.garageDoor_state == S_UNKNOWN:
                self.garageDoor_state = S_OPEN
                self.lastOpenedTime = current_ts
                self.lights_state = S_ON
                self.setLights(self.lights_state)
                self.buzzer(2)

    def garage_open_alert_event(self):
        self.doLog("Processing garage_open_alert_event...")
        if self.garageDoor_state == S_CLOSED or self.garageDoor_state == S_UNKNOWN:
            self.garageDoor_state = S_OPEN
            self.lastOpenedTime = time.time()
        self.setLights(S_OFF)
        self.buzzer(2)
        self.setLights(S_ON)
        self.buzzer(2)
        self.setLights(S_OFF)
        self.buzzer(2)
        self.setLights(S_ON)
        self.lights_state = S_ON

    def garage_close_event(self):
        if self.garageDoor_state != S_CLOSED:
            if self.garageDoor_state == S_OPEN:
                self.doLog("Processing garage_close_event...was open for %ds" % (time.time() - self.lastOpenedTime))
            else:
                self.doLog("Processing garage_close_event")
            self.garageDoor_state = S_CLOSED
            self.lastOpenedTime = 0
            self.lights_state = S_OFF
            self.setLights(self.lights_state)
            self.buzzer(3)

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

if __name__ == '__main__':

    def sigint_handler(signal, frame):
        print "Caught Ctrl-c..."
        eventMonitor.stop()
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(description='Event monitor system for Raspberry Pi')
    parser.add_argument('-g', '--gpio_setup', type=str, help='JSON file defining GPIO setup', required=True)
    parser.add_argument('-e', '--events', type=str, help='JSON file defining the events to monitor', required=True)
    parser.add_argument('-l', '--log_file', type=str, default='', help='log file path for processor (optional)', required=False)
    parser.add_argument('-k', '--log_key', type=str, default='', help='log file path for processor (optional)', required=False)
    parser.add_argument('-s', '--sleep_time', type=float, default=1.0, help='sleep time for event loop, in secs')
    args = parser.parse_args()

    gpio_settings = json.load(open(args.gpio_setup, 'r'))
    event_triggers = json.load(open(args.events, 'r'))

    eventMonitor = GPIOEventMonitor(gpio_settings, event_triggers, sim_mode, args.sleep_time)
    eventProcessor = GarageDoorEventProcessor(gpio_settings, sim_mode, args.log_file)

    eventMonitor.addCallback(eventProcessor.eventCB)
    eventMonitor.start()
    signal.pause()
    eventMonitor.join()
