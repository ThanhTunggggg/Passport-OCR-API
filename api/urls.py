from django.contrib import admin
#from django.urls import path
from django.conf.urls import url, include
import ocr
from ocr import views

urlpatterns = [
    url('api/ocr/', views.requested_url),
    url('admin/', admin.site.urls)
]
