# Azure 환경 마이그레이션 및 파이프라인 재배포 가이드

본 문서는 현재 사용 중인 Azure 구독을 삭제하고, **새로운 Azure 구독으로 전체 시스템(Dual Transformer ML 플랫폼)을 다시 구축(마이그레이션)할 때 사용하는 마스터 가이드**입니다.

모든 소스 코드와 로직은 GitHub(`https://github.com/wildparksm/when.git`)에 안전하게 백업되어 있으므로, 새 구독이 준비되면 아래 명령어들을 터미널에 순서대로 복사+붙여넣기 하여 인프라를 복구할 수 있습니다.

---

## 🛑 사전 준비 (Prerequisites)
1. 새로운 Azure 구독(Subscription) 생성 및 활성화
2. 로컬 터미널에서 새 구독으로 로그인
   ```bash
   az login
   az account set --subscription "<새_구독_ID_또는_이름>"
   ```

---

## 🏗️ 1단계: 기본 인프라 및 스토리지 구성

Azure 리소스 그룹과 데이터를 저장할 Blob Storage를 생성합니다.

```bash
# 1. 리소스 그룹 생성 (한국 중부)
az group create --name DualTransformer_RG --location koreacentral

# 2. 스토리지 계정 생성 (이름은 전 세계 고유해야 하므로 변경 필요, 예: dualtransstore2027)
STORAGE_NAME="dualtransstore2027"
az storage account create \
  --name $STORAGE_NAME \
  --resource-group DualTransformer_RG \
  --location koreacentral \
  --sku Standard_LRS

# 3. 스토리지 연결 문자열(Connection String) 확보 
# (출력되는 값을 메모장에 복사해두세요. Function App과 .env 파일에 필요합니다)
az storage account show-connection-string -g DualTransformer_RG -n $STORAGE_NAME -o tsv

# 4. Blob 컨테이너 생성
az storage container create --account-name $STORAGE_NAME --name raw-data
az storage container create --account-name $STORAGE_NAME --name checkpoints
```

---

## ⚙️ 2단계: 컨트롤 타워 (B1s VM) 컨트롤러 배포

GitHub CI/CD Runner와 Orchestrator 데몬이 상시 구동될 B1s 저사양 VM을 생성합니다.

```bash
# 1. B1s VM 생성 (Ubuntu 22.04)
az vm create \
  --resource-group DualTransformer_RG \
  --name control-tower \
  --image Ubuntu2204 \
  --size Standard_B1s \
  --admin-username azureuser \
  --generate-ssh-keys

# 2. 시스템 시간 KST 통일 (SSH 접속 후 수행)
# ssh azureuser@<생성된_B1s_공인IP>
# sudo timedatectl set-timezone Asia/Seoul
```
*💡 B1s VM 셋업이 끝나면 GitHub Repository (Settings -> Actions -> Runners)에서 새 Self-hosted runner를 설정 스크립트에 따라 B1s 안에 설치해주세요.*

---

## 📡 3단계: 다중 소스 주기적 수집기 (Azure Functions) 배포

API 및 RSS 데이터를 주기적으로 긁어올 서버리스 앱을 배포합니다.

```bash
# 1. 함수 앱 생성 (소비 플랜, 이름 고유해야 함)
FUNC_APP_NAME="dual-trans-collector"
az functionapp create \
  --resource-group DualTransformer_RG \
  --consumption-plan-location koreacentral \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name $FUNC_APP_NAME \
  --os-type linux \
  --storage-account $STORAGE_NAME

# 2. 필수 환경 변수 주입 (시간대, API 키, Blob 커넥션스트링)
az functionapp config appsettings set \
  --name $FUNC_APP_NAME \
  --resource-group DualTransformer_RG \
  --settings \
    "TZ=Asia/Seoul" \
    "CRYPTOCOMPARE_API_KEY=<크립토컴페어_API_키>" \
    "AzureWebJobsStorage=<1단계에서_확보한_연결문자열>"

# 3. 코드 배포 (로컬 깃허브 클론 폴더 내부에서 실행)
cd azure-functions-collection
func azure functionapp publish $FUNC_APP_NAME
```

---

## 💻 4단계: GPU 머신 (Spot VM) 프로비저닝 세팅

학습 시에만 잠깐 켜질 `ml-spot-vm`을 설정합니다. (생성 후 종료해둠)

```bash
# 1. Spot GPU VM 생성 (T4 GPU, 할당해제 정책 지정)
az vm create \
  --resource-group DualTransformer_RG \
  --name ml-spot-vm \
  --image Ubuntu2204 \
  --size Standard_NC4as_T4_v3 \
  --admin-username azureuser \
  --priority Spot \
  --eviction-policy Deallocate \
  --generate-ssh-keys

# 2. NVIDIA 드라이버 확장 프로그램 자동 설치
az vm extension set \
  --resource-group DualTransformer_RG \
  --vm-name ml-spot-vm \
  --name NvidiaGpuDriverLinux \
  --publisher Microsoft.HpcCompute \
  --version 1.2

# 3. 초기 세팅 완료 후 즉시 할당 해제(과금 정지)
az vm deallocate --resource-group DualTransformer_RG --name ml-spot-vm
```

---

## 🚀 5단계: Orchestrator 데몬 파이프라인 가동 (Final)

1. 컨트롤 타워(B1s VM) 내부에 배포된 폴더로 이동합니다.
2. `orchestrator.py` 의 라인 9 에 있는 `AzureWebJobsStorage` 변수 부분에 **새 구독의 스토리지 연결 문자열**을 업데이트합니다.
3. 백그라운드로 데몬을 켭니다.
   ```bash
   nohup python3 orchestrator.py > ~/orchestrator.log 2>&1 &
   ```

**🎉 이제 마이그레이션이 완료되었습니다! 데이터가 차오르면 새 구독 환경에서도 스스로 GPU를 켜고 끄며 Dual Transformer 모델을 학습시킵니다.**
