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
    Contact
)
from hr.models import (
    Department, Position, Employee,
)
from products.models import Product, ProductCategory, ProductImage


# ============================================
# PRODUCT MODULE - DASHBOARD VIEWS
# ============================================

@staff_member_required(login_url='login')
def product_list_dashboard(request):
    products = Product.objects.select_related('category').all()
    return render(request, 'dashboard/products/product_list.html', {'products': products})


@staff_member_required(login_url='login')
def product_create(request):
    categories = ProductCategory.objects.filter(is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug') or None
        category_id = request.POST.get('category')
        sku = request.POST.get('sku')
        short_description = request.POST.get('short_description')
        description = request.POST.get('description')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price') or None
        ingredients = request.POST.get('ingredients')
        usage_instructions = request.POST.get('usage_instructions')
        dosage = request.POST.get('dosage')
        warnings = request.POST.get('warnings')
        is_featured = request.POST.get('is_featured') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        in_stock = request.POST.get('in_stock') == 'on'
        meta_title = request.POST.get('meta_title')
        meta_description = request.POST.get('meta_description')
        
        product = Product.objects.create(
            name=name,
            slug=slug,
            category_id=category_id if category_id else None,
            sku=sku,
            short_description=short_description,
            description=description,
            price=price,
            discount_price=discount_price,
            ingredients=ingredients,
            usage_instructions=usage_instructions,
            dosage=dosage,
            warnings=warnings,
            is_featured=is_featured,
            is_active=is_active,
            in_stock=in_stock,
            meta_title=meta_title,
            meta_description=meta_description
        )
        
        if request.FILES.get('featured_image'):
            product.featured_image = request.FILES.get('featured_image')
            product.save()
        
        # Handle gallery images
        gallery_images = request.FILES.getlist('gallery_images')
        for i, img in enumerate(gallery_images):
            ProductImage.objects.create(
                product=product,
                image=img,
                order=i
            )
        
        messages.success(request, 'Product created successfully.')
        return redirect('product_list_dashboard')
    
    return render(request, 'dashboard/products/product_form.html', {
        'categories': categories,
        'action': 'Create'
    })


@staff_member_required(login_url='login')
def product_edit(request, id):
    product = get_object_or_404(Product, id=id)
    categories = ProductCategory.objects.filter(is_active=True)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.slug = request.POST.get('slug') or product.slug
        product.category_id = request.POST.get('category') or None
        product.sku = request.POST.get('sku')
        product.short_description = request.POST.get('short_description')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.discount_price = request.POST.get('discount_price') or None
        product.ingredients = request.POST.get('ingredients')
        product.usage_instructions = request.POST.get('usage_instructions')
        product.dosage = request.POST.get('dosage')
        product.warnings = request.POST.get('warnings')
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.is_active = request.POST.get('is_active') == 'on'
        product.in_stock = request.POST.get('in_stock') == 'on'
        product.meta_title = request.POST.get('meta_title')
        product.meta_description = request.POST.get('meta_description')
        
        if request.FILES.get('featured_image'):
            product.featured_image = request.FILES.get('featured_image')
        
        product.save()
        
        # Handle gallery images
        gallery_images = request.FILES.getlist('gallery_images')
        for i, img in enumerate(gallery_images):
            ProductImage.objects.create(
                product=product,
                image=img,
                order=product.images.count() + i
            )
        
        messages.success(request, 'Product updated successfully.')
        return redirect('product_list_dashboard')
    
    return render(request, 'dashboard/products/product_form.html', {
        'product': product,
        'categories': categories,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully.')
    return redirect('product_list_dashboard')


@staff_member_required(login_url='login')
def product_image_delete(request, id):
    image = get_object_or_404(ProductImage, id=id)
    product_id = image.product.id
    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Image deleted successfully.')
    return redirect('product_edit', id=product_id)


# ============================================
# PRODUCT MODULE - CATEGORY VIEWS
# ============================================

@staff_member_required(login_url='login')
def product_category_list(request):
    categories = ProductCategory.objects.annotate(product_count=Count('products'))
    return render(request, 'dashboard/products/category_list.html', {'categories': categories})


@staff_member_required(login_url='login')
def product_category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug') or None
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        
        category = ProductCategory.objects.create(
            name=name,
            slug=slug,
            description=description,
            is_active=is_active
        )
        
        if request.FILES.get('image'):
            category.image = request.FILES.get('image')
            category.save()
        
        messages.success(request, 'Category created successfully.')
        return redirect('product_category_list')
    
    return render(request, 'dashboard/products/category_form.html', {'action': 'Create'})


@staff_member_required(login_url='login')
def product_category_edit(request, id):
    category = get_object_or_404(ProductCategory, id=id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.slug = request.POST.get('slug') or category.slug
        category.description = request.POST.get('description')
        category.is_active = request.POST.get('is_active') == 'on'
        
        if request.FILES.get('image'):
            category.image = request.FILES.get('image')
        
        category.save()
        messages.success(request, 'Category updated successfully.')
        return redirect('product_category_list')
    
    return render(request, 'dashboard/products/category_form.html', {
        'category': category,
        'action': 'Edit'
    })


@staff_member_required(login_url='login')
def product_category_delete(request, id):
    category = get_object_or_404(ProductCategory, id=id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
    return redirect('product_category_list')

