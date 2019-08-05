import requests
import logging
import argparse

logger = logging.getLogger("Signals")

class Signals(object):
    """ 
        Signals class.

        Used to wrap the calling to remote IoT devices
        to cause some action, ie, turning on/off a light
     """

    def __init__(self, signal_defs):
        self.signal_defs = signal_defs

        # verify that signal defs is okay
        for k, v in self.signal_defs.items():
            if 'type' not in v:
                raise KeyError("Missing key in signal definition: type")
            if 'url' not in v:
                raise KeyError("Missing key in signal definition: url")

    def sendSignal(self, signalStr):
        try:
            for k, v in self.signal_defs.items():
                if k == signalStr:
                    # we found a matching signal
                    if v['type'] == "http_get":
                        logger.debug("Sending get request to %s" % (v['url']))
                        return self.doHTML_get(v['url'])
                    else:
                        logger.error("Invalid signal type: %s" % (v['type']))
        except Exception as e:
            logger.error("Error trying to send signal: ", signalStr)

    def doHTML_get(self, url):
        r = requests.get(url)
        try: 
            r.raise_for_status()
            return True
        except requests.exceptions.HTTPError as e:
            logger.error("Client error with URL: %s" % (url))
            #print(e)
            return False

def main():
    import json

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d (%(name)10s) [%(levelname)7s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[ logging.StreamHandler()])
    logger = logging.getLogger()

    parser = argparse.ArgumentParser(description='Utility for testing Signals class.')
    parser.add_argument("signal_file_path", help='Full path to signal file (JSON format)')
    args = parser.parse_args()

    if args.signal_file_path:
        with open(args.signal_file_path) as signal_file:
            signal_defs = json.load(signal_file)
    else:
        parser.print_help()
        sys.exit(1)

    signals = Signals(signal_defs)

    for k in signal_defs.keys():
        logger.info("Sending signal: %s" % (k))
        if signals.sendSignal(k):
            logger.info(" ...OK!")
        else:
            logger.info(" ...Error!")

    # Test for invalid signals
    for k in ['invalid_signalStr', 'foo', 'bar', 'garage_light_explode']:
        logger.info("Sending signal: %s" % (k))
        if signals.sendSignal(k):
            logger.info(" ...OK!")
        else:
            logger.info(" ...Error!")

if __name__ == '__main__':
    main()

'''
Use to test:

python signals_test_server.py signals.json

'''


