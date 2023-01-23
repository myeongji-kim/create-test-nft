"""
백오피스 어드민 API를 통해 NFT 생성 요청 및 Admin 데이터 조회 클래스

"""
import json

import requests


class SessionRequest:
    """
    백오피스 Admin API로 조회를 통해 확인 가능한 데이터 처리 클래스
    Super Admin 계정의 Bearer 토큰을 가지고 Admin이 조회 가능한 (NFT 생성 시 필요한) 데이터들을 조회할 수 있음

    작가 목록, 총 작가 수, 사용 가능한 NFT ID, NFT 생성 요청, HTTP request session 처리 (payload에 따라 다르게 요청)
    """
    def __init__(self, edition="eth", author_seller_id=0):
        self.addr = "https://qa.backoffice.admin.nftcreate.com/"
        self.headers = {
            "content-type": "application/json;charset=UTF-8",
            "accept": "application/json, text/plain, */*",
            "authorization": "Bearer <bearerToken>",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.edition = "eth" if edition == "auction" else edition
        if author_seller_id:
            self.author_seller_id = int(author_seller_id)
        else:
            self.author_seller_id = 100 if self.edition == "eth" else 200
        self.nftid = self.get_available_nft_id

    @property
    def get_authors(self):
        """
        에디션 유형에 따라 작가 or 브랜드 리스트로 조회하는 기능
        별도의 에디션 파라미터 입력이 없다면 기본 eth를 기본으로 하되, 입력받는 데이터가 있을 경우 그 값을 따른다.

        *전제: LIVE 상태인 작가/셀러의 데이터만 조회한다. LIVE 환경에서 DRAFT, DROPPED 상태의 작가는 유효하지 않으므로 배제

        :return: 조회된 작가/셀러의 리스트 및 조회된 작가/셀러의 총 수
        """
        # 일반 에디션이나 옥션 아닌 경우 BTC 셀러로 조회
        reqaddr = (
            self.addr + "authors" if self.edition == "eth" else self.addr + "sellers"
        )
        response = self.request_session(reqaddr, "GET").json()
        if not response["count"]:
            raise ValueError("LIVE인 셀러나 작가 카운트를 받아올 수 없습니다.")
        return response["list"], response["count"]

    def get_authorid_exist(self, authorlist: list, authorcount: int) -> any:
        """
        파라미터로 입력받은 작가 or 셀러 ID가 실제 리스트에 존재하는 지 체크하는 기능
        조회 API가 페이지 당 10명씩만 조회되므로 전체 페이지에 존재하는지 체크하려면 리스트를 받아서 10개씩 끊어서 조회해야 한다.

        authorcount 값이 10 초과인 경우 페이지가 1 이상이라는 의미이므로 이에 대한 조회 API 파라미터가 달라진다.
        quotient (전체 페이지 조회를 위한 몫 값)
        remainder (10으로 나눈 후 나머지가 있을 경우 올림 처리를 위해 필요한 나머지 값)

        ex 1) 33개 작가 조회 시 -> 몫: 3, 나머지: 3 -> 페이지: 4로 조회 필요
        ex 2) 40개 작가 조회 시 -> 몫: 4, 나머지: 0 -> 페이지: 4로 조회 필요

        모든 리스트를 다 조회했음에도 없을 경우 author/seller ID가 없음을 리턴하고 에러 발생시키며 종료

        :param authorlist: 작가/셀러 전체 리스트 (json)
        :param authorcount: 작가/셀러의 총 명수
        :return: 별도 리턴값 없이 조회 후 해당 ID가 없을 경우만 에러로 종료
        """
        # Backoffice 에서는 보통 10개씩 끊어서 리스트를 조회하기 때문에 작가 리스트가 10개 초과하는 경우 page 파라미터를 통해 추가로 조회해야 함
        # 아래 로직은 10을 초과하는 경우와 아닌 경우로 나누어 authorID 조회 가능하도록 만들었음
        if authorcount > 10:
            quotient, remainder = divmod(authorcount, 10)
            # 나머지가 존재할 경우 올림 처리
            if remainder != 0:
                quotient += 1
            for i in range(quotient):
                reqaddr = (
                    self.addr + f"authors?page={i + 1}&status=3"
                    if self.edition == "eth"
                    else self.addr + f"sellers?page={i + 1}&status=3"
                )
                response = self.request_session(reqaddr, "GET").json()
                idcheck = [
                    x["id"] for x in response["list"] if self.author_seller_id == x["id"]
                ]
                if idcheck:
                    print(
                        f"해당 authorID/sellerID {idcheck}가 작가 리스트에 존재합니다. 사용 가능한 NFT ID를 조회합니다."
                    )
                    break

                reqaddr = (
                    self.addr + f"authors?page={i + 1}&status=1"
                    if self.edition == "eth"
                    else self.addr + f"sellers?page={i + 1}&status=1"
                )
                response = self.request_session(reqaddr, "GET").json()
                idcheck = [
                    x["id"] for x in response["list"] if self.author_seller_id == x["id"]
                ]
                if idcheck:
                    print(
                        f"해당 authorID/sellerID {idcheck}가 작가 리스트에 존재합니다. 사용 가능한 NFT ID를 조회합니다."
                    )
                    break
            else:
                raise ValueError("해당하는 authorID/sellerID가 없습니다.")
        else:
            idcheck = [x["id"] for x in authorlist if self.author_seller_id == x["id"]]
            if idcheck:
                print(
                    f"해당 authorID/sellerID {idcheck}가 작가 리스트에 존재합니다. 사용 가능한 NFT ID를 조회합니다."
                )
            else:
                raise ValueError(f"해당하는 authorID {idcheck} 가 없습니다.")

    @property
    def get_available_nft_id(self):
        """
        작가/브랜드명 기준으로 생성 가능한 NFT ID를 조회하는 기능

        다만, 간혹 NFT 삭제 등으로 DB가 꼬이거나 DB상 존재하는 ID임에도 생성 가능하게 리턴받는 잠재 이슈가 존재함 (시스템 이슈)
        해서 isExisting flag를 통해 사용 중임을 체크하는 로직이 추가되었음

        NFT 유형에 따라 조회 엔드포인트가 다르다 (NFT 유형 + 작가 or 셀러 ID)

        :return: nextId: 사용 가능(가능하다고 리턴 받은) Drop ID
        """
        reqaddr = (
            self.addr + f"eth/nftId/{self.author_seller_id}"
            if self.edition == "eth"
            else self.addr + f"btc/nftId/{self.author_seller_id}"
        )
        response = self.request_session(reqaddr, "GET").json()

        available_nft_id = (
            response.get("nftId")
            if response.get("nftId")
            else ValueError("NFT ID가 조회되지 않습니다. 작가/셀러 ID를 다시 체크해주세요")
        )

        # 컨트랙트 단에서 Drop ID가 사용 중인지 체크
        is_existing = self.get_used_nft_id(available_nft_id)["isExisting"]
        if is_existing:
            print(f"해당 ID {available_nft_id}는 사용 중이거나 이슈가 있어 사용 불가합니다. 다음 ID로 등록합니다.")
            available_nft_id += 1

        return available_nft_id

    def get_used_nft_id(self, available_nft_id: object) -> object:
        """
        NFT ID 값이 사용 중인지 한 번 더 체크한다. 컨트랙트단 엔드포인트에 조회
        get_available_nft_id 함수는 1차적으로 DB에서 검색, 이 기능에서는 DB 검색이 완료되어도 컨트랙트단에서 사용 중인지 체크.

        :param available_nft_id: 사용 가능한 것으로 리턴받은 NFT ID를 인자로 받아서 조회
        :return: 응답 전체 리턴
        """
        # ID 받아온 다음, 사용 중인지 체크
        reqaddr = (
            self.addr + f"eth/{available_nft_id}/contract"
            if self.edition == "eth"
            else self.addr + f"btc/{available_nft_id}/contract"
        )
        response = self.request_session(reqaddr, "GET").json()

        return response

    def create_nft(self):
        """
        NFT ID 및 메타데이터 json 파일을 가지고 실제 NFT 생성 요청하는 기능
        (*Backoffice Admin API를 통한 생성)

        status code 200인 케이스를 제외하면 모두 에러이므로 valueError 발생시키며 종료

        최초 생성 시 DRAFT 상태이고 상태를 LIVE로 변경까지 진행한다.

        :return:
        """
        print(f'{self.nftid} ID로 NFT가 생성됩니다.')
        reqaddr = (
            self.addr + "eth"
            if self.edition == "eth"
            else self.addr + "btc"
        )
        with open("./senddata.json", "r", encoding="utf-8") as jsondata:
            response = self.request_session(reqaddr, "POST", json.load(jsondata))

        if response.status_code != 200:
            raise ValueError(
                f"해당 데이터로 NFT 생성에 실패했습니다 메타데이터를 다시 확인해주세요. status_code: {response.status_code}"
            )

        nft_url = f"https://qa.nftcreate.com/{self.edition}/detail/{self.nftid}"
        reqaddr = reqaddr + f"/{self.nftid}/status"
        datadict = {"id": self.nftid, "status": 3}
        response = self.request_session(reqaddr, "PUT", datadict)
        print("에디션이 라이브 상태로 변경되었습니다. 확인해보세요. " if response.status_code == 200 else None)
        print(f"생성된 에디션 링크는 다음과 같습니다.: {nft_url}")

    def request_session(self, url, method, payload=None):
        """
        payload를 입력 받느냐에 따라 session request 요청을 달리 보내는 단순 분기 처리

        :param url:
        :param method:
        :param payload:
        :return:
        """
        if payload:
            return self.session.request(method=method, url=url, json=payload)
        return self.session.request(method=method, url=url)
