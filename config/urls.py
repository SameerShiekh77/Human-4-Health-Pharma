
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path


urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('core.urls')),
    path('dashboard/hr/',include('hr.urls')),
    path('dashboard/products/',include('products.urls')),
    path("__reload__/", include("django_browser_reload.urls")),
     
    path('crm/',               include('crm_analytics.urls')),       # /crm/  → dashboard
    path('crm/products/',      include('crm_products.urls')),        # /crm/products/
    path('crm/distributors/',  include('crm_distributors.urls')),    # /crm/distributors/
    path('crm/sales/',         include('crm_sales.urls')),           # /crm/sales/
    path('crm/doctors/',       include('crm_doctors.urls')),         # /crm/doctors/
    path('crm/stores/',        include('crm_stores.urls')),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Media files - works in both development and production
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Force Django to serve media files in production
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]