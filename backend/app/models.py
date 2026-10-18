from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String

from .database import Base


class Transaction(Base):
    __tablename__ = "scored_payments"

    id = Column(Integer, primary_key=True, index=True)
    txn_id = Column(String(36), unique=True, index=True, nullable=False)
    source_id = Column(String(30))            # transaction_id from the CSV
    amount = Column(Float, nullable=False)
    merchant_category = Column(String(60))
    merchant_country = Column(String(30))
    channel = Column(String(30))
    fraud_probability = Column(Float)         # 0 to 1, from the model
    is_fraud = Column(Boolean, default=False, index=True)   # the model's verdict
    true_class = Column(Boolean, default=False)             # the real label from the CSV
    fraud_type = Column(String(60))
    features = Column(JSON)                   # all model inputs
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "txn_id": self.txn_id,
            "source_id": self.source_id,
            "amount": round(self.amount, 2),
            "merchant_category": self.merchant_category,
            "merchant_country": self.merchant_country,
            "channel": self.channel,
            "fraud_probability": round(self.fraud_probability, 4),
            "is_fraud": self.is_fraud,
            "true_class": self.true_class,
            "fraud_type": self.fraud_type,
            "created_at": self.created_at.isoformat(),
        }
