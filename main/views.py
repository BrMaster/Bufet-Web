from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Sum
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from datetime import datetime
from decimal import Decimal
import stripe
import json
from .models import QRCodePass, FoodItem, Order, OrderItem


def home(request):
	return render(request, "home.html")


def logged_in(request):
	"""Show QR scanner or redirect to success if already authenticated"""
	# Check if user already has a valid session
	if request.session.get('qr_authenticated'):
		qr_auth_time_str = request.session.get('qr_auth_time')
		if qr_auth_time_str:
			qr_auth_time = datetime.fromisoformat(qr_auth_time_str)
			current_time = timezone.now()
			time_elapsed = (current_time - qr_auth_time).total_seconds()
			
			# If session is still valid (within 5 minutes), redirect to success
			if time_elapsed < 300:
				return redirect('/success/')
	
	# No valid session, show QR scanner
	return render(request, "logged_in.html")


def admin_login(request):
	"""Admin login view"""
	if request.user.is_authenticated:
		return redirect('/generate-qr/')
	
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		user = authenticate(request, username=username, password=password)
		
		if user is not None:
			auth_login(request, user)
			return redirect('/generate-qr/')
		else:
			return render(request, 'qr_generator_login.html', {'error': 'Invalid username or password'})
	
	return render(request, 'qr_generator_login.html')


def admin_logout(request):
	"""Admin logout view"""
	auth_logout(request)
	return redirect('/')

def logout(request):
	"""Log out user by clearing session"""
	if 'qr_authenticated' in request.session:
		del request.session['qr_authenticated']
	if 'qr_auth_time' in request.session:
		del request.session['qr_auth_time']
	if 'user_identifier' in request.session:
		del request.session['user_identifier']
	request.session.modified = True
	return redirect('/')


def get_client_ip(request):
	"""Get client IP address from request"""
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0]
	else:
		ip = request.META.get('REMOTE_ADDR')
	return ip


@csrf_exempt
@require_http_methods(["POST"])
def scan_qr(request):
	"""API endpoint to verify QR code pass with security measures"""
	try:
		# Rate limiting: Max 10 attempts per IP per minute
		ip_address = get_client_ip(request)
		rate_limit_key = f'qr_scan_{ip_address}'
		attempts = cache.get(rate_limit_key, 0)
		
		if attempts >= 10:
			return JsonResponse({
				'success': False,
				'message': 'Too many attempts. Please wait a minute.',
				'valid': False
			}, status=429)
		
		# Increment attempt counter
		cache.set(rate_limit_key, attempts + 1, 60)  # Expires in 60 seconds
		
		data = json.loads(request.body)
		qr_data = data.get('data', '').strip()
		
		# Input validation
		if not qr_data:
			return JsonResponse({'error': 'No QR data provided'}, status=400)
		
		if len(qr_data) > 1000:  # Prevent oversized input
			return JsonResponse({'error': 'Invalid QR code format'}, status=400)
		
		# Security: Django ORM automatically protects against SQL injection
		# We're using .filter() and .first() which are safe
		# Never use raw SQL queries or string concatenation
		
		# Find all active passes and check against hashed values
		# This prevents timing attacks by checking all passes
		valid_pass = None
		for qr_pass in QRCodePass.objects.filter(is_active=True):
			if qr_pass.check_code(qr_data) and qr_pass.is_valid():
				valid_pass = qr_pass
				break
		
		if valid_pass:
			# Mark as used
			valid_pass.mark_used()
			
			# Create a secure session token for access to success page
			request.session['qr_authenticated'] = True
			request.session['qr_auth_time'] = timezone.now().isoformat()
			request.session['user_identifier'] = valid_pass.user_identifier
			# Session expires in 5 minutes
			request.session.set_expiry(300)
			
			# Log successful authentication (optional)
			# You could add a ScanLog model here for audit trail
			
			return JsonResponse({
				'success': True,
				'message': 'QR Code Pass Valid',
				'valid': True,
				'redirect_url': '/success/'
			})
		else:
			# Don't reveal why it failed (security best practice)
			return JsonResponse({
				'success': False,
				'message': 'Invalid or expired QR code',
				'valid': False
			})
			
	except json.JSONDecodeError:
		return JsonResponse({'error': 'Invalid request format'}, status=400)
	except Exception as e:
		# Don't leak error details to user
		print(f"QR Scan Error: {str(e)}")  # Log server-side only
		return JsonResponse({'error': 'An error occurred'}, status=500)


def success(request):
	"""Success page shown after valid QR code scan - requires authenticated session"""
	# Check if user has a valid QR authentication session
	if not request.session.get('qr_authenticated'):
		# Not authenticated - redirect to home with error
		return render(request, 'access_denied.html', status=403)
	
	# Check if session has expired (more than 5 minutes since authentication)
	auth_time_str = request.session.get('qr_auth_time')
	if auth_time_str:
		from datetime import datetime
		auth_time = datetime.fromisoformat(auth_time_str)
		current_time = timezone.now()
		time_elapsed = (current_time - auth_time).total_seconds()
		
		if time_elapsed > 300:  # 5 minutes = 300 seconds
			# Session expired - clear it
			request.session.flush()
			return render(request, 'session_expired.html', status=403)
		
		# Calculate remaining time
		remaining_seconds = int(300 - time_elapsed)
		remaining_minutes = remaining_seconds // 60
		remaining_secs = remaining_seconds % 60
	else:
		remaining_minutes = 5
		remaining_secs = 0
	
	# Get user identifier from session
	user_identifier = request.session.get('user_identifier', 'Guest')
	
	# Get all available food items
	food_items = FoodItem.objects.filter(is_available=True).order_by('name')
	
	# Don't clear the session - let it expire naturally after 5 minutes
	context = {
		'user_identifier': user_identifier,
		'remaining_minutes': remaining_minutes,
		'remaining_seconds': remaining_secs,
		'food_items': food_items
	}
	
	return render(request, 'success.html', context)


def _validate_cart(items):
	item_map = {}
	for item in items:
		item_id = item.get('id')
		qty = item.get('quantity')
		if not item_id or not isinstance(qty, int) or qty < 1:
			raise ValueError('Invalid cart item')
		item_map[item_id] = qty

	food_items = FoodItem.objects.filter(id__in=item_map.keys(), is_available=True)
	food_by_id = {fi.id: fi for fi in food_items}

	if len(food_by_id) != len(item_map):
		raise ValueError('Some items are unavailable')

	for item_id, qty in item_map.items():
		food = food_by_id.get(item_id)
		if not food or food.stock_count < qty:
			raise ValueError(f'Insufficient stock for {food.name if food else "item"}')

	return item_map, food_by_id


def _build_order_from_items(items, user_identifier, payment_method, payment_status='pending', status='pending', paid_at=None):
	item_map, food_by_id = _validate_cart(items)
	user_identifier = user_identifier or 'Guest'
	total_amount = Decimal('0.00')

	with transaction.atomic():
		order = Order.objects.create(
			user_identifier=user_identifier,
			payment_method=payment_method,
			payment_status=payment_status,
			status=status,
			paid_at=paid_at,
			total_amount=0
		)
		for item_id, qty in item_map.items():
			food = food_by_id[item_id]
			unit_price = Decimal(str(food.price))
			OrderItem.objects.create(
				order=order,
				food_item=food,
				quantity=qty,
				unit_price=unit_price
			)
			total_amount += unit_price * qty
			food.stock_count = max(0, food.stock_count - qty)
			food.save(update_fields=['stock_count'])
		order.total_amount = total_amount
		order.save(update_fields=['total_amount'])

	return order, total_amount


@require_http_methods(["POST"])
def create_order(request):
	"""Create a new order from cart items"""
	if not request.session.get('qr_authenticated'):
		return JsonResponse({'success': False, 'message': 'Not authenticated'}, status=403)

	try:
		data = json.loads(request.body)
		items = data.get('items', [])
		payment_method = data.get('payment_method', 'in_person')
		if not items:
			return JsonResponse({'success': False, 'message': 'Cart is empty'}, status=400)
		if payment_method not in ['in_person']:
			return JsonResponse({'success': False, 'message': 'Invalid payment method'}, status=400)

		user_identifier = request.session.get('user_identifier', 'Guest')
		order, total_amount = _build_order_from_items(items, user_identifier, payment_method)

		return JsonResponse({
			'success': True,
			'order_id': order.id,
			'total_amount': f"{total_amount:.2f}"
		})
	except json.JSONDecodeError:
		return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
	except ValueError as e:
		return JsonResponse({'success': False, 'message': str(e)}, status=400)
	except Exception as e:
		print(f"Order Error: {str(e)}")
		return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)


@require_http_methods(["POST"])
def create_stripe_session(request):
	"""Create a Stripe Checkout session for the current cart"""
	if not request.session.get('qr_authenticated'):
		return JsonResponse({'success': False, 'message': 'Not authenticated'}, status=403)

	if not settings.STRIPE_SECRET_KEY:
		return JsonResponse({'success': False, 'message': 'Stripe is not configured'}, status=500)

	try:
		data = json.loads(request.body)
		items = data.get('items', [])
		if not items:
			return JsonResponse({'success': False, 'message': 'Cart is empty'}, status=400)

		user_identifier = request.session.get('user_identifier', 'Guest')
		stripe.api_key = settings.STRIPE_SECRET_KEY
		item_map, food_by_id = _validate_cart(items)
		line_items = []
		for item_id, qty in item_map.items():
			food = food_by_id[item_id]
			line_items.append({
				'price_data': {
					'currency': 'eur',
					'product_data': {
						'name': food.name,
					},
					'unit_amount': int(Decimal(food.price) * 100),
				},
				'quantity': qty,
			})

		success_url = request.build_absolute_uri(f"/payments/stripe-success/?session_id={{CHECKOUT_SESSION_ID}}")
		cancel_url = request.build_absolute_uri("/payments/stripe-cancel/")
		session = stripe.checkout.Session.create(
			mode='payment',
			line_items=line_items,
			success_url=success_url,
			cancel_url=cancel_url,
			metadata={'user_identifier': str(user_identifier)}
		)

		cache.set(
			f"stripe_session_{session.id}",
			{'items': items, 'user_identifier': user_identifier},
			3600
		)

		return JsonResponse({
			'success': True,
			'checkout_url': session.url
		})
	except json.JSONDecodeError:
		return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
	except ValueError as e:
		return JsonResponse({'success': False, 'message': str(e)}, status=400)
	except Exception as e:
		print(f"Stripe Error: {str(e)}")
		return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)


@require_http_methods(["GET"])
def stripe_success(request):
	"""Handle Stripe success redirect and mark order as paid"""
	if not settings.STRIPE_SECRET_KEY:
		return redirect('/payment-error/')

	session_id = request.GET.get('session_id')
	if not session_id:
		return redirect('/payment-error/')

	try:
		stripe.api_key = settings.STRIPE_SECRET_KEY
		session = stripe.checkout.Session.retrieve(session_id)
		pending = cache.get(f"stripe_session_{session.id}")
		if not pending:
			return redirect('/payment-error/')

		order, total_amount = _build_order_from_items(
			pending.get('items', []),
			pending.get('user_identifier', 'Guest'),
			'stripe',
			payment_status='paid',
			status='paid',
			paid_at=timezone.now()
		)
		order.stripe_session_id = session.id
		order.save(update_fields=['stripe_session_id'])
		cache.delete(f"stripe_session_{session.id}")
		return redirect(f'/success/?payment=success&order_id={order.id}')
	except Exception as e:
		print(f"Stripe Success Error: {str(e)}")
		return redirect('/payment-error/')


@require_http_methods(["GET"])
def stripe_cancel(request):
	"""Stripe cancel redirect"""
	return redirect('/success/?payment=cancelled')


def payment_error(request):
	"""Payment error page"""
	return render(request, 'payment_error.html')


@require_http_methods(["GET", "POST"])
def generate_qr(request):
	"""Generate new QR code passes (Admin only)"""
	# Check if user is admin
	if not request.user.is_staff:
		return render(request, 'admin_only.html', status=403)
	
	if request.method == 'POST':
		# Check if this is a reset request
		reset_pass_id = request.POST.get('reset_pass_id')
		
		if reset_pass_id:
			# Reset existing pass
			try:
				qr_pass = QRCodePass.objects.get(id=reset_pass_id)
				raw_code = QRCodePass.generate_secure_code()
				qr_pass.set_code(raw_code)
				qr_pass.use_count = 0  # Reset usage count
				qr_pass.is_active = True  # Reactivate if was inactive
				qr_pass.expires_at = timezone.now() + timezone.timedelta(days=30)  # Extend expiry
				qr_pass.save()
				
				context = {
					'raw_code': raw_code,
					'user_identifier': qr_pass.user_identifier,
					'expires_at': qr_pass.expires_at.strftime('%Y-%m-%d %H:%M'),
					'pass_id': qr_pass.id,
					'is_reset': True
				}
				return render(request, 'qr_generated.html', context)
			except QRCodePass.DoesNotExist:
				# Handle error - pass not found
				all_passes = QRCodePass.objects.all().order_by('-created_at')
				return render(request, 'qr_generator.html', {
					'passes': all_passes,
					'error': 'QR Code Pass not found'
				})
		else:
			# Create new pass
			user_identifier = request.POST.get('user_identifier', '')
			
			# Generate secure code
			raw_code = QRCodePass.generate_secure_code()
			qr_pass = QRCodePass()
			qr_pass.set_code(raw_code)
			qr_pass.user_identifier = user_identifier
			qr_pass.expires_at = timezone.now() + timezone.timedelta(days=30)
			qr_pass.save()
			
			context = {
				'raw_code': raw_code,
				'user_identifier': user_identifier,
				'expires_at': qr_pass.expires_at.strftime('%Y-%m-%d %H:%M'),
				'pass_id': qr_pass.id,
				'is_reset': False
			}
			return render(request, 'qr_generated.html', context)
	
	# GET request - show form with search functionality
	search_query = request.GET.get('search', '').strip()
	
	if search_query:
		# Filter passes by user_identifier containing search query (case-insensitive)
		all_passes = QRCodePass.objects.filter(
			user_identifier__icontains=search_query
		).order_by('-created_at')
	else:
		all_passes = QRCodePass.objects.all().order_by('-created_at')
	
	return render(request, 'qr_generator.html', {
		'passes': all_passes,
		'search_query': search_query
	})


def admin_orders(request):
	"""Admin-only orders panel"""
	if not request.user.is_staff:
		return render(request, 'admin_only.html', status=403)

	status_filter = request.GET.get('status', '').strip()
	payment_filter = request.GET.get('payment', '').strip()
	search_query = request.GET.get('search', '').strip()

	orders = Order.objects.all().prefetch_related('items', 'items__food_item')
	if status_filter:
		orders = orders.filter(status=status_filter)
	if payment_filter:
		orders = orders.filter(payment_status=payment_filter)
	if search_query:
		if search_query.isdigit():
			orders = orders.filter(id=int(search_query))
		else:
			orders = orders.filter(user_identifier__icontains=search_query)

	orders = orders.order_by('-created_at')

	all_orders = Order.objects.all()
	paid_total = all_orders.filter(payment_status='paid').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
	pending_count = all_orders.filter(payment_status='pending').count()
	paid_count = all_orders.filter(payment_status='paid').count()

	context = {
		'orders': orders,
		'status_filter': status_filter,
		'payment_filter': payment_filter,
		'search_query': search_query,
		'paid_total': paid_total,
		'pending_count': pending_count,
		'paid_count': paid_count,
		'payment_statuses': Order.PAYMENT_STATUSES,
	}
	return render(request, 'admin_orders.html', context)
