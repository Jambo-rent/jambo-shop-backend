from django.utils.translation import gettext_lazy as _
from django.conf import settings

class Messages(object):
    EMAIL_VERIFICATION_EMAIL = _(
        f'We sent you this verification code in order to verify if it is you.\n\n This code will expire after {settings.CODE_EXPIRE_MIN} minutes!')
   