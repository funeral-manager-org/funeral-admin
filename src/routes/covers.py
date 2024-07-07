from flask import Blueprint, render_template, url_for, flash, redirect, request
from pydantic import ValidationError

from src.authentication import login_required
from src.database.models.companies import CoverPlanDetails
from src.database.models.users import User
from src.main import company_controller

covers_route = Blueprint('covers', __name__)


@covers_route.get('/admin/administrator/plans')
@login_required
async def get_covers(user: User):
    """

        :param user:
        :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    cover_details = await company_controller.get_company_covers(company_id=user.company_id)
    context = dict(user=user, branches=company_branches, cover_details=cover_details)
    return render_template('admin/managers/covers.html', **context)


@covers_route.post('/admin/administrator/plans/add-plan-cover')
@login_required
async def add_plan_cover(user: User):
    """
        :param user:
        :return:
    """
    try:
        plan_cover = CoverPlanDetails(**request.form)
        print(plan_cover)
        plan_cover.company_id = user.company_id
    except ValidationError as e:
        print(str(e))
        flash(message="Unable to create plan please provide all necessary details", category="danger")
        return redirect(url_for('covers.get_covers'))

    updated_plan_cover = await company_controller.create_plan_cover(plan_cover=plan_cover)

    flash(message="successfully created plan", category="success")
    return redirect(url_for('covers.get_covers'))


@covers_route.get('/admin/administrator/plan/<string:company_id>/<string:plan_number>')
@login_required
async def get_plan_cover(user: User, company_id: str, plan_number: str):
    """

    :param user:
    :param company_id:
    :param plan_number:
    :return:
    """
    if user.company_id != company_id:
        flash(message="You are not authorized to view the cover details", category="danger")
        return redirect('home.get_home')

    plan_cover = await company_controller.get_plan_cover(company_id=company_id, plan_number=plan_number)
    subscribed_clients = await company_controller.get_plan_subscribers(plan_number=plan_number)
    context = dict(user=user, plan_cover=plan_cover, subscribed_clients=subscribed_clients)
    return render_template('admin/managers/covers/view.html', **context)


@covers_route.get('/admin/premiums/current')
@login_required
async def get_current_premiums(user: User):
    """

    :param user:
    :return:
    """
    context = dict(user=user)
    return render_template('admin/premiums/current.html', **context)


@covers_route.get('/admin/premiums/outstanding')
@login_required
async def get_outstanding_premiums(user: User):
    """

    :param user:
    :return:
    """
    context = dict(user=user)
    return render_template('admin/premiums/outstanding.html', **context)


@covers_route.get('/admin/premiums/quick-pay')
@login_required
async def get_quick_pay(user: User):
    """

    :param user:
    :return:
    """
    company_branches = await company_controller.get_company_branches(company_id=user.company_id)
    context = dict(user=user, company_branches=company_branches)
    return render_template('admin/premiums/pay.html', **context)

