# Version 0.1.1

```
$ http POST localhost:5000/webhook Hello=World
HTTP/1.0 200 OK
Content-Length: 23
Content-Type: application/json
Date: Sun, 26 Nov 2017 11:20:04 GMT
Server: Werkzeug/0.12.2 Python/3.6.2

{
    "Hello": "World"
}
```

```
Request:
{
    "Hello": "World"
}
127.0.0.1 - - [26/Nov/2017 12:20:04] "POST /webhook HTTP/1.1" 200 -
```


Example hello world event:

```json
{
    "responseId": "6b0178b4-c9b2-42e3-b293-4c0d8030fc59",
    "queryResult": {
        "queryText": "Hello",
        "action": "hello",
        "parameters": {},
        "allRequiredParamsPresent": true,
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        ""
                    ]
                }
            }
        ],
        "intent": {
            "name": "projects/incidents-9359b/agent/intents/0f5d8d3c-f662-46a2-90e5-cc41e667301c",
            "displayName": "Hello"
        },
        "intentDetectionConfidence": 1.0,
        "diagnosticInfo": {},
        "languageCode": "en"
    },
    "originalDetectIntentRequest": {
        "payload": {}
    },
    "session": "projects/incidents-9359b/agent/sessions/60152c9d-ea6a-436a-af0a-fefdb76c891e"
}
```

Now from Slack

```json
{
    "responseId": "36f1d96a-e353-4f17-8b42-9b80aca2ce70",
    "queryResult": {
        "queryText": "Hello",
        "action": "hello",
        "parameters": {},
        "allRequiredParamsPresent": true,
        "fulfillmentMessages": [
            {
                "text": {
                    "text": [
                        ""
                    ]
                }
            }
        ],
        "intent": {
            "name": "projects/incidents-9359b/agent/intents/0f5d8d3c-f662-46a2-90e5-cc41e667301c",
            "displayName": "Hello"
        },
        "intentDetectionConfidence": 1.0,
        "diagnosticInfo": {},
        "languageCode": "en"
    },
    "originalDetectIntentRequest": {
        "payload": {
            "data": {
                "authed_users": [
                    "U84T2CA6R"
                ],
                "event_id": "Ev852SJBDF",
                "api_app_id": "A85BF397D",
                "team_id": "T84NUNW2W",
                "event": {
                    "event_ts": "1511720131.000023",
                    "channel": "D869XNK7Y",
                    "text": "Hello",
                    "type": "message",
                    "user": "U84T2CA6R",
                    "ts": "1511720131.000023"
                },
                "type": "event_callback",
                "event_time": 1511720131.0,
                "token": "q4GmpdQPQSUT9TlJhSiDrwhU"
            },
            "source": "slack"
        }
    },
    "session": "projects/incidents-9359b/agent/sessions/a488a01b-46b7-4db5-a703-f3bb2ef062ff"
}
```


# Configuration

`config.json` :

```
{
  "slack": {
    "channel": "#incidents",
    "self": {
      "token": "xoxb-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "id": "ABCD12345",
      "name": "incidents-bot"
    },
    "fake_user": {
      "email": "hello@example.org",
      "password": "ultrasecurepassword",
      "token": "xoxp-111111111111-222222222222-333333333333-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    },
    "apiai_user": {
      "id": "XYZ987654"
    }
  },
  "elasticsearch": {
    "index": "incidents",
    "host": "my-es-cluster.eu-west-1.es.amazonaws.com",
    "region": "eu-west-1"
  },
  "jira": {
    "host": "https://jira.example.org",
    "user": "incidents-bot",
    "password": "anotherultrasecurepassword",
    "project": "INCIDENTS"
  },
  "cachet": {
    "host": "http://status.example.org/api/v1",
    "token": "xxxxxxxxxxxxxxxxxxxx"
  }
}
```
