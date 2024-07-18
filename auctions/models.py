from django.contrib.auth.models import AbstractUser, User
from django.db import models
# from .models import category



class User(AbstractUser):
    def __str__(self):
        return "@{}".format(self.username)
    
class Category(models.Model):
    category_name = models.CharField(max_length=50)

    def __str__(self):
        return self.category_name
        
        
class AuctionListing(models.Model):
    title = models.CharField(max_length=225)
    description = models.CharField(max_length=225)
    image_url = models.URLField(max_length=500)
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="user")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, blank=True, related_name="category")

    def __str__(self):
        return self.title

# class comments(request):
#     pass