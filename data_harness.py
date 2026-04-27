import torch
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class DataHarness(ABC):
    """
    Chen & Kawashima (Dual Transformer) 모델을 위한 데이터 공급 추상화 파이프라인.
    """
    
    @abstractmethod
    def fetch_news_sentiment_data(self) -> torch.Tensor:
        """
        NewsEncoder를 위한 텍스트 관련 입력부 (RSS / CryptoCompare 기반 임베딩 차원).
        Returns:
            torch.Tensor: (Batch Size, Sequence Length (News), News Dim=768) 형태의 텐서
        """
        pass

    @abstractmethod
    def fetch_price_data(self) -> torch.Tensor:
        """
        PriceEncoder를 위한 시장 데이터 입력부
        Returns:
            torch.Tensor: (Batch Size, Sequence Length (Price), Feature Dim=7)
        """
        pass

class LocalFileDataHarness(DataHarness):
    """로컬 테스트를 위한 더미/파일 기반 하네스 구현체"""
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def fetch_news_sentiment_data(self) -> torch.Tensor:
        # 실제 환경에서는 RSS 피드와 API 수집 뉴스를 LLM이나 TF-IDF, RoBERTa 등으로 임베딩.
        # 더미 반환 예시: Batch=16, Seq=10, NewsDim=768
        print(f"[LocalFileHarness] Fetching news/sentiment data from {self.data_dir}...")
        return torch.randn(16, 10, 768)

    def fetch_price_data(self) -> torch.Tensor:
        # 더미 반환 예시: Batch=16, Seq=96, Features=7 (OHLCV 등)
        print(f"[LocalFileHarness] Fetching price data from {self.data_dir}...")
        prices = torch.randn(16, 96, 7)
        return prices

class AzureBlobDataHarness(DataHarness):
    """Azure Blob Storage 실시간 스트리밍용 하네스"""
    def __init__(self, conn_str: str, container_name: str):
        self.container_name = container_name
        
    def fetch_news_sentiment_data(self) -> torch.Tensor:
        # Blob 저장소에서 수집된 RSS/Cryptocompare JSON을 텍스트 임베딩화 (Batch=16, Seq=10, Dim=768)
        return torch.zeros(16, 10, 768)
        
    def fetch_price_data(self) -> torch.Tensor:
        # 시계열 가격 데이터 Blob에서 로딩 및 전처리 (Batch=16, Seq=96, Dim=7)
        return torch.zeros(16, 96, 7)

# ==== 사용 예시 ====
if __name__ == "__main__":
    # 사용 환경에 따라 하네스 교체 (의존성 주입)
    harness: DataHarness = LocalFileDataHarness("./dataset")
    
    news_batch = harness.fetch_news_sentiment_data()
    prices_batch = harness.fetch_price_data()
    
    print(f"News Shape: {news_batch.shape} (B, Seq_N, News_Dim)")
    print(f"Prices Shape: {prices_batch.shape} (B, Seq_P, Price_Dim)")
