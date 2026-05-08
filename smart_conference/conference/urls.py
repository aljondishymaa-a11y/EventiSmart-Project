from django.urls import path
from . import views

urlpatterns = [
    #الصفحة الرئيسية
    path('', views.home, name='home'),

    #لوحة التحكم
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # الملف الشخصي
    path('profile/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
   
    # إدارة المستخدمين
    path('users/', views.manage_users, name='manage_users'),
    
    # المؤتمرات
    path('conferences/', views.conferences_list, name='conferences_list'),
    path('conferences/requests/', views.manage_conference_requests, name='conference_requests'),
    path('conferences/<int:conference_id>/ratings/', views.conference_ratings, name='conference_ratings'),
    
    # التصنيفات
    path('categories/', views.manage_categories, name='manage_categories'),
    
    # الإحصائيات والتقارير
    path('statistics/', views.platform_statistics, name='platform_statistics'),
    path('reports/export/', views.export_reports, name='export_reports'),
    
    # إعدادات النظام
    path('settings/', views.system_settings, name='system_settings'),
]