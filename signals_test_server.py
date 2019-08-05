import argparse
import json
from flask import Flask, abort

valid_signal_list = []

app = Flask("Signals Test Server")

@app.route('/')
def handle_root():
    print("Received root")
    return ''

@app.route('/<string:signalStr>')
def handle_signal(signalStr):
    print("Received: %s" % (signalStr))
    if signalStr not in valid_signal_list:
        abort(404)
    return ''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test server for Signals class.')
    parser.add_argument("signal_file_path", help='Full path to signal file (JSON format)')
    args = parser.parse_args()

    if args.signal_file_path:
        with open(args.signal_file_path) as signal_file:
            signal_defs = json.load(signal_file)
    else:
        parser.print_help()
        sys.exit(1)

    for k in signal_defs.keys():
        print("  Adding valid signalStr: %s" % (k))
        valid_signal_list.append(k)

    app.run(host='0.0.0.0', port=8000, debug=True)
