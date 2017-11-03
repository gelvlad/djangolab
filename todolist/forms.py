from django import forms

class TaskCreateForm(forms.Form):
    name = forms.CharField(max_length=200)
    description = forms.CharField(max_length=1000, required=False)
    completed = forms.BooleanField(required=False)
    due_date = forms.DateField(required=False,
                               widget=forms.DateInput(attrs={'type': 'date'}))
    PRIORITY = (
        ('h', 'High'),
        ('m', 'Medium'),
        ('l', 'Low'),
        ('n', 'None')
    )
    priority = forms.ChoiceField(choices=PRIORITY, initial='n')
    tags = forms.CharField(max_length=500, required=False)


class TaskDetailForm(TaskCreateForm):
    name = forms.CharField(max_length=200, required=False)
