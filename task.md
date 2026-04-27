### [STEP 0] 인프라 및 CI/CD 컨트롤 타워 구축
- `[x]` 인프라 리소스 배포 (Resource Group 및 B1s VM 생성, 새로운 SSH Key 발급)
- `[x]` VM 내부 환경 초기화 (Docker & Azure CLI 설치)
- `[x]` GitHub Self-hosted Runner 셋업 스크립트 작성 및 배포
- `[x]` 로컬 `.ssh/config` 접속 환경 세팅
- `[x]` `.env` 보안 환경설정 파일 생성
- `[x]` `deploy.yml` 작성 및 Azure CI/CD 파이프라인 구성

### [STEP 1] GitHub 소스 분석 및 하네스 인터페이스 설계
- `[x]` Dual Transformer 모델 구조 (NewsEncoder, PriceEncoder) 입출력 분석
- `[x]` `DataHarness` 인터페이스 (추상 클래스) 설계 및 `data_harness.py` 생성
- `[x]` 로컬/Azure/API 호환용 데이터 주입부 수정 (`Dual Transformer.py` 또는 `train.py`)

### [STEP 2] Azure Functions 기반 다중 소스 수집 하네스
- `[x]` `function_app.py` Timer Trigger (30분 주기) 생성
- `[x]` `collectors/cryptocompare_api.py` (전문 뉴스 수집, CryptoCompare 기반) 작성
- `[x]` `collectors/rss_scraper.py` (소셜감성/경제지 RSS 수집) 작성
- `[x]` Cursor 기반 데이터 정합성 보장 로직 (중복제거/소급수집) 적용

### [STEP 3] Azure VM(Spot) 및 환경 최적화 설정
- `[x]` Spot VM (`Standard_NC4as_T4_v3`) 인프라 자동 생성 스크립트 작성 (`Eviction: Deallocate`)
- `[x]` GPU 드라이버 및 CUDA 자동 셋업 쉘 스크립트 또는 Azure Extension 세팅 자동화 구현
- `[x]` 로컬 IDE `.ssh/config` 접속 설정 갱신 적용

### [STEP 4] 이중 트랜스포머 모델 하네스 엔지니어링
- `[x]` `train_harness.py`: Data Bridge 모듈 결합 스크립트화
- `[x]` Spot Checkpointing 로직 작성 (매 에포크/10분 Blob Storage 저장 및 복구 `Resume` 로직)
- `[x]` Mixed Precision (`torch.amp.autocast`) 및 T4 메모리 자동 최적화 적용
- `[x]` CI/CD 배포 파이프라인(`deploy.yml` -> `main.yml`)과 Spot VM Bootup 스크립트 연동

### [STEP 5] A-Z 마스터 오케스트레이션 (비용 완전 차단)
- `[x]` `orchestrator.py` 제작 (Blob Storage 데이터 감시 데몬)
- `[x]` `az vm start` (Spot 자원 요청) 및 `az vm deallocate` (완료 후 리소스 소멸) 상태 머신 로직 적용
- `[x]` B1s 컨트롤 타워 서버에 Orchestrator 데몬화(Cron 잡 또는 백그라운드 등록)
