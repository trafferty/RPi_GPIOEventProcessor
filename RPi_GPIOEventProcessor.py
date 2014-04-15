import time, datetime, threading, sys, json
import RPi.GPIO as io
io.setmode(io.BCM)

(STOPPED, RUNNING) = range(2)

class GPIOEventMonitor:
    """ GPIO Event monitor object"""

    def __init__(self, gpio_settings, event_triggers):
        self.event_triggers = event_triggers
        self.gpio_settings = gpio_settings
        self.eventCallback = None
        self.state = STOPPED
        self.setupGPIO()
        self.input_states = {}
        print "initialized GPIO event processor object"

    def setCallback(self, callbackFuncion):
        self.eventCallback = callbackFuncion
        print "callback set"
        self.eventCallback("test callback")
        
    def getRunState(self):
        return self.state

    def setupGPIO(self):
        for key in self.gpio_settings['inputs']:
            input = self.gpio_settings['inputs'][key]
            if input[1]:
                io.setup(input[0], io.IN, pull_up_down=io.PUD_UP)
            else:
                io.setup(input[0], io.IN)
            self.input_states[key] = io.input(door_pin)
        for key in self.gpio_settings['outputs']:
            io.setup(self.gpio_settings['outputs'][key], io.OUT)

    def updateInputs(self):
        for key in self.gpio_settings['inputs']:
            input = self.gpio_settings['inputs'][key]
            self.input_states[key] = io.input(input[0])

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
            updateInputs()
            for trigger in self.event_triggers:
                # First see if current time falls within trigger's 
                # start and end times...
                if withinRange(trigger['start_time'], trigger['end_time']):
                    for input_event in self.input_states[trigger['input_events']]:
                        if self.input_states[input_event['name']] == input_event['value'] \
                        and self.eventCallback:
                            print 'calling callback for %d event(s)...' % (len(trigger['events']))
                            self.eventCallback(input_event['event'])
            time.sleep(1.0)
            continue

class EventProcessor:
    """ Event Processor object"""

    def eventCB(event):
        print 'Received callback: %s' % (event)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Event monitor system for Raspberry Pi')
    parser.add_argument('-g', '--gpio_setup', type=str, default="", help='JSON file defining GPIO setup')
    parser.add_argument('-e', '--events', type=str, default="", help='JSON file defining the events to monitor')

    gpio_settings = json.load(open(parser.gpio_setup, 'r'))
    event_triggers = json.load(open(parser.events, 'r'))

    eventMonitor = EventMonitor(gpio_settings, event_triggers)

    eventProcessor = EventProcessor()

    eventMonitor.setCallback = eventProcessor.eventCB
    eventMonitor.start()

    while 1:
        time.sleep(1.0)
        try:
            pass
        except KeyboardInterrupt, k:
            raise
            break
      
    eventMonitor.join()
