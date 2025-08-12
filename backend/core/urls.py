# core/urls.py
from django.urls import path
from core.views import MarketDataGroupedAPIView,AddAssetToWatchlistAPIView,WatchlistAPIView,RemoveAssetFromWatchlistAPIView

urlpatterns = [
    path("api/market-data/", MarketDataGroupedAPIView.as_view(), name="market-data-grouped"),
    path('api/watchlist/add-asset/', AddAssetToWatchlistAPIView.as_view(), name='add-asset-to-watchlist'),
    path('api/watchlist/', WatchlistAPIView.as_view(), name='watchlist'),
    path('api/watchlist/remove-asset/',RemoveAssetFromWatchlistAPIView.as_view(),name='remove-asset-from-watchlist')

]
