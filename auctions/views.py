from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import User, Listing, Bid, Comment, Watchlist, Category


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all()
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

def create_listing(request):
    return render(request, "auctions/create_listing.html")

def create(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        price = request.POST["price"]
        image = request.FILES.get("image", None)
        if not title or not description or not price:
            return render(request, "auctions/create_listing.html", {
                "message": "All fields are required."
            })
        try:
            price = float(price)
        except ValueError:
            return render(request, "auctions/create_listing.html", {
                "message": "Price must be a valid number."
            })

        Listing.objects.create(title=title, 
                               description=description, 
                               price=price, 
                               created_by=request.user,
                               image=image)
        


        return HttpResponseRedirect(reverse("index"))
    else:
        return HttpResponseRedirect(reverse("index"))

def listing(request, listing_id):
    try:
        listing = Listing.objects.get(id=listing_id)
        if listing.status == "closed":
            return redirect('close', listing_id=listing.id)  # Redirect to close view
        bids = listing.bids.all().order_by('-amount')
        comments = listing.comments.all().order_by('-id')
        winner = listing.bids.order_by('-amount').first()
        watchlist = Watchlist.objects.filter(user=request.user, listing=listing).exists() if request.user.is_authenticated else False
    except Listing.DoesNotExist:
        return HttpResponse("Listing not found.", status=404)
    
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bids": bids,
        "comments": comments,
        "watchlist": watchlist,
        "winner": winner,
    })


def bid(request, listing_id):
    if request.method == "POST":

        amount = request.POST.get("amount")
        listing = Listing.objects.get(id=listing_id)
        try:
            amount = float(amount)
        except ValueError:
            return render(request, "auctions/listing.html", {
                "message": "Invalid bid amount.",
                "listing": listing
            })
        
        if amount <= listing.price:
            return render(request, "auctions/listing.html", {
                "message": "Bid must be higher than the current price.",
                "listing": listing
            })
        
        listing.price = amount
        listing.save()
        Bid.objects.create(listing=listing, amount=amount, created_by=request.user)
        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
    else:
        return HttpResponse("Method not allowed.", status=405)
    
def close(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    bid = listing.bids.order_by('-amount').first()
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "bid": bid,
        "closed": True,
    })

def watchlist(request):
    if request.method == "POST":
        listing_id = request.POST.get("listing_id")
        action = request.POST.get("action")
        
        try:
            listing = Listing.objects.get(id=listing_id)
        except Listing.DoesNotExist:
            return HttpResponse("Listing not found.", status=404)

        if action == "add":
            Watchlist.objects.get_or_create(user=request.user, listing=listing)
        elif action == "remove":
            Watchlist.objects.filter(user=request.user, listing=listing).delete()
        
        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
    
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('listing')

    return render(request, "auctions/watchlist.html", {
        "watchlist": watchlist_items
    })

def categories(request):
    categories = Category.objects.all()
    return render(request, "auctions/categories.html", {
        "categories": categories
    })
def category_listings(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        listings = category.listings.all()
    except Category.DoesNotExist:
        return HttpResponse("Category not found.", status=404)

    return render(request, "auctions/category_listing.html", {
        "category": category,
        "listings": listings
    })

def add_comment(request, listing_id):
    if request.method == "POST":
        content = request.POST.get("content")
        if not content:
            return render(request, "auctions/listing.html", {
                "message": "Comment cannot be empty.",
                "listing": Listing.objects.get(id=listing_id)
            })
        
        listing = Listing.objects.get(id=listing_id)
        Comment.objects.create(created_by=request.user, listing=listing, content=content)
        return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
    else:
        return HttpResponse("Method not allowed.", status=405)
def remove_comment(request, comment_id):
    if request.method == "POST":
        try:
            comment = Comment.objects.get(id=comment_id, created_by=request.user)
            listing_id = comment.listing.id
            comment.delete()
            return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
        except Comment.DoesNotExist:
            return HttpResponse("Comment not found or you do not have permission to delete it.", status=404)
    else:
        return HttpResponse("Method not allowed.", status=405)