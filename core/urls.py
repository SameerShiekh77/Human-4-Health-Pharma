
from django.urls import path
from . import views
urlpatterns = [
    path('',views.home,name='home'),
    path('products/',views.products,name='products'),
    path('product/<int:id>/',views.product_detail,name='product_detail'),
    path('innovations/', views.innovations, name='innovations'),
    path('about-us/', views.about_us, name='about-us'),
    path('impact/', views.impact, name='impact'),
    path('bmi-calculator/', views.bmi_calculator, name='bmi-calculator'),
]
