from django.urls import path
from .models import *
from .views import *

urlpatterns = [
    path('', index, name='index'),
    path('home', home, name='home'),
    path('user/logout', logout, name='logout'),

    path('branch/add', add_branch, name="branch_add"),
    path('branch/<int:branch_id>', branch, name='branch'),
    path('branch/<int:branch_id>/info', branch_info, name='branch_info'),
    path('branch/<int:branch_id>/edit', edit_branch, name='edit_branch'),
    path('branch/<int:branch_id>/remove', remove_branch, name='remove_branch'),

    path('position/<position_id>', position, name='position'),

    path('item/<int:item_id>', item, name='item'),
    path('item/add', add_item, name='item_add'),
    path('item/<int:item_id>/remove', remove_item, name='item_remove'),
    path('item/<int:item_id>/edit', edit_item, name='item_edit'),
    path('contract/<int:contract_id>', contract, name='contract'),
    path('contract/add', add_contract, name="contract_add"),

    path('client/login', client_login, name='client_login'),
    path('client/<int:client_id>', client, name='client'),
    path('client/add', add_client, name='client_add'),
    path('client/<int:client_id>/edit', edit_client, name="client_edit"),
    path('client/<int:client_id>/remove', remove_client, name="client_remove"),

    path('worker/login', worker_login, name='worker_login'),
    path('worker/<int:worker_id>', worker, name='worker'),
    path('worker/add', add_worker, name="worker_add"),
    path('worker/<int:worker_id>/edit', edit_worker, name="worker_edit"),
    path('worker/<int:worker_id>/remove', remove_worker, name="worker_remove"),

    path('search_items', search_items, name='search_items'),
    path('search_workers', search_workers, name='search_workers'),
    path('seach_clients', search_clients, name='search_clients'),
    path('search_branches', search_branches, name='search_branches'),
    path('search_materials', search_materials, name='search_materials'),
    path('materials/<int:material_id>', edit_material, name="material_edit"),
    path('materuals/add', add_material, name="material_add"),

    path('query', query, name='query'),
    path('create_mock', create_mock_info, name='mock'),
    path('rebalance_log', view_rebalanse, name='rebalance_log'),
]

