from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Comment, CommentReport


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Administration des commentaires."""
    
    list_display = [
        'id', 'product_link', 'user_info', 'rating_display', 
        'comment_preview', 'created_at', 'updated_at'
    ]
    list_filter = [
        'rating', 'created_at', 'updated_at', 'product__category',
        'user__user_type'
    ]
    search_fields = [
        'comment', 'user__email', 'user__first_name', 
        'user__last_name', 'product__name'
    ]
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('product', 'user', 'rating', 'comment')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def product_link(self, obj):
        """Lien vers le produit."""
        if obj.product:
            url = reverse('admin:products_product_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    product_link.short_description = 'Produit'
    product_link.admin_order_field = 'product__name'
    
    def user_info(self, obj):
        """Informations sur l'utilisateur."""
        if obj.user:
            url = reverse('admin:accounts_user_change', args=[obj.user.id])
            return format_html(
                '<a href="{}">{} ({})</a>', 
                url, 
                obj.user.email, 
                obj.user.get_user_type_display()
            )
        return '-'
    user_info.short_description = 'Utilisateur'
    user_info.admin_order_field = 'user__email'
    
    def rating_display(self, obj):
        """Affichage du rating avec étoiles."""
        stars = '★' * int(obj.rating) + '☆' * (5 - int(obj.rating))
        if obj.rating % 1 != 0:
            stars = stars[:-1] + '★'
        return format_html(
            '<span style="color: #FFD700; font-size: 16px;">{}</span> {}',
            stars, obj.rating
        )
    rating_display.short_description = 'Note'
    rating_display.admin_order_field = 'rating'
    
    def comment_preview(self, obj):
        """Aperçu du commentaire."""
        preview = obj.comment[:100] + '...' if len(obj.comment) > 100 else obj.comment
        return format_html('<span title="{}">{}</span>', obj.comment, preview)
    comment_preview.short_description = 'Commentaire'
    
    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related."""
        return super().get_queryset(request).select_related('user', 'product')


@admin.register(CommentReport)
class CommentReportAdmin(admin.ModelAdmin):
    """Administration des signalements de commentaires."""
    
    list_display = [
        'id', 'comment_preview', 'reporter_info', 'reason_display',
        'is_resolved', 'created_at'
    ]
    list_filter = [
        'reason', 'is_resolved', 'created_at', 'reporter__user_type'
    ]
    search_fields = [
        'comment__comment', 'reporter__email', 'description'
    ]
    readonly_fields = ['created_at']
    list_per_page = 25
    date_hierarchy = 'created_at'
    actions = ['mark_as_resolved', 'mark_as_unresolved']
    
    fieldsets = (
        ('Signalement', {
            'fields': ('comment', 'reporter', 'reason', 'description')
        }),
        ('Statut', {
            'fields': ('is_resolved',)
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def comment_preview(self, obj):
        """Aperçu du commentaire signalé."""
        if obj.comment:
            preview = obj.comment.comment[:80] + '...' if len(obj.comment.comment) > 80 else obj.comment.comment
            url = reverse('admin:comments_comment_change', args=[obj.comment.id])
            return format_html(
                '<a href="{}" title="{}">{}</a>', 
                url, obj.comment.comment, preview
            )
        return '-'
    comment_preview.short_description = 'Commentaire signalé'
    
    def reporter_info(self, obj):
        """Informations sur l'utilisateur signalant."""
        if obj.reporter:
            url = reverse('admin:accounts_user_change', args=[obj.reporter.id])
            return format_html(
                '<a href="{}">{} ({})</a>', 
                url, 
                obj.reporter.email, 
                obj.reporter.get_user_type_display()
            )
        return '-'
    reporter_info.short_description = 'Utilisateur signalant'
    reporter_info.admin_order_field = 'reporter__email'
    
    def reason_display(self, obj):
        """Affichage de la raison avec couleur."""
        colors = {
            'inappropriate': '#FF6B6B',
            'spam': '#FFA500',
            'offensive': '#FF0000',
            'fake': '#8B0000',
            'other': '#6B6B6B'
        }
        color = colors.get(obj.reason, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_reason_display()
        )
    reason_display.short_description = 'Raison'
    reason_display.admin_order_field = 'reason'
    
    def mark_as_resolved(self, request, queryset):
        """Marquer les signalements comme résolus."""
        updated = queryset.update(is_resolved=True)
        self.message_user(
            request, 
            f'{updated} signalement(s) marqué(s) comme résolu(s).'
        )
    mark_as_resolved.short_description = 'Marquer comme résolu'
    
    def mark_as_unresolved(self, request, queryset):
        """Marquer les signalements comme non résolus."""
        updated = queryset.update(is_resolved=False)
        self.message_user(
            request, 
            f'{updated} signalement(s) marqué(s) comme non résolu(s).'
        )
    mark_as_unresolved.short_description = 'Marquer comme non résolu'
    
    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related."""
        return super().get_queryset(request).select_related('comment', 'reporter')
