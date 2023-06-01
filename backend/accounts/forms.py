from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'required': '',
            'class': 'form-control',
            'type': 'text',
        })
        self.fields['password1'].widget.attrs.update({
            'required': '',
            'class': 'form-control',
            'type': 'password',
        })
        self.fields['password2'].widget.attrs.update({
            'required': '',
            'class': 'form-control',
            'type': 'password',
        })

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']
