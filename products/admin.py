from django.contrib import admin
from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'producer', 'category', 'price', 'unit',
        'quantity_available', 'is_active', 'expiry_date'
    ]
    list_filter = [
        'category', 'is_active', 'is_organic', 'is_local', 
        'producer__region', 'created_at'
    ]
    search_fields = ['name', 'description', 'producer__business_name']
    raw_id_fields = ['producer']
    inlines = [ProductImageInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('producer', 'category', 'name', 'description')
        }),
        ('Prix et stock', {
            'fields': ('price', 'unit', 'quantity_available')
        }),
        ('Dates', {
            'fields': ('expiry_date', 'harvest_date')
        }),
        ('Caractéristiques', {
            'fields': ('is_organic', 'is_local', 'is_active')
        }),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'order', 'created_at']
    list_filter = ['created_at']
    raw_id_fields = ['product']