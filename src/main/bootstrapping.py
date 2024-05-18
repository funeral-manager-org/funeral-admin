
def bootstrapper():
    from src.database.sql.user import UserORM,  PayPalORM
    from src.database.sql.companies import CompanyORM, EmployeeORM, CompanyBranchesORM, CoverPlanDetailsORM
    from src.database.sql.bank_account import BankAccountORM
    from src.database.sql.contacts import AddressORM, PostalAddressORM, ContactsORM
    from src.database.sql.covers import ClientPersonalInformationORM, ClaimsORM, PolicyRegistrationDataORM
    from src.database.sql.messaging import SMSComposeORM, SMSInboxORM, EmailComposeORM
    from src.database.sql.subscriptions import SubscriptionsORM, SMSPackageORM

    classes_to_create = [UserORM, PayPalORM, CompanyORM, EmployeeORM, CompanyBranchesORM, CoverPlanDetailsORM,
                         BankAccountORM, AddressORM, PostalAddressORM, ContactsORM, ClientPersonalInformationORM,
                         ClaimsORM, PolicyRegistrationDataORM, SMSComposeORM, SMSInboxORM, EmailComposeORM,
                         SubscriptionsORM, SMSPackageORM]

    for cls in classes_to_create:
        cls.create_if_not_table()
