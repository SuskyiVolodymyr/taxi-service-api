from celery import shared_task
from datetime import date

from payment.models import Payment
from taxi.models import Order
from taxi.telegram_helper import send_message


@shared_task
def check_daily_profit() -> None:
    today = date.today()
    paid_payments = Payment.objects.filter(
        order__date_created__day=today.day,
        status=Payment.StatusEnum.paid,
    )

    if paid_payments.exists():
        profit = 0
        for payment in paid_payments:
            profit += round(payment.money_to_pay, 2)
        message = f"Daily profit: {profit}"
        send_message(message)
    else:
        send_message("No profit today!")
