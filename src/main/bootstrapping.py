
def bootstrapper():
    from src.database.sql.user import UserORM,  PayPalORM

    classes_to_create = [UserORM, PayPalORM]

    for cls in classes_to_create:
        cls.create_if_not_table()
