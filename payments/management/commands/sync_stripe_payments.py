"""
Management command to sync payments with Stripe.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import stripe
from payments.models import Payment
from payments.stripe_client import StripeClient
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync payment statuses with Stripe'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back for payments to sync (default: 7)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Get payments from the last N days that might need syncing
        cutoff_date = timezone.now() - timedelta(days=days)
        payments_to_sync = Payment.objects.filter(
            created_at__gte=cutoff_date,
            status__in=['PENDING', 'PROCESSING']
        )
        
        self.stdout.write(
            f"Found {payments_to_sync.count()} payments to sync from the last {days} days"
        )
        
        updated_count = 0
        error_count = 0
        
        for payment in payments_to_sync:
            try:
                # Retrieve current status from Stripe
                payment_intent = StripeClient.retrieve_payment_intent(
                    payment.stripe_payment_intent_id
                )
                
                old_status = payment.status
                new_status = self._map_stripe_status(payment_intent.status)
                
                if old_status != new_status:
                    if not dry_run:
                        payment.status = new_status
                        if new_status == 'SUCCEEDED':
                            payment.mark_as_succeeded()
                            # Also confirm the order if needed
                            if payment.order.status == 'PENDING':
                                payment.order.confirm()
                        elif new_status == 'FAILED':
                            failure_reason = ''
                            if hasattr(payment_intent, 'last_payment_error') and payment_intent.last_payment_error:
                                failure_reason = payment_intent.last_payment_error.get('message', '')
                            payment.mark_as_failed(failure_reason)
                        else:
                            payment.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{'[DRY RUN] ' if dry_run else ''}Updated payment {payment.id}: "
                            f"{old_status} -> {new_status}"
                        )
                    )
                    updated_count += 1
                
            except stripe.error.StripeError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Stripe error for payment {payment.id}: {e}"
                    )
                )
                error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error syncing payment {payment.id}: {e}"
                    )
                )
                error_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Sync complete. Updated: {updated_count}, Errors: {error_count}"
            )
        )
    
    def _map_stripe_status(self, stripe_status):
        """Map Stripe payment intent status to our payment status."""
        status_map = {
            'requires_payment_method': 'PENDING',
            'requires_confirmation': 'PENDING',
            'requires_action': 'PENDING',
            'processing': 'PROCESSING',
            'requires_capture': 'PROCESSING',
            'canceled': 'CANCELLED',
            'succeeded': 'SUCCEEDED',
        }
        return status_map.get(stripe_status, 'PENDING')
