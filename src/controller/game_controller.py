from base64 import b64encode, b64decode
from datetime import datetime, timedelta

import requests
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad
from Crypto.Util.Padding import unpad
from flask import Flask

from src.controller import Controllers, error_handler
from src.database.models.game import GameAuth, GameIDS, GiftCode, GiftCodeOut, GameDataInternal, GiftCodesSubscriptions
from src.database.models.users import User
from src.database.sql.game import GameAuthORM, GameIDSORM, GiftCodesORM, RedeemCodesORM, GiftCodesSubscriptionORM

# Dictionary containing hourly events for Last Shelter: Survival
weekdays_events = {
    "Monday": {
        "00": "Building + Building Speedups",
        "01": "Building",
        "02": "Use Training Speedups + Spend VIP points",
        "03": "Building + Training Troops + Spend VIP points",
        "04": "Building Speedups + Research Speedups + Training Speedups",
        "05": "Building + Tech Research + Training Speedups",
        "06": "Building + Tech Research + Training Troops",
        "07": "Building",
        "08": "Building + Building Speedups",
        "09": "Building",
        "10": "Use Training Speedups + Spend VIP points",
        "11": "Building + Training Troops + Spend VIP points",
        "12": "Building Speedups + Research Speedups + Training Speedups",
        "13": "Building + Tech Research + Training Speedups",
        "14": "Building + Tech Research + Training Troops",
        "15": "Building",
        "16": "Building + Building Speedups",
        "17": "Building",
        "18": "Use Training Speedups + Spend VIP points",
        "19": "Building + Training Troops + Spend VIP points",
        "20": "Building Speedups + Research Speedups + Training Speedups",
        "21": "Building + Tech Research + Training Speedups",
        "22": "Building + Tech Research + Training Troops",
        "23": "Building"
    },
    "Tuesday": {
        "00": "Building + Craft Parts",
        "01": "Building + Tech Research + Training Speedups",
        "02": "Building + Craft Parts",
        "03": "Use Any Speedups",
        "04": "Building + Tech Research",
        "05": "Building + Building Speedups + Consume Energy Core",
        "06": "Building + Tech Research",
        "07": "Building + Tech Research + Training Troops",
        "08": "Building + Craft Parts",
        "09": "Building + Tech Research + Training Speedups",
        "10": "Building + Craft Parts",
        "11": "Use Any Speedups",
        "12": "Building + Tech Research",
        "13": "Building + Building Speedups + Consume Energy Core",
        "14": "Building + Tech Research",
        "15": "Building + Tech Research + Training Troops",
        "16": "Building + Craft Parts",
        "17": "Building + Tech Research + Training Speedups",
        "18": "Building + Craft Parts",
        "19": "Use Any Speedups",
        "20": "Building + Tech Research",
        "21": "Building + Building Speedups + Consume Energy Core",
        "22": "Building + Tech Research",
        "23": "Building + Tech Research + Training Troops",
    },
    "Wednesday": {
        "00": "Use Any Speedups",
        "01": "Tech Research + Tech Research Speedups",
        "02": "Building Speedups + Tech Research Speedups + Training Speedups",
        "03": "Building + Tech Research + Craft Parts",
        "04": "Building + Tech Research + Craft Parts",
        "05": "Building Speedups + Tech Research Speedups + Training Speedups",
        "06": "Building + Tech Research + Training Speedups + Consume Energy Core",
        "07": "Building + Tech Research",
        "08": "Use Any Speedups",
        "09": "Tech Research + Tech Research Speedups",
        "10": "Building Speedups + Tech Research Speedups + Training Speedups",
        "11": "Building + Tech Research + Craft Parts",
        "12": "Building + Tech Research + Craft Parts",
        "13": "Building Speedups + Tech Research Speedups + Training Speedups",
        "14": "Building + Tech Research + Training Speedups + Consume Energy Core",
        "15": "Building + Tech Research",
        "16": "Use Any Speedups",
        "17": "Tech Research + Tech Research Speedups",
        "18": "Building Speedups + Tech Research Speedups + Training Speedups",
        "19": "Building + Tech Research + Craft Parts",
        "20": "Building + Tech Research + Craft Parts",
        "21": "Building Speedups + Tech Research Speedups + Training Speedups",
        "22": "Building + Tech Research + Training Speedups + Consume Energy Core",
        "23": "Building + Tech Research"
    },
    "Thursday": {
        "00": "Hero Recruitment + Kill Zombies",
        "01": "All Hero Development",
        "02": "Spend / Acquire Wisdom Medals + Kill Zombies",
        "03": "All Hero Development",
        "04": "Hero Recruitment + Spend Wisdom Medals",
        "05": "All Hero Development",
        "06": "Spend / Acquire Wisdom Medals + Kill Zombies",
        "07": "All Hero Development",
        "08": "Hero Recruitment + Kill Zombies",
        "09": "All Hero Development",
        "10": "Spend / Acquire Wisdom Medals + Kill Zombies",
        "11": "All Hero Development",
        "12": "Hero Recruitment + Spend Wisdom Medals",
        "13": "All Hero Development",
        "14": "Spend / Acquire Wisdom Medals + Kill Zombies",
        "15": "All Hero Development",
        "16": "Hero Recruitment + Kill Zombies",
        "17": "All Hero Development",
        "18": "Spend / Acquire Wisdom Medals + Kill Zombies",
        "19": "All Hero Development",
        "20": "Hero Recruitment + Spend Wisdom Medals",
        "21": "All Hero Development",
        "22": "Spend / Acquire Wisdom Medals + Kill Zombies",
        "23": "All Hero Development"
    },
    "Friday": {
        "00": "Use Any Speedups",
        "01": "Building Speedups + Tech Research Speedups + Training Speedups",
        "02": "Building + Tech Research + Training Speedups",
        "03": "Training Speedups",
        "04": "Building + Tech Research + Training Speedups",
        "05": "Building + Training Troops",
        "06": "Tech Research + Training Troops",
        "07": "Use Any Speedups",
        "08": "Use Any Speedups",
        "09": "Building Speedups + Tech Research Speedups + Training Speedups",
        "10": "Building + Tech Research + Training Speedups",
        "11": "Training Speedups",
        "12": "Building + Tech Research + Training Speedups",
        "13": "Building + Training Troops",
        "14": "Tech Research + Training Troops",
        "15": "Use Any Speedups",
        "16": "Use Any Speedups",
        "17": "Building Speedups + Tech Research Speedups + Training Speedups",
        "18": "Building + Tech Research + Training Speedups",
        "19": "Training Speedups",
        "20": "Building + Tech Research + Training Speedups",
        "21": "Building + Training Troops",
        "22": "Tech Research + Training Troops",
        "23": "Building + Tech Research + Training Speedups",
        "24": "Use Any Speedups"
    }
}

# Dictionary containing hourly events for Last Shelter: Survival
kill_events = {
    "Saturday": {
        "00": "Use Any Speedups",
        "01": "Tech Research + Research Speedups",
        "02": "Building + Building Speedups",
        "03": "Training Speedups",
        "04": "Building + Tech Research + Training Speedups",
        "05": "Building + Tech Research + Training Speedups",
        "06": "Building + Training Troops",
        "07": "Tech Research + Training Troops",
        "08": "Use Any Speedups",
        "09": "Tech Research + Research Speedups",
        "10": "Building + Building Speedups",
        "11": "Training Speedups",
        "12": "Building + Tech Research + Training Speedups",
        "13": "Building + Tech Research + Training Speedups",
        "14": "Building + Training Troops",
        "15": "Tech Research + Training Troops",
        "16": "Use Any Speedups",
        "17": "Tech Research + Research Speedups",
        "18": "Building + Building Speedups",
        "19": "Training Speedups",
        "20": "Building + Tech Research + Training Speedups",
        "21": "Building + Tech Research + Training Speedups",
        "22": "Building + Training Troops",
        "23": "Tech Research + Training Troops",  
    },
    "Sunday": {
         "00": "Use Any Speedups",
        "01": "Tech Research + Research Speedups",
        "02": "Building + Building Speedups",
        "03": "Training Speedups",
        "04": "Building + Tech Research + Training Speedups",
        "05": "Building + Tech Research + Training Speedups",
        "06": "Building + Training Troops",
        "07": "Tech Research + Training Troops",
        "08": "Use Any Speedups",
        "09": "Tech Research + Research Speedups",
        "10": "Building + Building Speedups",
        "11": "Training Speedups",
        "12": "Building + Tech Research + Training Speedups",
        "13": "Building + Tech Research + Training Speedups",
        "14": "Building + Training Troops",
        "15": "Tech Research + Training Troops",
        "16": "Use Any Speedups",
        "17": "Tech Research + Research Speedups",
        "18": "Building + Building Speedups",
        "19": "Training Speedups",
        "20": "Building + Tech Research + Training Speedups",
        "21": "Building + Tech Research + Training Speedups",
        "22": "Building + Training Troops",
        "23": "Tech Research + Training Troops",  
    }
}


class Encryption:
    def __init__(self, key):
        self.key = self.pad_key(key)

    def pad_key(self, key):
        # Pad or truncate the key to 8 bytes
        key_length = len(key)
        if key_length < 8:
            # Pad the key with zero bytes ('\x00') if it's shorter than 8 bytes
            padded_key = key + (8 - key_length) * '\x00'
        elif key_length > 8:
            # Truncate the key if it's longer than 8 bytes
            padded_key = key[:8]
        else:
            padded_key = key
        return padded_key

    def encrypt(self, plaintext):
        cipher = DES.new(self.key.encode(), DES.MODE_ECB)
        padded_plaintext = pad(plaintext.encode(), DES.block_size)
        ciphertext = cipher.encrypt(padded_plaintext)
        return b64encode(ciphertext).decode()

    def decrypt(self, ciphertext):
        cipher = DES.new(self.key.encode(), DES.MODE_ECB)
        decrypted_data = cipher.decrypt(b64decode(ciphertext))
        unpadded_data = unpad(decrypted_data, DES.block_size)
        return unpadded_data.decode()


class GameController(Controllers):

    def __init__(self):
        super().__init__()
        self.redeem_url = "https://gslls.im30app.com/gameservice/web_code.php"
        self.captcha = "PQcA&id=bfbb020d-7579-4bd1-bc82-8be6005820c4"
        self._game_data_url: str = 'https://gslls.im30app.com/gameservice/web_getserverbyname.php'
        self._account_verification_endpoint: str = "https://lsaccount.im30.net/common/v1/login"
        self._encryption_key: str = "$VfXlM^U#*"
        self._headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,ja;q=0.8",
            "Connection": "keep-alive",
            "Dnt": "1",
            "Host": "gslls.im30app.com",
            "Origin": "https://ls.im30.net",
            "Referer": "https://ls.im30.net/",
            "Sec-Ch-Ua": "\"Google Chrome\";v=\"123\", \"Not:A-Brand\";v=\"8\", \"Chromium\";v=\"123\"",
            "Sec-Ch-Ua-Mobile": "?1",
            "Sec-Ch-Ua-Platform": "\"Android\"",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36"
        }

    def init_app(self, app: Flask):
        super().init_app(app=app)

    async def get_day_and_hour(self):
        # Get the current system time in UTC

        current_time_utc = datetime.utcnow()

        # Convert the datetime object to a string
        current_time = (current_time_utc - timedelta(hours=2))
        return current_time.strftime("%A"), current_time.strftime("%H")

    async def get_hourly_event(self):
        day, hour = await self.get_day_and_hour()

        if day in weekdays_events and hour in weekdays_events[day]:
            return weekdays_events[day][hour]
        if day in kill_events and hour in kill_events[day]:
            return kill_events[day][hour]

    async def game_account_valid(self, email: str, password: str):
        """
            This method will Validate Game Accounts
        :param email:
        :param password:
        :return:
        """
        # Create a dictionary with form data

        encryptor = Encryption(self._encryption_key)
        encrypted_password = encryptor.encrypt(password)
        form_data = {'email': email, 'pass': encrypted_password}

        # Make the request with form data
        response = requests.post(url=self._account_verification_endpoint, data=form_data)
        if response.ok:
            response_data = response.json()
            print(response_data)
            return int(response_data.get('code')) == 10000
        return False

    @error_handler
    async def create_account_verification_request(self, game_data: GameAuth) -> GameAuth:
        """

        :param game_data:
        :return:
        """
        with self.get_session() as session:
            account_verification: GameAuthORM = session.query(GameAuthORM.game_id == game_data.game_id).first()
            if account_verification and account_verification.game_id == game_data.game_id:
                return GameAuth(**account_verification.to_dict())

            game_orm = GameAuthORM(**game_data.dict())
            session.add(game_orm)
            session.commit()
            return game_data

    @error_handler
    async def _get_game_data(self, uid: str, game_id: str, lang: str = 'en') -> GameDataInternal:
        """

        :param game_id:
        :param lang:
        :return:
        """
        _params = {'name': game_id, 'lang': lang}
        response = requests.get(url=self._game_data_url, params=_params, headers=self._headers)
        game_data = response.json()
        return GameDataInternal.from_json(data=game_data, game_id=game_id, uid=uid)

    @error_handler
    async def get_users_game_ids(self, uid: str) -> list[GameDataInternal]:
        """

        :param uid:
        :return:
        """
        with self.get_session() as session:
            return [GameDataInternal(**game_data.to_dict()) for game_data in
                    session.query(GameIDSORM).filter(GameIDSORM.uid == uid).all()]

    async def add_game_ids(self, uid: str, game_ids: GameIDS):
        with self.get_session() as session:
            for game_id in game_ids.game_id_list:
                # Check if the uid already exists in the database
                existing_game_id = session.query(GameIDSORM).filter(GameIDSORM.game_id == game_id).first()

                if not isinstance(existing_game_id, GameIDSORM):
                    # If the uid doesn't exist, create a new entry
                    game_data: GameDataInternal = await self._get_game_data(uid=uid,
                                                                            game_id=game_id)
                    new_game_data = GameIDSORM(**game_data.dict())
                    session.add(new_game_data)

            session.commit()

        return True

    @error_handler
    async def get_active_gift_codes(self) -> list[GiftCodeOut]:
        """

        :return:
        """
        with self.get_session() as session:
            gift_codes_list = await self.get_all_gift_codes()
            return [gift_code for gift_code in gift_codes_list if gift_code.is_valid]

    @error_handler
    async def get_all_gift_codes(self) -> list[GiftCodeOut]:
        """

        :return:
        """
        with self.get_session() as session:
            return [GiftCodeOut(**gift_code_orm.to_dict()) for gift_code_orm in session.query(GiftCodesORM).all()]

    @error_handler
    async def add_new_gift_code(self, gift_code: GiftCode) -> GiftCode:
        with self.get_session() as session:
            gift_code_orm_ = session.query(GiftCodesORM.code == gift_code.code).first()
            if isinstance(gift_code_orm_, GiftCodesORM):
                return GiftCode(**gift_code_orm_.to_dict())

            gift_code_orm = GiftCodesORM(**gift_code.dict())

            session.add(gift_code_orm)

            gift_code = GiftCode(**gift_code_orm.to_dict())
            session.commit()

            return gift_code

    async def get_game_uid(self, game_id: str) -> tuple[str, str]:
        """
            Put this headers on this request


            https://gslls.im30app.com/gameservice/web_getserverbyname.php?name=3XZXLABF&lang=en
        :param game_id:
        :return:
        """
        url = "https://gslls.im30app.com/gameservice/web_getserverbyname.php"
        _params = dict(name=game_id.upper(), lang="en")
        _response = requests.get(url=url, params=_params, headers=self._headers)
        data = _response.json()
        # print("get game uid")
        # print(data)
        return data.get('name'), data.get('gameUid')

    @error_handler
    async def redeem_external(self, game_id: str, gift_code: str):
        """
            "will actually call the game servers and redeem the code"
        :param game_id:
        :param gift_code:
        :return:
        """
        name, game_uid = await self.get_game_uid(game_id=game_id)
        _url = f"{self.redeem_url}?name={game_uid}&code={gift_code}&captcha={self.captcha}&lang=en"
        _response = requests.get(url=_url, headers=self._headers)
        response = _response.json()

        return {
            'msg': response.get('msg'),
            'game_id': game_id,
            'name': name,
            'code': gift_code,
            'status': response.get('result')
        }

    @error_handler
    async def redeem_code_for_all_game_ids(self, gift_code: GiftCode):
        """
        # dud = requests.get(url="https://gslls.im30app.com/gameservice/web_code.php?name=480322464001388&code=DSC98000&captcha=Z7Gf&id=db17bb79-9f56-4fd1-a641-a84d3edf6a08&lang=en")
        # print("prining dud")

        Redeems a specific gift code for all present game ids
        :param gift_code: The gift code to redeem
        :return: True if redemption is successful, False otherwise
        """
        with self.get_session() as session:
            game_ids = {game.uid for game in session.query(GameIDSORM).all()}
            redeemed_game_ids = {redeemed.uid for redeemed in
                                 session.query(RedeemCodesORM).filter(RedeemCodesORM.code == gift_code.code)}

            unredeemed_game_ids = game_ids - redeemed_game_ids

            for game_id in unredeemed_game_ids:
                if game_id == 8:
                    result = await self.redeem_external(game_id=game_id, gift_code=gift_code.code)
                    if result:
                        session.add(RedeemCodesORM(code=gift_code.code, game_id=game_id))

            session.commit()

        return True

    @error_handler
    async def redeem_none_expired_codes(self):
        """
        this should be called automatically on certain times of day
        :return:
        """
        with self.get_session() as session:
            none_expired_codes = [gift_code.code for gift_code in session.query(GiftCodesORM.is_valid == True).all()]
            for code in none_expired_codes:
                await self.redeem_code_for_all_game_ids(gift_code=code)

    @error_handler
    async def delete_game(self, game_id: str):
        with self.get_session() as session:
            game_to_delete = session.query(GameIDSORM).filter(GameIDSORM.game_id == game_id).first()
            if isinstance(game_to_delete, GameIDSORM):
                session.delete(game_to_delete)

            redeemed_codes_delete = session.query(RedeemCodesORM).filter(RedeemCodesORM.game_id == game_id).all()
            for redeemed in redeemed_codes_delete:
                session.delete(redeemed)

            session.commit()

            return True

    @error_handler
    async def get_game_accounts(self, uid: str) -> list[GameDataInternal]:
        with self.get_session() as session:
            game_accounts = session.query(GameIDSORM).filter(GameIDSORM.uid == uid).all()
            return [GameDataInternal(**game_account.to_dict()) for game_account in game_accounts if
                    isinstance(game_account, GameIDSORM)]

    @error_handler
    async def get_game_by_game_id(self, uid: str, game_id: str) -> GameDataInternal | None:
        with self.get_session() as session:
            game_account: GameIDSORM = session.query(GameIDSORM).filter(GameIDSORM.uid == uid,
                                                                        GameIDSORM.game_id == game_id).first()
            if isinstance(game_account, GameIDSORM):
                return GameDataInternal(**game_account.to_dict())
            return None

    @error_handler
    async def fetch_game_by_game_id(self, game_id: str) -> GameDataInternal | None:
        with self.get_session() as session:
            game_account: GameIDSORM = session.query(GameIDSORM).filter(GameIDSORM.game_id == game_id).first()
            if isinstance(game_account, GameIDSORM):
                return GameDataInternal(**game_account.to_dict())
            return None


    @error_handler
    async def update_game_account_type(self, game_id: str, account_type: str):
        with self.get_session() as session:
            game_account: GameIDSORM = session.query(GameIDSORM).filter(GameIDSORM.game_id == game_id).first()
            if isinstance(game_account, GameIDSORM):
                game_account.account_type = account_type
                _game_account = GameDataInternal(**game_account.to_dict())
                session.merge(game_account)
                session.commit()
                return _game_account
            return {}

    @error_handler
    async def create_gift_code_subscription(self, user: User, subscription_amount: int,
                                            base_limit: int) -> GiftCodesSubscriptions | None:
        with self.get_session() as session:
            gift_codes_subscriptions_orm = session.query(GiftCodesSubscriptionORM).filter(
                GiftCodesSubscriptionORM.uid == user.uid).first()
            if isinstance(gift_codes_subscriptions_orm, GiftCodesSubscriptionORM):

                if not gift_codes_subscriptions_orm.subscription_active:
                    return GiftCodesSubscriptions(**gift_codes_subscriptions_orm.to_dict())

                return None

            gift_codes_subscription = GiftCodesSubscriptions(uid=user.uid,
                                                             base_limit=base_limit,
                                                             amount_paid=subscription_amount)
            session.add(GiftCodesSubscriptionORM(**gift_codes_subscription.dict()))
            session.commit()
            return gift_codes_subscription

    @error_handler
    async def get_gift_code_subscription(self, user: User) -> GiftCodesSubscriptions | None:
        with self.get_session() as session:
            gift_code_subscriptions_orm = session.query(GiftCodesSubscriptionORM).filter(
                GiftCodesSubscriptionORM.uid == user.uid).first()
            if isinstance(gift_code_subscriptions_orm, GiftCodesSubscriptionORM):
                return GiftCodesSubscriptions(**gift_code_subscriptions_orm.to_dict())
            else:
                return None

    @error_handler
    async def gift_code_subscription_is_active(self, subscription_id: str, is_active: bool):
        with self.get_session() as session:
            gift_code_subscription_orm = session.query(GiftCodesSubscriptionORM).filter(
                GiftCodesSubscriptionORM.subscription_id == subscription_id).first()
            if isinstance(gift_code_subscription_orm, GiftCodesSubscriptionORM):
                gift_code_subscription_orm.subscription_active = is_active
                gift_code_subscription = GiftCodesSubscriptions(**gift_code_subscription_orm.to_dict())
                session.merge(gift_code_subscription_orm)
                session.commit()
                return gift_code_subscription

