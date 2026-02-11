from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required

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

def news(request):
    return render(request, 'web/news.html')

def news_detail(request, id):
    return render(request, 'web/news_detail.html', {'news_id': id})

def contact(request):
    return render(request, 'web/contact.html')

def bmi_calculator(request):
    return render(request, 'web/bmi_calculator.html')

# Login View
def login_view(request):
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login the user
            login(request, user)
            
            # Set session expiry
            if not remember_me:
                # Session expires when browser closes
                request.session.set_expiry(0)
            else:
                # Session expires in 2 weeks
                request.session.set_expiry(1209600)
            
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            
            # Redirect to next page or home
            next_page = request.GET.get('next', 'home')
            return redirect(next_page)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
            return render(request, 'web/login.html', {'username': username})
    
    return render(request, 'web/login.html')

# Logout View
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

# Register View
def register_view(request):
    # If user is already logged in, redirect to home
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'web/register.html', {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            })
        
        if len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'web/register.html', {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            })
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return render(request, 'web/register.html', {
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            })
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please use a different email or login.')
            return render(request, 'web/register.html', {
                'username': username,
                'first_name': first_name,
                'last_name': last_name
            })
        
        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            messages.success(request, 'Account created successfully! You can now login.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'An error occurred while creating your account. Please try again.')
            return render(request, 'web/register.html', {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name
            })
    
    return render(request, 'web/register.html')