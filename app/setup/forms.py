from django import forms

from setup.models import AppConfiguration


class AppConfigurationForm(forms.ModelForm):

    class Meta:
        model = AppConfiguration
        exclude = [
            "id",
        ]