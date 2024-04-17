
def bootstrapper():
    from src.database.sql.user import UserORM,  PayPalORM
    from src.database.sql.companies import CompanyORM, EmployeeORM, CompanyBranchesORM, CoverPlanDetailsORM
    classes_to_create = [UserORM, PayPalORM, CompanyORM, EmployeeORM, CompanyBranchesORM, CoverPlanDetailsORM]

    for cls in classes_to_create:
        cls.create_if_not_table()
