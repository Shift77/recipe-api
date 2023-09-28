'''Django admin customization.'''
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as gl
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    ordering = ['id']
    list_display = ['email', 'name']
    fieldsets = [
        (None, {'fields':('email', 'password')}),
        (gl('Permissions'), {'fields':('is_active', 'is_staff', 'is_superuser')}),
        (gl('Dates'), {'fields':('last_login',)}),

    ]
    add_fieldsets = [
        (None, {
            'fields': ('email', 'password1', 'password2', 'name'),
            'classes': ('wide',)
            }),

        (gl('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser'),
            'classes':('wide',)
            }),
    ]

    readonly_fields = ('last_login',)
