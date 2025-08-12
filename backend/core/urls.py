# core/urls.py
from django.urls import path
from core.views import MarketDataGroupedAPIView,AddAssetToWatchlistAPIView

urlpatterns = [
    path("api/market-data/", MarketDataGroupedAPIView.as_view(), name="market-data-grouped"),
    path('api/watchlist/add-asset/', AddAssetToWatchlistAPIView.as_view(), name='add-asset-to-watchlist'),

]
