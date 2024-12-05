from datetime import timezone,datetime
from django.dispatch import Signal
from django.conf import settings
from django.dispatch import receiver
from djoser.signals import user_registered
from django.db.models.signals import post_save, pre_save, pre_delete

from accounts.tasks import created_update_email_verification_task
from utils.generator_code import random_with_N_digits
from utils.send_email import send_email

from accounts.models import ProfilePicture, UserAddress, VerificationCode


# email verification
verification_email_signal = Signal()


@receiver(user_registered)
def create_profile(sender, user, request, **kwargs):
    if not user.admin:
        ProfilePicture.objects.get_or_create(user=user)
        UserAddress.objects.get_or_create(user=user)
        code_ins=VerificationCode.objects.create(user=user,label=VerificationCode.SIGNUP,email=user.email)
          # custom signal for sending email to signup verifiy code
        created_update_email_verification_task(code_ins.id,True)

@receiver(pre_save, sender=VerificationCode)
def delete_all_expired_verification_code(sender, instance, **kwargs):
    VerificationCode.objects.filter(created_on__lt=datetime.now(timezone.utc) - settings.VERIFICATION_CODE_LIFETIME,).delete()
    instance.code=random_with_N_digits()

@receiver(verification_email_signal)  # sending email verification code signals
def created_update_EmailVerification(sender, instance, created, request, **kwargs):
    return created_update_email_verification_task.delay(instance, created)

