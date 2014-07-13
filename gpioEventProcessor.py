import time

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