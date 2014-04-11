import time, datetime, threading, sys, json

(STOPPED, RUNNING) = range(2)

def getCurrentTime():
  return time.localtime().tm_hour + (time.localtime().tm_min/60.0) + (time.localtime().tm_sec/3600.0)

class EventProcessor:
  """ Event processor object"""

  def __init__(self, event_triggers):
    self.event_triggers = event_triggers
    self.eventCallback = None
    self.state = STOPPED
    print "initialized event processor object"

  def setCallback(self, callbackFuncion):
    self.eventCallback = callbackFuncion
    print "callback set"
    self.eventCallback("test callback")
    
  def getState(self):
    return self.state

  def withinRange(start_time, end_time):
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
      current_time = getCurrentTime()
      for trigger in self.event_triggers:
        # First see if current time falls within trigger's 
        # start and end times...
        if current_time > trigger['start_time'] and current_time < trigger['end_time']:
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
    parser.add_argument('-d', '--dio_setup', type=str, default="", help='JSON file defining GPIO setup')
    parser.add_argument('-e', '--events', type=str, default="", help='JSON file defining the events to monitor')

    event_triggers = json.load(open(parser.events, 'r'))

    ep = EventProcessor(event_triggers)
    ep.setCallback = eventCB
    ep.start()


