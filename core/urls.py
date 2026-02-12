
from django.urls import path
from . import views

urlpatterns = [
    # Frontend URLs
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('innovations/', views.innovations, name='innovations'),
    path('about-us/', views.about_us, name='about-us'),
    path('impact/', views.impact, name='impact'),
    path('news/', views.news, name='news'),
    path('news-detail/<int:id>/', views.news_detail, name='news-detail'),
    path('contact/', views.contact, name='contact'),
    path('bmi-calculator/', views.bmi_calculator, name='bmi-calculator'),
    
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # User Module - Users
    path('dashboard/users/', views.user_list, name='user_list'),
    path('dashboard/users/create/', views.user_create, name='user_create'),
    path('dashboard/users/<int:id>/edit/', views.user_edit, name='user_edit'),
    path('dashboard/users/<int:id>/delete/', views.user_delete, name='user_delete'),
    
    # User Module - Groups
    path('dashboard/users/groups/', views.group_list, name='group_list'),
    path('dashboard/users/groups/create/', views.group_create, name='group_create'),
    path('dashboard/users/groups/<int:id>/edit/', views.group_edit, name='group_edit'),
    path('dashboard/users/groups/<int:id>/delete/', views.group_delete, name='group_delete'),
    
    # News Module
    path('dashboard/news/', views.news_list_dashboard, name='news_list_dashboard'),
    path('dashboard/news/create/', views.news_create, name='news_create'),
    path('dashboard/news/<int:id>/edit/', views.news_edit, name='news_edit'),
    path('dashboard/news/<int:id>/delete/', views.news_delete, name='news_delete'),
    
    # News Module - Categories
    path('dashboard/news/categories/', views.news_category_list, name='news_category_list'),
    path('dashboard/news/categories/create/', views.news_category_create, name='news_category_create'),
    path('dashboard/news/categories/<int:id>/edit/', views.news_category_edit, name='news_category_edit'),
    path('dashboard/news/categories/<int:id>/delete/', views.news_category_delete, name='news_category_delete'),
    
  
    # Contact Module
    path('dashboard/contacts/', views.contact_list, name='contact_list'),
    path('dashboard/contacts/<int:id>/', views.contact_detail, name='contact_detail'),
    path('dashboard/contacts/<int:id>/mark-responded/', views.contact_mark_responded, name='contact_mark_responded'),
    path('dashboard/contacts/<int:id>/delete/', views.contact_delete, name='contact_delete'),
    
    # Teams Module
    path('dashboard/teams/', views.team_list, name='team_list'),
    path('dashboard/teams/create/', views.team_create, name='team_create'),
    path('dashboard/teams/<int:id>/edit/', views.team_edit, name='team_edit'),
    path('dashboard/teams/<int:id>/delete/', views.team_delete, name='team_delete'),
    
    # Cities Module
    path('dashboard/cities/', views.city_list, name='city_list'),
    path('dashboard/cities/create/', views.city_create, name='city_create'),
    path('dashboard/cities/<int:id>/edit/', views.city_edit, name='city_edit'),
    path('dashboard/cities/<int:id>/delete/', views.city_delete, name='city_delete'),
]