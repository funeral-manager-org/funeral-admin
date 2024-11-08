import os
from flask import Blueprint
from flask import send_from_directory, abort, url_for, redirect, flash

from src.database.models.covers import Claims
from src.main import covers_controller
from src.database.models.users import User
from src.authentication import login_required
from src.logger import init_logger
from src.utils import claims_folder_path

documents_route = Blueprint('documents', __name__)
documents_logger = init_logger('documents_logger')


@documents_route.get('/documents/<string:company_id>/<string:claim_number>/<string:filename>')
@login_required
async def download_claims_documents(user: User, company_id: str, claim_number: str, filename: str):
    """
        allows employess to download claims documents
    :param user:
    :param company_id:
    :param claim_number:
    :param filename:
    :return:
    """
    file_path = claims_folder_path(company_id=company_id, claim_number=claim_number)
    claim_data: Claims = await covers_controller.get_claim_data(claim_number=claim_number)

    documents_logger.info(f"Company ID for User: {user.company_id}")
    if user.company_id != claim_data.company_id:
        flash(message="You are not authorized to download this claim file")
        return redirect(url_for('admin.get_admin'))

    # Check if the file exists
    if not os.path.exists(os.path.join(file_path, filename )):
        return abort(404)  # Return a 404 if the file does not exist

    # Serve the file
    return send_from_directory(directory=file_path, path=filename)
