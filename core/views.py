from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'web/index.html')

def products(request):
    return render(request, 'web/products.html')

def product_detail(request, id):
    return render(request, 'web/product_detail.html', {'product_id': id})

def innovations(request):
    return render(request, 'web/innovations.html')

def about_us(request):
    return render(request, 'web/about_us.html')

def impact(request):
    return render(request, 'web/impact.html')


def bmi_calculator(request):
    return render(request, 'web/bmi_calculator.html')