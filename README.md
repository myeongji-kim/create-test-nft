# QA NFT test with admin API

https://github.com/myeongji-kim/create-test-nft/actions/workflows/pylint.yml/badge.svg


## 사전 설치 필요
- Python 3.8 이상
- 아래 명령어 실행해서 필수 python 모듈 설치 (IDE 사용 시 IDE 내에서 설치 가능함)
```
$ pip3 install requests
$ pip3 install Image
$ pip3 install qrcode
$ pip3 install bitlyshortener
$ pip3 install ffmpeg-python (~v0.6)
```

## 실행 방법
- 소스 다운로드 및 createEdition 폴더 진입
- 아래 명령어 형식으로 실행
```
$ python3 main.py -k edition=[eth|btc|auction] totalSupply=(supply) coin=(coin) krw=(krw) id=(author/seller id) title=(title) pay=(paymethod) future=(yyyy-mm-dd)
```
- 필수 주의: coin, krw 파라미터를 모두 생략 시 에어드롭 NFT로 생성한다.
- 주의 1: 옥션, 에어드롭, 결제 방식: 코인, 코인+계좌이체+휴대폰 결제, 계좌이체+휴대폰 결제 방식은 pay 파라미터 "없이" 자동으로 생성되므로 입력하지 않아야 한다.
- 주의 2: 옥션 생성 시 auction 뒤에 아무런 파라미터를 붙이지 않아야 한다. 
- 주의 3: pay 파라미터는 4가지 유형만 입력 (coinmobile, coinbank, mobile, bank)
 * coinmobile : 코인 + 휴대폰 결제 (계좌이체 X)
 * coinbank : 코인 + 계좌이체 (휴대폰결제 X)
 * bank : 계좌이체 only
 * mobile : 휴대폰결제 only

## 에디션 + 유형 + 결제 수단 선택 테스트
* 에어드롭 + 오프라인 + 인톡 only
  * ```$ python3 main.py -k edition=eth totalSupply=20 title=비디오테스트 -v -i -o```
* quantityPerUser 파라미터 추가 (중복 구매, 인당 10개)
  * ```$ python3 main.py -k edition=eth totalSupply=20 title=생성테스트 quantityPerUser=10 ```
* 비디오 에디션 (모든 파라미터 입력 후 맨 마지막에 -v 옵션을 추가)
  * ```$ python3 main.py -k edition=eth totalSupply=20 title=비디오테스트 -v```
* 인증코드
  * ```$ python3 main.py -k edition=eth totalSupply=20 coin=1 krw=1000 id=201 accessCode=111111```
* 파트너ID, 그룹ID 지정
  * ```$ python3 main.py -k edition=eth totalSupply=20 coin=1 krw=1000 id=201 partnerID=19 groupID=999```
* 일반 에디션 (eth, 공급 수량 20개, 1이더 1000원, 작가 ID: 201, 제목: 어쩔티비, 이더 + 휴대폰 결제)
  * ```$ python3 main.py -k edition=eth totalSupply=20 coin=1 krw=1000 id=201 title=어쩔티비 pay=coinmobile```
* 일반 에디션 (eth, 공급 수량 20개, 1이더 1000원, 작가 ID: 201, 제목: 어쩔티비, 이더 + 계좌이체)
  * ```$ python3 main.py -k edition=eth totalSupply=20 coin=1 krw=1000 id=201 title=어쩔티비 pay=coinbank```
* 일반 에디션 (btc, 공급 수량 20개, 1000원, 작가 ID: 111222, 제목: 어쩔티비, 휴대폰 결제)
  * ```$ python3 main.py -k edition=btc totalSupply=20 krw=1000 id=111222 title=어쩔티비 pay=mobile```
* 일반 에디션 (btc, 공급 수량 20개, 1000원, 작가 ID: 111222, 제목: 어쩔티비, 계좌이체)
  * ```$ python3 main.py -k edition=btc totalSupply=20 krw=1000 id=111222 title=어쩔티비 pay=bank```
* 일반 에디션 (eth, 공급 수량 20개, 1이더 1000원, 작가 ID: 201, 제목: 어쩔티비, 이더 + 휴대폰 결제, 판매 예정)
  * ```$ python3 main.py -k edition=eth totalSupply=20 coin=1 krw=1000 id=201 title=어쩔티비 pay=coinmobile future=2022-11-20```
* 옥션 (auction)
  * ```$ python3 main.py -k edition=auction```
