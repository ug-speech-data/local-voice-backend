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
            'password',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = self.Meta.model(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user