import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
import json
import re

# SSL 경고 메시지 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API 설정
API_KEY = '2N5eiWa4zz2u3wj6ntsxPlT9YlgcIxZkLwKZQJJmmLo'

def extract_cctv_info(soup):
    """HTML에서 CCTV 정보를 추출하는 함수"""
    cctv_list = []
    links = soup.find_all('a')
    
    current_name = None
    for link in links:
        href = link.get('href')
        text = link.get_text().strip()
        
        if href and 'javascript:test' in href:
            # CCTV ID 추출
            cctv_id = re.search(r"'(E\d+)'", href)
            if cctv_id:
                cctv_id = cctv_id.group(1)
                name = text.split('.')[1] if '.' in text else text
                cctv_list.append({
                    'id': cctv_id,
                    'name': name,
                })
    
    return cctv_list

def get_cctv_stream_url(cctv_id):
    """CCTV 스트리밍 URL을 가져오는 함수"""
    try:
        session = requests.Session()
        session.verify = False
        
        # CCTV 스트리밍 URL을 가져오는 API 엔드포인트 
        stream_url = 'https://www.utic.go.kr/guide/cctvOpenData.do?key=2N5eiWa4zz2u3wj6ntsxPlT9YlgcIxZkLwKZQJJmmLo'
        params = {
            'apiKey': API_KEY,   # ← 여기에 본인의 실제 API 키 입력
            'type': 'its',        # 국도 (서울 시내 포함)
            'cctvType': '1',      # 실시간 스트리밍 영상만
            'minX': 127.02619934,     # 강남대로 시작점 부근 경도
            'maxX': 127.02619934,     # 강남대로 끝점 부근 경도
            'minY': 37.5013504,      # 강남대로 시작점 부근 위도
            'maxY': 37.5013504,      # 강남대로 끝점 부근 위도
            'getType': 'xml'      # XML로 받을 것
                }
        
        response = session.get(stream_url, params=params, verify=False)
        print(f"API 응답 ({cctv_id}):")
        print(response.text)  # 디버깅용 출력
        
        if response.status_code == 200:
            # XML 응답 파싱
            from xml.etree import ElementTree as ET
            root = ET.fromstring(response.text)
            
            # items > item > cctvurl 경로로 검색
            cctv_url = root.find('.//items/item/cctvurl')
            if cctv_url is not None:
                return cctv_url.text
            else:
                print(f"cctvurl 태그를 찾을 수 없습니다. XML 구조: {ET.tostring(root, encoding='unicode')}")

        return None
        
    except Exception as e:
        print(f"스트리밍 URL 조회 실패 ({cctv_id}): {str(e)}")
        return None

def test_api_connection():
    try:
        session = requests.Session()
        session.verify = False
        
        # CCTV 목록 API URL
        base_url = 'http://www.utic.go.kr/guide/cctvOpenData.do'
        params = {
            'key': API_KEY,
            'type': 'ex'
        }
        
        headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0'
        }
        
        print("=== CCTV 목록 요청 ===")
        response = session.get(base_url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            cctv_list = extract_cctv_info(soup)
            
            print("\n=== CCTV 정보 및 스트리밍 URL ===")
            for cctv in cctv_list:
                stream_url = get_cctv_stream_url(cctv['id'])
                print(f"이름: {cctv['name']}")
                print(f"ID: {cctv['id']}")
                print(f"스트리밍 URL: {stream_url}\n")
                
    except Exception as e:
        print(f"예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    test_api_connection()