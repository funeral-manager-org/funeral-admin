import pytest
from pydantic import ValidationError
from src.database.models.companies import Company
from src.database.models.companies import CompanyBranches

def test_company_model_validation():
    company_data = {
        "admin_uid": "A1B2C3D4E5",
        "reg_ck": "CK1234567890",
        "company_name": "Test Company",
        "company_description": "Description of the company",
        "company_slogan": "Slogan of the company",
        "total_users": 10,
        "total_clients": 50
    }

    company = Company(**company_data)
    assert company.company_id is not None
    assert company.total_users == 10

def test_company_invalid_users():
    with pytest.raises(ValidationError):
        Company(
            admin_uid="A1B2C3D4E5",
            reg_ck="CK1234567890",
            company_name="Test Company",
            company_description="Description of the company",
            company_slogan="Slogan of the company",
            total_users=-1  # Invalid number of users
        )




def test_company_branches_model():
    branch_data = {
        "company_id": "C1D2E3F4G5",
        "branch_name": "Main Branch",
        "branch_description": "This is the main branch.",
        "total_clients": 100,
        "total_employees": 50
    }

    branch = CompanyBranches(**branch_data)
    assert branch.branch_id is not None
    assert branch.total_clients == 100
    assert branch.total_employees == 50
