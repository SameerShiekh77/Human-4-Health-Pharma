from django import forms
from .models import Division, ProductMaster, BatchManagement, CompanyStock


class DivisionForm(forms.ModelForm):
    class Meta:
        model  = Division
        fields = ['name', 'manager_name', 'is_active']
        widgets = {
            'name':         forms.TextInput(attrs={'placeholder': 'e.g., Cardiology Division'}),
            'manager_name': forms.TextInput(attrs={'placeholder': 'Division Manager Name'}),
        }


class ProductMasterForm(forms.ModelForm):
    class Meta:
        model  = ProductMaster
        fields = [
            'product_name', 'generic_name', 'brand_name', 'category', 'division',
            'strength', 'packing_size', 'manufacturing_cost_per_unit',
            'trade_price', 'retail_price', 'distributor_price',
            'status', 'description', 'image',
        ]
        widgets = {
            'product_name':               forms.TextInput(attrs={'placeholder': 'e.g., Amoxicillin 500mg'}),
            'generic_name':               forms.TextInput(attrs={'placeholder': 'e.g., Amoxicillin'}),
            'brand_name':                 forms.TextInput(attrs={'placeholder': 'e.g., Augmentin'}),
            'strength':                   forms.TextInput(attrs={'placeholder': 'e.g., 500mg'}),
            'packing_size':               forms.TextInput(attrs={'placeholder': 'e.g., 10x10'}),
            'manufacturing_cost_per_unit':forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
            'trade_price':                forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
            'retail_price':               forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
            'distributor_price':          forms.NumberInput(attrs={'placeholder': '0.00', 'step': '0.01'}),
            'description':                forms.Textarea(attrs={'rows': 3}),
        }


class BatchManagementForm(forms.ModelForm):
    class Meta:
        model  = BatchManagement
        fields = [
            'batch_number', 'product', 'manufacturing_date', 'expiry_date',
            'quantity_manufactured', 'quantity_sent_to_distributors', 'notes',
        ]
        widgets = {
            'batch_number':               forms.TextInput(attrs={'placeholder': 'e.g., BT-2024-001'}),
            'manufacturing_date':         forms.DateInput(attrs={'type': 'date'}),
            'expiry_date':                forms.DateInput(attrs={'type': 'date'}),
            'quantity_manufactured':      forms.NumberInput(attrs={'placeholder': '0'}),
            'quantity_sent_to_distributors': forms.NumberInput(attrs={'placeholder': '0'}),
            'notes':                      forms.Textarea(attrs={'rows': 2}),
        }


class CompanyStockForm(forms.ModelForm):
    class Meta:
        model  = CompanyStock
        fields = ['product', 'batch', 'warehouse_location', 'low_stock_threshold']
        widgets = {
            'low_stock_threshold': forms.NumberInput(attrs={'placeholder': '100'}),
        }