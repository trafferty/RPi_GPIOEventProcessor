import requests
import logging
import argparse

logger = logging.getLogger("Actions")

class Actions(object):
    """ 
        Actions class.

        Used to wrap the calling to remote IoT devices
        to cause some action, ie, turning on/off a light
     """

    def __init__(self, action_defs, timeout=5):
        self.action_defs = action_defs
        self.timeout = timeout

        # verify that action defs is okay
        for k, v in self.action_defs.items():
            if 'type' not in v:
                raise KeyError("Missing key in action definition: type")
            if 'url' not in v:
                raise KeyError("Missing key in action definition: url")

    def processAction(self, action_str):
        try:
            for k, v in self.action_defs.items():
                if k == action_str:
                    # we found a matching action
                    if v['type'] == "http_get":
                        logger.debug("Sending get request to %s" % (v['url']))
                        return self.doHTML_get(v['url'])
                    else:
                        logger.error("Invalid action type: %s" % (v['type']))
        except Exception as e:
            logger.error("Error trying to send action: ", action_str)

    def doHTML_get(self, url):
        try:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            return True
        except requests.exceptions.Timeout:
            logger.error("Timed out after %ds sending action to URL: %s" % (self.timeout, url))
            return False
        except requests.exceptions.ConnectionError:
            logger.error("ConnectionError sending action to URL: %s" % (url))
            return False
        except requests.exceptions.HTTPError as e:
            logger.error("Client error with URL: %s" % (url))
            return False

def main():
    import json

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d (%(name)10s) [%(levelname)7s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[ logging.StreamHandler()])
    logger = logging.getLogger()

    parser = argparse.ArgumentParser(description='Utility for testing Actions class.')
    parser.add_argument("action_file_path", help='Full path to action file (JSON format)')
    args = parser.parse_args()

    if args.action_file_path:
        with open(args.action_file_path) as action_file:
            action_defs = json.load(action_file)
    else:
        parser.print_help()
        sys.exit(1)

    timeout = 1
    actions = Actions(action_defs, timeout)

    # test all the actions in the given actionsDef file.  If IP address is invalid
    # then you should get timeout failures except for the test actions
    for k in action_defs.keys():
        logger.info("Processing action: %s" % (k))
        if actions.processAction(k):
            logger.info(" ...OK!")
        else:
            logger.info(" ...Error!")

    # Test for invalid actions...should just 
    for k in ['invalid_actionStr', 'foo', 'bar', 'garage_light_explode']:
        logger.info("Processing action: %s" % (k))
        if actions.processAction(k):
            logger.info(" ...OK!")
        else:
            logger.info(" ...Error! Invalid action?")

if __name__ == '__main__':
    main()

'''
Use to test:

python actions_test_server.py actionDefs.json

'''


