/**
 * ملف JavaScript الرئيسي لمنصة المؤتمرات الذكية
 */

$(document).ready(function() {
    // تهيئة عناصر Bootstrap
    $('[data-bs-toggle="tooltip"]').tooltip();
    $('[data-bs-toggle="popover"]').popover();
    
    // التحقق من صحة النماذج
    $('form').on('submit', function() {
        const submitBtn = $(this).find('button[type="submit"]');
        submitBtn.prop('disabled', true);
        submitBtn.html('<span class="spinner-border spinner-border-sm" role="status"></span> جاري المعالجة...');
    });
    
    // البحث الديناميكي في الجداول
    $('.search-table').on('keyup', function() {
        const value = $(this).val().toLowerCase();
        const tableId = $(this).data('table');
        $(`#${tableId} tbody tr`).filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
        });
    });
    
    // تأكيد الحذف
    $('.confirm-delete').on('click', function(e) {
        e.preventDefault();
        const url = $(this).attr('href');
        const message = $(this).data('message') || 'هل أنت متأكد من الحذف؟';
        
        if (confirm(message)) {
            window.location.href = url;
        }
    });
    
    // تحديث حالة الحقول الديناميكية
    $('.dynamic-field').on('change', function() {
        const target = $(this).data('target');
        const value = $(this).val();
        
        if (target && value) {
            $.ajax({
                url: $(this).data('url'),
                data: { value: value },
                success: function(data) {
                    $(target).html(data);
                }
            });
        }
    });
    
    // عرض كلمة المرور
    $('.toggle-password').on('click', function() {
        const input = $(this).parent().find('input');
        const icon = $(this).find('i');
        
        if (input.attr('type') === 'password') {
            input.attr('type', 'text');
            icon.removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            input.attr('type', 'password');
            icon.removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });
    
    // حساب الأحرف في حقول النص
    $('.char-count').on('keyup', function() {
        const maxLength = $(this).attr('maxlength');
        const currentLength = $(this).val().length;
        const counter = $(this).next('.char-counter');
        
        if (counter.length) {
            counter.text(`${currentLength}/${maxLength}`);
            
            if (currentLength > maxLength * 0.8) {
                counter.css('color', '#ff9800');
            }
            if (currentLength > maxLength * 0.9) {
                counter.css('color', '#f44336');
            }
        }
    });
    
    // فرز الجداول
    $('.sortable').on('click', function() {
        const table = $(this).closest('table');
        const column = $(this).index();
        const rows = table.find('tbody > tr').toArray();
        const order = $(this).hasClass('asc') ? -1 : 1;
        
        $(this).toggleClass('asc desc');
        
        rows.sort(function(a, b) {
            const aVal = $(a).children('td').eq(column).text();
            const bVal = $(b).children('td').eq(column).text();
            
            if ($.isNumeric(aVal) && $.isNumeric(bVal)) {
                return (parseFloat(aVal) - parseFloat(bVal)) * order;
            }
            return aVal.localeCompare(bVal) * order;
        });
        
        table.find('tbody').empty().append(rows);
    });
    
    // تحديث الوقت الحالي
    function updateDateTime() {
        const now = new Date();
        const options = {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZone: 'Asia/Damascus'
        };
        
        const arDate = now.toLocaleDateString('ar-SY', options);
        $('.current-datetime').text(arDate);
    }
    
    setInterval(updateDateTime, 1000);
    updateDateTime();
    
    // التحقق من الاتصال بالإنترنت
    function checkInternetConnection() {
        if (!navigator.onLine) {
            showNotification('فقدان الاتصال بالإنترنت', 'warning');
        }
    }
    
    window.addEventListener('online', checkInternetConnection);
    window.addEventListener('offline', checkInternetConnection);
    
    // إظهار إشعارات مخصصة
    function showNotification(title, type, message = '') {
        const alertClass = {
            'success': 'alert-success',
            'warning': 'alert-warning',
            'error': 'alert-danger',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const icon = {
            'success': 'fa-check-circle',
            'warning': 'fa-exclamation-triangle',
            'error': 'fa-times-circle',
            'info': 'fa-info-circle'
        }[type] || 'fa-info-circle';
        
        const notification = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="fas ${icon}"></i>
                <strong>${title}</strong> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('#notifications').append(notification);
        
        setTimeout(function() {
            $('.alert').alert('close');
        }, 5000);
    }
    
    // تحديث العدادات الديناميكية
    function animateCounter(element, target, duration = 2000) {
        const start = parseInt(element.text()) || 0;
        const increment = (target - start) / (duration / 16);
        let current = start;
        
        const timer = setInterval(function() {
            current += increment;
            if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
                element.text(target);
                clearInterval(timer);
            } else {
                element.text(Math.round(current));
            }
        }, 16);
    }
    
    // تطبيق العدادات على العناصر ذات الكلاس counter
    $('.counter').each(function() {
        const target = parseInt($(this).data('target')) || 0;
        animateCounter($(this), target);
    });
    
    // تحميل الملفات بتحميل تدريجي
    $('.file-upload').on('change', function() {
        const fileName = $(this).val().split('\\').pop();
        $(this).next('.custom-file-label').html(fileName);
    });
    
    // عرض معاينة الصور
    $('.image-preview').on('change', function() {
        const input = $(this)[0];
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = function(e) {
                $(input).closest('.image-upload-container').find('.preview').attr('src', e.target.result);
            }
            reader.readAsDataURL(input.files[0]);
        }
    });
    
    // وظائف خاصة بالمدير
    if ($('body').hasClass('admin-dashboard')) {
        // تحديث الإحصائيات كل دقيقة
        setInterval(function() {
            $.ajax({
                url: '/api/stats/',
                success: function(data) {
                    // تحديث العدادات
                    $('.total-users').text(data.total_users);
                    $('.active-conferences').text(data.active_conferences);
                    // ... تحديث باقي الإحصائيات
                }
            });
        }, 60000);
        
        // التحديث التلقائي للقوائم
        $('.auto-refresh').each(function() {
            const url = $(this).data('url');
            const interval = $(this).data('interval') || 30000;
            
            setInterval(function() {
                $.get(url, function(data) {
                    $(this).html(data);
                }.bind(this));
            }.bind(this), interval);
        });
    }
});

// وظائف مساعدة عامة
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SY', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ar-SY', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('تم النسخ', 'success');
    }, function(err) {
        console.error('فشل النسخ: ', err);
        showNotification('فشل النسخ', 'error');
    });
}

// معالجة الأخطاء
window.onerror = function(msg, url, lineNo, columnNo, error) {
    console.error('خطأ: ', msg, 'في: ', url, 'السطر: ', lineNo);
    showNotification('حدث خطأ غير متوقع', 'error');
    return false;
};

// استدعاء API
function callAPI(url, method = 'GET', data = null) {
    return new Promise(function(resolve, reject) {
        $.ajax({
            url: url,
            method: method,
            data: data,
            success: resolve,
            error: function(xhr, status, error) {
                reject({ xhr: xhr, status: status, error: error });
            }
        });
    });
}