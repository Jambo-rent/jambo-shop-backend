from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Messages(object):
    EMAIL_VERIFICATION_EMAIL = _(
        f'We sent you this verification code in order to verify if it is you.\n\n This code will expire after {settings.CODE_EXPIRE_MIN} minutes!')
    CODE_NOT_VALID=_(
       "Incorrect token provided"
   )
    EMAIL_NOT_FOUND=_(
        "Email Not Found !"
    )
    INVALID_PASSWORD=_(
        "Invalid password !"
    )
    INVALID_PASSWORD=_(
        "Incorrect password !"
    )