from django import forms
from django.forms import Form, ModelForm
from . import models
from django.db.models import Sum


# Worker part

class WorkerLoginForm(Form):
    passport_number = forms.CharField(max_length=64, label="Номер паспорта")
    password = forms.CharField(max_length=128, widget=forms.PasswordInput, label="Пароль")


class WorkerFilterForm(Form):
    first_name = forms.CharField(max_length=64, required=False, label="І'мя")
    last_name = forms.CharField(max_length=64, required=False, label="Прізвище")
    by_father_name = forms.CharField(max_length=64, required=False, label="По батькові")

    positions = forms.MultipleChoiceField(
        choices=[(p.id, p.position_name) for p in models.Position.objects.all()],
        widget=forms.CheckboxSelectMultiple,
        required=False, label="Посада"
    )

    branches = forms.ChoiceField(
        choices=[(None, "Всі")] + [(b.id, b.branch_address) for b in models.Branch.objects.all()],
        required=False, label="Філія"
    )
    order_by = forms.ChoiceField(
        choices=[(None, "Без"), (1, "За алфавітом"), (2, "За постадою")],
        required=False, label="Сортувати за"
    )


class WorkersSearchForm(Form):
    passwort_num = forms.CharField(max_length=9, required=False, label="Номер паспорта")
    identification_code = forms.CharField(required=False, label="Ідентифікаційний код")
    phone = forms.IntegerField(required=False, label="Номер телефона")
    email = forms.EmailField(max_length=64, required=False, label="Електрона пошла")


class WorkerModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in ("by_father_name", "email"):
            self.fields[key].required = False

    class Meta:
        model = models.Worker
        exclude = ["id"]
        labels = {
            "passport_num": "Номер паспорта",
            "identification_code": "Ідентифікаційний код",
            "first_name": "Ім'я",
            "last_name": "Призвище",
            "by_father_name": "По батькові",
            "birthday": "Дата народження",
            "phone": "Номер телефона",
            "email": "Пошта",
            "card_num": "Номер карти",
            "worker_address": "Адреса проживання",
            "start_work_at": "Почав працювати у",
            "password": "Пароль",
            "position": "Посада",
            "branch": "Філія"
        }
        widgets = {
            "start_work_at": forms.DateInput,
            "birthday": forms.DateInput
        }


# Client part


class ClientLoginForm(Form):
    CHOICES = [(doc_type.id, doc_type.document_type_name) for doc_type in models.DocumentType.objects.all()]
    document_type = forms.ChoiceField(choices=CHOICES, label="Тип документу")
    document_number = forms.CharField(max_length=64, label="Номер документу")


class ClientFilterForm(Form):
    first_name = forms.CharField(max_length=64, required=False, label="І'мя")
    last_name = forms.CharField(max_length=64, required=False, label="Прізвище")
    by_father_name = forms.CharField(max_length=64, required=False, label="По батькові")


class ClientSearchForm(Form):
    document_type = forms.ChoiceField(
        choices=[(d.id, d.document_type_name) for d in models.DocumentType.objects.all()],
        required=False, label="Тип документу")
    document_num = forms.CharField(max_length=64, required=False, label="Номер документу")


class ClientModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in ("email", "by_father_name"):
            self.fields[key].required = False

    class Meta:
        model = models.Client
        exclude = ["id"]
        labels = {
            "identification_code": "Ідентифікаційний код",
            "first_name": "Ім'я",
            "last_name": "Призвище",
            "by_father_name": "По батькові",
            "birthday": "Дата народження",
            "phone": "Номер телефона",
            "email": "Пошта",
            "document_num": "Номер документа",
            "document_type": "Тип документа",
        }
        widgets = {
            "birthday": forms.DateInput
        }


# Item part


class ItemFilterForm(Form):
    item_types = forms.MultipleChoiceField(
        choices=[(t.id, t.item_type_name) for t in models.ItemType.objects.all()],
        widget=forms.CheckboxSelectMultiple,
        required=False, label="Категорія"
    )
    materials = forms.MultipleChoiceField(
        choices=[(m.id, m.material_name) for m in models.Material.objects.all()],
        widget=forms.CheckboxSelectMultiple,
        required=False, label="Матеріал"
    )
    min_cost = forms.IntegerField(min_value=0, required=False, label="Мінімальна вартість")
    max_cost = forms.IntegerField(
        max_value=models.Item.objects.aggregate(sum_of_cost=Sum("cost"))["sum_of_cost"],
        required=False, label="Максимальная вартість"
    )
    have_contract = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=[(0, "Всі"), (1, "Для продажу"), (2, "Для повернення")],
        initial=0, label=""
    )
    order_by = forms.ChoiceField(choices=[(0, "None"), (1, "Ціною")], label="Сортувати за")


class ItemSearchForm(Form):
    item_id = forms.IntegerField(required=False, label="Номер предмета")


class ItemModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in ("description", "materials", "types", "contract", "volume"):
            self.fields[key].required = False

    class Meta:
        model = models.Item
        exclude = ['id']
        widgets = {
            "types": forms.CheckboxSelectMultiple,
            "materials": forms.CheckboxSelectMultiple
        }
        labels = {
            "item_name": "Назва",
            "cost": "Вартість",
            "weight": "Вага",
            "volume": "Об'єм",
            "description": "Опис",
            "branch": "Філія",
            "contract": "Контракт",
            "types": "Категорії",
            "materials": "Матеріали"
        }


class MaterialModelForm(ModelForm):
    need_remove = forms.BooleanField(required=False, label="Видалити?")

    class Meta:
        model = models.Material
        exclude = ["id"]
        labels = {
            "material_name": "Назва",
            "selling_price": "Ціна продажу",
            "purchase_price": "Ціна купівлі"
        }


class ContractModelForm(ModelForm):
    class Meta:
        model = models.Contract
        exclude = ["id"]
        labels = {
            "from_date": "Дата укладеня контракту",
            "to_date": "Дата закінчення",
            "money_out": "Видано грошей",
            "client": "Клієнт",
            "worker": "Працівник",
            "money_in_percent": "Відсоток до поверненої суми"
        }



# Branch Part
class BranchFilterForm(Form):
    open_at = forms.TimeField(required=False, label="Відчиняється з")
    close_at = forms.TimeField(required=False, label="Закривается після")


class BranchSearchForm(Form):
    branch_id = forms.IntegerField(required=False, label="Номер філії")


class BranchModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key in ():
            self.fields[key].required = False

    class Meta:
        model = models.Branch
        exclude = ["id"]
        labels = {
            "open_time": "Відчиняється з",
            "close_time": "Закривается після",
            "branch_address": "Адреса"
        }


# Other part

class QueryForm(Form):
    query = forms.CharField(widget=forms.Textarea, required=False, label="Запит")
    top_queries = forms.ChoiceField(
        choices=[
            (0, "Власний запит"),
            (1, "Найприбутковіші філії за N днів"),
            (2, "Кількість речей з коштовного матеріалу"),
            (3, "Кількість предметів певного типу"),
            (4, "Топ філій за кількістю зданих  предметів"),
            (5, "Топ клієнтів за загальною вартістю контрактів")
        ],
        required=False, label=""
    )
