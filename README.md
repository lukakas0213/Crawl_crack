# WRT Tech Assignment

웹 크롤링과 Apache Airflow, Docker를 활용한 데이터 파이프라인 프로젝트입니다.

---

## 프로젝트 구조

아래는 이 프로젝트의 주요 폴더와 파일 구조입니다.

```
wrt_tech_assignment 프로젝트 구성:

- crawler                크롤링 코드가 담긴 폴더
  - crawl_get_info.py    메인 크롤링 스크립트
- dags                   Airflow DAG 파일 폴더
  ─ crawl_character_dag.py
- data                   크롤링 결과 저장용 폴더
  ─ characters.csv
  - categories.csv
- db                     데이터베이스 관련 폴더
- docker-compose.yml     도커 컴포즈 설정 파일
- Dockerfile.crawler     크롤러용 도커파일
- requirements.txt       파이썬 패키지 목록
- README.md              프로젝트 설명 문서
```


---

## 프로젝트 설명
- 웹 크롤링: selenium 등으로 캐릭터/카테고리 데이터 수집
- 데이터 저장: PostgreSQL DB에 저장, CSV 파일로도 저장
- 워크플로우 관리: Apache Airflow DAG로 크롤링 자동화
- 컨테이너화: Docker, docker-compose로 손쉬운 환경 구축
- 의존성 관리: Poetry 사용

---

## 데이터 파이프라인 실행 방법

### 1. Docker 컨테이너
```bash
# 컨테이너 빌드 및 실행
docker-compose up --build -d

# Airflow 웹 UI 접속 (http://localhost:8080)

# 컨테이너 중지
docker-compose down
```

---

## 크롤링 결과 파일
- `characters.csv` : 크롤링된 캐릭터 데이터
- `categories.csv` : 크롤링된 카테고리 데이터

---

## Airflow 웹 UI 접속 정보

- 주소: http://localhost:8080
- 기본 아이디: admin
- 기본 비밀번호: admin


