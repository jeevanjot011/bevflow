from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from bevflow.models import UserProfile

def login_view(request):
    if request.method == "POST":
        action = request.POST.get("action")

        # LOGIN FLOW
        if action == "login":
            username = request.POST.get("username")
            password = request.POST.get("password")

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)

                try:
                    profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    messages.error(request, "Profile missing. Please sign up again.")
                    return redirect("login")

                if profile.role == "manufacturer":
                    return redirect("manufacturer_dashboard")
                else:
                    return redirect("customer_home")

            messages.error(request, "Invalid username or password")
            return redirect("login")


        # SIGNUP FLOW
        elif action == "signup":
            username = request.POST.get("username")
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            role = request.POST.get("role")
            area_code = request.POST.get("area_code")

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect("login")

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already taken.")
                return redirect("login")

            # Create user
            user = User.objects.create_user(username=username, password=password)

            # Create profile
            UserProfile.objects.create(
                user=user,
                role=role,
                area_code=area_code
            )

            # Auto login
            login(request, user)

            if role == "manufacturer":
                return redirect("manufacturer_dashboard")
            else:
                return redirect("customer_home")

    return render(request, "bevflow/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")
