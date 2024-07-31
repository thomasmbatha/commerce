from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import User, Category, AuctionListing, Comment, Bid

# View to display a specific auction listing
def listing_view(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    # Check if the current user has the listing in their watchlist
    check_listing_in_watchlist = request.user.is_authenticated and request.user in listing_data.watchlist.all()
    # Get all comments for the listing
    all_comments = Comment.objects.filter(listing=listing_data)
    # Check if the current user is the owner of the listing
    is_owner = request.user.is_authenticated and request.user == listing_data.owner
    # Render the listing page with the relevant context
    return render(request, "auctions/listing.html", {
        "listing": listing_data,
        "check_listing_in_watchlist": check_listing_in_watchlist,
        "all_comments": all_comments,
        "is_owner": is_owner,
    })

# View to close an auction listing
def close_auction(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    # Check if the current user is the owner of the listing
    if request.user.is_authenticated and request.user.username == listing_data.owner.username:
        # Remove the listing from all users' watchlists
        for user in listing_data.watchlist.all():
            user.listing_watchlist.remove(listing_data)
        
        # Mark the listing as inactive
        listing_data.is_active = False
        listing_data.save()
        
        messages.success(request, "Congratulations! You have closed this auction.")
    else:
        messages.error(request, "You do not have permission to close this auction.")
    
    # Redirect to the listing page
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to add a new bid to an auction listing
def add_bid(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    # Check if the current user is the owner of the listing
    is_owner = request.user.is_authenticated and request.user.username == listing_data.owner.username
    # Get the new bid amount from the POST request
    new_bid = request.POST.get('starting_bid')
    
    # Check if the new bid is valid and higher than the current bid
    if new_bid and int(new_bid) > listing_data.starting_bid.bid:
        updated_bid = Bid(user=request.user, bid=int(new_bid))
        updated_bid.save()
        listing_data.starting_bid = updated_bid
        listing_data.save()
        messages.success(request, "Bid was updated successfully.")
    else:
        messages.error(request, "Bid update failed. Ensure your bid is higher than the current bid.")
    
    # Redirect to the listing page
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to add a new comment to an auction listing
def add_comment(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    # Get the new comment message from the POST request
    message = request.POST.get('new_comment')
    
    # Check if the comment message is not empty
    if message:
        new_comment = Comment(author=request.user, listing=listing_data, message=message)
        new_comment.save()
        messages.success(request, "Comment added successfully.")
    else:
        messages.error(request, "Comment cannot be empty.")
    
    # Redirect to the listing page
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to display the current user's watchlist
def watchlist_view(request):
    if request.user.is_authenticated:
        # Fetch only active listings for the current user
        listings = request.user.listing_watchlist.filter(is_active=True)
        return render(request, "auctions/watchlist.html", {
            "listings": listings
        })
    else:
        # Redirect to login page if the user is not authenticated
        return HttpResponseRedirect(reverse("login"))

# View to remove an auction listing from the current user's watchlist
def remove_watchlist(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    if request.user.is_authenticated:
        listing_data.watchlist.remove(request.user)
        messages.success(request, "Removed from watchlist.")
    else:
        messages.error(request, "You need to be logged in to remove from watchlist.")
    
    # Redirect to the listing page
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to add an auction listing to the current user's watchlist
def add_watchlist(request, id):
    # Retrieve the listing or return a 404 error if not found
    listing_data = get_object_or_404(AuctionListing, pk=id)
    if request.user.is_authenticated:
        listing_data.watchlist.add(request.user)
        messages.success(request, "Added to watchlist.")
    else:
        messages.error(request, "You need to be logged in to add to watchlist.")
    
    # Redirect to the listing page
    return HttpResponseRedirect(reverse("listing", args=(id, )))

# View to display all active auction listings and categories on the homepage
def index(request):
    active_listings = AuctionListing.objects.filter(is_active=True)
    all_categories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": active_listings,
        "categories": all_categories,
    })

# View to filter auction listings based on category
def display(request):
    if request.method == "POST":
        category_id = request.POST.get('category')
        if category_id:
            category = get_object_or_404(Category, id=category_id)
            active_listings = AuctionListing.objects.filter(is_active=True, category=category)
        else:
            active_listings = AuctionListing.objects.filter(is_active=True)
        
        all_categories = Category.objects.all()
        return render(request, "auctions/index.html", {
            "listings": active_listings,
            "categories": all_categories,
        })
    else:
        # Redirect to the homepage if not a POST request
        return HttpResponseRedirect(reverse("index"))

# View to handle the creation of a new auction listing
def create_listing(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        image_url = request.POST.get("image_url")
        price = request.POST.get("starting_bid")
        category_id = request.POST.get("category")
        
        # Check if all required fields are provided
        if not all([title, description, image_url, price, category_id]):
            messages.error(request, "All fields are required.")
            return render(request, "auctions/create_listing.html", {
                "categories": Category.objects.all()
            })
        
        # Retrieve the category or return a 404 error if not found
        category_data = get_object_or_404(Category, id=category_id)
        bid = Bid(bid=int(price), user=request.user)
        bid.save()
        
        # Create and save the new listing
        new_listing = AuctionListing(
            title=title,
            description=description,
            image_url=image_url,
            starting_bid=bid,
            category=category_data,
            owner=request.user,
        )
        new_listing.save()
        messages.success(request, "Listing created successfully.")
        return HttpResponseRedirect(reverse("index"))
    
    # Render the listing creation page
    return render(request, "auctions/create_listing.html", {
        "categories": Category.objects.all()
    })

# View to handle user login
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        
        # Check if authentication is successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            messages.error(request, "Invalid username and/or password.")
    
    # Render the login page
    return render(request, "auctions/login.html")

# View to handle user logout
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return HttpResponseRedirect(reverse("index"))

# View to handle user registration
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")
        
        # Check if password and confirmation match
        if password != confirmation:
            messages.error(request, "Passwords must match.")
            return render(request, "auctions/register.html")
        
        try:
            # Create a new user
            user = User.objects.create_user(username, email, password)
            user.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return HttpResponseRedirect(reverse("index"))
        except IntegrityError:
            messages.error(request, "Username already exists.")
    
    # Render the registration page
    return render(request, "auctions/register.html")
