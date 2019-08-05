import time
import logging
try:
    import urllib2
except ImportError:
    sim_data_log = True

logger = logging.getLogger("EventProc")

class MyException(Exception):
    pass

class GPIOEventProcessor(object):
    """ Event Processor object"""

    def __init__(self, gpio_settings, sim_mode, log_file, data_log_uri_base, signal_defs):
        self.gpio_settings = gpio_settings
        self.sim_mode = sim_mode
        self.log_file = log_file
        self.data_log_uri_base = data_log_uri_base
        self.signal_defs = signal_defs

    def eventCB(self, event):
        logger.info('Default handler for event: %s' % (event))

    def doLog(self, log_msg):
        logger.info(msg)

    def dataLog(self, data):
        if len(self.data_log_uri_base) > 0 and not sim_data_log: 
            try:
                rep = urllib2.urlopen("%s%s" % (self.data_log_uri_base, data)).read()
                logger.info("Logging data: %s. reply: %s" % ( data, rep))
            except:
                logger.warn("Error connecting to data logger; skipping post")
