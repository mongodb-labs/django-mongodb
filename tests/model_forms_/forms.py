from django import forms

from .models import Author


class AuthorForm(forms.ModelForm):
    class Meta:
        fields = "__all__"
        model = Author
