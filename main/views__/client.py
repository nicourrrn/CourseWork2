from typing import Type, Literal
from random import randint, choice
from time import sleep
import threading
from dataclasses import dataclass

from django.shortcuts import redirect, render
from django.db import connection
from django.http import HttpRequest

from faker import Faker

from main.models import *
from main import forms


def search_clients(request: HttpRequest):
    context = create_context(request)

    if request.session["user_type"] == 1:
        redirect("index")

    if request.method == "POST" \
            and (form := forms.ClientSearchForm(request.POST)).is_valid():
        document_type = form.cleaned_data["document_type"]
        document_num = form.cleaned_data["document_num"]
        print(document_num, document_type)
        try:
            return redirect('client', Client.objects.get(document_type=document_type, document_num=document_num).id)
        except Exception as e:
            print(e)

    context["search_form"] = forms.ClientSearchForm()

    clients = Client.objects.all()

    if request.method == "POST" and (form := forms.ClientFilterForm(request.POST)).is_valid():
        if (d := form.cleaned_data["first_name"]) != "":
            clients = clients.filter(first_name__startswith=d)
        if (d := form.cleaned_data["last_name"]) != "":
            clients = clients.filter(last_name__startswith=d)
        if (d := form.cleaned_data["by_father_name"]) != "":
            clients = clients.filter(by_father_name__startswith=d)

        context["filter_form"] = form
    else:
        context["filter_form"] = forms.ClientFilterForm()

    context["clients"] = clients

    return render(request, "clients/search_clients.html", context)


def client(request: HttpRequest, client_id: int):
    context = create_context(request)

    if type(context["user"]) is not Worker:
        return redirect("index")

    context["client"] = Client.objects.get(id=client_id)

    return render(request, 'clients/client.html', context)


def add_client(request: HttpRequest):
    pass


def edit_client(request: HttpRequest):
    pass


def remove_client(request: HttpRequest):
    pass

