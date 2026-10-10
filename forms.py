from django import forms
from .models import Expense
from .utils import CATEGORIES


class ExpenseForm(forms.ModelForm):
    category = forms.ChoiceField(
        choices=[("Auto", "Auto (predict)")] + [(c, c) for c in CATEGORIES],
        initial="Auto",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Expense
        fields = ["description", "amount", "date", "category", "notes"]
        widgets = {
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Uber to office"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
