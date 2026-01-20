# QR Code Security Documentation

## Security Measures Implemented

### 1. **SQL Injection Protection** ✓

**How it's protected:**
- Using Django ORM's `.filter()` method instead of raw SQL
- All database queries are parameterized automatically
- Never concatenating user input into SQL strings

```python
# ✓ SAFE - Django ORM automatically escapes parameters
QRCodePass.objects.filter(code=qr_data, is_active=True)

# ✗ DANGEROUS - Never do this!
# cursor.execute(f"SELECT * FROM passes WHERE code = '{qr_data}'")
```

### 2. **Password-Style Hashing** ✓

**How QR codes are stored:**
- QR codes are hashed using Django's `make_password()` (PBKDF2 algorithm)
- Original codes are **never** stored in plaintext
- Uses salt and multiple iterations to prevent rainbow table attacks
- Admin only sees the raw code once when creating it

```python
# Code is hashed before storing
obj.set_code(raw_code)  # Internally uses make_password()
obj.check_code(user_input)  # Uses check_password() for verification
```

### 3. **Cryptographically Secure Random Generation** ✓

**How codes are generated:**
- Using `secrets.token_urlsafe(32)` from Python's secrets module
- Generates 256-bit random tokens (43 URL-safe characters)
- Cryptographically secure random number generator (CSRNG)
- Practically impossible to guess or brute force

```python
secrets.token_urlsafe(32)  # Example: "DFu8mKzO1kJ9XnB_vR3tP2qL8wE5yH4cA6sM7dN9fG1"
```

### 4. **Rate Limiting** ✓

**Protection against brute force:**
- Maximum 10 scan attempts per IP address per minute
- Uses Django's caching framework
- Returns HTTP 429 (Too Many Requests) when exceeded
- Automatically resets after 60 seconds

```python
# Rate limit key based on IP address
rate_limit_key = f'qr_scan_{ip_address}'
attempts = cache.get(rate_limit_key, 0)
if attempts >= 10:
    return 429 error
```

### 5. **Single-Use or Limited-Use Tokens** ✓

**Prevents replay attacks:**
- `max_uses` field controls how many times a code can be used
- Default is 1 (single-use)
- Auto-deactivates after reaching max uses
- Tracks `use_count` for audit trail

```python
qr_pass.mark_used()  # Increments use_count, deactivates if max reached
```

### 6. **Expiration Timestamps** ✓

**Time-based validity:**
- Each pass has an `expires_at` field
- Default expiry: 30 days from creation
- Automatically invalidated after expiration
- Prevents indefinite validity

```python
if self.expires_at and timezone.now() > self.expires_at:
    return False
```

### 7. **Input Validation** ✓

**Prevents malicious input:**
- Checks for empty data
- Limits maximum length (1000 characters)
- Strips whitespace
- Validates JSON format

```python
if not qr_data or len(qr_data) > 1000:
    return error
```

### 8. **Error Message Sanitization** ✓

**Prevents information leakage:**
- Generic error messages to users
- Doesn't reveal why authentication failed
- Detailed errors only logged server-side
- Prevents enumeration attacks

```python
# ✓ SAFE - Generic message
"Invalid or expired QR code"

# ✗ DANGEROUS - Reveals too much
# "Code exists but is expired" or "Code not found"
```

### 9. **Constant-Time Comparison** ✓

**Prevents timing attacks:**
- Using `check_password()` which uses constant-time comparison
- Iterates through all passes to prevent timing leaks
- Doesn't stop at first match

### 10. **CSRF Protection** ⚠️

**Currently disabled for API:**
- Using `@csrf_exempt` for easier mobile/cross-origin access
- **Recommendation:** Enable CSRF tokens for production
- Or use token-based authentication (JWT)

## Best Practices for Production

### Enable HTTPS (Already Done) ✓
```python
# You're already using mkcert and HTTPS
python manage.py runserver_plus --cert-file localhost+2.pem --key-file localhost+2-key.pem
```

### Add Audit Logging (Optional)
Create a ScanLog model to track all authentication attempts:
```python
class ScanLog(models.Model):
    ip_address = models.GenericIPAddressField()
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)
```

### Enable CSRF Protection (Production)
Remove `@csrf_exempt` and use proper CSRF tokens:
```javascript
// In frontend
fetch('/api/scan-qr/', {
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    }
})
```

### Add User Authentication (Optional)
Link QR passes to specific users:
```python
user = models.ForeignKey(User, on_delete=models.CASCADE)
```

## How to Use Securely

### Creating QR Codes (Admin Panel)

1. Go to `/admin/main/qrcodepass/`
2. Click "Add QR code pass"
3. Set `user_identifier` (optional, for tracking)
4. Set `max_uses` (default: 1)
5. Set `expires_at` (default: 30 days)
6. Save - **Copy the generated code immediately!**
7. Generate QR code from this text using any QR generator
8. The code is now hashed and cannot be retrieved

### Scanning QR Codes

1. User scans QR code with camera
2. System verifies against hashed database entries
3. Rate limiting prevents brute force
4. Single-use codes auto-deactivate after scan
5. Expired codes are rejected
6. Valid codes redirect to success page

## Attack Scenarios & Mitigations

| Attack Type | Mitigation |
|------------|------------|
| SQL Injection | Django ORM with parameterized queries |
| Brute Force | Rate limiting (10 attempts/minute) |
| Replay Attack | Single-use tokens with use counting |
| Rainbow Tables | Salted PBKDF2 hashing |
| Timing Attack | Constant-time password comparison |
| Token Prediction | Cryptographically secure random generation |
| Information Leak | Generic error messages |
| Expired Token Reuse | Timestamp validation |

## Security Checklist

- [x] SQL injection protection (Django ORM)
- [x] Password hashing for QR codes (PBKDF2)
- [x] Cryptographically secure random generation
- [x] Rate limiting (10/minute per IP)
- [x] Single-use or limited-use tokens
- [x] Expiration timestamps
- [x] Input validation
- [x] Error message sanitization
- [x] HTTPS enabled
- [x] Constant-time comparison
- [ ] CSRF protection (currently disabled for API)
- [ ] Audit logging (optional)
- [ ] User authentication integration (optional)

## Maintenance

### Cleanup Expired Passes
Run this periodically to remove old passes:
```python
from django.utils import timezone
QRCodePass.objects.filter(expires_at__lt=timezone.now()).delete()
```

### Monitor Failed Attempts
Check logs for patterns of failed authentication attempts.
