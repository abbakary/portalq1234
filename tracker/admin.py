from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.db import models
from .models import Customer, Vehicle, Order, InventoryItem, Branch, ServiceType, ServiceAddon, LabourCode, DelayReasonCategory, DelayReason, Salesperson, Invoice, InvoiceLineItem, Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    fields = ('branch', 'photo')
    extra = 0

class CustomUserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_superuser', 'get_branch', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__branch')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_branch(self, obj):
        try:
            return obj.profile.branch if obj.profile.branch else '—'
        except Profile.DoesNotExist:
            return '—'
    get_branch.short_description = 'Branch'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("code", "full_name", "phone", "customer_type", "total_visits", "last_visit", "branch")
    search_fields = ("code", "full_name", "phone", "email")
    list_filter = ("customer_type", "current_status", "branch")
    autocomplete_fields = ('branch',)

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "customer", "make", "model")
    search_fields = ("plate_number", "make", "model")

@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "estimated_minutes", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(ServiceAddon)
class ServiceAddonAdmin(admin.ModelAdmin):
    list_display = ("name", "estimated_minutes", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "customer", "type", "status", "priority", "created_at", "started_at", "completed_at", "cancelled_at", "signed_by", "branch")
    search_fields = ("order_number", "customer__full_name")
    list_filter = ("type", "status", "priority", "signed_by", "completed_at", "cancelled_at", "branch")
    readonly_fields = ("order_number", "created_at", "started_at", "completed_at", "cancelled_at", "signed_at")
    autocomplete_fields = ('branch',)

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            ('Basic Information', {
                'fields': ('order_number', 'branch', 'customer', 'vehicle', 'type', 'priority'),
                'classes': ('wide', 'extrapretty'),
            }),
            ('Status & Progress', {
                'fields': ('status', 'description'),
                'classes': ('wide', 'extrapretty'),
            }),
        )

        # Add type-specific fields
        if obj and obj.type == 'service':
            fieldsets += (
                ('Service Details', {
                    'fields': ('item_name', 'brand', 'quantity', 'tire_type'),
                    'classes': ('wide', 'extrapretty'),
                }),
            )
        elif obj and obj.type == 'sales':
            fieldsets += (
                ('Sales Details', {
                    'fields': ('item_name', 'brand', 'quantity'),
                    'classes': ('wide', 'extrapretty'),
                }),
            )
        elif obj and obj.type == 'inquiry':
            fieldsets += (
                ('Consultation Details', {
                    'fields': ('inquiry_type', 'questions', 'contact_preference', 'follow_up_date'),
                    'classes': ('wide', 'extrapretty'),
                }),
            )

        fieldsets += (
            ('Assignment', {
                'fields': ('assigned_to',),
                'classes': ('wide', 'extrapretty'),
            }),
            ('Timestamps', {
                'fields': ('created_at', 'started_at', 'completed_at', 'cancelled_at'),
                'classes': ('wide', 'extrapretty'),
            }),
        )

        # Show completion fields only when completed
        if obj and obj.status == 'completed':
            fieldsets += (
                ('Completion & Signature', {
                    'fields': ('signature_file', 'completion_attachment', 'signed_by', 'signed_at'),
                    'classes': ('wide', 'extrapretty'),
                }),
            )

        # Show cancellation reason only when cancelled
        if obj and obj.status == 'cancelled':
            fieldsets += (
                ('Cancellation', {
                    'fields': ('cancellation_reason',),
                    'classes': ('wide', 'extrapretty'),
                }),
            )

        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            # Make certain fields readonly based on status
            if obj.status in ['completed', 'cancelled']:
                readonly_fields = ['status', 'type', 'priority', 'description']
                for field in readonly_fields:
                    if field in form.base_fields:
                        form.base_fields[field].disabled = True
        return form

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'status':
            obj = kwargs.get('obj')
            if obj:
                current_status = obj.status
                # Define allowed transitions
                transitions = {
                    'created': ['in_progress', 'cancelled'],
                    'in_progress': ['overdue', 'completed', 'cancelled'],
                    'overdue': ['completed', 'cancelled'],
                    'completed': [],  # No further transitions
                    'cancelled': [],  # No further transitions
                }
                allowed_statuses = transitions.get(current_status, [])
                # Always include current status
                allowed_statuses.append(current_status)
                # Get all choices
                all_choices = dict(Order.STATUS_CHOICES)
                # Filter choices
                kwargs['choices'] = [(k, v) for k, v in all_choices.items() if k in allowed_statuses]
            else:
                # For new objects, show only 'created'
                kwargs['choices'] = [('created', 'Start')]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if change:  # Only for existing objects
            old_obj = Order.objects.get(pk=obj.pk)
            if old_obj.status != obj.status:
                # Status changed
                from django.utils import timezone
                if obj.status == 'completed' and not obj.completed_at:
                    obj.completed_at = timezone.now()
                elif obj.status == 'cancelled' and not obj.cancelled_at:
                    obj.cancelled_at = timezone.now()
                elif obj.status == 'in_progress' and not obj.started_at:
                    obj.started_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "quantity", "price", "created_at")
    search_fields = ("name", "brand")
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)

@admin.register(LabourCode)
class LabourCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "description", "category", "is_active", "created_at", "updated_at")
    search_fields = ("code", "description", "category")
    list_filter = ("category", "is_active", "created_at")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ('Labour Code Information', {
            'fields': ('code', 'description', 'category', 'is_active'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'extrapretty'),
        }),
    )

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "region", "parent_display", "branch_type", "is_active", "created_at", "user_count")
    search_fields = ("name", "code", "region")
    list_filter = ("region", "is_active", "parent")
    readonly_fields = ("created_at",)
    fieldsets = (
        ('Branch Information', {
            'fields': ('name', 'code', 'region', 'parent'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Status', {
            'fields': ('is_active',),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('wide', 'extrapretty'),
        }),
    )

    def parent_display(self, obj):
        if obj.parent:
            return f"{obj.parent.name} (Main)"
        return "—"
    parent_display.short_description = 'Parent Branch'

    def branch_type(self, obj):
        if obj.parent:
            return "Sub-Branch"
        return "Main Branch"
    branch_type.short_description = 'Type'

    def user_count(self, obj):
        return obj.profiles.count()
    user_count.short_description = 'Users'

    def get_search_results(self, request, queryset, search_term):
        """Prioritize exact (case-insensitive) name matches for admin autocomplete.
        If the user types the full exact branch name, return that branch as the primary result.
        Otherwise fall back to default behaviour which uses icontains.
        """
        if search_term:
            exact_qs = queryset.filter(name__iexact=search_term)
            if exact_qs.exists():
                return exact_qs, False
        return super().get_search_results(request, queryset, search_term)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Non-superuser staff can only manage their assigned branch and its sub-branches
        user_branch = self._get_user_branch(request.user)
        if user_branch:
            return qs.filter(models.Q(pk=user_branch.pk) | models.Q(parent=user_branch))
        return qs.none()

    def has_add_permission(self, request):
        """Only superusers can add branches."""
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete branches."""
        return request.user.is_superuser

    def _get_user_branch(self, user):
        """Get the user's assigned branch."""
        try:
            return user.profile.branch
        except (Profile.DoesNotExist, AttributeError):
            return None


@admin.register(Salesperson)
class SalespersonAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "is_default", "created_at")
    search_fields = ("code", "name")
    list_filter = ("is_active", "is_default", "created_at")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ('Salesperson Information', {
            'fields': ('code', 'name', 'is_active', 'is_default'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('wide', 'extrapretty'),
        }),
    )

    def get_search_results(self, request, queryset, search_term):
        """Prioritize exact (case-insensitive) code matches for admin autocomplete."""
        if search_term:
            exact_qs = queryset.filter(code__iexact=search_term)
            if exact_qs.exists():
                return exact_qs, False
        return super().get_search_results(request, queryset, search_term)


@admin.register(DelayReasonCategory)
class DelayReasonCategoryAdmin(admin.ModelAdmin):
    list_display = ("get_category_display", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("category",)
    readonly_fields = ("created_at",)

    fieldsets = (
        ('Category Information', {
            'fields': ('category', 'description', 'is_active'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('wide', 'extrapretty'),
        }),
    )


@admin.register(DelayReason)
class DelayReasonAdmin(admin.ModelAdmin):
    list_display = ("reason_text", "category", "is_active", "created_at")
    list_filter = ("category", "is_active", "created_at")
    search_fields = ("reason_text", "category__category")
    readonly_fields = ("created_at",)

    fieldsets = (
        ('Delay Reason Information', {
            'fields': ('category', 'reason_text', 'is_active'),
            'classes': ('wide', 'extrapretty'),
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('wide', 'extrapretty'),
        }),
    )
