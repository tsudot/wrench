# The first phone number the call needs to be forwarded to
FIRST_CONTACT = '' # Eg. 15555555555. Make sure you add the country code.

# Needs to be a tuple of numbers the call will be broadcasted
# if it does not get answered by the FIRST_CONTACT
BROADCAST_CONTACTS = [''] # Eg. 15555555555. Make sure you add the country code.

IVR_MESSAGE = "Thank you for calling Plivo. Press 1 to talk to our sales team."
IVR_TIMEOUT = 8

DIAL_MUSIC = "http://s3.amazonaws.com/plivocloud/music.mp3" 
DIAL_TIMEOUT = 15
BROADCAST_DIAL_TIMEOUT = 20

NO_INPUT_MESSAGE = "I'm sorry, I didn't catch that. \
              Press 1 to talk to our sales team."

WRONG_INPUT_MESSAGE = "I'm sorry, that was a wrong input. \
              Press 1 to talk to our sales team."

WRONG_INPUT_GOODBYE = "I'm sorry, that was a wrong input. \
            Please hang up and try again. Thank you, goodbye."

TRANSFER_MESSAGE = "Thank you, your call is now being transferred to our sales team."

GOODBYE_MESSAGE = "Sorry, I didn't catch that. Please hang up and \
                try again. Thank you, goodbye."

TRANSFER_BUSY_MESSAGE = "Thank you for your patience. Our sales team is \
        currently busy assisting other customers. Please stay on the \
        line while we connect your call."

VOICEMAIL_MESSAGE = "Sorry, our sales team is currently unavailable. \
        Please leave your name and message at the tone. \
        We will get back to you within 24 hours."

# Tuple of emails. An email with the voicemail recording
# will be sent to these addresses.
VOICEMAIL_EMAIL_RECEIVERS = ['']
VOICEMAIL_EMAIL_SUBJECT = "Voicemail received on the Sales Line"
VOICEMAIL_EMAIL_BODY = "Hello,\n\nDetails of the voicemail received on %s from %s is - \n Voicemail link - %s \n Voicemail Duration - %ss \n\nThanks, \nPlivo Team"

# Tuple of emails. An email with the call recording
# will be sent to these addresses.
CALL_RECORDING_EMAIL_RECEIVERS = ['']
CALL_RECORDING_EMAIL_SUBJECT = "Details of Plivo Sales Line Call"
CALL_RECORDING_EMAIL_BODY = "Hello,\n\nRecording of the call received on %s from %s - %s \n\nThanks, \nPlivo Team"

# Your Plivo number. This will be used as a caller ID for the SMS.
SMS_SOURCE_NUMBER = ''

# Needs to be a list of numbers. The SMS with the voicemail recording
# will be sent to these numbers.
VOICEMAIL_SMS_RECEIVERS = [''] # Eg. 15555555555. Make sure you add the country code.
VOICEMAIL_SMS_BODY = "Call not answered on the sales line %s from %s - Voicemail: %s"

# Needs to be a tuple of phone numbers. The SMS with the call recording will be sent to
# these numbers
CALL_RECORDING_SMS_RECEIVERS = VOICEMAIL_SMS_RECEIVERS
CALL_RECORDING_SMS_BODY = "Recording of the call received on %s from %s - %s."

# All notifications will be sent the HipChat Room.
VOICEMAIL_HIPCHAT_ROOMS = ['']
VOICEMAIL_HIPCHAT_BODY = "Call not answered by anyone. Received a voicemail on the sales line %s from %s - Voicemail link - <a href='%s'>%s</a> Voicemail Duration - %ss."
CALL_RECORDING_HIPCHAT_ROOMS = VOICEMAIL_HIPCHAT_ROOMS
CALL_RECORDING_HIPCHAT_BODY = "Recording of the call received on %s from %s - <a href='%s'>%s</a>."

LINE_SEPARATOR = '------------------------------------------------------------------------------------------------------------------'

# Mailgun From Email. Will be used as the source of all emails.
MAILGUN_FROM_EMAIL = ""
