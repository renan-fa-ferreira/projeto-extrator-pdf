from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Transaction:
    date: datetime
    description: str
    value: float
    balance: Optional[float] = None
    type: Optional[str] = None  # 'debit' or 'credit'
    
    def to_dict(self):
        return {
            'data': self.date.strftime('%d/%m/%Y'),
            'descricao': self.description,
            'valor': self.value,
            'saldo': self.balance,
            'tipo': self.type
        }