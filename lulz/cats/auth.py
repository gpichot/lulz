from .models import User


def authenticate(username=None, password=None):
    user = User.objects.get(username=username)

    if user.check_password(password):
        return user
