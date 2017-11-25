#! venv/bin/python

from flask import Flask, request
import json

app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)
    print("Request:")
    print(json.dumps(req, indent=4))

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
