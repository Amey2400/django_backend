from django.contrib import admin
from .models import blocks,outputplot,NgspiceCode,Users

# Register your models here.
admin.site.register(blocks)
admin.site.register(outputplot)
admin.site.register(NgspiceCode)
admin.site.register(Users)