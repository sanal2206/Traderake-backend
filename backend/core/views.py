from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.core.cache import cache
from core.models import Stock, Index, MutualFund, Watchlist,WatchlistItem
from core.serializers import StockSerializer, IndexSerializer, MutualFundSerializer, WatchlistSerializer
from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

 

CACHE_TIMEOUT = 60  # seconds


class MarketDataGroupedAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_cached_or_fetch(self, cache_key, fetch_func):
        """Try cache, if miss fetch from DB and update cache."""
        data = cache.get(cache_key)
        if data is not None:
            return data

        # Cache miss: fetch fresh data
        data = fetch_func()

        # Store serialized data in cache asynchronously in production, but here do immediately
        cache.set(cache_key, data, timeout=CACHE_TIMEOUT)
        return data

    def get(self, request, *args, **kwargs):
        user = request.user if request.user.is_authenticated else None
        data_types = request.query_params.get("data_type", "indian_stocks")
        requested_types = [t.strip() for t in data_types.split(",")]

        response_data = {}

        if "indian_stocks" in requested_types:
            response_data["indian_stocks"] = self.get_cached_or_fetch(
                "indian_stocks",
                lambda: StockSerializer(
                    Stock.objects.filter(exchange__country="India"),
                    many=True,
                    context={"user": user}
                ).data
            )

        if "us_stocks" in requested_types:
            response_data["us_stocks"] = self.get_cached_or_fetch(
                "us_stocks",
                lambda: StockSerializer(
                    Stock.objects.filter(exchange__country="USA"),
                    many=True,
                    context={"user": user}
                ).data
            )

        if "indian_indexes" in requested_types:
            response_data["indian_indexes"] = self.get_cached_or_fetch(
                "indian_indexes",
                lambda: IndexSerializer(
                    Index.objects.filter(name__icontains="India"),
                    many=True
                ).data
            )

        if "global_indexes" in requested_types:
            response_data["global_indexes"] = self.get_cached_or_fetch(
                "global_indexes",
                lambda: IndexSerializer(
                    Index.objects.exclude(name__icontains="India"),
                    many=True
                ).data
            )

        if "mutual_funds" in requested_types:
            response_data["mutual_funds"] = self.get_cached_or_fetch(
                "mutual_funds",
                lambda: MutualFundSerializer(
                    MutualFund.objects.all(),
                    many=True,
                    context={"user": user}
                ).data
            )

        if "watchlists" in requested_types and user:
            # For watchlists, cache per user key
            cache_key = f"watchlists_user_{user.id}"
            response_data["watchlists"] = self.get_cached_or_fetch(
                cache_key,
                lambda: WatchlistSerializer(
                    Watchlist.objects.filter(user=user),
                    many=True,
                    context={"user": user}
                ).data
            )
        elif "watchlists" in requested_types:
            # no user => empty list
            response_data["watchlists"] = []

        return Response(response_data)

 


class AddAssetToWatchlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        watchlist_id = request.data.get("watchlist_id")
        asset_type = request.data.get("asset_type")  # e.g., 'stock', 'mutualfund', 'index'
        asset_id = request.data.get("asset_id")

        if not all([watchlist_id, asset_type, asset_id]):
            return Response(
                {"error": "watchlist_id, asset_type, and asset_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate watchlist ownership
        try:
            watchlist = Watchlist.objects.get(id=watchlist_id, user=user)
        except Watchlist.DoesNotExist:
            return Response({"error": "Watchlist not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

        # Validate content type
        try:
            content_type = ContentType.objects.get(model=asset_type.lower())
        except ContentType.DoesNotExist:
            return Response({"error": f"Invalid asset_type '{asset_type}'."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate asset existence
        model_class = content_type.model_class()
        try:
            asset_instance = model_class.objects.get(id=asset_id)
        except model_class.DoesNotExist:
            return Response({"error": f"{asset_type} with id {asset_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if already added
        exists = WatchlistItem.objects.filter(
            watchlist=watchlist,
            content_type=content_type,
            object_id=asset_id,
        ).exists()

        if exists:
            return Response({"message": "Asset already in watchlist."}, status=status.HTTP_200_OK)

        # Create watchlist item
        WatchlistItem.objects.create(
            watchlist=watchlist,
            content_type=content_type,
            object_id=asset_id,
        )

        return Response({"message": "Asset added to watchlist."}, status=status.HTTP_201_CREATED)
