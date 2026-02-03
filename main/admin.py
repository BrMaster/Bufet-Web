from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import QRCodePass, FoodItem, Order, OrderItem
@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock_count', 'is_available', 'updated_at')
    list_filter = ('is_available', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock_count', 'is_available')
@admin.register(QRCodePass)
class QRCodePassAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_identifier', 'created_at', 'expires_at', 'is_active', 'use_count')
    list_filter = ('created_at', 'is_active', 'expires_at')
    search_fields = ('user_identifier',)
    readonly_fields = ('code_hash', 'created_at', 'used_at', 'use_count')
    
    fieldsets = (
        ('Pass Information', {
            'fields': ('user_identifier', 'code_hash')
        }),
        ('Security Settings', {
            'fields': ('is_active', 'use_count', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'used_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Display the raw code only once when creating"""
        if not change:  # Only for new objects
            raw_code = QRCodePass.generate_secure_code()
            obj.set_code(raw_code)
            # Set default expiry to 30 days from now
            if not obj.expires_at:
                obj.expires_at = timezone.now() + timedelta(days=30)
            obj.save()
            # Show the code to admin (only time it's visible)
            self.message_user(request, f'⚠️ SAVE THIS CODE - It will not be shown again: {raw_code}')
        else:
            super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('food_item', 'quantity', 'unit_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_identifier', 'created_at', 'status', 'payment_method', 'payment_status', 'total_amount')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    search_fields = ('user_identifier',)
    readonly_fields = ('created_at', 'total_amount', 'stripe_session_id', 'paid_at')
    inlines = [OrderItemInline]
