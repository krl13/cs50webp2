from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass

class Listing(models.Model):
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=512)
    price = models.FloatField()
    image = models.ImageField(upload_to='listing_images/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="listings")
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name="listings", null=True, blank=True)
    status = models.CharField(max_length=40, default="active") 

class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids")
    amount = models.FloatField(default=0.0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    created_at = models.DateTimeField(auto_now_add=True)  # temporarily add default


class Comment(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")
    content = models.CharField(max_length=256)

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlists")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="watchlists")

    class Meta:
        unique_together = ('user', 'listing')

class Category(models.Model):
    name = models.CharField(max_length=64, unique=True)
