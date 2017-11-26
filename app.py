#! venv/bin/python

from flask import Flask, request, jsonify
import json
import traceback

from log import log
from incidents_manager import IncidentsManager

app = Flask(__name__)

incidents = IncidentsManager()

# Error Handlers


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': str(error)}), 404)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': str(error)}), 400)


@app.errorhandler(422)
def unprocessable_entity(error):
    return make_response(jsonify({'error': str(error)}), 422)

# Handlers


@app.route('/')
def index():
    """
    Simple debugging endpoint
    """
    return "Hello, I'm incidents bot!"


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main webhook
    """
    req = request.get_json(silent=True, force=True)
    log.info("Handling new request:\n" + json.dumps(req, indent=4))

    # Parsing intent
    # noinspection PyBroadException
    try:
        log.info("Parsing intent...")
        intent = req['queryResult']['intent']['displayName']
        log.info("Got a new intent: " + intent)
    except Exception:
        traceback.print_exc()
        log.error("Failed to parse intent")
        return jsonify({"status": "failed"})

    # Dispatching based on parsed intent
    if intent == "incident.create":
        incidents.create_incident(req['queryResult']['parameters'])
    else:
        log.warning("Couldn't dispatch intent {intent} to anything "
                    "known".format(intent=intent))
        return jsonify({"status": "failed"})
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
