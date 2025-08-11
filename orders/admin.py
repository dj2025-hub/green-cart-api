from django.contrib import admin
from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ['product', 'producer']


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    raw_id_fields = ['changed_by']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'consumer', 'status', 'total_amount',
        'order_date', 'delivery_date'
    ]
    list_filter = [
        'status', 'order_date', 'delivery_date',
        'consumer__user_type'
    ]
    search_fields = [
        'order_number', 'consumer__email', 
        'consumer__first_name', 'consumer__last_name'
    ]
    raw_id_fields = ['consumer']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('order_number', 'consumer', 'status')
        }),
        ('Livraison', {
            'fields': (
                'delivery_address', 'delivery_city', 'delivery_postal_code',
                'delivery_date'
            )
        }),
        ('Dates', {
            'fields': (
                'order_date', 'confirmed_at', 'shipped_at', 'delivered_at'
            )
        }),
        ('Montant', {
            'fields': ('total_amount',)
        }),
        ('Notes', {
            'fields': ('notes', 'consumer_notes')
        }),
    )
    
    readonly_fields = ['order_number', 'order_date', 'total_amount']
    
    def total_amount_display(self, obj):
        return f"{obj.total_amount}€"
    total_amount_display.short_description = 'Total'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'product', 'producer', 'quantity', 
        'unit_price', 'total_price'
    ]
    list_filter = [
        'order__status', 'producer__region',
        'product__category', 'created_at'
    ]
    search_fields = [
        'order__order_number', 'product__name',
        'producer__business_name'
    ]
    raw_id_fields = ['order', 'product', 'producer']


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'old_status', 'new_status', 
        'changed_by', 'changed_at'
    ]
    list_filter = ['old_status', 'new_status', 'changed_at']
    search_fields = [
        'order__order_number', 'changed_by__email',
        'reason'
    ]
    raw_id_fields = ['order', 'changed_by']