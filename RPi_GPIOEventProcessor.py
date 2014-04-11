import time, datetime, threading, sys, json
import RPi.GPIO as io
io.setmode(io.BCM)

(STOPPED, RUNNING) = range(2)

class GPIOEventProcessor:
    """ GPIO Event processor object"""

    def __init__(self, gpio_settings, event_triggers):
        self.event_triggers = event_triggers
        self.gpio_settings = gpio_settings
        self.eventCallback = None
        self.state = STOPPED
        self.setupGPIO()
        print "initialized event processor object"

    def setCallback(self, callbackFuncion):
        self.eventCallback = callbackFuncion
        print "callback set"
        self.eventCallback("test callback")
        
    def getRunState(self):
        return self.state

    def setupGPIO(self):

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
        self.processing_thread = threading.Thread(target=self.processEvents)
        self.processing_thread.setDaemon(1)
        self.processing_thread.start()
        self.state = RUNNING

    def stop(self):
        print "Shutting down event processing..."
        self.alive = False
        self.state = STOPPED

    def join(self):
        self.processing_thread.join()

    def processEvents(self):
        print "Event processing thread started."
        while self.alive:
            for trigger in self.event_triggers:
                # First see if current time falls within trigger's 
                # start and end times...
                if withinRange(trigger['start_time'], trigger['end_time']):
                    if self.eventCallback:
                        print 'calling callback for %d event(s)...' % (len(trigger['events']))
                        for event in trigger['events']:
                            self.eventCallback(event)
            time.sleep(1.0)
            continue

def eventCB(event):
    print 'Received callback: %s' % (event)

if __name__ == '__main__':
        parser = argparse.ArgumentParser(description='Event monitor system for Raspberry Pi')
        parser.add_argument('-g', '--gpio_setup', type=str, default="", help='JSON file defining GPIO setup')
        parser.add_argument('-e', '--events', type=str, default="", help='JSON file defining the events to monitor')

        gpio_settings = json.load(open(parser.gpio_setup, 'r'))
        event_triggers = json.load(open(parser.events, 'r'))

        ep = EventProcessor(gpio_settings, event_triggers)
        ep.setCallback = eventCB
        ep.start()


