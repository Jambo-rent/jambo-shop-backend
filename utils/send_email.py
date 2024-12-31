from django.conf import settings
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives


User = get_user_model()



def send_email(full_name,code,body,rec):
    context = {
            "name": full_name,
            "verify_code": code,
            "message":body,
        }
    html_content = render_to_string("welcome_email.html", context)
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(
        "Reset Account verification code",
        text_content,
        settings.EMAIL_HOST_USER,
        [rec],
    )
    email.attach_alternative(html_content, "text/html")
    return email.send()
    
        

def send_email_no_full_name(code,body,rec):
    context = {
           
            "verify_code": code,
            "message":body,
        }
    html_content = render_to_string("welcome_email.html", context)
    text_content = strip_tags(html_content)
    email = EmailMultiAlternatives(
        "Reset Account verification code",
        text_content,
        settings.EMAIL_HOST_USER,
        [rec],
    )
    email.attach_alternative(html_content, "text/html")
    return email.send()
    