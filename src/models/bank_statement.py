from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class BankHeader:
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    account_number: Optional[str] = None
    agency: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    initial_balance: Optional[float] = None
    final_balance: Optional[float] = None

@dataclass
class BankTransaction:
    movement_date: datetime  # Dt. movimento
    balance_date: Optional[datetime] = None  # Dt. balancete
    description: str = ""  # Histórico
    document: Optional[str] = None  # Documento
    value: float = 0.0  # Valor R$
    balance: Optional[float] = None  # Saldo
    type: Optional[str] = None  # 'debit' or 'credit'
    
    def to_dict(self):
        return {
            'dt_movimento': self.movement_date.strftime('%d/%m/%Y'),
            'dt_balancete': self.balance_date.strftime('%d/%m/%Y') if self.balance_date else '',
            'historico': self.description,
            'documento': self.document or '',
            'valor': self.value,
            'saldo': self.balance,
            'tipo': self.type
        }

@dataclass
class BankStatement:
    header: BankHeader
    transactions: List[BankTransaction]
    
    def to_dataframe(self):
        import pandas as pd
        return pd.DataFrame([t.to_dict() for t in self.transactions])