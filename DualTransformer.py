import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiHeadCrossAttention(nn.Module):
    """
    크로스 어텐션 메커니즘을 통해 뉴스의 컨텍스트를 가격 데이터 투영에 융합.
    """
    def __init__(self, d_model=64, nhead=4):
        super().__init__()
        self.multihead_attn = nn.MultiheadAttention(embed_dim=d_model, num_heads=nhead, batch_first=True)
        self.layer_norm = nn.LayerNorm(d_model)

    def forward(self, query, key, value):
        # query: price context (B, L_p, d_model)
        # key/value: news context (B, L_n, d_model)
        attn_output, _ = self.multihead_attn(query, key, value)
        return self.layer_norm(query + attn_output)

class NewsEncoder(nn.Module):
    """
    RSS 피드, CryptoCompare 등에서 수집된 뉴스/소셜 텍스트 임베딩을 인코딩.
    """
    def __init__(self, news_dim=768, d_model=64, nhead=4, num_layers=2):
        super().__init__()
        # 로버타(RoBERTa)나 핀버트(FinBERT) 같은 768차원을 d_model 차원으로 압축
        self.embedding = nn.Linear(news_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
    def forward(self, news_features):
        # news_features: (B, L_n, news_dim) -> (B, L_n, d_model)
        x = self.embedding(news_features)
        out = self.transformer(x)
        return out

class PriceEncoder(nn.Module):
    """
    시계열 가격 데이터(OHLCV 등) 및 기술적 지표 인코딩.
    """
    def __init__(self, price_dim=7, d_model=64, nhead=4, num_layers=2):
        super().__init__()
        self.embedding = nn.Linear(price_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
    def forward(self, prices):
        # prices: (B, L_p, price_dim) -> (B, L_p, d_model)
        x = self.embedding(prices)
        out = self.transformer(x)
        return out

class DualTransformerAIModel(nn.Module):
    """
    Chen & Kawashima 논문 기반 Dual Transformer 예측 모델 구현체.
    뉴스 스트림과 가격 스트림을 병렬로 인코딩한 뒤, 크로스 어텐션(Cross-Attention) 메커니즘을 통해 
    이종(Heterogeneous) 데이터를 결합합니다.
    """
    def __init__(self, news_dim=768, price_dim=7, d_model=64, num_companies=13):
        super().__init__()
        self.news_encoder = NewsEncoder(news_dim, d_model)
        self.price_encoder = PriceEncoder(price_dim, d_model)
        
        # 퓨전 레이어 (Cross-Attention 기반)
        self.cross_attention = MultiHeadCrossAttention(d_model=d_model, nhead=4)
        
        # 최종 예측 (분류 또는 회귀)
        # B x num_companies 차원으로 각 종목별 상승/하락 트렌드 예측 
        self.fc_out = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, num_companies)
        )
        
    def forward(self, news_features, prices):
        """
        입력 텐서 규격:
        news_features: (B, Seq_N, News_Dim) - RSS 및 외부 API 연동 뉴스 임베딩
        prices: (B, Seq_P, Price_Dim) - 과거 가격 데이터
        """
        # 개별 인코더 통과
        news_context = self.news_encoder(news_features)  # (B, Seq_N, d_model)
        price_context = self.price_encoder(prices)       # (B, Seq_P, d_model)
        
        # Cross Attention: 가격 데이터를 Query로, 뉴스 데이터를 Key/Value로 사용하여 융합
        fused_context = self.cross_attention(query=price_context, key=news_context, value=news_context) # (B, Seq_P, d_model)
        
        # 결과 투영: 시계열의 마지막 스텝 융합 결과를 바탕으로 예측 수행
        last_step_feature = fused_context[:, -1, :] # (B, d_model)
        pred = self.fc_out(last_step_feature)       # (B, num_companies)
        return pred
