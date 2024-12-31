
from django.conf import settings
from accounts.models import (VerificationCode)
from utils.send_email import send_email,send_email_no_full_name


# @shared_task
def created_update_email_verification_task(id, created):

    instance = VerificationCode.objects.get(id=id)
    if instance.label == VerificationCode.CHANGE_EMAIL:
        send_email(instance.user.get_full_name,instance.code,settings.ACCOUNT_CONSTANTS.messages.EMAIL_VERIFICATION_EMAIL,instance.user.email)
        
    elif instance.label == VerificationCode.RESET_PASSWORD:
        send_email_no_full_name(instance.code,settings.ACCOUNT_CONSTANTS.messages.EMAIL_VERIFICATION_EMAIL,instance.email)
        
     
    elif instance.label ==VerificationCode.SIGNUP:
        send_email(instance.user.get_full_name,instance.code,settings.ACCOUNT_CONSTANTS.messages.EMAIL_VERIFICATION_EMAIL,instance.user.email)