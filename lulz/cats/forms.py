from django.utils.translation import ugettext_lazy as _
from django import forms
from django.forms.models import modelform_factory

from django.contrib.auth.models import Group

from taggit.forms import TagField

from .models import Post


class PostForm(forms.ModelForm):

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


GroupForm = modelform_factory(
    Group,
    fields=('name', ),
)
