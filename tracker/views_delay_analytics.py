"""
Advanced analytics and reporting views for delay reason management.
Helps users understand, analyze, and manage order delays effectively.
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q, F, Value, CharField, FloatField, Case, When, Sum, Avg, Max, Min
from django.db.models.functions import Coalesce, TruncDate, Cast
from django.utils import timezone
from django.contrib import messages

from .models import Order, DelayReason, DelayReasonCategory, User, Branch
from .utils import get_user_branch

logger = logging.getLogger(__name__)


def _get_category_display(category_code):
    """Convert category code to display name using DelayReasonCategory choices"""
    category_choices = dict(DelayReasonCategory.CATEGORY_CHOICES)
    return category_choices.get(category_code, category_code)


@login_required
@permission_required('tracker.view_order', raise_exception=True)
def delay_analytics_dashboard(request):
    """Main delay analytics dashboard with overview and filters"""
    user_branch = get_user_branch(request.user)
    
    # Get time period filter from request
    time_period = request.GET.get('period', '30days')
    start_date = _get_start_date_from_period(time_period)
    
    # Get category filter
    selected_category = request.GET.get('category', '')
    
    # Get user/team filter
    selected_user = request.GET.get('user', '')
    
    # Get order type filter (service, sales, inquiry, labour, unspecified, mixed)
    selected_order_type = request.GET.get('order_type', '')
    
    # FIX: Query orders with delay_reason directly from database
    if user_branch:
        orders_qs = Order.objects.filter(
            branch=user_branch,
            delay_reason__isnull=False,
            delay_reason_reported_at__isnull=False
        )
    else:
        # If no branch, show all orders with delay reasons
        orders_qs = Order.objects.filter(
            delay_reason__isnull=False,
            delay_reason_reported_at__isnull=False
        )
    
    if start_date:
        orders_qs = orders_qs.filter(delay_reason_reported_at__gte=start_date)
    
    if selected_category:
        orders_qs = orders_qs.filter(delay_reason__category__category=selected_category)
    
    if selected_user:
        orders_qs = orders_qs.filter(delay_reason_reported_by__id=selected_user)
    
    if selected_order_type:
        orders_qs = orders_qs.filter(type=selected_order_type)
    
    # Get statistics
    total_delayed_orders = orders_qs.count()
    total_orders = Order.objects.filter(
        branch=user_branch,
        status='completed',
        delay_reason_reported_at__isnull=False
    )
    if start_date:
        total_orders = total_orders.filter(delay_reason_reported_at__gte=start_date)
    
    delay_rate = (total_delayed_orders / total_orders.count() * 100) if total_orders.count() > 0 else 0
    
    # Get categories and users for filters
    categories = DelayReasonCategory.objects.filter(is_active=True).values_list('category', 'category')
    users = User.objects.filter(
        groups__permissions__codename='view_order'
    ).distinct().values('id', 'first_name', 'last_name', 'username')
    
    context = {
        'time_period': time_period,
        'selected_category': selected_category,
        'selected_user': selected_user,
        'selected_order_type': selected_order_type,
        'total_delayed_orders': total_delayed_orders,
        'delay_rate': round(delay_rate, 2),
        'categories': categories,
        'users': users,
        'order_types': Order.TYPE_CHOICES,
    }
    
    return render(request, 'tracker/delay_analytics_dashboard.html', context)


@login_required
@require_http_methods(["GET"])
def api_delay_analytics_summary(request):
    """API endpoint for delay analytics summary statistics - Query directly from DelayReason table"""
    user_branch = get_user_branch(request.user)

    time_period = request.GET.get('period', '30days')
    selected_category = request.GET.get('category', '')
    selected_user = request.GET.get('user', '')
    selected_order_type = request.GET.get('order_type', '')
    start_date = _get_start_date_from_period(time_period)

    # FIX: Query directly from DelayReason table using reverse relationship
    delay_reasons_qs = DelayReason.objects.filter(
        orders__isnull=False,
        orders__delay_reason_reported_at__isnull=False
    )
    
    # Apply branch filter through orders
    if user_branch:
        delay_reasons_qs = delay_reasons_qs.filter(orders__branch=user_branch)
    
    # Apply date filter
    if start_date:
        delay_reasons_qs = delay_reasons_qs.filter(orders__delay_reason_reported_at__gte=start_date)
    
    # Apply category filter
    if selected_category:
        delay_reasons_qs = delay_reasons_qs.filter(category__category=selected_category)
    
    # Apply user filter
    if selected_user:
        delay_reasons_qs = delay_reasons_qs.filter(orders__delay_reason_reported_by__id=selected_user)
    
    # Apply order type filter
    if selected_order_type:
        delay_reasons_qs = delay_reasons_qs.filter(orders__type=selected_order_type)
    
    # Get distinct orders with delay reasons (using distinct to avoid duplicates from joins)
    orders_with_delays = Order.objects.filter(
        delay_reason__isnull=False,
        delay_reason_reported_at__isnull=False
    )
    
    if user_branch:
        orders_with_delays = orders_with_delays.filter(branch=user_branch)
    if start_date:
        orders_with_delays = orders_with_delays.filter(delay_reason_reported_at__gte=start_date)
    if selected_category:
        orders_with_delays = orders_with_delays.filter(delay_reason__category__category=selected_category)
    if selected_user:
        orders_with_delays = orders_with_delays.filter(delay_reason_reported_by__id=selected_user)
    if selected_order_type:
        orders_with_delays = orders_with_delays.filter(type=selected_order_type)
    
    # Calculate metrics
    total_delayed = orders_with_delays.distinct().count()
    
    # Get total orders in same period for comparison
    if user_branch:
        total_all_orders = Order.objects.filter(branch=user_branch)
    else:
        total_all_orders = Order.objects.all()
    
    if start_date:
        total_all_orders = total_all_orders.filter(created_at__gte=start_date)
    
    total_all = total_all_orders.count()
    delay_percentage = (total_delayed / total_all * 100) if total_all > 0 else 0
    
    # Orders with exceeded 2 hours threshold
    exceeded_2_hours_count = orders_with_delays.filter(exceeded_9_hours=True).distinct().count()
    
    # Average time from start to completion for delayed orders
    delayed_orders_with_times = orders_with_delays.filter(
        started_at__isnull=False,
        completed_at__isnull=False
    ).distinct()
    
    total_duration = 0
    count = 0
    for order in delayed_orders_with_times[:1000]:  # Limit to avoid memory issues
        if order.completed_at and order.started_at:
            duration = (order.completed_at - order.started_at).total_seconds() / 3600
            total_duration += duration
            count += 1
    
    avg_hours = total_duration / count if count > 0 else 0
    
    # Most common delay reasons - query directly from DelayReason
    top_reasons_raw = delay_reasons_qs.annotate(
        order_count=Count('orders', distinct=True)
    ).filter(order_count__gt=0).order_by('-order_count')[:10]
    
    top_reasons = []
    for delay_reason in top_reasons_raw:
        count_for_reason = orders_with_delays.filter(delay_reason=delay_reason).distinct().count()
        percentage = (count_for_reason / total_delayed * 100) if total_delayed > 0 else 0
        top_reasons.append({
            'delay_reason__reason_text': delay_reason.reason_text,
            'delay_reason__category__category': delay_reason.category.category if delay_reason.category else '',
            'delay_reason__category__get_category_display': _get_category_display(delay_reason.category.category) if delay_reason.category else 'Unknown',
            'count': count_for_reason,
            'percentage': percentage,
        })

    return JsonResponse({
        'success': True,
        'summary': {
            'total_delayed_orders': total_delayed,
            'total_all_orders': total_all,
            'delay_percentage': round(delay_percentage, 2),
            'exceeded_2_hours': exceeded_2_hours_count,
            'average_hours': round(avg_hours, 1),
        },
        'top_reasons': top_reasons
    })


@login_required
@require_http_methods(["GET"])
def api_delay_reasons_breakdown(request):
    """API endpoint for delay reasons breakdown by category - Query from DelayReason table"""
    user_branch = get_user_branch(request.user)

    time_period = request.GET.get('period', '30days')
    start_date = _get_start_date_from_period(time_period)
    selected_category = request.GET.get('category', '')
    selected_user = request.GET.get('user', '')
    selected_order_type = request.GET.get('order_type', '')
    
    # FIX: Query directly from DelayReasonCategory through DelayReason
    categories_qs = DelayReasonCategory.objects.filter(
        reasons__orders__isnull=False,
        reasons__orders__delay_reason_reported_at__isnull=False
    )
    
    # Apply filters through orders relationship
    if user_branch:
        categories_qs = categories_qs.filter(reasons__orders__branch=user_branch)
    if start_date:
        categories_qs = categories_qs.filter(reasons__orders__delay_reason_reported_at__gte=start_date)
    if selected_category:
        categories_qs = categories_qs.filter(category=selected_category)
    if selected_user:
        categories_qs = categories_qs.filter(reasons__orders__delay_reason_reported_by__id=selected_user)
    if selected_order_type:
        categories_qs = categories_qs.filter(reasons__orders__type=selected_order_type)
    
    # Get counts per category
    data = []
    for category in categories_qs.distinct():
        # Count orders with this category
        orders_count = Order.objects.filter(
            delay_reason__category=category,
            delay_reason_reported_at__isnull=False
        )
        if user_branch:
            orders_count = orders_count.filter(branch=user_branch)
        if start_date:
            orders_count = orders_count.filter(delay_reason_reported_at__gte=start_date)
        if selected_user:
            orders_count = orders_count.filter(delay_reason_reported_by__id=selected_user)
        if selected_order_type:
            orders_count = orders_count.filter(type=selected_order_type)
        
        count = orders_count.distinct().count()
        if count > 0:
            data.append({
                'category': category.category,
                'category_name': _get_category_display(category.category),
                'count': count,
            })
    
    # Sort by count descending
    data.sort(key=lambda x: x['count'], reverse=True)
    total = sum(item['count'] for item in data)
    
    # Calculate percentages
    for item in data:
        item['percentage'] = round(item['count'] / total * 100, 1) if total > 0 else 0
    
    return JsonResponse({
        'success': True,
        'data': data,
        'total': total
    })


@login_required
@require_http_methods(["GET"])
def api_delay_trends(request):
    """API endpoint for delay trends over time - Query from Order table with delay_reason"""
    user_branch = get_user_branch(request.user)

    time_period = request.GET.get('period', '30days')
    start_date = _get_start_date_from_period(time_period)
    selected_category = request.GET.get('category', '')
    selected_user = request.GET.get('user', '')
    selected_order_type = request.GET.get('order_type', '')

    # FIX: Query orders with delay_reason directly
    orders_qs = Order.objects.filter(
        delay_reason__isnull=False,
        delay_reason_reported_at__isnull=False
    )
    
    if user_branch:
        orders_qs = orders_qs.filter(branch=user_branch)
    
    if start_date:
        orders_qs = orders_qs.filter(delay_reason_reported_at__gte=start_date)
    
    if selected_category:
        orders_qs = orders_qs.filter(delay_reason__category__category=selected_category)
    
    if selected_user:
        orders_qs = orders_qs.filter(delay_reason_reported_by__id=selected_user)
    
    if selected_order_type:
        orders_qs = orders_qs.filter(type=selected_order_type)
    
    # Group by date
    daily_delays = orders_qs.annotate(
        date=TruncDate('delay_reason_reported_at')
    ).values('date').annotate(
        count=Count('id', distinct=True),
        exceeded_9h=Count('id', filter=Q(exceeded_9_hours=True), distinct=True)
    ).order_by('date')
    
    # Also get total orders per day for context
    if user_branch:
        all_orders_daily = Order.objects.filter(branch=user_branch, status='completed')
    else:
        all_orders_daily = Order.objects.filter(status='completed')
    
    if start_date:
        all_orders_daily = all_orders_daily.filter(completed_at__gte=start_date)
    
    all_daily = all_orders_daily.annotate(
        date=TruncDate('completed_at')
    ).values('date').annotate(
        total=Count('id', distinct=True)
    ).order_by('date')
    
    all_daily_dict = {item['date']: item['total'] for item in all_daily}
    
    data = []
    for item in daily_delays:
        date_str = item['date'].strftime('%Y-%m-%d') if item['date'] else 'Unknown'
        total_day = all_daily_dict.get(item['date'], 0)
        data.append({
            'date': date_str,
            'delayed_count': item['count'],
            'exceeded_9h': item['exceeded_9h'],
            'total_orders': total_day,
            'delay_rate': round(item['count'] / total_day * 100, 1) if total_day > 0 else 0,
        })
    
    return JsonResponse({
        'success': True,
        'data': data
    })


@login_required
@require_http_methods(["GET"])
def api_delay_by_order_type(request):
    """API endpoint for delay breakdown by order type - Query from Order table"""
    user_branch = get_user_branch(request.user)

    time_period = request.GET.get('period', '30days')
    start_date = _get_start_date_from_period(time_period)
    selected_category = request.GET.get('category', '')
    selected_user = request.GET.get('user', '')
    selected_order_type = request.GET.get('order_type', '')

    # FIX: Query orders with delay_reason directly
    orders_qs = Order.objects.filter(
        delay_reason__isnull=False,
        delay_reason_reported_at__isnull=False
    )
    
    if user_branch:
        orders_qs = orders_qs.filter(branch=user_branch)
    
    if start_date:
        orders_qs = orders_qs.filter(delay_reason_reported_at__gte=start_date)
    
    if selected_category:
        orders_qs = orders_qs.filter(delay_reason__category__category=selected_category)
    
    if selected_user:
        orders_qs = orders_qs.filter(delay_reason_reported_by__id=selected_user)
    
    if selected_order_type:
        orders_qs = orders_qs.filter(type=selected_order_type)
    
    # Breakdown by order type
    type_breakdown = orders_qs.values('type').annotate(
        count=Count('id', distinct=True),
        percentage=Cast(Count('id', distinct=True) * 100.0 / orders_qs.count(), FloatField())
    ).order_by('-count')
    
    data = []
    for item in type_breakdown:
        order_type_display = dict(Order.TYPE_CHOICES).get(item['type'], item['type'])
        data.append({
            'type': item['type'],
            'type_name': order_type_display,
            'count': item['count'],
            'percentage': round(item['percentage'], 1),
        })
    
    return JsonResponse({
        'success': True,
        'data': data
    })


@login_required
@require_http_methods(["GET"])
def api_delay_by_user(request):
    """API endpoint for delay breakdown by user/team member - Query from Order table"""
    user_branch = get_user_branch(request.user)

    time_period = request.GET.get('period', '30days')
    start_date = _get_start_date_from_period(time_period)
    selected_category = request.GET.get('category', '')
    selected_user = request.GET.get('user', '')
    selected_order_type = request.GET.get('order_type', '')

    # FIX: Query orders with delay_reason directly
    orders_qs = Order.objects.filter(
        delay_reason__isnull=False,
        delay_reason_reported_at__isnull=False,
        delay_reason_reported_by__isnull=False
    )
    
    if user_branch:
        orders_qs = orders_qs.filter(branch=user_branch)
    
    if start_date:
        orders_qs = orders_qs.filter(delay_reason_reported_at__gte=start_date)
    
    if selected_category:
        orders_qs = orders_qs.filter(delay_reason__category__category=selected_category)
    
    if selected_user:
        orders_qs = orders_qs.filter(delay_reason_reported_by__id=selected_user)
    
    if selected_order_type:
        orders_qs = orders_qs.filter(type=selected_order_type)
    
    # Breakdown by user
    user_breakdown = orders_qs.values(
        'delay_reason_reported_by__id',
        'delay_reason_reported_by__first_name',
        'delay_reason_reported_by__last_name',
        'delay_reason_reported_by__username'
    ).annotate(
        count=Count('id', distinct=True),
        exceeded_2h_count=Count('id', filter=Q(exceeded_9_hours=True), distinct=True)
    ).order_by('-count')
    
    data = []
    for item in user_breakdown:
        first_name = item['delay_reason_reported_by__first_name'] or ''
        last_name = item['delay_reason_reported_by__last_name'] or ''
        username = item['delay_reason_reported_by__username'] or ''
        user_name = f"{first_name} {last_name}".strip() or username
        
        data.append({
            'user_id': item['delay_reason_reported_by__id'],
            'user_name': user_name,
            'delay_count': item['count'],
            'exceeded_2h_count': item['exceeded_2h_count'],
        })
    
    return JsonResponse({
        'success': True,
        'data': data
    })


@login_required
@require_http_methods(["GET"])
def api_delay_impact_analysis(request):
    """API endpoint for delay impact analysis (revenue, time, customer impact)"""
    user_branch = get_user_branch(request.user)

    time_period = request.GET.get('period', '30days')
    start_date = _get_start_date_from_period(time_period)

    # FIX: Query orders with delay_reason directly
    orders_qs = Order.objects.filter(
        delay_reason__isnull=False,
        delay_reason_reported_at__isnull=False
    )
    
    if user_branch:
        orders_qs = orders_qs.filter(branch=user_branch)
    
    if start_date:
        orders_qs = orders_qs.filter(delay_reason_reported_at__gte=start_date)
    
    # Calculate impact metrics
    total_delayed_hours = 0
    total_revenue_at_risk = Decimal('0')
    
    for order in orders_qs.filter(started_at__isnull=False, completed_at__isnull=False):
        duration = (order.completed_at - order.started_at).total_seconds() / 3600
        if duration > 9:
            total_delayed_hours += (duration - 9)
        
        # Rough revenue estimate from invoices
        invoices = order.invoices.all()
        for invoice in invoices:
            if invoice.total_amount:
                total_revenue_at_risk += invoice.total_amount
    
    # Get repeat delay customers
    customers_with_delays = orders_qs.values('customer').annotate(
        delay_count=Count('id', distinct=True)
    ).filter(delay_count__gte=2).count()
    
    # Get most problematic reasons by impact
    reason_impact_raw = orders_qs.values(
        'delay_reason__reason_text',
        'delay_reason__category__category'
    ).annotate(
        count=Count('id', distinct=True),
        affected_customers=Count('customer', distinct=True)
    ).order_by('-count')[:5]

    reason_impact = []
    for item in reason_impact_raw:
        reason_impact.append({
            'delay_reason__reason_text': item['delay_reason__reason_text'],
            'delay_reason__category__category': item['delay_reason__category__category'],
            'delay_reason__category__get_category_display': _get_category_display(item['delay_reason__category__category']),
            'count': item['count'],
            'affected_customers': item['affected_customers'],
        })

    return JsonResponse({
        'success': True,
        'impact': {
            'total_delayed_hours': round(total_delayed_hours, 1),
            'estimated_revenue_impact': str(total_revenue_at_risk),
            'customers_with_repeat_delays': customers_with_delays,
            'total_unique_customers_affected': orders_qs.values('customer').distinct().count(),
        },
        'reason_impact': reason_impact
    })


@login_required
@require_http_methods(["GET"])
def api_delay_recommendations(request):
    """API endpoint for AI-generated recommendations based on delay patterns"""
    user_branch = get_user_branch(request.user)

    time_period = request.GET.get('period', '30days')
    start_date = _get_start_date_from_period(time_period)

    # FIX: Query orders with delay_reason directly
    orders_qs = Order.objects.filter(
        delay_reason__isnull=False,
        delay_reason_reported_at__isnull=False
    )
    
    if user_branch:
        orders_qs = orders_qs.filter(branch=user_branch)
    
    if start_date:
        orders_qs = orders_qs.filter(delay_reason_reported_at__gte=start_date)
    
    recommendations = []
    
    # Analysis 1: Most common category
    category_counts = orders_qs.values(
        'delay_reason__category__category'
    ).annotate(count=Count('id', distinct=True)).order_by('-count')

    if category_counts.exists():
        top_cat = category_counts[0]
        if top_cat['count'] > orders_qs.count() * 0.3:
            category_display = _get_category_display(top_cat['delay_reason__category__category'])
            recommendations.append({
                'priority': 'high',
                'category': 'Process Improvement',
                'title': f"Address {category_display} Issues",
                'description': f"{category_display} accounts for {round(top_cat['count'] / orders_qs.count() * 100, 1)}% of delays. Consider process improvements or resource allocation.",
                'impact': 'high'
            })
    
    # Analysis 2: Orders exceeding 2 hours threshold
    exceeded_count = orders_qs.filter(exceeded_9_hours=True).count()
    if exceeded_count > 0 and orders_qs.count() > 0:
        pct = (exceeded_count / orders_qs.count()) * 100
        priority = 'high' if pct > 20 else 'medium'
        recommendations.append({
            'priority': priority,
            'category': 'Urgent',
            'title': f"{pct:.1f}% of Delays Exceed 2 Hours",
            'description': f"{exceeded_count} orders exceeded 2 hours. Implement preventive measures to reduce critical delays.",
            'impact': 'critical'
        })
    
    # Analysis 3: Specific problematic reasons
    top_reasons = orders_qs.values('delay_reason__reason_text').annotate(
        count=Count('id', distinct=True)
    ).order_by('-count')[:3]
    
    for reason in top_reasons:
        recommendations.append({
            'priority': 'medium',
            'category': 'Root Cause Analysis',
            'title': f"Investigate: {reason['delay_reason__reason_text']}",
            'description': f"This reason accounts for {reason['count']} delay incidents. Consider root cause analysis and preventive actions.",
            'impact': 'medium'
        })
    
    # Analysis 4: Delay rate trend
    daily_rates = orders_qs.annotate(
        date=TruncDate('delay_reason_reported_at')
    ).values('date').annotate(count=Count('id', distinct=True)).order_by('-date')[:7]
    
    if daily_rates.exists():
        recent_avg = sum(item['count'] for item in daily_rates) / len(list(daily_rates))
        if recent_avg > 2:
            recommendations.append({
                'priority': 'high',
                'category': 'Trend',
                'title': 'Increasing Delay Incidents',
                'description': f"Recent average of {recent_avg:.1f} delays per day. Escalating trend detected. Immediate action recommended.",
                'impact': 'high'
            })
    
    # Sort by priority
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
    
    return JsonResponse({
        'success': True,
        'recommendations': recommendations[:8]  # Return top 8 recommendations
    })


@login_required
@require_http_methods(["GET"])
def api_all_delay_reasons(request):
    """API endpoint to fetch all delay reasons from database with their submission counts - Query from Order table"""
    user_branch = get_user_branch(request.user)

    time_period = request.GET.get('period', '30days')
    selected_category = request.GET.get('category', '')
    selected_user = request.GET.get('user', '')
    selected_order_type = request.GET.get('order_type', '')

    start_date = _get_start_date_from_period(time_period)

    # FIX: Query orders with delay_reason directly
    orders_qs = Order.objects.filter(
        delay_reason__isnull=False,
        delay_reason_reported_at__isnull=False
    )
    
    if user_branch:
        orders_qs = orders_qs.filter(branch=user_branch)
    
    if start_date:
        orders_qs = orders_qs.filter(delay_reason_reported_at__gte=start_date)
    
    if selected_category:
        orders_qs = orders_qs.filter(delay_reason__category__category=selected_category)
    
    if selected_user:
        orders_qs = orders_qs.filter(delay_reason_reported_by__id=selected_user)
    
    if selected_order_type:
        orders_qs = orders_qs.filter(type=selected_order_type)

    # Get all unique delay reasons submitted
    total_delayed = orders_qs.count()

    if total_delayed == 0:
        return JsonResponse({
            'success': True,
            'data': [],
            'total': 0,
            'message': 'No delay reasons submitted in the selected period.'
        })

    # Get all delay reasons with counts
    all_reasons = orders_qs.values(
        'delay_reason__id',
        'delay_reason__reason_text',
        'delay_reason__category__category'
    ).annotate(
        count=Count('id', distinct=True),
        percentage=Cast(Count('id', distinct=True) * 100.0 / total_delayed, FloatField())
    ).order_by('-count')

    data = []
    for item in all_reasons:
        data.append({
            'id': item['delay_reason__id'],
            'reason_text': item['delay_reason__reason_text'],
            'category': item['delay_reason__category__category'],
            'category_name': _get_category_display(item['delay_reason__category__category']),
            'count': item['count'],
            'percentage': round(item['percentage'], 1),
        })

    return JsonResponse({
        'success': True,
        'data': data,
        'total': total_delayed,
        'message': f'Showing {len(data)} unique delay reasons from {total_delayed} submitted.'
    })


def _get_start_date_from_period(period):
    """Convert period string to start date"""
    now = timezone.now()

    period_map = {
        '7days': now - timedelta(days=7),
        '30days': now - timedelta(days=30),
        '90days': now - timedelta(days=90),
        '6months': now - timedelta(days=180),
        '1year': now - timedelta(days=365),
        'all': None,
    }

    return period_map.get(period, now - timedelta(days=30))
