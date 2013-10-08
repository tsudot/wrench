import os

from flask import Flask, Response, request, url_for
import redis
from rq import Queue
from worker import conn
import plivoxml as plivo

from config import *
from utils import send_email, send_sms, send_hipchat, incoming_call_details

app = Flask(__name__)
app.debug = False

q = Queue(connection=conn)

@app.route('/response/forward/', methods=['GET'])
def forward():
    args = request.args

    from_number = args.get('From', '')
    to_number = args.get('To', '')
    call_status = args.get('CallStatus', '')
    call_uuid = args.get('CallUUID', '')
    source = args.get('source', '')

    rd = get_redis_connection()
    rd.set(to_number, source)

    response = plivo.Response()

    getdigits_action_url = url_for('get_digits', _external=True)
    getDigits = plivo.GetDigits(action=getdigits_action_url, method='GET',
                                        timeout=IVR_TIMEOUT, numDigits=1, retries=1)
    getDigits.addSpeak(IVR_MESSAGE)
    response.add(getDigits)

    getDigits = plivo.GetDigits(action=getdigits_action_url, method='GET',
                                        timeout=IVR_TIMEOUT, numDigits=1, retries=1)
    getDigits.addSpeak(NO_INPUT_MESSAGE)
    response.add(getDigits)

    response.addSpeak(GOODBYE_MESSAGE)

    if call_status == "ringing":
        q.enqueue(send_hipchat, VOICEMAIL_HIPCHAT_ROOMS, LINE_SEPARATOR, color='gray')
        q.enqueue(incoming_call_details, to_number, from_number, source)

    elif call_status == "completed":
        email_body = rd.get('call_recording_email_body'+call_uuid)
        sms_body = rd.get('call_recording_sms_body'+call_uuid)
        hipchat_body = rd.get('call_recording_hipchat_body'+call_uuid)

        rd.delete('call_recording_email_body'+call_uuid)
        rd.delete('call_recording_sms_body'+call_uuid)
        rd.delete('call_recording_hipchat_body'+call_uuid)

        if email_body:
            q.enqueue(send_email, CALL_RECORDING_EMAIL_RECEIVERS, CALL_RECORDING_EMAIL_SUBJECT, email_body)
            q.enqueue(send_sms, CALL_RECORDING_SMS_RECEIVERS, sms_body)
            q.enqueue(send_hipchat, CALL_RECORDING_HIPCHAT_ROOMS, hipchat_body, color='gray')
        q.enqueue(send_hipchat, VOICEMAIL_HIPCHAT_ROOMS, LINE_SEPARATOR, color='gray')

    return Response(str(response), mimetype='text/xml')


@app.route('/response/getdigits/', methods=['GET'])
def get_digits():
    args = request.args

    digits = args.get('Digits', None)
    from_number = args.get('From', None)
    to_number = args.get('To', None)
    wrong_input = args.get('wrong_input', False)

    response = plivo.Response()

    confirm_key = '1'
    timeout = DIAL_TIMEOUT

    callback_url = url_for('dial_callback', _external=True)
    dial_action_url = url_for('dial_action', _external=True)
    record_dial_action_url = url_for('record_dial_action', _external=True)
    dial_music_url = url_for('dial_music', _external=True)
    confirm_sound_url = url_for('confirm_sound_speak', _external=True)

    rd = get_redis_connection()
    on_call = rd.get('on_call_%s' % FIRST_CONTACT)

    # Sales
    if digits == '1':
        if on_call:
            contact = BROADCAST_CONTACTS[0]
        else:
            contact = FIRST_CONTACT

        record = response.addRecord(action=record_dial_action_url, startOnDialAnswer="true", redirect="false", maxLength="3600")
        dial = response.addDial(action=dial_action_url, method='GET', dialMusic=dial_music_url, callerName=to_number, callerId=to_number, timeout=timeout, confirmKey=confirm_key, confirmSound=confirm_sound_url, callbackUrl=callback_url, callbackMethod='GET')
        dial = add_endpoint_to_dial(dial, contact)

        hipchat_body = 'Forwarding sales call to %s.' % contact
        q.enqueue(send_hipchat, VOICEMAIL_HIPCHAT_ROOMS, hipchat_body, color='purple')
    elif not wrong_input:
        action_url = url_for('get_digits', _external=True)
        action_url = action_url + '?wrong_input=True&'
        getDigits = plivo.GetDigits(action=action_url, method='GET',
                                            timeout=5, numDigits=1, retries=1)
        getDigits.addSpeak(WRONG_INPUT_MESSAGE)
        response.add(getDigits)

        response.addSpeak(GOODBYE_MESSAGE)
    elif wrong_input:
        response.addSpeak(WRONG_INPUT_GOODBYE)
    else:
        response.addSpeak(GOODBYE_MESSAGE)

    return Response(str(response), mimetype='text/xml')


@app.route('/dial/music/', methods=['POST', 'GET'])
def dial_music():
    response = plivo.Response()
    response.addSpeak(TRANSFER_MESSAGE)
    response.addPlay(DIAL_MUSIC)

    return Response(str(response), mimetype='text/xml')


@app.route('/dial/music/broadcast/', methods=['POST', 'GET'])
def dial_music_broadcast():
    response = plivo.Response()
    response.addSpeak(TRANSFER_BUSY_MESSAGE)
    response.addPlay(DIAL_MUSIC)

    return Response(str(response), mimetype='text/xml')


@app.route('/dial/confirmSound/', methods=['POST', 'GET'])
def confirm_sound_speak():
    response = plivo.Response()
    response.addSpeak('Press 1 to answer this call')

    return Response(str(response), mimetype='text/xml')


@app.route('/dial/action/', methods=['GET'])
def dial_action():
    get_args = request.args

    dial_status = get_args.get('DialStatus', None)
    from_number = get_args.get('From', '')
    to_number = get_args.get('To', '')
    call_uuid = get_args.get('CallUUID', '')
    is_broadcast = get_args.get('is_broadcast', False)

    response = plivo.Response()

    timeout = BROADCAST_DIAL_TIMEOUT
    confirm_key = '1'
    dial_action_url = url_for('dial_action', _external=True)
    callback_url = url_for('dial_callback', _external=True)
    record_action_url = url_for('record_action', _external=True)
    transcription_url = url_for('transcription', _external=True)
    record_dial_action_url = url_for('record_dial_action', _external=True)
    dial_music_url = url_for('dial_music_broadcast', _external=True)
    confirm_sound_url = url_for('confirm_sound_speak', _external=True)

    if dial_status == 'no-answer' and not is_broadcast:
        # Broadcast call to the entire team and adding is_broadcast parameter to the action url
        dial_action_url = dial_action_url + '?is_broadcast=True&'

        record = response.addRecord(action=record_dial_action_url, startOnDialAnswer="true", redirect="false", maxLength="3600")
        broadcast = response.addDial(action=dial_action_url, method='GET', dialMusic=dial_music_url, callerName=to_number, callerId=to_number, timeout=timeout,  confirmKey=confirm_key, confirmSound=confirm_sound_url, callbackUrl=callback_url, callbackMethod='GET')
        for number in BROADCAST_CONTACTS:
            broadcast = add_endpoint_to_dial(broadcast, number)

        calling_contacts = ', '.join(BROADCAST_CONTACTS)

        hipchat_body = 'Call not answered by %s, broadcasting to %s.' % (FIRST_CONTACT, calling_contacts)

        q.enqueue(send_hipchat, VOICEMAIL_HIPCHAT_ROOMS, hipchat_body, color='yellow')

    elif dial_status == 'no-answer' and is_broadcast:
        # Call not answered after the broadcast, going to VM
        response.addSpeak(VOICEMAIL_MESSAGE)

        response.addRecord(action=record_action_url, method='POST', maxLength='30', 
                transcriptionType='hybrid', transcriptionUrl=transcription_url, transcriptionMethod='GET')

        hipchat_body = 'Call not answered by the sales team, forwarding to voicemail.'
        q.enqueue(send_hipchat, VOICEMAIL_HIPCHAT_ROOMS, hipchat_body, color='red')

        # Need to suppress recording notification if voicemail is present
        rd = get_redis_connection()
        rd.set('voice_mail_%s' % call_uuid, True)

    elif dial_status == 'completed':
        rd = get_redis_connection()
        rd.delete('on_call_%s' % (to_number))

    return Response(str(response), mimetype='text/xml')


@app.route('/dial/callback/', methods=['GET'])
def dial_callback():
    get_args = request.args

    dial_action = get_args.get('DialAction', '')
    dial_bleg_to = get_args.get('DialBLegTo', '')
    dial_bleg_from = get_args.get('DialBLegFrom', '')
    dial_hangup = get_args.get('DialBLegHangupCause', '')

    if dial_action == "answer":
        rd = get_redis_connection()
        rd.set('on_call_%s' % (dial_bleg_to), True)
        hipchat_body = 'Sales call answered by %s' % dial_bleg_to
        q.enqueue(send_hipchat, VOICEMAIL_HIPCHAT_ROOMS, hipchat_body, color='green')
    
    response = plivo.Response()
    return Response(str(response), mimetype='text/xml')


@app.route('/record/action/', methods=['POST'])
def record_action():
    post_args = request.form
    print post_args

    # Fetch record url
    record_url = post_args.get('RecordUrl', '')
    record_duration = post_args.get('RecordingDuration', '')
    record_ms = post_args.get('RecordingStartMs', '')
    from_number = post_args.get('From', '')
    to_number = post_args.get('To', '')

    if record_duration == "-1":
        response = plivo.Response()
        return Response(str(response), mimetype='text/xml')

    recording_id = record_url.split('/')[-1].split('.mp3')[0]

    rd = get_redis_connection()

    email_body = VOICEMAIL_EMAIL_BODY % (to_number, from_number, record_url, record_duration)
    sms_body = VOICEMAIL_SMS_BODY % (to_number, from_number, record_url)
    hipchat_body = VOICEMAIL_HIPCHAT_BODY % (to_number, from_number, record_url, record_url, record_duration)


    rd.set(recording_id+'email_body', email_body)
    rd.set(recording_id+'sms_body', sms_body)
    rd.set(recording_id+'hipchat_body', hipchat_body)

    response = plivo.Response()
    return Response(str(response), mimetype='text/xml')


@app.route('/record/dial/action/', methods=['POST',])
def record_dial_action():
    post_args = request.form
    print post_args

    # Fetch record url
    record_url = post_args.get('RecordUrl', '')
    record_duration = post_args.get('RecordingDuration', '')
    from_number = post_args.get('From', '')
    to_number = post_args.get('To', '')
    call_uuid = post_args.get('CallUUID', '')

    email_body = CALL_RECORDING_EMAIL_BODY % (to_number, from_number, record_url)
    sms_body = CALL_RECORDING_SMS_BODY % (to_number, from_number, record_url)
    hipchat_body = CALL_RECORDING_HIPCHAT_BODY % (to_number, from_number, record_url, record_url)

    rd = get_redis_connection()

    voice_mail = rd.get('voice_mail_%s' % call_uuid)
    if voice_mail:
        response = plivo.Response()
        return Response(str(response), mimetype='text/xml')

    rd.set('call_recording_email_body'+call_uuid, email_body)
    rd.set('call_recording_sms_body'+call_uuid, sms_body)
    rd.set('call_recording_hipchat_body'+call_uuid, hipchat_body)

    response = plivo.Response()
    return Response(str(response), mimetype='text/xml')


def add_endpoint_to_dial(dial, endpoint):
    """
    Adds a SIP endpoint or a PSTN number based on the
    format of the endpoint to the Dial XML element
    """

    if endpoint.startswith('sip:') or '@' in endpoint:
        dial.addUser(endpoint)
    elif endpoint.isdigit():
        dial.addNumber(endpoint)
    return dial


@app.route('/transcription/action/', methods=['GET',])
def transcription():
    get_args = request.args
    print get_args

    transcription = get_args.get('transcription', '')
    recording_id = get_args.get('recording_id', '')

    rd = get_redis_connection()

    email_body = rd.get(recording_id+'email_body')
    sms_body = rd.get(recording_id+'sms_body')
    hipchat_body = rd.get(recording_id+'hipchat_body')

    rd.delete(recording_id+'email_body')
    rd.delete(recording_id+'sms_body')
    rd.delete(recording_id+'hipchat_body')

    recording_transcribed = 'Recording transcribed - %s' % transcription
    email_body = email_body + recording_transcribed
    sms_body = sms_body + recording_transcribed
    hipchat_body = hipchat_body + recording_transcribed

    q.enqueue(send_email, VOICEMAIL_EMAIL_RECEIVERS, VOICEMAIL_EMAIL_SUBJECT, email_body)
    q.enqueue(send_sms, VOICEMAIL_SMS_RECEIVERS, sms_body)
    q.enqueue(send_hipchat, VOICEMAIL_HIPCHAT_ROOMS, hipchat_body, color='gray')

    response = plivo.Response()
    return Response(str(response), mimetype='text/xml')

def get_redis_connection():
    redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
    rd = redis.from_url(redis_url)
    return rd

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
