# -*- coding:utf-8 -*-
"""
메타데이터 핸들링

정적 데이터 및 입력을 받는 가변 데이터를 합쳐서 dictionary 형태로 가공한 뒤 json 파일에 쓰는 모듈
이미지, 비디오 처리는 이미지 핸들러를 통해 받아온 데이터를 가지고 메타데이터를 형성

"""
import argparse
import json
import os
import calendar
from collections import defaultdict
from datetime import datetime, timedelta
import qrcode
import bitlyshortener

# import pyshorteners
from lib.image_handler import ImageHandler
from lib.session_request import SessionRequest


class ParseKwargs(argparse.Action):
    """
    파라미터 Action 클래스
    key, value 형태의 입력 파싱을 위한 별도의 처리 클래스

    """
    def __call__(self, parser, namespace, values, option_string=None):
        """
        입력받은 파라미터들은 key/value로 리턴해주되, key=value 형태로 입력 받아야 하는 점 주의(ex. key:value -> X)

        :param parser:
        :param namespace:
        :param values:
        :param option_string:
        :return:
        """
        setattr(namespace, self.dest, {})
        for value in values:
            key, value = value.split("=")
            getattr(namespace, self.dest)[key] = value


class MetadataHandler:
    """
    실질적으로 메타데이터 핸들링하는 클래스

    NFT 생성에 필요한 메타데이터 개별 key마다 개별 기능 안에서 각각 업데이트하는 구조
    정적 데이터는 별도 파일에서 불러온 뒤 한꺼번에 업데이트하며 그 외 입력받을 필요가 있는 메타데이터들은 개별 기능으로 대응하였음
    """
    def __init__(self):
        """
        해당 클래스 객체를 생성하면 오늘, 내일 날짜를 기본 런타임에서 가져와 할당해준다.
        그 외 파싱된 파라미터 데이터, Admin API 요청을 위한 세션 객체, NFT ID, 메타데이터 업데이트를 위한 객체 초기화가 있다.
        """
        self.today = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        self.args = self.parsing()
        self.session = SessionRequest(
            edition=self.args.k.get("edition"), author_seller_id=self.args.k.get("id")
        )
        self.nft_id = self.session.nftid
        self.jsondict = defaultdict(dict)

    @staticmethod
    def parsing():
        """
        입력 파라미터 파싱
        입력받는 파라미터를 key/value로 입력받거나 단순 flag 형태로 받게 처리하였음

        :return:
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("-k", nargs="*", action=ParseKwargs)
        parser.add_argument("-v", help="add video option", action="store_true")
        parser.add_argument("-i", help="add intalk only option", action="store_true")
        parser.add_argument("-o", help="add offline option", action="store_true")
        args = parser.parse_args()
        return args

    def set_author_seller_id(self):
        """
        에디션 생성 시 원하는 특정 작가/판매자 ID로 생성하고 싶은 경우 id 파라미터를 입력하면 해당 id로 생성해주는 기능
        입력받지 않으면 기본 id로 설정

        :return:
        """
        author_seller_id = (
            self.args.k.get("id")
            if self.args.k.get("id")
            else self.session.author_seller_id
        )
        if (
            self.args.k.get("edition") != "eth"
            and self.args.k.get("edition") != "auction"
        ):
            self.jsondict.update({"sellerID": author_seller_id})
        else:
            self.jsondict.update({"authorID": author_seller_id})

    def set_date_time(self):
        """
        오픈/판매 시작/판매 종료 날짜를 자동으로 계산하되, future 파라미터로 입력 받는 경우 해당 날짜를 기점으로 오픈한다.
        판매 종료 날짜는 오픈/시작 날짜의 +1일이다.

        :return:
        """
        # 특정 날짜를 입력 받았다면 그 일정 기준으로 포매팅
        if self.args.k.get("future"):
            hour, minute, second = datetime.utcnow().strftime("%H:%M:%S").split(":")
            year, month, day = self.args.k.get("future").split("-")
            tgm = calendar.timegm(
                datetime(
                    year=int(year),
                    month=int(month),
                    day=int(day),
                    hour=int(hour),
                    minute=int(minute),
                    second=int(second),
                ).timetuple()
            )
            today_notformatted = datetime.utcfromtimestamp(tgm)
            self.today = today_notformatted.strftime("%Y-%m-%d %H:%M:%S")
            # self.today = datetime.strptime(self.args.k.get('future'), "%Y-%m-%d")
            self.tomorrow = (today_notformatted + timedelta(days=1)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        deadline = datetime.strptime(self.tomorrow, "%Y-%m-%d %H:%M:%S") + timedelta(
            hours=1
        )
        # 에디션 시작/종료 시간
        open_at, start_at, end_at = self.today, self.today, self.tomorrow
        self.jsondict.update(
            dict(
                openAt=str(open_at),
                startAt=str(start_at),
                endAt=str(end_at),
                deadline=str(deadline),
            )
        )

    def set_title(self):
        """
        별도로 입력받지 않으면 자동으로 타이틀을 설정해주는 기능
        [에디션 유형] 오픈시간, 종료시간 형태로 설정하되 별도 입력 받는 경우는 그를 따른다

        :return:
        """
        tag = "[btc]" if self.args.k.get("edition") == "btc" else "[eth]"
        title = (
            self.args.k.get("title")
            if self.args.k.get("title")
            else f"{tag} {self.today} {self.tomorrow}"
        )
        self.jsondict.update({"title": title, "titleEn": title})

    def set_selltype(self):
        """
        옥션(1), 에디션(2)에 따라 sellType을 구분하여 저장

        :return:
        """
        self.jsondict.update(
            dict(sellType=1 if self.args.k.get("edition") == "auction" else 2)
        )

    def set_nft_id(self):
        """
        NFT ID 설정
        :return:
        """
        self.jsondict.update({"id": self.nft_id})

    def set_price(self):
        """
        시스템 상 정해진 금액 설정 템플릿이 있어 이를 처리하기 위한 기능
        코인, 원화 금액에 따라 입력받은 값을 특정 템플릿으로 변환하여 저장한다.

        :return:
        """
        if self.args.k.get("coin") and not self.args.k.get("krw"):
            fixed_price_coin, fixed_price_won = int(self.args.k.get("coin")), 0
        elif self.args.k.get("krw") and not self.args.k.get("coin"):
            fixed_price_won, fixed_price_coin = int(self.args.k.get("krw")), 0
        elif self.args.k.get("krw") and self.args.k.get("coin"):
            fixed_price_won, fixed_price_coin = int(self.args.k.get("krw")), int(
                self.args.k.get("coin")
            )
        else:
            fixed_price_coin, fixed_price_won = 0, 0

        # 둘 다 0보다 클 때
        if fixed_price_coin >= 0 and fixed_price_won >= 0:
            fixed_price = (
                '{"coin":' + str(fixed_price_coin) + ', "krw":' + str(fixed_price_won) + "}"
            )
        # 코인 only
        elif fixed_price_coin >= 0 and fixed_price_won == 0:
            fixed_price = '{"coin":' + str(fixed_price_coin) + "}"
        # 그 외 (원화 only)
        else:
            fixed_price = '{"krw":' + str(fixed_price_won) + "}"

        self.jsondict.update(
            dict(
                fixedPriceCOIN=fixed_price_coin,
                fixedPriceWON=fixed_price_won,
                fixedPrice=fixed_price,
            )
        )

    def set_totalsupply(self):
        """
        기본 1개로 설정되고 그 외 파라미터로 입력받은 값으로 업데이트하여 생성한다.
        총 공급 개수 설정

        """
        total_supply = (
            self.args.k.get("totalSupply") if self.args.k.get("totalSupply") else 1
        )
        self.jsondict.update(dict(fixedTotalSupply=int(total_supply)))

    def set_quantity_per_user(self):
        """
        기본 1인1구매 설정이나 중복 구매 갯수 설정 필요 시 입력받아 업데이트 하는 기능

        :return:
        """
        quantity_per_user = (
            self.args.k.get("quantityPerUser")
            if self.args.k.get("quantityPerUser")
            else 1
        )
        self.jsondict.update(dict(quantityPerUser=quantity_per_user))

    def set_transfer_agreement(self):
        """
        에어드롭 / 그 외 에디션의 양수도계약서를 구분하여 설정하는 기능

        :return:
        """
        # coin 및 krw 파라미터 미입력 및 옥션이 아닐 경우 에어드롭 에디션 판정하여 설정
        if (
            not self.args.k.get("coin")
            and not self.args.k.get("krw")
            and not self.args.k.get("edition") == "auction"
        ):
            transfer_agreement = "contract_v2_airdrop"
        # 그 외에는 통합버전 양수도계약서 적용
        else:
            transfer_agreement = "contract_v2_integrated_primary_market"

        print(f"양수도 계약서 설정 : {transfer_agreement}")
        # return transferAgreement
        self.jsondict.update(dict(transferAgreementVersion=transfer_agreement))

    def set_pay_method(self):
        """
        원하는 결제 수단별 조합에 따라 dictionary 형태로 리턴 및 객체 업데이트하는 기능
        카드 결제는 현재 Scope Out 이나 추후 추가될 경우 아래 조합 및 명령어 네이밍 룰을 정하여 추가할 것

        ex) card, cardbank, cardmobile, ...

        입력받는 조합에 따라 key/value 값이 다르다. 0: 비활성화, 1: 활성화
        pay 파라미터를 따로 입력 받는 경우에만 활성화되고 그 외에는 자동 설정된다.

        ex) 에어드롭, 코인 only, 원화 only(계좌이체/휴대폰 모두 자동 활성화됨), 코인+원화

        코인+원화 에디션을 생성하지만 결제 수단을 달리하고 싶을 때 이 기능이 활성화된다.

        ex) pay="coinbank" -> 코인 + 원화(계좌이체) 생성 (휴대폰 결제는 비활성화)

        :return:
        """
        if self.args.k.get("pay") == "coinmobile":
            self.jsondict.update(
                dict(
                    allowPaymentCard=0,
                    allowPaymentBankTransfer=0,
                    allowPaymentCoin=1,
                    allowPaymentMobile=1,
                )
            )
        elif self.args.k.get("pay") == "coinbank":
            self.jsondict.update(
                dict(
                    allowPaymentCard=0,
                    allowPaymentBankTransfer=1,
                    allowPaymentCoin=1,
                    allowPaymentMobile=0,
                )
            )
        elif self.args.k.get("pay") == "mobile":
            self.jsondict.update(
                dict(
                    allowPaymentCard=0,
                    allowPaymentBankTransfer=0,
                    allowPaymentCoin=0,
                    allowPaymentMobile=1,
                )
            )
        elif self.args.k.get("pay") == "bank":
            self.jsondict.update(
                dict(
                    allowPaymentCard=0,
                    allowPaymentBankTransfer=1,
                    allowPaymentCoin=0,
                    allowPaymentMobile=0,
                )
            )
        elif self.args.k.get("pay") and self.args.k.get("pay") not in [
            "coinmobile",
            "coinbank",
            "mobile",
            "bank",
        ]:
            raise ValueError("결제수단을 잘못 입력하셨습니다.")
        else:
            print("별도의 결제수단 입력이 없으므로 금액에 따라 자동으로 수단이 설정됩니다.")

    def set_shortening_url(self):
        """
        에어드롭 에디션인 경우 자동으로 QR 코드를 생성해줄 수 있게 URL Shortening 해주는 기능
        bit.ly의 python 라이브러리인 bitlyshortener 패키지를 활용

        tokens_pool: 계정별 개인키 리스트
        (여러 키 존재 이유: 계정별로 50개만 free 제공, 랜덤하게 하나의 키를 가져와서 그 키를 통해 URL shortening 진행)

        :return:
        """
        # 별도로 입력 받지 않으면 에어드롭 처리하므로 not check
        if (
            not self.args.k.get("coin")
            and not self.args.k.get("krw")
            and not self.args.k.get("edition") == "auction"
        ):
            # nextId = self.nft_id
            edition = self.args.k.get("edition")  # edition

            airdrop_base_url = "https://qa.nftcreate.com/" + \
                               "?target=/external" + \
                               "?target_key=airdrop&target_link="
            drop_url = f"https://qa.nftcreate.com/{edition}/detail/{self.nft_id}"
            full_url = airdrop_base_url + drop_url
            intalk_link = full_url + "&intalk_only=true"

            # customize account token
            # tokens_pool = ["8e0124e426e702b3d859baba8782af7ea366edb9",
            # "fc38fdde6ffd136d53c981a1076d175a75c9cf43",
            # "6d17056c5d5e637f71207f700a8e4c84ef2db5a6",
            # "8f5619e47825b957bcfc67bb0fe6ef8f92da3b58",
            # "d99ce4c2ffe0b47d3b9f28d05c41fa6299b9231f"]
            tokens_pool = [
                "fc38fdde6ffd136d53c981a1076d175a75c9cf43",
                "6d17056c5d5e637f71207f700a8e4c84ef2db5a6",
                "8f5619e47825b957bcfc67bb0fe6ef8f92da3b58",
                "d99ce4c2ffe0b47d3b9f28d05c41fa6299b9231f",
                "57602ac16229f873da755e029fc4bc833acb78ae",
            ]
            shortener = bitlyshortener.Shortener(tokens=tokens_pool, max_cache_size=256)

            # bit.ly 동작 실패 시 아래 라이브러리로 활용 대체할 것
            # type_tiny = pyshorteners.Shortener()

            if self.args.i:
                print("인톡클립 우선으로 에어드롭 링크가 생성됩니다.")
                url_dict = shortener.shorten_urls_to_dict([intalk_link])
                full_short = url_dict.get(intalk_link)
                # tiny_short_url = type_tiny.tinyurl.short(intalk_link)
                print(
                    f"URL Shortening이 완료되었습니다.\n- Base URL 포함 전체 링크 축약 : {full_short}"
                )
                self.make_qrcode_and_download(full_short, intalk_link)
            else:
                # bit.ly shortening as dict
                url_dict = shortener.shorten_urls_to_dict([full_url])
                full_short = url_dict.get(full_url)
                # tiny_short_url = type_tiny.tinyurl.short(full_url)
                print(
                    f"URL Shortening이 완료되었습니다.\n- Base URL 포함 전체 링크 축약 : {full_short}"
                )
                self.make_qrcode_and_download(full_short, full_url)

        else:
            print("에어드롭에 해당하지 않아 에어드롭 URL 생성을 생략합니다.")

    def set_is_offline(self):
        """
        toggle flag 입력 받으나 optional 파라미터인 경우 이를 처리해주는 기능 (클래스 객체에 업데이트)
        현재는 오프라인만 존재하나 필요 시 함수명 수정, 추가 로직이 반영되어야 한다

        :return:
        """
        # 굳이 입력하지 않아도 되는 optional 값이 들어오는 경우의 처리 / toggle flag
        if self.args.o:
            self.jsondict.update(dict(isOffline=1))

    def set_optional(self):
        """
        NFT 생성 테스트 시 간혹 조합 테스트에서 특정 옵셔널한 값이 필요하여 별도로 처리해주는 기능
        추후 조합 테스트에 옵셔널한 값이 추가로 필요한 경우 optional array 안에 값만 추가해 주면 된다

        :return:
        """
        # toggle 아닌 경우이면서 간혹 테스트 시 필요하여 적용이 불가피한 파라미터들
        optional = ["accessCode", "partnerID", "groupID"]
        for option in optional:
            if self.args.k.get(option):
                self.jsondict.update({option: int(self.args.k.get(option))})

    def make_qrcode_and_download(self, full_shorten_url, full_origin_url):
        """
        AOS 특성 상 일부 URL에서 https:// 포함된 경우 QR 코드 파싱하는 부분이 시스템 상 이슈가 있어 iOS와 별도 URL을 가짐
        URL은 상위 기능에서 호출하면서 AOS, iOS 따로 생성한 뒤 해당 기능에 파라미터로 입력함

        파라미터로 입력받는 각각의 URL을 통해 QR 코드를 생성해주는 기능

        QR 폴더가 없을 경우 생성하고 있을 경우 그 안에서 <OS>_QR_<Drop ID>.jpg 형태로 QR 코드를 자동 생성/저장

        :param full_shorten_url: AOS용 URL
        :param full_origin_url: iOS용 URL
        :return:
        """
        qr_code = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        if not os.path.exists("QR"):
            print("QR 폴더가 없으므로 새로 생성해서 QR 코드를 저장합니다.")
            os.mkdir("QR")

        print(f"AOS용 QR 코드를 생성합니다. QR base 링크 : {full_shorten_url}")
        qr_code.add_data(full_shorten_url)
        qr_code.make()
        img = qr_code.make_image(fill_color="black", back_color="white")
        img.save(f"./QR/aos_QR_{self.nft_id}.png")

        qr_code.clear()

        print(f"iOS용 QR 코드를 생성합니다. QR base 링크 :{full_origin_url}")
        qr_code.add_data(full_origin_url)
        qr_code.make()
        img = qr_code.make_image(fill_color="black", back_color="white")
        img.save(f"./QR/ios_QR_{self.nft_id}.png")

        print("QR 코드 생성 완료되었습니다.")

    def get_static_data_and_update(self):
        """
        정적 데이터 즉, 임의로 수정할 일이 없는 메타데이터는 파일을 따로 static.json에 저장하였음
        해당 파일에서 데이터 load 후 클래스 객체에 업데이트하는 기능

        :return:
        """
        with open("./static.json", "r", encoding="utf-8") as stat:
            tempdump = json.load(stat)
            self.jsondict.update(tempdump)

    def update_metadata_dict(self):
        """
        개별 메타데이터 : 개별 기능 (1:1) 구조로 구현했고 설정 필요한 값들을 모두 호출하는 구조

        :return:
        """
        self.get_static_data_and_update()
        self.set_title()
        self.set_nft_id()
        self.set_date_time()
        self.set_selltype()
        self.set_price()
        self.set_totalsupply()
        self.set_quantity_per_user()
        self.set_transfer_agreement()
        self.set_author_seller_id()
        self.set_is_offline()
        self.set_optional()
        self.set_pay_method()
        self.set_image_video()

    def write_dict_data_to_json(self):
        """
        클래스 객체로 저장했던 메타데이터 (dictionary)를 json 파일에 쓰는 작업
        ensure_ascii 옵션 False로 해야 한글이 깨지지 않는다.

        :return:
        """
        with open("senddata.json", "x", encoding="utf-8") as file:
            file.write(json.dumps(self.jsondict, ensure_ascii=False))

    @staticmethod
    def remove_json_file():
        """
        테스트 전 기존 파일이 있으면 지운다. 목적은 기존 json 파일 데이터와 충돌되지 않기 위해 삭제 후 재생성을 목포로 하였음

        :return:
        """
        if os.path.exists("senddata.json"):
            os.remove("senddata.json")

    def set_image_video(self):
        """
        image handler 통해서 pixabay 이미지 및 영상 메타데이터를 리턴받아 메타데이터 dictionary에 업데이트

        :return:
        """
        img_obj = ImageHandler().get_all_images()
        self.jsondict.update(
            {
                "mainImage": {
                    "file": img_obj.get("imageBase64"),
                    "name": img_obj.get("imageName"),
                    "size": {
                        "width": int(img_obj.get("imageWidth")),
                        "height": int(img_obj.get("imageHeight")),
                    },
                },
                "mainImageHiRes": {
                    "file": img_obj.get("imageHiresBase64"),
                    "name": img_obj.get("imageHiresName"),
                    "size": {
                        "width": int(img_obj.get("imageHiresWidth")),
                        "height": int(img_obj.get("imageHiresHeight")),
                    },
                },
                "bannerImage": {
                    "file": img_obj.get("imageHiresBase64"),
                    "name": img_obj.get("imageHiresName"),
                    "size": {
                        "width": int(img_obj.get("imageHiresWidth")),
                        "height": int(img_obj.get("imageHiresHeight")),
                    },
                },
            }
        )
        # 비디오 옵션 있는 경우
        if self.args.v:
            video_obj = ImageHandler().get_all_videos()
            self.jsondict.update(
                {
                    "mainVideo": {
                        "file": video_obj.get("videoBase64"),
                        "name": video_obj.get("videoName"),
                        "size": {
                            "width": int(video_obj.get("videoWidth")),
                            "height": int(video_obj.get("videoHeight")),
                        },
                    },
                    "mainVideoHiRes": {
                        "file": video_obj.get("videoHiresBase64"),
                        "name": video_obj.get("videoHiresName"),
                        "size": {
                            "width": int(video_obj.get("videoHiresWidth")),
                            "height": int(video_obj.get("videoHiresHeight")),
                        },
                    },
                }
            )
