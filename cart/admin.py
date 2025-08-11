from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    raw_id_fields = ['product']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['consumer', 'total_items', 'total_amount', 'updated_at']
    search_fields = ['consumer__email', 'consumer__first_name', 'consumer__last_name']
    raw_id_fields = ['consumer']
    inlines = [CartItemInline]
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Articles'
    
    def total_amount(self, obj):
        return f"{obj.total_amount}€"
    total_amount.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'price_at_time', 'total_price']
    list_filter = ['created_at', 'product__category']
    search_fields = [
        'cart__consumer__email', 
        'product__name',
        'product__producer__business_name'
    ]
    raw_id_fields = ['cart', 'product']
    
    def total_price(self, obj):
        return f"{obj.total_price}€"
    total_price.short_description = 'Prix total'