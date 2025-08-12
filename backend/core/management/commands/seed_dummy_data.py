from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import CustomUser
from core.models import Exchange, Index, Sector, Stock, MutualFund, Watchlist, WatchlistItem
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = "Seed the database with dummy data for testing."

    def handle(self, *args, **kwargs):
        # -------------------------
        # Create a test user
        # -------------------------
        user, created = CustomUser.objects.get_or_create(
            username="testuser",
            defaults={"email": "test@example.com", "role": "customer"}
        )
        if created:
            user.set_password("password123")
            user.save()
        self.stdout.write(self.style.SUCCESS(f"User: {user.username}"))

        # -------------------------
        # Create Exchanges
        # -------------------------
        nse = Exchange.objects.get_or_create(name="NSE", country="India", currency="INR")[0]
        bse = Exchange.objects.get_or_create(name="BSE", country="India", currency="INR")[0]
        nyse = Exchange.objects.get_or_create(name="NYSE", country="USA", currency="USD")[0]

        # -------------------------
        # Create Indexes
        # -------------------------
        nifty50 = Index.objects.get_or_create(name="Nifty 50", symbol="NIFTY50")[0]
        sensex = Index.objects.get_or_create(name="Sensex", symbol="SENSEX")[0]
        sp500 = Index.objects.get_or_create(name="S&P 500", symbol="SPX")[0]

        # -------------------------
        # Create Sectors
        # -------------------------
        tech_sector = Sector.objects.get_or_create(name="Technology")[0]
        finance_sector = Sector.objects.get_or_create(name="Finance")[0]

        # -------------------------
        # Create Stocks
        # -------------------------
        tcs = Stock.objects.get_or_create(
            symbol="TCS", name="Tata Consultancy Services",
            last_price=3500, previous_close_price=3480, currency="INR",
            sector=tech_sector, index=nifty50, exchange=nse
        )[0]

        reliance = Stock.objects.get_or_create(
            symbol="RELIANCE", name="Reliance Industries",
            last_price=2600, previous_close_price=2580, currency="INR",
            sector=finance_sector, index=sensex, exchange=bse
        )[0]

        apple = Stock.objects.get_or_create(
            symbol="AAPL", name="Apple Inc.",
            last_price=180, previous_close_price=175, currency="USD",
            sector=tech_sector, index=sp500, exchange=nyse
        )[0]

        # -------------------------
        # Create Mutual Funds
        # -------------------------
        mf1 = MutualFund.objects.get_or_create(name="HDFC Equity Fund", category="Equity", nav=750.25)[0]
        mf2 = MutualFund.objects.get_or_create(name="ICICI Prudential Debt Fund", category="Debt", nav=120.80)[0]

        # -------------------------
        # Create Watchlist
        # -------------------------
        watchlist = Watchlist.objects.get_or_create(user=user, name="My Investments")[0]

        # -------------------------
        # Add Stocks to Watchlist
        # -------------------------
        stock_ct = ContentType.objects.get_for_model(Stock)
        WatchlistItem.objects.get_or_create(watchlist=watchlist, content_type=stock_ct, object_id=tcs.id)
        WatchlistItem.objects.get_or_create(watchlist=watchlist, content_type=stock_ct, object_id=apple.id)

        # -------------------------
        # Add Mutual Funds to Watchlist
        # -------------------------
        mf_ct = ContentType.objects.get_for_model(MutualFund)
        WatchlistItem.objects.get_or_create(watchlist=watchlist, content_type=mf_ct, object_id=mf1.id)

        # -------------------------
        # Add Index to Watchlist
        # -------------------------
        index_ct = ContentType.objects.get_for_model(Index)
        WatchlistItem.objects.get_or_create(watchlist=watchlist, content_type=index_ct, object_id=nifty50.id)

        self.stdout.write(self.style.SUCCESS("Dummy data seeded successfully!"))
