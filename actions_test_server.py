import argparse
import json
from flask import Flask, abort

valid_action_list = []

app = Flask("Actions Test Server")

@app.route('/')
def handle_root():
    print("Received root")
    return ''

@app.route('/<string:action_str>')
def handle_action(action_str):
    print("Received: %s" % (action_str))
    if action_str not in valid_action_list:
        abort(404)
    return ''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test server for Actions class.')
    parser.add_argument("action_file_path", help='Full path to action file (JSON format)')
    args = parser.parse_args()

    if args.action_file_path:
        with open(args.action_file_path) as action_file:
            action_defs = json.load(action_file)
    else:
        parser.print_help()
        sys.exit(1)

    for k in action_defs.keys():
        print("  Adding valid action_str: %s" % (k))
        valid_action_list.append(k)

    app.run(host='0.0.0.0', port=80, debug=True)
