#!/usr/bin/env python

import signal
import json
import os.path
import argparse
import time
import logging
from actions import Actions

(S_OFF, S_ON) = range(2)

if __name__ == '__main__':

    def sigint_handler(signal, frame):
        logger.info("Caught Ctrl-c...")
        eventMonitor.stop()
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(description='Event monitor system for Raspberry Pi')
    parser.add_argument('-d', '--duration_h', type=float, help='Test duration in hours', required=True)
    parser.add_argument('-p', '--pause_s', default=30, type=int, help='Pause time between toggles (optional)')
    parser.add_argument('-a', '--actions', type=str, help='JSON file defining the actions', required=True)
    parser.add_argument('-l', '--log_file', type=str, default='~/action_test.txt', help='log file path for test (optional)', required=False)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d (%(name)10s) [%(levelname)7s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.expanduser(args.log_file), mode='a')
        ])
    logger = logging.getLogger("Test")

    action_defs = json.load(open(args.actions, 'r'))

    actions = Actions(action_defs)

    test_duration_s = args.duration_h * 3600
    logger.info("Test duration: %0.2f hours (%d sec)" % (args.duration_h, test_duration_s))

    garageLights_state = S_OFF
    def toggleGarageLight():
        global garageLights_state
        if garageLights_state == S_OFF:
            if actions.processAction('garage_light_on'):
                garageLights_state = S_ON
                logger.info("turned garage light on")
                return True
            else:
                logger.warn("Error turning garage light on")
                return False
        else:
            if actions.processAction('garage_light_off'):
                garageLights_state = S_OFF
                logger.info("turned garage light off")
                return True
            else:
                logger.warn("Error turning garage light off")
                return False

    fail_cnt = 0
    good_cnt = 0
    logger.info("Starting test...")
    start_ts = time.time()
    while start_ts+test_duration_s > time.time():
        if toggleGarageLight():
            good_cnt += 1
        else:
            fail_cnt += 1
        logger.info("Num good: %d, Num fails: %d.  Pausing for %ds..." % (good_cnt, fail_cnt, args.pause_s))
        time.sleep(args.pause_s)

    logger.info("Test completed after %0.2f hours" % (args.duration_h))
