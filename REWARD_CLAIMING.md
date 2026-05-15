# Reward Claiming Logic

## Answer: Yes, claiming reduces points

Points act as currency. When a reward is claimed, the cost is deducted from the user balance.

## Data Model

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    points_balance INTEGER DEFAULT 0,
    total_earned INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0
);

CREATE TABLE point_transactions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    type VARCHAR(50),  -- earn, spend, refund
    amount INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE reward_claims (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    reward_id UUID REFERENCES rewards(id),
    points_spent INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Implementation

```python
class RewardService:
    def claim_reward(self, user_id, reward_id):
        balance = self.get_balance(user_id)
        reward = self.get_reward(reward_id)
        
        if balance < reward.cost:
            raise InsufficientPointsError()
        
        with self.db.transaction():
            self.deduct_points(user_id, reward.cost)
            self.record_transaction(user_id, 'spend', reward.cost)
            self.create_claim(user_id, reward_id, reward.cost)
        
        return {"new_balance": balance - reward.cost}
```

## Key Rules

- Atomic transactions prevent double-spending
- Full audit trail in point_transactions
- Refund support via 'refund' type
- Points expire via scheduled jobs
