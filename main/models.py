from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
import secrets
from datetime import timedelta

class FoodItem(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_count = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='food_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - ${self.price}"

class QRCodePass(models.Model):
    code_hash = models.CharField(max_length=255, unique=True)  # Hashed QR code
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    used_at = models.DateTimeField(null=True, blank=True)
    use_count = models.IntegerField(default=0)  # How many times it was used
    user_identifier = models.CharField(max_length=100, blank=True)  # Optional: link to user
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pass (Active: {self.is_active}, Uses: {self.use_count})"
    
    @staticmethod
    def generate_secure_code():
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(32)
    
    def set_code(self, raw_code):
        """Hash and store the QR code securely"""
        self.code_hash = make_password(raw_code)
    
    def check_code(self, raw_code):
        """Verify the raw code against the stored hash"""
        return check_password(raw_code, self.code_hash)
    
    def is_valid(self):
        """Check if the pass is still valid"""
        if not self.is_active:
            return False
        
        # Check if expired
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        
        return True
    
    def mark_used(self):
        """Mark the pass as used"""
        self.use_count += 1
        self.used_at = timezone.now()
        self.save()
