from django.contrib import admin
from .models import Rider

# Register your models here.
@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    pass