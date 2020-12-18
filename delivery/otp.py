from random import randint
import datetime


def generate_random_otp(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    otp = randint(range_start, range_end)

    # check if otp has already been generated for the provided phone number
    # result = Otp.query.filter_by(phone=phone).filter_by(otp=otp).first()
    # if result:
    #     generate_random_otp(n, phone)
    return otp

def is_otp_expired(result):
    added_time = result.date_created
    current_time = datetime.datetime.now(datetime.timezone.utc)
    difference = current_time - added_time
    if difference.seconds > 3600:
        return True
    return False

def get_otp_phone_number(phone):
    phone_length = len(phone)
    if phone_length == 13:
        return phone[1:]
    elif phone_length == 10:
        return '254{}'.format(phone[1:])
    else:
        return phone
