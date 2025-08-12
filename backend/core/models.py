from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Exchange(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or "Unknown Exchange"



class Index(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)  # e.g., India, USA
    currency = models.CharField(max_length=10, blank=True, null=True)  # e.g., INR, USD, GBP
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_block = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.symbol or 'N/A'})"


class Sector(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_block = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Stock(models.Model):
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    last_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    previous_close_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=10, blank=True, null=True)
    sector = models.ForeignKey(Sector, on_delete=models.SET_NULL, null=True, blank=True)
    index = models.ForeignKey(Index, on_delete=models.SET_NULL, null=True, blank=True)
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE, null=True, blank=True)
    price_updated_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_block = models.BooleanField(default=False)

    def price_difference(self):
        if self.last_price is not None and self.previous_close_price is not None:
            return self.last_price - self.previous_close_price
        return None

    def price_difference_percentage(self):
        if self.previous_close_price and self.previous_close_price != 0:
            return ((self.last_price - self.previous_close_price) / self.previous_close_price) * 100
        return None

    def __str__(self):
        return f"{self.symbol} - {self.name or 'Unknown'}"


class MutualFund(models.Model):
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=100, blank=True, null=True)
    nav = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return self.name


class Watchlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100,default='my_watchlist')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_block = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.user.username})"


class WatchlistItem(models.Model):
    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, related_name='items')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    asset = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(default=timezone.now)
    is_block = models.BooleanField(default=False)

    class Meta:
        unique_together = (('watchlist', 'content_type', 'object_id'),)

    def __str__(self):
        asset_type = self.content_type.model
        return f"{asset_type.capitalize()} - {self.asset} in {self.watchlist.name}"
