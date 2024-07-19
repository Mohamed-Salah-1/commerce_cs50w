from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .forms import ListingForm, CommentForm, BidForm
from .models import User, Listing, Bid, Comment, Category

# ------------------------- Index -------------------------------------
def index(request):
    listings = Listing.objects.filter(isActive=True).order_by("-created")
    return render(request, "auctions/index.html", {
        "listings": listings
    })

# -------------------------Login user----------------------------------------
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

# -------------------------Register a new user------------------------------------
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        # Ensure password matches confirmation
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

# -------------------------Create a new listing------------------------------------
@login_required(login_url="login")
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.created_by = request.user
            listing.save()
            return HttpResponseRedirect(reverse("index"))
    else:
        form = ListingForm()
    context = {
        "form": form,
    }
    return render(request, "auctions/create_listing.html", context)

# -------------------------listing------------------------------------
def listing(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if request.method == "POST":
        if "add_to_watchlist" in request.POST:
            user = request.user
            if listing in user.watchlist.all():
                user.watchlist.remove(listing)
            else:
                user.watchlist.add(listing)
            return HttpResponseRedirect(reverse("listing", args=(listing_id,)))
        
        # Handle bid submissions
        if "bid" in request.POST:
            bid_form = BidForm(request.POST)
            if bid_form.is_valid():
                bid = bid_form.save(commit=False)
                bid.listing = listing
                bid.bidder = request.user
                if bid.amount > listing.starting_bid:
                    highest_bid = listing.bids.order_by("amount").last()
                    if highest_bid is None or bid.amount > highest_bid.amount:
                        bid.save()
                    else:
                        return render(request, "auctions/listing.html", {
                            "listing": listing,
                            "message": "Bid must be higher than current highest bid."
                        })
                else:
                    return render(request, "auctions/listing.html", {
                        "listing": listing,
                        "message": "Bid must be higher than starting bid."
                    })
                    
        # Handle Comments submissions
        elif "comment" in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.listing = listing
                comment.commenter = request.user
                comment.save()
                return redirect('listing', listing_id=listing_id)

    context = {
        "listing": listing,
        "bid_form": BidForm(),
        "comment_form": CommentForm()
    }
    return render(request, "auctions/listing.html", context)
    
        

@login_required
def watchlist(request):
    user = request.user
    watchlist_items = user.watchlist.all()
    context = {
        'watchlist_items': watchlist_items
    }
    return render(request, "auctions/watchlist.html", context)


def categories(request):
    if request.method == "GET":
        categories = Category.objects.all()
        return render(request, "auctions/categories.html", {
            "categories": categories
        })
    

def category_listings(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = category.listings.filter(isActive=True)
    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": listings
    })