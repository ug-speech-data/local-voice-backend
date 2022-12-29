from django import forms
from django.contrib.auth.models import Group

from accounts.models import User


class GroupForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = [
            'name',
        ]


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            'email_address',
            'phone',
            'surname',
            'other_names',
        ]