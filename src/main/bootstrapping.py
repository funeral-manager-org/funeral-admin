import time


def bootstrapper():
    from src.database.sql.user import UserORM,  PayPalORM
    from src.database.sql.companies import CompanyORM, EmployeeORM, CompanyBranchesORM, CoverPlanDetailsORM
    from src.database.sql.bank_account import BankAccountORM
    from src.database.sql.contacts import AddressORM, PostalAddressORM, ContactsORM
    from src.database.sql.covers import ClientPersonalInformationORM, ClaimsORM, PolicyRegistrationDataORM , PremiumsORM
    from src.database.sql.messaging import SMSComposeORM, SMSInboxORM, EmailComposeORM
    from src.database.sql.subscriptions import (SubscriptionsORM, PackageORM, PaymentORM, SubscriptionStatusORM,
                                                PaymentNoticeIntervalORM)
    from src.database.sql.support import TicketORM, TicketMessageORM

    classes_to_create = [UserORM, PayPalORM, CompanyORM, EmployeeORM, CompanyBranchesORM, CoverPlanDetailsORM,
                         BankAccountORM, AddressORM, PostalAddressORM, ContactsORM, ClientPersonalInformationORM,
                         ClaimsORM,PremiumsORM, PolicyRegistrationDataORM, SMSComposeORM, SMSInboxORM, EmailComposeORM,
                         SubscriptionsORM, PackageORM, PaymentORM, SubscriptionStatusORM,
                         PaymentNoticeIntervalORM, TicketMessageORM, TicketORM ]

    classes_to_create.reverse()
    for cls in classes_to_create:
        try:
            cls.create_if_not_table()
        except Exception as e:
            print(str(e))

        time.sleep(1)
