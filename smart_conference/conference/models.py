from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class SyrianCity(models.Model):
    name = models.CharField(max_length=100)
    governorate = models.CharField(max_length=100)
    
    class Meta:
        verbose_name_plural = "Syrian Cities"
    
    def __str__(self):
        return f"{self.name} - {self.governorate}"

class UserProfile(models.Model):
    USER_TYPES = [
        ('admin', 'مدير النظام'),
        ('organizer', 'منظم المؤتمر'),
        ('speaker', 'متحدث'),
        ('attendee', 'مشارك'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='attendee')
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.ForeignKey(SyrianCity, on_delete=models.SET_NULL, null=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_user_type_display()}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name

class Conference(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('approved', 'مقبول'),
        ('rejected', 'مرفوض'),
        ('active', 'نشط'),
        ('completed', 'منتهي'),
        ('cancelled', 'ملغي'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    organizer = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    city = models.ForeignKey(SyrianCity, on_delete=models.SET_NULL, null=True)
    max_attendees = models.IntegerField(default=100)
    current_attendees = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class ConferenceRequest(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=50)  # approval, modification, cancellation
    status = models.CharField(max_length=20, choices=[
        ('pending', 'قيد الانتظار'),
        ('approved', 'مقبول'),
        ('rejected', 'مرفوض'),
    ], default='pending')
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.conference.title} - {self.request_type}"

class Rating(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['conference', 'user']
    
    def __str__(self):
        return f"{self.conference.title} - {self.rating} stars"

class Attendance(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    attended = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)
    attended_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['conference', 'user']
    
    def __str__(self):
        return f"{self.user} - {self.conference}"

class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.key