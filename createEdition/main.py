"""
    입력받은 에디션, 작가 ID를 통해 세션 객체 생성하고 해당 객체를 통해 HTTP request 처리
    메타데이터 핸들러에서는 NFT 생성을 위한 메타데이터를 생성하여 json 파일로 write

    백오피스 Admin API를 통해 메타데이터를 가지고 NFT를 생성
"""
from lib.session_request import SessionRequest
from lib.metadata_handler import MetadataHandler


if __name__ == "__main__":
    handler = MetadataHandler()

    # API 호출 및 처리 모듈
    reqsession = SessionRequest(
        edition=handler.args.k.get("edition"), author_seller_id=handler.args.k.get("id")
    )
    # 작가 리스트 조회
    authorlist, totalCount = reqsession.get_authors
    # 작가 ID 존재 여부 조회
    reqsession.get_authorid_exist(authorlist, totalCount)
    # json 파일이 있을 경우 삭제 처리
    handler.remove_json_file()
    # static + dynamic 데이터 dict에 업데이트
    handler.update_metadata_dict()
    # 업데이트한 dict json 파일에 저장
    handler.write_dict_data_to_json()
    # NFT 생성 (with json 파일)
    reqsession.create_nft()
    # 에어드롭 작품인 경우 자동으로 QR 이미지 생성해서 다운로드
    handler.set_shortening_url()
