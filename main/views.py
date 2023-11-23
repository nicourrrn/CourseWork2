import datetime
import time
from typing import Type, Literal
from random import randint, choice
from time import sleep
import threading
from dataclasses import dataclass

from django.shortcuts import redirect, render
from django.db import connection
from django.http import HttpRequest

from faker import Faker

from .models import *
from . import forms


# Support classes and data

@dataclass
class SessionKeys:
    user_type: Literal[0, 1] = None
    user_id: int = None


@dataclass
class ModelFormContext:
    form_title: str
    submit_title: str
    form_class: Type[forms.ModelForm]
    model_class: Type[Model]
    redirect_name: str
    model_id: int | None = None


rebalanced_history = []


def create_context(request: HttpRequest) -> dict:
    session = SessionKeys(**request.session)
    context = {}
    try:
        match session.user_type:
            case 0:
                context["user"] = Worker.objects.get(id=session.user_id)
            case 1:
                context["user"] = Client.objects.get(id=session.user_id)
            case _:
                context["user"] = None
    except Exception as e:
        print(e)

    return context


def add_model(request: HttpRequest, add_context: ModelFormContext):
    context = create_context(request)

    context["form_title"] = add_context.form_title
    context["submit_title"] = add_context.submit_title

    if request.method == "POST":
        if not (form := add_context.form_class(request.POST)).is_valid():
            context["form"] = form
            return render(request, 'model_form.html', context)

        new_model = form.save()
        return redirect(add_context.redirect_name, new_model.id)

    context["form"] = add_context.form_class()
    return render(request, 'model_form.html', context)


def edit_model(request: HttpRequest, model_context: ModelFormContext):
    context = create_context(request)
    context["form_title"] = model_context.form_title
    context["submit_title"] = model_context.submit_title

    if request.method == "POST":
        if not (form := model_context
                .form_class(request.POST,
                            instance=model_context.model_class.objects.get(id=model_context.model_id))).is_valid():
            context["form"] = form
            return render(request, 'model_form.html', context)
        form.save()
        return redirect(model_context.redirect_name, model_context.model_id)

    context["form"] = model_context.form_class(
        instance=model_context.model_class.objects.get(id=model_context.model_id))
    print(type(context['form']))
    return render(request, 'model_form.html', context)


# Index


def index(request):
    # Index
    context = create_context(request)
    return render(request, "index.html", context)


def home(request: HttpRequest):
    context = create_context(request)

    if type(context["user"]) is Worker:
        return render(request, 'workers/home_worker.html', context)
    elif type(context["user"]) is Client:
        return render(request, 'clients/home_client.html', context)
    else:
        return redirect("index")


# Login part

def worker_login(request: HttpRequest):
    context = create_context(request)

    if context["user"] is not None:
        return redirect("index")

    if request.method == "POST" and (form := forms.WorkerLoginForm(request.POST)).is_valid():
        print(form.cleaned_data)
        try:
            worker = Worker.objects.get(passport_num=form.cleaned_data["passport_number"],
                                        password=form.cleaned_data["password"])
        except Exception as e:
            print(e)
            form.add_error(None, "Неправильно введені дані")
            worker = None
        if worker is not None:
            request.session["user_type"] = 0
            request.session["user_id"] = worker.id
            return redirect("index")
        context["form"] = form
    else:
        context["form"] = forms.WorkerLoginForm()

    context["login_type"] = 0

    return render(request, 'login.html', context)


def client_login(request: HttpRequest):
    context = create_context(request)

    if context["user"] is not None:
        return redirect("index")

    if request.method == "POST" and (form := forms.ClientLoginForm(request.POST)).is_valid():
        try:
            client = Client.objects.get(document_type=form.cleaned_data["document_type"],
                                        document_num=form.cleaned_data["document_number"])
        except:
            form.add_error(None, "Неправильно введені дані")
            client = None
        if client is not None:
            request.session["user_type"] = 1
            request.session["user_id"] = client.id
            return redirect("index")
        context["form"] = form
    else:
        context["form"] = forms.ClientLoginForm()

    context["login_type"] = 1

    return render(request, "login.html", context)


def logout(request: HttpRequest):
    del request.session["user_type"]
    del request.session["user_id"]
    return redirect("index")


# Items part

def item(request: HttpRequest, item_id: int):
    context = create_context(request)
    context["item"] = Item.objects.get(id=item_id)
    return render(request, 'items/item.html', context)


def add_item(request: HttpRequest):
    context = create_context(request)

    is_worker = type(context["user"]) is Worker
    if not is_worker:
        redirect('index')

    high_rank = context["user"].position.rank < 5
    if not high_rank:
        redirect('index')

    add_context = ModelFormContext(
        form_title="Реєстрація предмету",
        submit_title="Додати предмет",
        form_class=forms.ItemModelForm,
        redirect_name="item",
        model_class=Item,
        model_id=None
    )
    return add_model(request, add_context)


def edit_item(request: HttpRequest, item_id: int):
    context = create_context(request)

    is_worker = type(context["user"]) is not Worker
    if not is_worker:
        redirect("index")

    on_him_branch = Item.objects.get(id=item_id).branch_id == context["user"].branch_id
    high_rank = context["user"].position.rank < 5
    if not on_him_branch or not high_rank:
        return redirect('item', item_id)

    edit_context = ModelFormContext(
        form_class=forms.ItemModelForm,
        model_class=Item,
        form_title="Редагування премету",
        submit_title="Зберегти",
        redirect_name="item",
        model_id=item_id
    )
    return edit_model(request, edit_context)


def remove_item(request: HttpRequest, item_id: int):
    context = create_context(request)

    if type(context["user"]) is not Worker \
            and (Item.objects.get(id=item_id).branch_id != context["user"].branch_id or
                 context["user"].position.rank < 5):
        return redirect('item', item_id)

    Item.objects.get(id=item_id).delete()

    return redirect('index')


def search_items(request: HttpRequest):
    context = create_context(request)

    if type(request.session.get('user')) is Worker:
        items = Item.objects.all()
    else:
        items = Item.objects.filter(contract_id=None)

    if request.method == "POST" and (form := forms.ItemSearchForm(request.POST)).is_valid():
        try:
            return redirect('item', Item.objects.get(id=form.cleaned_data["item_id"]).id)
        except Exception as e:
            print(e)

    context["search_form"] = forms.ItemSearchForm()

    if request.method == "POST" and (form := forms.ItemFilterForm(request.POST)).is_valid():
        if len(m := form.cleaned_data["materials"]) > 0:
            items = items.filter(materials__in=m).distinct()
        if len(t := form.cleaned_data["item_types"]) > 0:
            items = items.filter(types__item__in=t).distinct()

        if form.cleaned_data["order_by"] == "1":
            items = items.order_by("cost")

        if (min_cost := form.cleaned_data["min_cost"]) is not None:
            items = items.filter(cost__gte=min_cost)
        if (max_cost := form.cleaned_data["max_cost"]) is not None:
            items = items.filter(cost__lte=max_cost)

        if "1" == form.cleaned_data["have_contract"]:
            items = items.filter(contract_id__isnull=True)
        if "2" == form.cleaned_data["have_contract"]:
            items = items.exclude(contract_id__isnull=True)

        context["filter_form"] = form
    else:
        context["filter_form"] = forms.ItemFilterForm()

    context["items"] = items

    return render(request, "items/search_items.html", context)


def contract(request: HttpRequest, contract_id: int):
    context = create_context(request)

    context["contract"] = Contract.objects.get(id=contract_id)

    return render(request, 'items/contract.html', context)


def add_contract(request: HttpRequest):
    context = create_context(request)

    is_worker = type(context["user"]) is Worker
    if not is_worker:
        redirect('index')

    high_rank = context["user"].position.rank < 3
    if not high_rank:
        redirect('index')

    context["form_title"] = "Реєстрація нового контракту"
    context["submit_title"] = "Створити"

    if request.method == "POST":
        if not (form := forms.ContractModelForm(request.POST)).is_valid():
            context["form"] = form
            return render(request, 'model_form.html', context)
        form.save()
        return redirect("index")

    context["form"] = forms.ContractModelForm()
    return render(request, 'model_form.html', context)


def search_materials(request: HttpRequest):
    context = create_context(request)

    context["materials"] = Material.objects.all()

    return render(request, 'items/search_materials.html', context)


def add_material(request: HttpRequest):
    context = create_context(request)

    context["form_title"] = "Додати матеріал"
    context["submit_title"] = "Додати"

    if request.method == "POST":
        if not (form := forms.MaterialModelForm(request.POST)).is_valid():
            del form.fields['need_remove']
            context["form"] = form
            return render(request, 'model_form.html', context)
        form.save()
        return redirect("search_materials")

    context["form"] = forms.MaterialModelForm()
    del context["form"].fields['need_remove']
    return render(request, 'model_form.html', context)


def edit_material(request: HttpRequest, material_id: int):
    context = create_context(request)

    is_worker = type(context["user"]) is not Worker
    if not is_worker:
        redirect("index")

    high_rank = context["user"].position.rank < 3
    if not high_rank:
        return redirect('search_materials')

    context["form_title"] = "Зміна матеріалу"
    context["submit_title"] = "Зберегти"

    if request.method == "POST":
        if not (form := forms.MaterialModelForm(request.POST,
                                                instance=Material.objects.get(id=material_id))).is_valid():
            context["form"] = form
            return render(request, 'model_form.html', context)

        if form.cleaned_data['need_remove'] is True:
            Material.objects.get(id=material_id).delete()
        else:
            form.save()
        return redirect('search_materials')

    context["form"] = forms.MaterialModelForm(
        instance=Material.objects.get(id=material_id))
    return render(request, 'model_form.html', context)


# Worker part

def search_workers(request: HttpRequest):
    context = create_context(request)

    if request.session["user_type"] == 1:
        redirect("index")

    if request.method == "POST" and (form := forms.WorkersSearchForm(request.POST)).is_valid():
        args = {}
        if (d := form.cleaned_data["passwort_num"]) != '':
            args |= {"passport_num": d}
        if (d := form.cleaned_data["identification_code"]) != '':
            args |= {"identification_code": d}
        if (d := form.cleaned_data["phone"]) is not None:
            args |= {"phone": d}
        if (d := form.cleaned_data["email"]) != '':
            args |= {"email": d}

        for key, value in args.items():
            try:
                return redirect('worker', Worker.objects.get(**{key: value}).id)
            except Exception as e:
                print(e)

    context["search_form"] = forms.WorkersSearchForm()

    workers = Worker.objects.all()

    if request.method == "POST" and (form := forms.WorkerFilterForm(request.POST)).is_valid():
        if (worker_id := form.cleaned_data["branches"]) != "":
            workers = workers.filter(branch_id=worker_id)
        if len(pos := form.cleaned_data["positions"]) > 0:
            workers = workers.filter(position__in=pos)

        if (d := form.cleaned_data["first_name"]) != "":
            workers = workers.filter(first_name__startswith=d)
        if (d := form.cleaned_data["last_name"]) != "":
            workers = workers.filter(last_name__startswith=d)
        if (d := form.cleaned_data["by_father_name"]) != "":
            workers = workers.filter(by_father_name__startswith=d)

        orders = {
            "1": "first_name",
            "2": "position__rank"
        }

        if (data := form.cleaned_data["order_by"]) in orders.keys():
            workers = workers.order_by(orders[data])
            print(data)

        context["filter_form"] = form
    else:
        context["filter_form"] = forms.WorkerFilterForm()

    context["workers"] = workers

    return render(request, "workers/search_workers.html", context)


def worker(request: HttpRequest, worker_id: int):
    context = create_context(request)

    if type(context['user']) is not Worker:
        return redirect("index")

    context["worker"] = Worker.objects.get(id=worker_id)

    return render(request, 'workers/worker.html', context)


def add_worker(request: HttpRequest):
    context = create_context(request)

    is_worker = type(context["user"]) is Worker
    if not is_worker:
        redirect('index')

    high_rank = context["user"].position.rank < 3
    if not high_rank:
        redirect('index')

    add_context = ModelFormContext(
        form_title="Реєстрація працівника",
        submit_title="Додати працівника",
        form_class=forms.WorkerModelForm,
        redirect_name="worker",
        model_class=Worker,
        model_id=None
    )
    return add_model(request, add_context)


def edit_worker(request: HttpRequest, worker_id: int):
    context = create_context(request)

    is_worker = type(context["user"]) is not Worker
    if not is_worker:
        redirect("index")

    high_rank = context["user"].position.rank < 3
    if not high_rank:
        return redirect('worker', worker_id)

    edit_context = ModelFormContext(
        form_class=forms.WorkerModelForm,
        model_class=Worker,
        form_title="Редагування працівника",
        submit_title="Зберегти",
        redirect_name="worker",
        model_id=worker_id
    )
    return edit_model(request, edit_context)


def remove_worker(request: HttpRequest, worker_id: int):
    context = create_context(request)

    if type(context["user"]) is not Worker and context["user"].position.rank < 3:
        return redirect('worker', worker_id)

    Worker.objects.get(id=worker_id).delete()

    return redirect('index')


def position(request: HttpRequest, position_id: int):
    context = create_context(request)

    context["position"] = Position.objects.get(id=position_id)

    return render(request, 'position.html', context)


# Branch part

def search_branches(request: HttpRequest):
    context = create_context(request)

    if request.method == "POST" and (form := forms.BranchSearchForm(request.POST)).is_valid():
        try:
            return redirect('branch', Branch.objects.get(id=form.cleaned_data["branch_id"]).id)
        except Exception as e:
            print(e)

    context["search_form"] = forms.BranchSearchForm()

    branches = Branch.objects.all()

    if request.method == "POST" and (form := forms.BranchFilterForm(request.POST)).is_valid():
        print(form.cleaned_data)

        if (open_at := form.cleaned_data["open_at"]) is not None:
            branches = branches.filter(open_time__gt=open_at)
        if (close_at := form.cleaned_data["close_at"]) is not None:
            branches = branches.filter(close_time__lt=close_at)

        context["filter_form"] = form
    else:
        context["filter_form"] = forms.BranchFilterForm()

    context["branches"] = branches

    return render(request, "branches/search_branches.html", context)


def branch(request: HttpRequest, branch_id: int):
    context = create_context(request)

    context["branch"] = Branch.objects.get(id=branch_id)

    return render(request, 'branches/branch.html', context)


def add_branch(request: HttpRequest):
    context = create_context(request)

    add_context = ModelFormContext(
        form_class=forms.BranchModelForm,
        model_class=Branch,
        form_title="Реєстрацію нової філії",
        submit_title="Зареєструвати",
        redirect_name='branch',
        model_id=None
    )
    return add_model(request, add_context)


def edit_branch(request: HttpRequest, branch_id: int):
    context = create_context(request)

    add_context = ModelFormContext(
        form_class=forms.BranchModelForm,
        model_class=Branch,
        form_title="Зміна філії",
        submit_title="Зберегти",
        redirect_name='branch',
        model_id=branch_id,
    )
    return edit_model(request, add_context)


def remove_branch(request: HttpRequest, branch_id: int):
    context = create_context(request)

    if type(context["user"]) is not Worker and context["user"].position.rank > 3:
        return redirect('branch', branch_id)

    Branch.objects.get(id=branch_id).delete()

    return redirect('index')


def branch_info(request: HttpRequest, branch_id: int):
    context = create_context(request)

    context["branch"] = Branch.objects.get(id=branch_id)

    return render(request, 'branches/branch_info.html', context)


# Client part

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
    context = create_context(request)

    is_worker = type(context["user"]) is not Worker
    if not is_worker:
        redirect("index")

    add_context = ModelFormContext(
        form_title="Зареєструвати клієнта",
        submit_title="Зберегти",
        form_class=forms.ClientModelForm,
        model_class=Client,
        redirect_name='client',
        model_id=None
    )
    return add_model(request, add_context)


def edit_client(request: HttpRequest, client_id: int):
    context = create_context(request)

    is_worker = type(context["user"]) is not Worker
    if not is_worker:
        redirect("index")

    edit_context = ModelFormContext(
        form_title="Змінити клієнта",
        submit_title="Зберегти зміни",
        redirect_name='client',
        form_class=forms.ClientModelForm,
        model_class=Client,
        model_id=client_id
    )
    return edit_model(request, edit_context)


def remove_client(request: HttpRequest, client_id: int):
    context = create_context(request)

    if type(context["user"]) is not Worker and context["user"].position.rank < 4:
        return redirect('client', client_id)

    Client.objects.get(id=client_id).delete()

    return redirect('index')


# Technical part

def query(request: HttpRequest):
    context = create_context(request)

    context["form"] = forms.QueryForm()

    if request.method == "POST" and (form := forms.QueryForm(request.POST)).is_valid():
        match form.cleaned_data["top_queries"]:
            case "1":
                form.cleaned_data["query"] = """select branch_address, sum(cost) as sum_cost from main_branch
    join main_item on main_branch.id = main_item.branch_id
    join main_contract on main_item.contract_id = main_contract.id
    where contract_id is not null
    group by branch_address
    having sum(cost) >= all (select sum(cost) from main_item where contract_id is not null group by branch_id)
    order by sum_cost desc"""
            case "2":
                form.cleaned_data["query"] = """ select branch_address, material_name, count(main_item.id) as cou from main_item
    join main_item_materials on main_item.id = main_item_materials.item_id
    join main_material on main_item_materials.material_id = main_material.id
    join main_branch on main_item.branch_id = main_branch.id
    group by branch_address, material_name
    order by cou desc , branch_address;"""
            case "3":
                form.cleaned_data["query"] = """ select branch_address, item_type_name, count(main_item.id) as cou from main_item
join main_item_types on main_item.id = main_item_types.item_id
join main_itemtype on main_item_types.itemtype_id = main_itemtype.id
join main_branch mb on main_item.branch_id = mb.id
group by branch_address, item_type_name
order by cou desc, branch_address; """
            case "4":
                form.cleaned_data["query"] = """ select branch_address, count(main_item.id) as cou from main_branch
join main_item on main_branch.id = main_item.branch_id
group by branch_address
having count(main_item.id) >= all (select count(main_item.id) from main_item group by branch_id);"""
            case "5":
                form.cleaned_data["query"] = """ select client_id, first_name, last_name, sum(money_out) as s from main_client
join main_contract mc on main_client.id = mc.client_id
group by client_id, first_name, last_name
order by s desc;"""
        cursor = connection.cursor()
        try:
            cursor.execute(form.cleaned_data['query'])
            context["headers"] = [i[0] for i in cursor.description]
            context["rows"] = cursor.fetchall()
        except Exception as e:
            form.add_error('query', e)
        finally:
            cursor.close()

        context["form"] = form

    return render(request, 'workers/query.html', context)


def view_rebalanse(request: HttpRequest):
    context = create_context(request)

    global rebalanced_history
    context["logs"] = rebalanced_history

    return render(request, 'workers/rebalance.html', context)


# Avg = Count_item_by_type / count_branch +- 0.5avg

def rebalance(relocate_from=0, can_relocated=True):
    cursor = connection.cursor()
    branch_count = Branch.objects.all().count()
    global rebalanced_history
    cursor.execute("""select main_itemtype.id,  count(main_item.id) as item_count from main_item join main_item_types on main_item.id = main_item_types.item_id
join main_itemtype on main_item_types.itemtype_id = main_itemtype.id
group by main_itemtype.id order by item_count desc;""")
    categories_count = dict(cursor.fetchall())
    print(categories_count)
    get_types_count_query = """select main_itemtype.id,  count(main_item.id) as item_count from main_item join main_item_types on main_item.id = main_item_types.item_id
join main_itemtype on main_item_types.itemtype_id = main_itemtype.id
where branch_id = {branch_id}
group by main_itemtype.id order by item_count desc;"""
    double_continue = False
    while relocate_from != branch_count - 1:
        cursor.execute("""select mb.id , sum(main_item.cost) as s from main_item
right join main_branch mb on mb.id = main_item.branch_id
        group by mb.id
        order by s desc;""")
        relocate_from += 0 if can_relocated else 1

        branches = [(b[0], b[1] if b[1] is not None else 0) for b in cursor.fetchall()]
        branches.sort(key=lambda x: x[1], reverse=True)

        cursor.execute(
            f"""select id, cost from main_item where branch_id = {branches[relocate_from][0]} order by cost desc;""")
        items_from_top = cursor.fetchall()

        for item_id, item_cost in items_from_top:
            is_will_top = item_cost + branches[-1][1] > branches[relocate_from][1] - item_cost

            cursor.execute(f"select itemtype_id from main_item_types where item_id  = {item_id}")
            item_types = [i[0] for i in cursor.fetchall()]

            cursor.execute(get_types_count_query.format(branch_id=branches[relocate_from][0]))
            branch_types_count = dict(cursor.fetchall())

            greater_count_categories = []
            for key in item_types:
                greater_count_categories.append(
                     categories_count[key] / len(branches) * 0.2 > branch_types_count[key]
                )

            if any(greater_count_categories): print("A lot of catergory item in branch")
            if is_will_top or any(greater_count_categories):
                can_relocated = False
                continue
            cursor.execute(f"""update main_item
        set branch_id = {branches[-1][0]}
        where id = {item_id}""")
            log = f"Item {item_id} with cost {item_cost} relocate from {branches[0][0]} to {branches[-1][0]}"
            print(log)

            rebalanced_history.append((item_id, item_cost, branches[0][0], branches[-1][0]))
            can_relocated = True
            break
        sleep(0.1)
    cursor.close()


def remove_contract():
    for item in Item.objects.all():
        if item.contract is None:
            continue
        if item.contract.to_date < datetime.date.today():
            item.contract = None
            item.save()


def automatic_resend():
    while True:
        print("Start rebalanced")
        global rebalanced_history
        rebalanced_history = []
        rebalance()
        print("Rebalanced")
        remove_contract()
        print("Contract removed")
        sleep(1000)


thread = threading.Thread(target=automatic_resend, name="automatic", daemon=True)
thread.start()


def create_mock_info(request: HttpRequest):
    DocumentType.objects.create(document_type_name="Паспорт")
    DocumentType.objects.create(document_type_name="Водійське посвідчення")

    Position.objects.create(position_name="Продавець", rank=9)
    Position.objects.create(position_name="Власник", rank=1)

    for i in ["Телефон", "Ноутбук", "Камера", "Планшет"]:
        ItemType.objects.create(item_type_name=i)

    for i in [("Золото", 200, 210), ("Серебро", 100, 109), ("Аметист", 500, 550)]:
        Material.objects.create(material_name=i[0], selling_price=i[1], purchase_price=i[2])

    faker = Faker('uk_UA')

    for _ in range(20):
        Branch.objects.create(branch_address=faker.address(), open_time=faker.time_object(),
                              close_time=faker.time_object())

    for _ in range(100):
        Client.objects.create(
            identification_code=f"{randint(100_000, 999_999)}{randint(100_000, 999_999)}",
            first_name=faker.name().split(' ')[0],
            last_name=faker.name().split(' ')[1],
            birthday=faker.date_of_birth(minimum_age=18),
            phone=380 * 10 ** 9 + randint(0, 999_999_999),
            email=faker.profile()['mail'],
            document_num=randint(0, 100_000_000),
            document_type=choice(DocumentType.objects.all())
        )

    for _ in range(40):
        Worker.objects.create(
            identification_code=f"{randint(100_000, 999_999)}{randint(100_000, 999_999)}",
            first_name=faker.name().split(' ')[0],
            last_name=faker.name().split(' ')[1],
            phone=380 * 10 ** 9 + randint(0, 999_999_999),
            email=faker.profile()['mail'],
            birthday=faker.date_of_birth(minimum_age=18),
            passport_num=randint(0, 100_000_000),
            card_num=faker.credit_card_number(),
            worker_address=faker.address(),
            start_work_at=faker.past_date(),
            password="123456",
            position=choice(Position.objects.all()),
            branch=choice(Branch.objects.all()),
        )

    for _ in range(100):
        Contract.objects.create(
            from_date=faker.date_between(start_date='-2w', end_date='today'),
            to_date=faker.date_between(start_date='+1w', end_date='+3w'),
            money_out=randint(100, 1_000_000),
            worker=choice(Worker.objects.all()),
            client=choice(Client.objects.all())
        )

    with open('words.txt', 'r') as file:
        items_name = file.read().split('\n')
    for i in range(200):
        item = Item(
            item_name=choice(items_name),
            cost=randint(1, 100000),
            weight=randint(100, 1000000),
            branch=choice(Branch.objects.all()),
            contract=choice(Contract.objects.all()) if i < 100 else None,
            volume=0,
        )

        item.save()
        used_types = []
        for j in range(randint(1, 3)):
            if (rand := choice(ItemType.objects.all())) not in used_types:
                used_types.append(rand)
                item.types.add(rand)

        used_mats = []
        for j in range(randint(0, 2)):
            if (rand := choice(Material.objects.all())) not in used_mats:
                used_mats.append(rand)
                item.materials.add(rand)

    return redirect("index")
