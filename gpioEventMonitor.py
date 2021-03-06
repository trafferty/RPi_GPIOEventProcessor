import sys
import time
import datetime
import threading
import logging

try:
    import RPi.GPIO as io
    io.setmode(io.BCM)
except ImportError:
    from random import randint

(STOPPED, RUNNING) = range(2)

logger = logging.getLogger("EventMonitor")

class GPIOEventMonitor:
    """ GPIO Event monitor object"""

    def __init__(self, gpio_settings, event_triggers, sim_mode, sleep_time=1.0):
        self.event_triggers = event_triggers
        self.gpio_settings = gpio_settings
        self.eventCallbackList = []
        self.state = STOPPED
        self.sim_mode = sim_mode
        self.sleep_time = sleep_time
        if not sim_mode:
            self.setupGPIO()
        self.input_states = {}
        logger.info("initialized GPIO event processor object")

    def addCallback(self, callbackFuncion):
        self.eventCallbackList.append(callbackFuncion)
        logger.info("callback added")
        callbackFuncion("test callback")
        
    def getRunState(self):
        return self.state

    def setupGPIO(self):
        for key in self.gpio_settings['inputs']:
            input = self.gpio_settings['inputs'][key]
            if input[1]:
                io.setup(input[0], io.IN, pull_up_down=io.PUD_UP)
            else:
                io.setup(input[0], io.IN)
        for key in self.gpio_settings['outputs']:
            io.setup(self.gpio_settings['outputs'][key], io.OUT)

    def updateInputs(self):
        for key in self.gpio_settings['inputs']:
            input = self.gpio_settings['inputs'][key]
            if not self.sim_mode:
                self.input_states[key] = io.input(input[0])
            else:
                self.input_states[key] = randint(0,1)

    def withinRange(self, start_time, end_time):
        '''
        start_time and end_time are both strings representing 
        a time in HH:MM:SS format, with a range of 00:00:00 to
        23:59:59.  if start_time > end_time (ie, start at 20:00:00
        and end at 06:00:00) it is assumed that this range spans
        two days (start_time in one day, end_time in the next).
        '''
        st = [int(n) for n in start_time.split(':')]
        et = [int(n) for n in end_time.split(':')]
        current = datetime.datetime.now().time()
        start   = datetime.time(*st)
        end     = datetime.time(*et)
        if start > end:
            return (current <= end) or (current >= start)
        else:
            return start <= current <= end

    def start(self):
        self.alive = True
        # start processing thread
        self.processing_thread = threading.Thread(target=self.monitorEvents)
        self.processing_thread.setDaemon(1)
        self.processing_thread.start()
        self.state = RUNNING

    def stop(self):
        logger.info("Shutting down event processing...")
        self.alive = False
        self.state = STOPPED

    def join(self):
        self.processing_thread.join()

    def monitorEvents(self):
        logger.info("Event processing thread started.")
        while self.alive:
            self.updateInputs()
            for trigger in self.event_triggers:
                # First see if current time falls within trigger's 
                # start and end times...
                if self.withinRange(trigger['start_time'], trigger['end_time']):
                    for input_event in trigger['input_events']:
                        if input_event['value'] == self.input_states[input_event['name']] \
                        and len(self.eventCallbackList) > 0:
                            for eventCallback in self.eventCallbackList:
                                eventCallback(input_event['event'])
            time.sleep(self.sleep_time)
            continue