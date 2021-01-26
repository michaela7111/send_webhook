from flask import request
from flask import Flask
from gevent.pywsgi import WSGIServer
import requests
import json
import time

###########################################################################
# This is a simple Flask web-app backend server that can process a webhook
# invoked from a PagerDuty incident.  The invocation of the webhook is 
# automated based on the action a responder takes on an incident.
#
# For example, if a responder adds a note to an incident the webhook will
# be called and the event attribute of 'incident.annote' will be true
# and sent as part of the event payload to the webhook endpoint.  You will
# evaluate against 'incident.annote' and perform an action such as calling
# a script.
#
# Please refer to 'def api_pd_info()' function for more information.
###########################################################################

PORT = 9004
APP = Flask(__name__)

API_KEY = '<PROVIDE PAGERDUTY API_KEY HERE>'
EMAIL = '<PROVIDE EMAIL ADDRESS HERE>'
CONTENT = 'The incident has been acknowledged and responders have been notified.'

def create_incident_note(incident_id):
    url = 'https://api.pagerduty.com/incidents/{id}/notes'.format(id=incident_id)
    headers = {
        'Accept': 'application/vnd.pagerduty+json;version=2',
        'Authorization': 'Token token={token}'.format(token=API_KEY),
        'Content-Type': 'application/json',
        'From': EMAIL
    }
    payload = {
        'note': {
            'content': CONTENT
        }
    }

    req = requests.post(url, headers=headers, data=json.dumps(payload))
    print('Status Code: {code}'.format(code=req.status_code))

# Testbed to see if web app is working properly upon start
@app.route('/')
def api_root():
	return "Flask web app is operational and accessible"

#
# When invoking a webhook from a PagerDuty incident, the entire incident object will be
# as part of the webhook and there will be a corresponding event (JSON payload) that
# will be sent to the webhook endpoint.
#
# You will want to evaluate against the event in order to determine what action on the
# incident object (trigger, acknowledge, unacknowledge, resolve, assign, escalate,
# delegate or annotate) when any of the above mentioned actions is performed on the
# incident object.
# 
# The above incident actions are based on PagerDuty webhook v2.
#
@app.route('/credit_card_application', methods=['POST'])
def api_pd_info():
    if request.headers['Content-Type'] == 'application/json':
        # dumps() method converts dictionary object of Python into JSON string data format
        pd_data = json.dumps(request.json)
        data = json.loads(pd_data)
                
        for item in data['messages']:
            # check for when an incident is newly created/triggered
            if item['event'] == 'incident.trigger':
                # make API call on your backend system with PD payload
                print('New triggered incident: ', item['incident']['incident_number'])
                
            # sent when an incident is acknowledged by a user
            if item['event'] == 'incident.acknowledge': 
                # make API call on your backend system with PD payload
                print('Incident ACK on service: ', item['incident']['service']['name'])
                incident_id = item['log_entries'][0]['incident']['id']
                
                # creating a simple scenario where the callback to PagerDuty will simulate
                # an ack-back to PagerDuty and will update the incident's Note section
                create_incident_note(incident_id)
                
            # sent when an incident is unacknowledged due to acknowledgement timeout
            if item['event'] == 'incident.unacknowledge': 
                # make API call on your backend system with PD payload
                print('Incident acknowledgement has timed out and re-triggered.')
            
            # sent when an incident has been resolved
            if item['event'] == 'incident.resolve': 
                # make API call on your backend system with PD payload
                print('Incident status is now: ', item['incident']['status'])
                
            # sent when an incident is assigned to another user
            if item['event'] == 'incident.assign': 
                # make API call on your backend system with PD payload
                print(item['log_entries'][0]['summary'])
                
            # sent when an incident has been escalated to another user in
            # the same escalation chain/policy
            if item['event'] == 'incident.escalate': 
                # make API call on your backend system with PD payload
                print(item['log_entries'][0]['summary'])
                
            # sent when an incident has been reassigned to another escalation policy
            if item['event'] == 'incident.delegate': 
                # make API call on your backend system with PD payload
                print(item['log_entries'][0]['summary'])
                
            # sent when a note is created on an incident
            if item['event'] == 'incident.annotate': 
                # make API call on your backend system with PD payload
                print('Note added to incident: ', item['log_entries'][0]['channel']['summary'])
                                                    
        return data
	
if __name__ == '__main__':
    http_server = WSGIServer(('', PORT), APP)
    http_server.serve_forever()
    
