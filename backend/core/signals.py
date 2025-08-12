from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import CustomUser
from core.models import Watchlist

@receiver(post_save,sender=CustomUser)
def create_user_watchlist(sender,instance,created,**kwargs):
    if created:
        Watchlist.objects.create(user=instance,name='my_watchlist')
