from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from django.http import HttpResponse
import pandas as pd
import json
from django.db.models.functions import ExtractMonth
from datetime import datetime, timedelta
from io import BytesIO
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from .models import (
    UserProfile, Conference, Category, ConferenceRequest, 
    Rating, Attendance, SystemSetting, SyrianCity
)

def home(request):
    """الصفحة الرئيسية"""
    conferences = Conference.objects.filter(
        Q(status='approved') | Q(status='active'),
        start_date__gte=timezone.now()
    ).order_by('start_date')[:6]
    
    context = {
        'conferences': conferences,
    }
    return render(request, 'conference/list.html', context)

def login_view(request):
    """تسجيل الدخول"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # التحقق من صلاحية الحساب
            try:
                profile = user.userprofile
                if not profile.is_approved and profile.user_type != 'admin':
                    messages.warning(request, 'حسابك قيد المراجعة من قبل المدير')
            except UserProfile.DoesNotExist:
                # إنشاء ملف تعريف إذا لم يكن موجوداً
                UserProfile.objects.create(user=user)
            
            return redirect('dashboard')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    """تسجيل الخروج"""
    logout(request)
    return redirect('login')

@login_required
def admin_dashboard(request):
    """لوحة تحكم المدير"""
    # التحقق من صلاحيات المدير
    try:
        profile = request.user.userprofile
        if profile.user_type != 'admin':
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'يرجى تحديث الملف الشخصي')
        return redirect('home')
    
    # الإحصائيات
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total_users': UserProfile.objects.count(),
        'new_users_week': UserProfile.objects.filter(created_at__date__gte=week_ago).count(),
        'total_conferences': Conference.objects.count(),
        'pending_conferences': Conference.objects.filter(status='pending').count(),
        'active_conferences': Conference.objects.filter(status='active').count(),
        'total_ratings': Rating.objects.count(),
        'pending_requests': ConferenceRequest.objects.filter(status='pending').count(),
    }
    
    # آخر المؤتمرات
    recent_conferences = Conference.objects.all().order_by('-created_at')[:10]
    
    # آخر المستخدمين
    recent_users = UserProfile.objects.all().order_by('-created_at')[:10]
    
    context = {
        'stats': stats,
        'recent_conferences': recent_conferences,
        'recent_users': recent_users,
    }
    
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
def user_profile(request):
    """عرض الملف الشخصي"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        # إنشاء ملف تعريف إذا لم يكن موجوداً
        profile = UserProfile.objects.create(user=request.user)
    
    context = {
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    """تعديل البيانات الشخصية"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        # تحديث بيانات المستخدم
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # تحديث ملف التعريف
        profile.phone = request.POST.get('phone', profile.phone)
        profile.address = request.POST.get('address', profile.address)
        profile.bio = request.POST.get('bio', profile.bio)
        
        if 'city' in request.POST and request.POST['city']:
            try:
                profile.city = SyrianCity.objects.get(id=request.POST['city'])
            except SyrianCity.DoesNotExist:
                pass
        
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        
        profile.save()
        
        messages.success(request, 'تم تحديث البيانات الشخصية بنجاح')
        return redirect('user_profile')
    
    cities = SyrianCity.objects.all()
    
    context = {
        'profile': profile,
        'cities': cities,
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required
def change_password(request):
    """تغيير كلمة المرور"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # تحديث الجلسة
            messages.success(request, 'تم تغيير كلمة المرور بنجاح')
            return redirect('user_profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/change_password.html', context)

@login_required
def manage_users(request):
    """إدارة المستخدمين"""
    # التحقق من صلاحيات المدير
    try:
        if request.user.userprofile.user_type != 'admin':
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'يرجى تحديث الملف الشخصي')
        return redirect('home')
    
    users = UserProfile.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        if user_id and action:
            user_profile = get_object_or_404(UserProfile, id=user_id)
            
            if action == 'approve':
                user_profile.is_approved = True
                user_profile.save()
                messages.success(request, f'تم تفعيل حساب {user_profile.user.get_full_name()}')
            elif action == 'reject':
                user_profile.is_approved = False
                user_profile.save()
                messages.warning(request, f'تم تعطيل حساب {user_profile.user.get_full_name()}')
            elif action == 'delete':
                user_profile.user.delete()
                messages.success(request, f'تم حذف المستخدم بنجاح')
    
    context = {
        'users': users,
    }
    return render(request, 'accounts/users_list.html', context)

@login_required
def conferences_list(request):
    """قائمة المؤتمرات"""
    conferences = Conference.objects.all().order_by('-created_at')
    
    context = {
        'conferences': conferences,
    }
    return render(request, 'conference/conferences_list.html', context)

@login_required
def manage_conference_requests(request):
    """إدارة طلبات المؤتمرات"""
    # التحقق من صلاحيات المدير
    try:
        if request.user.userprofile.user_type != 'admin':
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'يرجى تحديث الملف الشخصي')
        return redirect('home')
    
    requests = ConferenceRequest.objects.filter(status='pending').order_by('-created_at')
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        
        if request_id and action:
            conf_request = get_object_or_404(ConferenceRequest, id=request_id)
            
            if action == 'approve':
                conf_request.status = 'approved'
                conf_request.reviewed_by = request.user
                conf_request.reviewed_at = timezone.now()
                conf_request.save()
                
                # تحديث حالة المؤتمر
                conf_request.conference.status = 'approved'
                conf_request.conference.save()
                
                messages.success(request, 'تم الموافقة على الطلب')
            elif action == 'reject':
                conf_request.status = 'rejected'
                conf_request.reviewed_by = request.user
                conf_request.reviewed_at = timezone.now()
                conf_request.save()
                
                # تحديث حالة المؤتمر
                conf_request.conference.status = 'rejected'
                conf_request.conference.save()
                
                messages.warning(request, 'تم رفض الطلب')
    
    context = {
        'pending_requests': requests,
    }
    return render(request, 'conference/requests.html', context)

@login_required
def conference_ratings(request, conference_id):
    """عرض تقييمات مؤتمر"""
    conference = get_object_or_404(Conference, id=conference_id)
    ratings = Rating.objects.filter(conference=conference).order_by('-created_at')
    
    # متوسط التقييم
    avg_rating = ratings.aggregate(avg=Avg('rating'))['avg'] or 0
    
    context = {
        'conference': conference,
        'ratings': ratings,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'conference/ratings.html', context)

@login_required
def manage_categories(request):
    """إدارة التصنيفات (إضافة، تعديل، حذف)"""
    # التحقق من صلاحيات المدير
    try:
        if request.user.userprofile.user_type != 'admin':
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'يرجى تحديث الملف الشخصي')
        return redirect('home')
    
    categories = Category.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            description = request.POST.get('description')
            if name:
                Category.objects.create(
                    name=name,
                    description=description,
                    created_by=request.user
                )
                messages.success(request, 'تم إضافة التصنيف بنجاح')
        
        elif action == 'edit':
            category_id = request.POST.get('category_id')
            name = request.POST.get('name')
            description = request.POST.get('description')
            if category_id and name:
                category = get_object_or_404(Category, id=category_id)
                category.name = name
                category.description = description
                category.save()
                messages.success(request, 'تم تحديث التصنيف بنجاح')
                
        elif action == 'delete':
            category_id = request.POST.get('category_id')
            if category_id:
                category = get_object_or_404(Category, id=category_id)
                category.delete()
                messages.success(request, 'تم حذف التصنيف بنجاح')
        
        return redirect('manage_categories')
    
    context = {
        'categories': categories,
    }
    return render(request, 'categories/list.html', context)

@login_required
def platform_statistics(request):
    """إحصائيات شاملة عن عمل المنصة"""
    # التحقق من صلاحيات المدير
    try:
        if request.user.userprofile.user_type != 'admin':
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'يرجى تحديث الملف الشخصي')
        return redirect('home')
    
    # الإحصائيات العامة
    total_stats = {
        'total_users': UserProfile.objects.count(),
        'total_conferences': Conference.objects.count(),
        'total_ratings': Rating.objects.count(),
        'total_attendances': Attendance.objects.count(),
    }
    
    # إحصائيات المستخدمين (للجدول)
    user_stats_query = UserProfile.objects.values('user_type').annotate(
        count=Count('id'),
        approved=Count('id', filter=Q(is_approved=True))
    )
    
    # تجهيز بيانات المستخدمين للرسم البياني (JSON)
    user_data_list = [{'user_type': s['user_type'], 'count': s['count']} for s in user_stats_query]
    
    # إحصائيات المؤتمرات
    conference_stats = Conference.objects.values('status').annotate(
        count=Count('id')
    )
    
    # المؤتمرات حسب الشهر (JSON) للسنة الحالية
    monthly_query = Conference.objects.filter(
        created_at__year=timezone.now().year
    ).annotate(month=ExtractMonth('created_at')).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    monthly_data_list = [{'month': m['month'], 'count': m['count']} for m in monthly_query]
    
    # إحصاءات الحضور
    attendance_stats = {
        'total_registered': Attendance.objects.count(),
        'total_attended': Attendance.objects.filter(attended=True).count(),
        'attendance_rate': 0
    }
    
    if attendance_stats['total_registered'] > 0:
        attendance_stats['attendance_rate'] = round(
            (attendance_stats['total_attended'] / attendance_stats['total_registered']) * 100, 1
        )
    
    context = {
        'total_stats': total_stats,
        'user_stats': user_stats_query,
        'conference_stats': conference_stats,
        'attendance_stats': attendance_stats,
        # هذه المتغيرات ضرورية جداً لعمل الرسم البياني في القالب
        'monthly_data_json': json.dumps(monthly_data_list),
        'user_data_json': json.dumps(user_data_list),
    }
    return render(request, 'dashboard/stats.html', context)

# ====== دوال التصدير ======

def get_user_type_arabic(user_type):
    """تحويل نوع المستخدم إلى عربي"""
    user_type_map = {
        'admin': 'مدير النظام',
        'organizer': 'منظم المؤتمر',
        'speaker': 'متحدث',
        'attendee': 'مشارك',
    }
    return user_type_map.get(user_type, user_type)

def get_status_arabic(status):
    """تحويل حالة المؤتمر إلى عربي"""
    status_map = {
        'pending': 'قيد الانتظار',
        'approved': 'مقبول',
        'rejected': 'مرفوض',
        'active': 'نشط',
        'completed': 'منتهي',
        'cancelled': 'ملغي',
    }
    return status_map.get(status, status)

def export_users_report_data():
    """جلب بيانات تقرير المستخدمين"""
    users_data = []
    for profile in UserProfile.objects.select_related('user', 'city').all():
        users_data.append({
            'اسم المستخدم': profile.user.username,
            'الاسم الأول': profile.user.first_name or '',
            'الاسم الأخير': profile.user.last_name or '',
            'الاسم الكامل': f"{profile.user.first_name or ''} {profile.user.last_name or ''}".strip(),
            'البريد الإلكتروني': profile.user.email or '',
            'نوع المستخدم': get_user_type_arabic(profile.user_type),
            'رقم الهاتف': profile.phone or '',
            'المدينة': profile.city.name if profile.city else '',
            'المحافظة': profile.city.governorate if profile.city else '',
            'مفعل': 'نعم' if profile.is_approved else 'لا',
            'تاريخ التسجيل': profile.created_at.replace(tzinfo=None) if profile.created_at else '',
        })
    
    return pd.DataFrame(users_data)

def export_conferences_report_data():
    """جلب بيانات تقرير المؤتمرات"""
    conferences_data = []
    for conference in Conference.objects.select_related('organizer__user', 'category', 'city').all():
        conferences_data.append({
            'عنوان المؤتمر': conference.title,
            'وصف المؤتمر': conference.description[:100] + '...' if conference.description else '',
            'اسم المنظم': conference.organizer.user.username if conference.organizer else '',
            'الاسم الكامل للمنظم': f"{conference.organizer.user.first_name or ''} {conference.organizer.user.last_name or ''}".strip(),
            'التصنيف': conference.category.name if conference.category else '',
            'تاريخ البدء': conference.start_date.replace(tzinfo=None) if conference.start_date else '',
            'تاريخ الانتهاء': conference.end_date.replace(tzinfo=None) if conference.end_date else '',
            'المكان': conference.location,
            'المدينة': conference.city.name if conference.city else '',
            'الحالة': get_status_arabic(conference.status),
            'الحد الأقصى': conference.max_attendees,
            'عدد المشاركين الحالي': conference.current_attendees,
            'مميز': 'نعم' if conference.is_featured else 'لا',
            'تاريخ الإنشاء': conference.created_at.replace(tzinfo=None) if conference.created_at else '',
        })
    
    return pd.DataFrame(conferences_data)

def export_ratings_report_data():
    """جلب بيانات تقرير التقييمات"""
    ratings_data = []
    for rating in Rating.objects.select_related('conference', 'user__user').all():
        ratings_data.append({
            'عنوان المؤتمر': rating.conference.title,
            'اسم المستخدم': rating.user.user.username,
            'الاسم الكامل': f"{rating.user.user.first_name or ''} {rating.user.user.last_name or ''}".strip(),
            'التقييم': rating.rating,
            'النجوم': '★' * rating.rating + '☆' * (5 - rating.rating),
            'التعليق': rating.comment or '',
            'تاريخ التقييم': rating.created_at.replace(tzinfo=None) if rating.created_at else '',
        })
    
    return pd.DataFrame(ratings_data)

def export_to_excel(df, filename):
    """تصدير DataFrame إلى Excel"""
    output = BytesIO()
    
    # استخدام ExcelWriter مع openpyxl
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='تقرير')
        
        # تحسين عرض الأعمدة
        worksheet = writer.sheets['تقرير']
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
            col_idx = df.columns.get_loc(column)
            worksheet.column_dimensions[chr(65 + col_idx)].width = min(column_width, 50)
    
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    
    return response

def export_to_csv(df, filename):
    """تصدير DataFrame إلى CSV"""
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    df.to_csv(response, index=False, encoding='utf-8-sig')
    
    return response

@login_required
def export_reports(request):
    """تصدير التقارير"""
    # التحقق من صلاحيات المدير
    try:
        if request.user.userprofile.user_type != 'admin':
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'يرجى تحديث الملف الشخصي')
        return redirect('home')
    
    if request.method == 'GET' and 'type' in request.GET:
        report_type = request.GET.get('type', 'users')
        format_type = request.GET.get('format', 'excel')
        
        try:
            if report_type == 'users':
                df = export_users_report_data()
                filename = f"تقرير_المستخدمين_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
                
            elif report_type == 'conferences':
                df = export_conferences_report_data()
                filename = f"تقرير_المؤتمرات_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
                
            elif report_type == 'ratings':
                df = export_ratings_report_data()
                filename = f"تقرير_التقييمات_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
                
            else:
                messages.error(request, 'نوع التقرير غير صالح')
                return redirect('export_reports')
            
            # تصدير حسب النوع المطلوب
            if format_type == 'excel':
                return export_to_excel(df, filename)
                
            elif format_type == 'csv':
                return export_to_csv(df, filename)
                
            else:
                messages.error(request, 'تنسيق التصدير غير صالح')
                return redirect('export_reports')
                
        except Exception as e:
            messages.error(request, f'خطأ في تصدير التقرير: {str(e)}')
            import traceback
            traceback.print_exc()
            return redirect('export_reports')
    
    # إذا كان طلب GET بدون معاملات، عرض صفحة التصدير
    context = {
        'total_users': UserProfile.objects.count(),
        'total_conferences': Conference.objects.count(),
        'total_ratings': Rating.objects.count(),
    }
    
    return render(request, 'reports/export.html', context)

@login_required
def system_settings(request):
    """إدارة إعدادات النظام للحقول الأربعة المحددة فقط"""
    try:
        if request.user.userprofile.user_type != 'admin':
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')
    except UserProfile.DoesNotExist:
        messages.error(request, 'يرجى تحديث الملف الشخصي')
        return redirect('home')

    # تعريف المفاتيح المطلوبة
    required_settings = {
        'site_name': 'اسم المنصة',
        'site_description': 'وصف المنصة',
        'contact_email': 'بريد التواصل',
        'contact_phone': 'رقم التواصل'
    }

    if request.method == 'POST':
        for key in required_settings.keys():
            value = request.POST.get(key, '')
            setting, created = SystemSetting.objects.get_or_create(key=key)
            setting.value = value
            setting.description = required_settings[key]
            setting.updated_by = request.user
            setting.save()
        
        messages.success(request, 'تم حفظ إعدادات النظام بنجاح')
        return redirect('system_settings')

    # جلب الإعدادات الحالية لعرضها في القالب
    settings_data = {s.key: s.value for s in SystemSetting.objects.filter(key__in=required_settings.keys())}
    
    context = {
        'settings': settings_data,
        'labels': required_settings
    }
    return render(request, 'dashboard/settings.html', context)