
from django.urls import path
from . import views
urlpatterns = [
    path('',views.home,name='home'),
    path('products/',views.products,name='products'),
    path('product/<int:id>/',views.product_detail,name='product_detail'),
    path('innovations/', views.innovations, name='innovations'),
    path('about-us/', views.about_us, name='about-us'),
    path('impact/', views.impact, name='impact'),
    path('news/', views.news, name='news'),
    path('news-detail/<int:id>/', views.news_detail, name='news-detail'),
    path('contact/', views.contact, name='contact'),
    path('bmi-calculator/', views.bmi_calculator, name='bmi-calculator'),
    
    # users
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]
