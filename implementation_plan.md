# Dual Transformer ML 플랫폼 구축 완료 보고서

프로젝트의 지속적인 통합/배포(CI/CD) 통제, 데이터 파이프라인(Harness Engineering), 비용 통제형 학습 파이프라인(Master Orchestration)을 아우르는 최종 명세입니다.

## Final Status: ALL STEPS COMPLETED 🚀

모든 인프라와 파이프라인 컴포넌트가 성공적으로 작성 및 구동 환경에 배포되었습니다. 

---

### [STEP 0] 인프라 및 CI/CD 컨트롤 타워 구축 (완료)
- `DualTransformer-Control` (B1s VM) 셋업 및 GitHub Self-Hosted Runner 연동 완료.
- **`.github/workflows/deploy.yml`**: B1s 및 Spot GPU VM(가동 시)으로의 자동 CD 동기화 완료.

---

### [STEP 1] GitHub 소스 분석 및 하네스 설계 (완료)
- **`data_harness.py`**: 로컬/Azure 데이터를 모델 입력용 텐서 규격`(B, L, C)`과 `(B, L, D)`로 완벽히 맞추는 `DataBridge` 추상 클래스 설계 완료.

---

### [STEP 2] Azure Functions 다중 소스 수집 하네스 (완료)
- `CryptoCompare API` 및 RSS Feed (Bloomberg, Reuters) 수집기와 30분 타이머 트리거 연동.
- Azure Storage Account (`dualtransstore2026`) 커넥션 스트링 맵핑 완료.
- 서버리스 중단 시 Blob 커서를 통한 '정합성/소급' 방어 로직 적용 완료.

---

### [STEP 3] Azure VM(Spot) 및 환경 최적화 설정 (완료)
- `Standard_NC4as_T4_v3` Spot 인스턴스(--eviction-policy Deallocate) 프로비저닝 완료.
- Azure Extension을 활용한 NVIDIA Driver 및 CUDA 즉시 할당 완료. 
- 로컬 `~/.ssh/config` 내 `spot-gpu` 호스트 터널링 완료.

---

### [STEP 4] 이중 트랜스포머 학습 하네스 엔지니어링 (완료)
Chen & Kawashima 모델의 훈련 루프(`train_harness.py`)를 Spot 및 T4 한계에 맞춰 마개조 완료했습니다.
- **Data Bridge 연동**: Azure Blob의 최신 데이터를 가져오는 `AzureBlobDataHarness` 모듈 주입 대기 완비.
- **Spot-Resilient Checkpointing**: Spot VM 강제 할당 해제를 완벽 방어하기 위해 `.pth` 가중치를 Azure Blob Storage로 즉시 전송. 학습 재시작 시 최종 Epoch부터 `Resume` 하도록 생존력 부여.
- **T4 Mixed Precision**: 16GB VRAM 초과(OOM) 방지를 위해 `torch.amp.autocast()` 적용. 메모리 밸런싱 및 속도 향상 달성.

---

### [STEP 5] A-Z 마스터 오케스트레이터 (완료 및 데몬화)
단 돈 1원의 누수도 차단하는 **무인 상태머신(State-Machine)**, `orchestrator.py`가 컨트롤 타워(B1s) 장비에 이식되어 백그라운드로 돌아가기 시작했습니다!
- **로직**: Blob Storage 데이터 감시 ➡️ 데이터량이 충족되면 GPU Spot VM 전원 ON (`az vm start`) ➡️ Run-command를 통한 `train_harness.py` 트리거 ➡️ 완료(또는 중단) 시 즉각 GPU VM 할당 해제 (`az vm deallocate`).
- **현재 상태**: B1s 내부 터미널 백그라운드 환경(`nohup`)에서 데몬이 실행 중이며, `~/orchestrator.log` 경로를 통해 감시 활동 내역을 24시간 추적 기록 중입니다.

### 🎉 Verification Checklist
1. 컨트롤 타워 상태 감지: `ssh control-tower` 후 `tail -f ~/orchestrator.log` 커맨드로 30분 주기 감시 루틴 확인 가능.
2. 수집 데이터가 임계점(테스트 기준 5건)을 돌파하면 자동으로 `ml-spot-vm` 자원이 Azure Portal 상에서 켜졌다가, 코드 실행 후 즉시 꺼지는 상태 전이(State Transition) 완료!
---

### [STEP 6] Chen & Kawashima Dual Transformer 모델 이식 (진행 완료)
- **DualTransformer.py 아키텍처 재구축**: 
  - 단순 Pooling을 Cross-Attention 기반의 퓨전(Fusion) 모델(MultiHeadCrossAttention)로 고도화 전환 완료.
  - 텍스트 임베딩을 전담하는 NewsEncoder 및 시계열 지표를 전담하는 PriceEncoder 로직 분리 적용.
- **data_harness.py 입출력 텐서 정렬 (Interface Alignment)**: 
  - RSS 피드 및 CryptoCompare에서 가져온 해외 뉴스 API를 RoBERTa/FinBERT 수준으로 토큰화할 상황을 대비하여 차원(News_Dim)을  상향 설계.
  - (Batch, Seq_N, 768) 및 (Batch, Seq_P, 7)로 입력단 정합성 검증 완료.

