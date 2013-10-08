import requests
import simplejson as json
import plivo
import hipchat

from creds import *
from config import *

def send_email(to, subject, body):
    if MAILGUN_KEY and MAILGUN_FROM_EMAIL:
        auth = ("api", MAILGUN_KEY)
        message = {"from": MAILGUN_FROM_EMAIL,
                    "to": to,
                    "subject": subject,
                    "text": body}

        result = requests.post(MAILGUN_URL, auth=auth, data=message)
        return True

def send_sms(to, text):
    client = plivo.RestAPI(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN)
    params = {'src':SMS_SOURCE_NUMBER,
             'text':text,
            }
    for number in to:
        params['dst'] = number
        message = client.send_message(params)
    return True

def send_hipchat(rooms, text, color='green'):
    hipster = hipchat.HipChat(token=HIPCHAT_API_KEY)
    for room in rooms:
        hipster.method('rooms/message', method='POST', parameters={'room_id':room, 'from':'IVR Bot', 'message':text, 'notify':1, 'color':color})
    return True

def incoming_call_details(to_number, from_number, source):
    opencnam = get_opencnam(from_number)

    if not opencnam:
        send_hipchat(VOICEMAIL_HIPCHAT_ROOMS, 'Incoming call on the sales line %s from %s. Source - %s.' % (to_number, from_number, source))
    else:
        send_hipchat(VOICEMAIL_HIPCHAT_ROOMS, 'Incoming call on the sales line %s from %s. Source - %s. OpenCNAM -%s' % (to_number, from_number, source, opencnam))

def get_truecaller(phone_number):
    params = {'userKey':TRUECALLER_API_KEY,
            'phone':phone_number
            }
    response = requests.get(TRUECALLER_URL, params=params)
    data = json.loads(response.content)
    try:
        if data['code'] == 1003:
            return None
    except KeyError:
        return None
    return data['message']

def get_opencnam(phone_number):
    if not OPENCNAM_URL:
        return False
    try:
        url = OPENCNAM_URL+phone_number
        response = requests.get(url, auth=(OPENCNAM_AUTH_ID, OPENCNAM_AUTH_TOKEN))
        if response.content == 'Payment required.':
            response = requests.get(url)
            return response.content
        return response.content
    except Exception as e:
        return False


