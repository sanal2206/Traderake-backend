# core/serializers.py
from rest_framework import serializers
from core.models import Exchange, Index, Sector, Stock, MutualFund, Watchlist, WatchlistItem

class ExchangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exchange
        fields = "__all__"


class IndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = Index
        fields = "__all__"


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = "__all__"


class StockSerializer(serializers.ModelSerializer):
    exchange = ExchangeSerializer()
    sector = SectorSerializer()
    index = IndexSerializer()

    price_difference = serializers.SerializerMethodField()
    price_difference_percentage = serializers.SerializerMethodField()
    watchlist_status = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = "__all__"

    def get_price_difference(self, obj):
        return obj.price_difference()

    def get_price_difference_percentage(self, obj):
        return obj.price_difference_percentage()

    def get_watchlist_status(self, obj):
        user = self.context.get("user")
        if not user or user.is_anonymous:
            return False
        return WatchlistItem.objects.filter(
            watchlist__user=user,
            content_type__model="stock",
            object_id=obj.id
        ).exists()


class MutualFundSerializer(serializers.ModelSerializer):
    watchlist_status = serializers.SerializerMethodField()

    class Meta:
        model = MutualFund
        fields = "__all__"

    def get_watchlist_status(self, obj):
        user = self.context.get("user")
        if not user or user.is_anonymous:
            return False
        return WatchlistItem.objects.filter(
            watchlist__user=user,
            content_type__model="mutualfund",
            object_id=obj.id
        ).exists()


class GenericAssetRelatedField(serializers.RelatedField):
    """Handles GenericForeignKey for assets"""
    def to_representation(self, value):
        if isinstance(value, Stock):
            return StockSerializer(value, context=self.context).data
        elif isinstance(value, MutualFund):
            return MutualFundSerializer(value, context=self.context).data
        elif isinstance(value, Index):
            return IndexSerializer(value).data
        return str(value)


class WatchlistItemSerializer(serializers.ModelSerializer):
    asset = GenericAssetRelatedField(read_only=True)

    class Meta:
        model = WatchlistItem
        fields = ["id", "asset", "created_at", "is_block"]


class WatchlistSerializer(serializers.ModelSerializer):
    items = WatchlistItemSerializer(many=True)

    class Meta:
        model = Watchlist
        fields = ["id", "name", "created_at", "items"]
