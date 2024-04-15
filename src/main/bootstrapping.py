
def bootstrapper():
    from src.database.sql.user import UserORM, ProfileORM, PayPalORM

    classes_to_create = [UserORM, PayPalORM, ProfileORM]

    for cls in classes_to_create:
        cls.create_if_not_table()
