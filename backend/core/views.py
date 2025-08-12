from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.core.cache import cache
from core.models import Stock, Index, MutualFund, Watchlist,WatchlistItem
from core.serializers import StockSerializer, IndexSerializer, MutualFundSerializer, WatchlistSerializer
from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from accounts.models import CustomUser

CACHE_TIMEOUT = 60  # seconds


class MarketDataGroupedAPIView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_cached_or_fetch(self, cache_key, fetch_func):
        data = cache.get(cache_key)
        if data is not None:
            return data
        data = fetch_func()
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
                    Index.objects.filter(country__iexact="India"),
                    many=True
                ).data
            )

        if "global_indexes" in requested_types:
            response_data["global_indexes"] = self.get_cached_or_fetch(
                "global_indexes",
                lambda: IndexSerializer(
                    Index.objects.exclude(country__iexact="India"),
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
            response_data["watchlists"] = []

        return Response(response_data)



class AddAssetToWatchlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        asset_type = request.data.get("asset_type")  #e.g., 'stock', 'mutualfund', 'index'
        asset_id = request.data.get("asset_id")

        if not all([asset_type, asset_id]):
            return Response(
                {"error": "asset_type and asset_id are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            watchlist = Watchlist.objects.get(user=user)
        except Watchlist.DoesNotExist:
            return Response(
                {"error": "Watchlist not found. Please contact support."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate content type
        try:
            content_type = ContentType.objects.get(model=asset_type.lower())
        except ContentType.DoesNotExist:
            return Response(
                {"error": f"Invalid asset_type '{asset_type}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate asset existence
        model_class = content_type.model_class()
        try:
            asset_instance = model_class.objects.get(id=asset_id)
        except model_class.DoesNotExist:
            return Response(
                {"error": f"{asset_type} with id {asset_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

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


#fetch from watchlist
class WatchlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        watchlist = Watchlist.objects.filter(user=user).first()

        if not watchlist:
            return Response({"error": "No watchlist found"}, status=404)

        # Fetch grouped items
        stock_ct = ContentType.objects.get_for_model(Stock)
        mf_ct = ContentType.objects.get_for_model(MutualFund)
        index_ct = ContentType.objects.get_for_model(Index)

        stocks = Stock.objects.filter(
            id__in=watchlist.items.filter(content_type=stock_ct).values_list('object_id', flat=True)
        )
        mfs = MutualFund.objects.filter(
            id__in=watchlist.items.filter(content_type=mf_ct).values_list('object_id', flat=True)
        )
        indexes = Index.objects.filter(
            id__in=watchlist.items.filter(content_type=index_ct).values_list('object_id', flat=True)
        )

        return Response({
            "stocks": StockSerializer(stocks, many=True).data,
            "mutual_funds": MutualFundSerializer(mfs, many=True).data,
            "indexes": IndexSerializer(indexes, many=True).data
        })
 


class RemoveAssetFromWatchlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        asset_type = request.data.get('asset_type')
        asset_id = request.data.get('asset_id')

        if not all([asset_id, asset_type]):
            return Response(
                {"error": "asset_type and asset_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            watchlist = Watchlist.objects.get(user=user)
        except Watchlist.DoesNotExist:
            return Response(
                {'error': 'Watchlist not found. Please contact support.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate content type
        try:
            content_type = ContentType.objects.get(model=asset_type.lower())
        except ContentType.DoesNotExist:
            return Response(
                {"error": f"Invalid asset_type '{asset_type}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate asset existence
        model_class = content_type.model_class()
        try:
            asset_instance = model_class.objects.get(id=asset_id)
        except model_class.DoesNotExist:
            return Response(
                {"error": f"{asset_type} with id {asset_id} not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Delete asset from watchlist
        deleted, _ = WatchlistItem.objects.filter(
            watchlist=watchlist,
            content_type=content_type,
            object_id=asset_id,
        ).delete()

        if deleted:
            return Response({"message": "Asset removed from watchlist."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Asset not found in watchlist."}, status=status.HTTP_404_NOT_FOUND)
