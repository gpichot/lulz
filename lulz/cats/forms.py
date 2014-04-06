import re

from django.utils.translation import ugettext_lazy as _
from django import forms
from django.forms.models import modelform_factory

from django.contrib.auth import authenticate

from taggit.forms import TagField
from taggit.models import Tag


from .models import Post, User, Group


class UserForm(forms.ModelForm):
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(),
    )
    password2 = forms.CharField(
        label=_('Confirm password'),
        widget=forms.PasswordInput(),
    )

    def clean(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password1 != password2:
            raise forms.ValidationError(_("Passwords do not match"))

        return self.cleaned_data 

    def save(self, commit=True):
        user = super(UserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', )
        widgets = {
            'password': forms.PasswordInput(),
        }
        

class AuthenticationForm(forms.Form):
    username = forms.CharField(label=_('Username'))
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(),
    )

    error_messages = {
        'invalid_login': _(
            "Please enter a correct username and password. "
            "Note that both fields may be case-sensitive."
        ),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super(AuthenticationForm, self).__init__(*args, **kwargs)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(username=username,
                                           password=password)
            if self.user_cache is None:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                )

        return self.cleaned_data

    def get_user(self):
        return self.user_cache


class PostForm(forms.ModelForm):

    def clean(self):
        message = self.cleaned_data.get('message')
        tags = self.cleaned_data.get('tags')

        reg = r'#([\w-]+)'
        chans = re.findall(reg, message)
        if len(chans) > 0:
            self.cleaned_data['tags'] = chans + tags
            self.cleaned_data['message'] = re.sub(reg, '', message)

        return super(PostForm, self).clean()

    class Meta:
        model = Post
        fields = ('message', 'url', 'parent', 'tags', )
        widgets = {
            'message': forms.TextInput(attrs={
                'class': 'form-control post-message',
            }),
            'url': forms.HiddenInput(attrs={
                'class': 'post-url',   
            }), 
            'parent': forms.HiddenInput(attrs={
                'class': 'post-parent',
            }),
            'tags': forms.HiddenInput(attrs={
                'class': 'post-tags',
            }),
        }


class AddTagForm(forms.Form):
    chan = TagField()

    def clean(self):
        chan_name = self.cleaned_data.get('chan')[0]
        chan = Tag.objects.get(name=chan_name)
        
        self.chan_cache = chan

    def get_chan(self):
        return self.chan_cache


class AddMemberForm(forms.Form):
    username = forms.CharField()

    def clean(self):
        username = self.cleaned_data.get('username')

        user = User.objects.get(username=username)

        self.user_cache = user

    def get_user(self):
        return self.user_cache

GroupForm = modelform_factory(
    Group,
    fields=('name', 'hidden'),
)
