"""
이미지/영상 메타데이터를 Pixabay API를 활용하여 처리하는 모듈
고해상도/저해상도 이미지/영상 데이터를 dictionary 형태로 리턴 제공해준다.
"""
import base64
import random
from collections import defaultdict
import requests
from PIL import Image, ImageFile


class ImageHandler:
    """
    Pixabay 이미지/비디오 데이터 처리 클래스
    Full API 접근 가능한 개인 API Key를 가지고 최고해상도 이미지/영상 데이터를 가져와 메타데이터 형태로 처리가능하도록 dict 리턴
    """
    def __init__(self):
        # 지정해주지 않으면 에러 발생 (PIL.Image.DecompressionBombError 방지용)
        Image.MAX_IMAGE_PIXELS = None
        self.session = requests.Session()

    def get_all_images(self):
        """
        pixabay API를 호출하여 이미지 데이터를 얻어온 뒤 dictionary 리턴
        1920 해상도 이상인 이미지를 찾아 랜덤하게 하나를 선택, 그 이미지로 저해상도/고해상도 이미지 메타데이터를 리턴해준다.

        imageURL : 원래 이미지의 URL (최고해상도)
        imageWidth, imageHeight : 최고해상도의 원래 이미지 가로, 세로 길이
        largeImageURL : width가 1280인 이미지의 URL (저해상도용)

        api key : pixabay full api 접근 가능용 개인키
        pixabay API 문서 참조 : https://pixabay.com/api/docs/

        :return: dict
        """
        # 이미지 리스트 리턴 (200개)
        image_hits = (
            self.session.request(
                url="https://pixabay.com/api/" +
                    "?key=25876342-aa505c23cebd2518dd1680797" +
                    "&min_width=1920&order=popular&per_page=200",
                method="GET",
            )
            .json()
            .get("hits")
        )

        # random pick one
        pick_one = random.choice(list(image_hits))
        # 고해상도 이미지 URL
        hires_image_url = pick_one.get("imageURL")
        # 저해상도 이미지 URL
        common_image_url = pick_one.get("largeImageURL")
        # 저해상도 이미지의 w/h를 알기 위해 content 데이터 get
        image_response = self.session.request(
            url=common_image_url, method="GET"
        ).content
        # largeImageURL 링크는 가져오지만 해당 저해상도 이미지의 w/h를 알 수 없어 PIL 라이브러리 통해 feeding 후 알아내기
        parse_image = ImageFile.Parser()
        parse_image.feed(image_response)
        # base64 인코딩 (시스템 업로드용)
        common_image_base64 = "data:image/jpeg;base64," + \
                              base64.b64encode(image_response).decode("utf-8")
        hires_image_response = self.session.request(
            url=hires_image_url, method="GET"
        ).content
        hires_image_base64 = "data:image/jpeg;base64," + \
                             base64.b64encode(hires_image_response).decode("utf-8")

        # return dict
        image_dict = defaultdict(dict)
        image_dict.update(
            dict(
                imageName=pick_one.get("pageURL")
                    .split("https://pixabay.com/")[1]
                    .split("/")[1]
                    + ".jpg",
                imageBase64=common_image_base64,
                imageWidth=parse_image.image.width,
                imageHeight=parse_image.image.height,
                imageHiresName=pick_one.get("pageURL")
                    .split("https://pixabay.com/")[1]
                    .split("/")[1]
                    + ".jpg",
                imageHiresBase64=hires_image_base64,
                imageHiresWidth=pick_one.get("imageWidth"),
                imageHiresHeight=pick_one.get("imageHeight"),
            )
        )
        return image_dict

    def get_all_videos(self):
        """
        pixabay API를 호출하여 비디오 데이터를 얻어온 뒤 dictionary 리턴
        1920 해상도 이상인 이미지를 찾아 랜덤하게 하나를 선택, 그 이미지로 저해상도/고해상도 영상 메타데이터를 리턴해준다.

        랜덤 선택 후 videos key의 value 값에는 4가지 유형의 비디오를 리턴한다. [large, medium, small, tiny]
        4가지 유형 중 필요한 데이터 (고해상도/저해상도에 해당하는 비디오의 URL 및 width/height)를 획득 후 dict로 리턴해준다.

        1920 해상도 기준으로 저해상도/고해상도 영상을 구분한다.
        ex. 3840x2160, 1920x1080, 640x360, 150x150 -> 고해상도 w/h : 3840x2160, 저해상도 w/h : 1920x1080
        ex. 1920x1080, 1280x720, 640x360, 150x10 -> 고/저해상도 w/h : 1920x1080

        api key : pixabay full api 접근 가능용 개인키
        pixabay API 문서 참조 : https://pixabay.com/api/docs/

        :return: dict
        """
        # 비디오 리스트 리턴 (200개)
        response = (
            self.session.request(
                url="https://pixabay.com/api/videos/" +
                "?key=25876342-aa505c23cebd2518dd1680797" +
                "&min_width=1920&order=popular&per_page=200",
                method="GET",
            )
            .json()
            .get("hits")
        )

        # random pick one
        pick_one = random.choice(list(response))
        # 필요 로컬 변수 초기화
        width_hires_video, height_hires_video, width_video, height_video = 0, 0, 0, 0
        hires_video_url, video_url = "", ""

        # 고해상도 데이터 할당
        for one in pick_one.get("videos"):
            if pick_one["videos"].get(one)["width"] >= 1920:
                hires_video_url = pick_one["videos"].get(one)["url"]
                width_hires_video, height_hires_video = (
                    pick_one["videos"].get(one)["width"],
                    pick_one["videos"].get(one)["height"],
                )
                break
        # 저해상도 데이터 할당
        for one in pick_one.get("videos"):
            if pick_one["videos"].get(one)["width"] <= 1920:
                video_url = pick_one["videos"].get(one)["url"]
                width_video, height_video = (
                    pick_one["videos"].get(one)["width"],
                    pick_one["videos"].get(one)["height"],
                )
                break

        # base64 인코딩을 위한 작업
        hires_video_response = self.session.request(
            url=hires_video_url, method="GET"
        ).content

        video_response = self.session.request(url=video_url, method="GET").content

        # base64 인코딩
        video_hires_base64 = "data:video/mp4;base64," + base64.b64encode(
            hires_video_response
        ).decode("utf-8")
        video_base64 = "data:video/mp4;base64," + base64.b64encode(
            video_response
        ).decode("utf-8")
        # return dict
        video_dict = defaultdict(dict)
        video_dict.update(
            dict(
                videoName=pick_one.get("videos")["large"]["url"]
                    .split("https://cdn.pixabay.com/vimeo/")[1]
                    .split("/")[1]
                    .split("?")[0],
                videoBase64=video_base64,
                videoWidth=width_video,
                videoHeight=height_video,
                videoHiresName=pick_one.get("videos")["large"]["url"]
                    .split("https://cdn.pixabay.com/vimeo/")[1]
                    .split("/")[1]
                    .split("?")[0],
                videoHiresBase64=video_hires_base64,
                videoHiresWidth=width_hires_video,
                videoHiresHeight=height_hires_video,
            )
        )

        return video_dict
