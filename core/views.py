from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse

from core.models import (
    NewsCategory, News,
    Contact, Teams, Cities
)
from hr.models import (
    Department, Position, Employee,
)

from products.models import Product, ProductCategory, ProductImage

# ============================================
# FRONTEND VIEWS
# ============================================

def home(request):
    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:6]
    latest_news = News.objects.filter(is_published=True)[:3]
    cities = Cities.objects.all()[:10]
    context = {
        'featured_products': featured_products,
        'latest_news': latest_news,
        'cities': cities,
        'cities_length': cities.count(),
    }
    return render(request, 'web/index.html', context)


def products(request):
    products_list = Product.objects.filter(is_active=True)
    categories = ProductCategory.objects.filter(is_active=True)
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        products_list = products_list.filter(category__slug=category_slug)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        products_list = products_list.filter(
            Q(name__icontains=search_query) |
            Q(short_description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(products_list, 12)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)
    
    context = {
        'products': products_page,
        'categories': categories,
        'current_category': category_slug,
        'search_query': search_query,
    }
    return render(request, 'web/products.html', context)


def product_detail(request, id):
    # product = get_object_or_404(Product, id=id, is_active=True)
    # related_products = Product.objects.filter(
    #     category=product.category, 
    #     is_active=True
    # ).exclude(id=product.id)[:4]
    
    # context = {
    #     'product': product,
    #     'related_products': related_products,
    # }
    context = {}
    return render(request, 'web/product_detail.html', context)


def innovations(request):
    return render(request, 'web/innovations.html')


def about_us(request):
    teams = Teams.objects.filter(is_active=True)
    context = {
        'teams': teams,
    }
    return render(request, 'web/about_us.html',context)


def impact(request):
    return render(request, 'web/impact.html')


def news(request):
    news_list = News.objects.filter(is_published=True)
    categories = NewsCategory.objects.filter(is_active=True)
    featured_news = news_list.filter(is_featured=True).first()
    
    # Filter by category
    category_slug = request.GET.get('category')
    if category_slug:
        news_list = news_list.filter(category__slug=category_slug)
    
    # Pagination
    paginator = Paginator(news_list, 9)
    page = request.GET.get('page')
    news_page = paginator.get_page(page)
    
    context = {
        'news_list': news_page,
        'categories': categories,
        'featured_news': featured_news,
        'current_category': category_slug,
    }
    return render(request, 'web/news.html', context)


def news_detail(request, id):
    news_item = get_object_or_404(News, id=id, is_published=True)
    news_item.increment_views()
    
    related_news = News.objects.filter(
        is_published=True,
        category=news_item.category
    ).exclude(id=news_item.id)[:3]
    
    context = {
        'news': news_item,
        'related_news': related_news,
    }
    return render(request, 'web/news_detail.html', context)


def contact(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        name = f"{first_name} {last_name}".strip()
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        Contact.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return redirect('contact')
    
    return render(request, 'web/contact.html')


def bmi_calculator(request):
    return render(request, 'web/bmi_calculator.html')

# Login View
def login_view(request):
    # If user is already logged in, redirect appropriately
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('dashboard')
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
            
            # Redirect staff to dashboard, others to home or next page
            next_page = request.GET.get('next')
            if next_page:
                return redirect(next_page)
            elif user.is_staff:
                return redirect('dashboard')
            return redirect('home')
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


# ============================================
# DASHBOARD VIEWS
# ============================================

@staff_member_required(login_url='login')
def dashboard(request):
    """Dashboard Overview with stats"""
    context = {
        'total_employees': Employee.objects.filter(is_active=True).count(),
        'total_departments': Department.objects.filter(is_active=True).count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_news': News.objects.filter(is_published=True).count(),
        'total_users': User.objects.count(),
        'unread_contacts': Contact.objects.filter(is_read=False).count(),
        'recent_contacts': Contact.objects.order_by('-created_at')[:5],
        'recent_news': News.objects.order_by('-created_at')[:5],
    }
    return render(request, 'dashboard/index.html', context)


# ============================================
# USER MODULE VIEWS
# ============================================

@staff_member_required(login_url='login')
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'dashboard/users/user_list.html', {'users': users})


@staff_member_required(login_url='login')
def user_create(request):
    groups = Group.objects.all()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        selected_groups = request.POST.getlist('groups')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'dashboard/users/user_form.html', {
                'groups': groups,
                'action': 'Create'
            })
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user.is_staff = is_staff
        user.is_active = is_active
        user.save()
        
        if selected_groups:
            user.groups.set(selected_groups)
        
        messages.success(request, 'User created successfully.')
        return redirect('user_list')
    
    return render(request, 'dashboard/users/user_form.html', {
        'groups': groups,
        'action': 'Create'
    })


@staff_member_required(login_url='login')
def user_edit(request, id):
    user_obj = get_object_or_404(User, id=id)
    groups = Group.objects.all()
    
    if request.method == 'POST':
        user_obj.username = request.POST.get('username')
        user_obj.email = request.POST.get('email')
        user_obj.first_name = request.POST.get('first_name')
        user_obj.last_name = request.POST.get('last_name')
        user_obj.is_staff = request.POST.get('is_staff') == 'on'
        user_obj.is_active = request.POST.get('is_active') == 'on'
        
        password = request.POST.get('password')
        if password:
            user_obj.set_password(password)
        
        user_obj.save()
        
        selected_groups = request.POST.getlist('groups')
        user_obj.groups.set(selected_groups)
        
        messages.success(request, 'User updated successfully.')
        return redirect('user_list')
    
    return render(request, 'dashboard/users/user_form.html', {
        'user_obj': user_obj,
        'groups': groups,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def user_delete(request, id):
    user_obj = get_object_or_404(User, id=id)
    if request.method == 'POST':
        if user_obj == request.user:
            messages.error(request, 'You cannot delete your own account.')
        else:
            user_obj.delete()
            messages.success(request, 'User deleted successfully.')
    return redirect('user_list')


# ============================================
# USER MODULE - GROUP VIEWS
# ============================================

@staff_member_required(login_url='login')
def group_list(request):
    groups = Group.objects.annotate(user_count=Count('user'))
    return render(request, 'dashboard/users/group_list.html', {'groups': groups})


@staff_member_required(login_url='login')
def group_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        
        if Group.objects.filter(name=name).exists():
            messages.error(request, 'Group with this name already exists.')
            return render(request, 'dashboard/users/group_form.html', {'action': 'Create'})
        
        Group.objects.create(name=name)
        messages.success(request, 'Group created successfully.')
        return redirect('group_list')
    
    return render(request, 'dashboard/users/group_form.html', {'action': 'Create'})


@staff_member_required(login_url='login')
def group_edit(request, id):
    group = get_object_or_404(Group, id=id)
    
    if request.method == 'POST':
        group.name = request.POST.get('name')
        group.save()
        messages.success(request, 'Group updated successfully.')
        return redirect('group_list')
    
    return render(request, 'dashboard/users/group_form.html', {
        'group': group,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def group_delete(request, id):
    group = get_object_or_404(Group, id=id)
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Group deleted successfully.')
    return redirect('group_list')


# ============================================
# NEWS MODULE - DASHBOARD VIEWS
# ============================================

@staff_member_required(login_url='login')
def news_list_dashboard(request):
    news_list = News.objects.select_related('category', 'author').all()
    return render(request, 'dashboard/news/news_list.html', {'news_list': news_list})


@staff_member_required(login_url='login')
def news_create(request):
    categories = NewsCategory.objects.filter(is_active=True)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        slug = request.POST.get('slug') or None
        category_id = request.POST.get('category')
        excerpt = request.POST.get('excerpt')
        content = request.POST.get('content')
        is_featured = request.POST.get('is_featured') == 'on'
        is_published = request.POST.get('is_published') == 'on'
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        
        news_item = News.objects.create(
            title=title,
            slug=slug,
            category_id=category_id if category_id else None,
            excerpt=excerpt,
            content=content,
            author=request.user,
            is_featured=is_featured,
            is_published=is_published,
            meta_title=meta_title,
            meta_description=meta_description
        )
        
        if request.FILES.get('featured_image'):
            news_item.featured_image = request.FILES.get('featured_image')
        if request.FILES.get('thumbnail'):
            news_item.thumbnail = request.FILES.get('thumbnail')
        news_item.save()
        
        messages.success(request, 'News article created successfully.')
        return redirect('news_list_dashboard')
    
    return render(request, 'dashboard/news/news_form.html', {
        'categories': categories,
        'action': 'Create'
    })


@staff_member_required(login_url='login')
def news_edit(request, id):
    news_item = get_object_or_404(News, id=id)
    categories = NewsCategory.objects.filter(is_active=True)
    
    if request.method == 'POST':
        news_item.title = request.POST.get('title')
        news_item.slug = request.POST.get('slug') or news_item.slug
        news_item.category_id = request.POST.get('category') or None
        news_item.excerpt = request.POST.get('excerpt')
        news_item.content = request.POST.get('content')
        news_item.is_featured = request.POST.get('is_featured') == 'on'
        news_item.is_published = request.POST.get('is_published') == 'on'
        news_item.meta_title = request.POST.get('meta_title')
        news_item.meta_description = request.POST.get('meta_description')
        
        if request.FILES.get('featured_image'):
            news_item.featured_image = request.FILES.get('featured_image')
        if request.FILES.get('thumbnail'):
            news_item.thumbnail = request.FILES.get('thumbnail')
        
        news_item.save()
        messages.success(request, 'News article updated successfully.')
        return redirect('news_list_dashboard')
    
    return render(request, 'dashboard/news/news_form.html', {
        'news_item': news_item,
        'categories': categories,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def news_delete(request, id):
    news_item = get_object_or_404(News, id=id)
    if request.method == 'POST':
        news_item.delete()
        messages.success(request, 'News article deleted successfully.')
    return redirect('news_list_dashboard')


# ============================================
# NEWS MODULE - CATEGORY VIEWS
# ============================================

@staff_member_required(login_url='login')
def news_category_list(request):
    categories = NewsCategory.objects.annotate(news_count=Count('news'))
    return render(request, 'dashboard/news/category_list.html', {'categories': categories})


@staff_member_required(login_url='login')
def news_category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug') or None
        is_active = request.POST.get('is_active') == 'on'
        
        NewsCategory.objects.create(
            name=name,
            slug=slug,
            is_active=is_active
        )
        messages.success(request, 'Category created successfully.')
        return redirect('news_category_list')
    
    return render(request, 'dashboard/news/category_form.html', {'action': 'Create'})


@staff_member_required(login_url='login')
def news_category_edit(request, id):
    category = get_object_or_404(NewsCategory, id=id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.slug = request.POST.get('slug') or category.slug
        category.is_active = request.POST.get('is_active') == 'on'
        category.save()
        messages.success(request, 'Category updated successfully.')
        return redirect('news_category_list')
    
    return render(request, 'dashboard/news/category_form.html', {
        'category': category,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def news_category_delete(request, id):
    category = get_object_or_404(NewsCategory, id=id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
    return redirect('news_category_list')


# ============================================
# CONTACT MODULE - DASHBOARD VIEWS
# ============================================

@staff_member_required(login_url='login')
def contact_list(request):
    contacts = Contact.objects.all()
    
    # Filter by read status
    status = request.GET.get('status')
    if status == 'unread':
        contacts = contacts.filter(is_read=False)
    elif status == 'read':
        contacts = contacts.filter(is_read=True)
    
    return render(request, 'dashboard/contacts/contact_list.html', {
        'contacts': contacts,
        'current_status': status
    })


@staff_member_required(login_url='login')
def contact_detail(request, id):
    contact_item = get_object_or_404(Contact, id=id)
    
    # Mark as read
    if not contact_item.is_read:
        contact_item.is_read = True
        contact_item.save()
    
    if request.method == 'POST':
        contact_item.reply_notes = request.POST.get('reply_notes')
        contact_item.is_replied = request.POST.get('is_replied') == 'on'
        contact_item.save()
        messages.success(request, 'Contact updated successfully.')
        return redirect('contact_list')
    
    return render(request, 'dashboard/contacts/contact_detail.html', {'contact': contact_item})


@staff_member_required(login_url='login')
def contact_mark_responded(request, id):
    contact_item = get_object_or_404(Contact, id=id)
    if request.method == 'POST':
        contact_item.is_responded = True
        contact_item.save()
        messages.success(request, 'Contact marked as responded.')
    return redirect('contact_detail', id=id)


@staff_member_required(login_url='login')
def contact_delete(request, id):
    contact_item = get_object_or_404(Contact, id=id)
    if request.method == 'POST':
        contact_item.delete()
        messages.success(request, 'Contact deleted successfully.')
    return redirect('contact_list')

# ============================================
# TEAM MODULE - DASHBOARD VIEWS
# ============================================


@staff_member_required(login_url='login')
def team_list(request):
    teams = Teams.objects.all()
    return render(request, 'dashboard/teams/team_list.html', {'teams': teams})

@staff_member_required(login_url='login')
def team_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        designation = request.POST.get('designation')
        picture = request.FILES.get('picture')
        is_active = request.POST.get('is_active') == 'on'
        
        Teams.objects.create(
            name=name,
            picture=picture,
            designation=designation if designation else None,
            is_active=is_active
        )
        messages.success(request, 'Team created successfully.')
        return redirect('team_list')
    
    return render(request, 'dashboard/teams/team_form.html', {
        'action': 'Create'
    })
    

@staff_member_required(login_url='login')
def team_edit(request, id):
    team = get_object_or_404(Teams, id=id)
    
    if request.method == 'POST':
        team.name = request.POST.get('name')
        team.designation = request.POST.get('designation') or None
        team.is_active = request.POST.get('is_active') == 'on'
        
        # Update picture if a new one is uploaded
        if request.FILES.get('picture'):
            team.picture = request.FILES.get('picture')
        
        team.save()
        messages.success(request, 'Team updated successfully.')
        return redirect('team_list')
    
    return render(request, 'dashboard/teams/team_form.html', {
        'team': team,
        'action': 'Edit'
    })
    

@staff_member_required(login_url='login')
def team_delete(request, id):
    team = get_object_or_404(Teams, id=id)
    if request.method == 'POST':
        team.delete()
        messages.success(request, 'Team deleted successfully.')
    return redirect('team_list')


# ============================================
# CITIES MODULE - DASHBOARD VIEWS
# ============================================

@staff_member_required(login_url='login')
def city_list(request):
    cities = Cities.objects.all()
    return render(request, 'dashboard/cities/city_list.html', {'cities': cities})


@staff_member_required(login_url='login')
def city_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        
        if Cities.objects.filter(name=name).exists():
            messages.error(request, 'City with this name already exists.')
            return render(request, 'dashboard/cities/city_form.html', {'action': 'Create'})
        
        Cities.objects.create(name=name)
        messages.success(request, 'City created successfully.')
        return redirect('city_list')
    
    return render(request, 'dashboard/cities/city_form.html', {'action': 'Create'})


@staff_member_required(login_url='login')
def city_edit(request, id):
    city = get_object_or_404(Cities, id=id)
    
    if request.method == 'POST':
        city.name = request.POST.get('name')
        city.save()
        messages.success(request, 'City updated successfully.')
        return redirect('city_list')
    
    return render(request, 'dashboard/cities/city_form.html', {
        'city': city,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def city_delete(request, id):
    city = get_object_or_404(Cities, id=id)
    if request.method == 'POST':
        city.delete()
        messages.success(request, 'City deleted successfully.')
    return redirect('city_list')