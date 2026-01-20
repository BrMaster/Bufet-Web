from django.shortcuts import render


def home(request):
	return render(request, "home.html")


def logged_in(request):
	return render(request, "logged_in.html")
