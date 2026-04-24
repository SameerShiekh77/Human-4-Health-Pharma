from django import forms


class DataUploadForm(forms.Form):
    data_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file that matches the sample template.'
    )
