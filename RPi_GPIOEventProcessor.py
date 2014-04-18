import time, datetime, threading, signal, sys, json
import argparse

try:
    import RPi.GPIO as io
    io.setmode(io.BCM)
    sim_mode = False
except ImportError:
    print " --------- Running in RPi Simulation mode (input values are random, outputs are skipped) ----------"
    from random import randint
    sim_mode = True

(STOPPED, RUNNING) = range(2)

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
        print "initialized GPIO event processor object"

    def addCallback(self, callbackFuncion):
        self.eventCallbackList.append(callbackFuncion)
        print "callback added"
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
            if not sim_mode:
                self.input_states[key] = io.input(input[0])
            else:
                self.input_states[key] = randint(0,1)

    def withinRange(self, start_time, end_time):
        '''
        start_time and end_time are both strings representing 
        a time in HH:MM:SS format, with a range of 00:00:00 to
        23:59:59.  end_time must be later than start_time, and 
        they cannot span more than a full day.
        '''
        st = [int(n) for n in start_time.split(':')]
        et = [int(n) for n in end_time.split(':')]
        current = datetime.datetime.now().time()
        start   = datetime.time(*st)
        end     = datetime.time(*et)
        return start <= current <= end

    def start(self):
        self.alive = True
        # start processing thread
        self.processing_thread = threading.Thread(target=self.monitorEvents)
        self.processing_thread.setDaemon(1)
        self.processing_thread.start()
        self.state = RUNNING

    def stop(self):
        print "Shutting down event processing..."
        self.alive = False
        self.state = STOPPED

    def join(self):
        self.processing_thread.join()

    def monitorEvents(self):
        print "Event processing thread started."
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

class GPIOEventProcessor(object):
    """ Event Processor object"""

    def __init__(self, gpio_settings, sim_mode, log_file):
        self.gpio_settings = gpio_settings
        self.sim_mode = sim_mode
        self.log_file = log_file

    def eventCB(self, event):
        self.doLog('Default handler for event: %s' % (event))

    def doLog(self, log_msg):
        msg = "%s: %s" % (time.strftime("[%Y_%d_%m (%a) - %H:%M:%S]", time.localtime()), log_msg)
        print msg
        if len(self.log_file) > 0: 
            f = open(self.log_file, 'a')
            f.write(msg + '\n')
            f.close()

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
        self.opened_threshold_1 = 60 * 1
        self.opened_threshold_2 = 60 * 2

    def eventCB(self, event):
        if event == 'heartbeat':
            self.heartbeat()
        elif event == 'Garage_open_normal':
            self.garage_open_event(False)
        elif event == 'Garage_open_alert':
            self.garage_open_event(True)
        elif event == 'Garage_closed':
            self.garage_close_event()
        else:
            self.doLog('Unhandled event: %s' % (event))

    def garage_open_event(self, alert_flag):
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
                self.doLog("Nothing to do...opened for %d" % (how_long_opened)
        else:
            self.doLog("Processing garage_open_event, alert = %d" % (alert_flag))
            if self.garageDoor_state == S_CLOSED or self.garageDoor_state == S_UNKNOWN:
                self.garageDoor_state = S_OPEN
                self.lastOpenedTime = current_ts
                self.lights_state = S_ON
                self.setLights(self.lights_state)
                self.buzzer(2)

            if alert_flag:
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
                time.sleep(0.5)
                io.output(buzzer_pin, io.LOW)
                time.sleep(0.5)
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
