from django.contrib import admin
from .models import (
    UserProfile, Conference, Category, ConferenceRequest,
    Rating, Attendance, SystemSetting, SyrianCity
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'city', 'is_approved', 'created_at']
    list_filter = ['user_type', 'is_approved', 'city']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'category', 'start_date', 'status', 'city']
    list_filter = ['status', 'category', 'city', 'start_date']
    search_fields = ['title', 'description', 'location']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    search_fields = ['name']

@admin.register(ConferenceRequest)
class ConferenceRequestAdmin(admin.ModelAdmin):
    list_display = ['conference', 'request_type', 'status', 'requested_by', 'created_at']
    list_filter = ['status', 'request_type']
    search_fields = ['conference__title', 'details']

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['conference', 'user', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['conference__title', 'comment']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['conference', 'user', 'attended', 'registered_at']
    list_filter = ['attended']
    search_fields = ['conference__title', 'user__user__username']

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'updated_at', 'updated_by']
    search_fields = ['key', 'description']

@admin.register(SyrianCity)
class SyrianCityAdmin(admin.ModelAdmin):
    list_display = ['name', 'governorate']
    list_filter = ['governorate']
    search_fields = ['name']