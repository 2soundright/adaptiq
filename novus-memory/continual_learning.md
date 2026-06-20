# Continual Learning System

## How AdaptIQ Improves Over Time

AdaptIQ features a continual learning system that automatically adapts the knowledge base based on user interactions and feedback. This ensures the AI assistant becomes more accurate and relevant over time without manual intervention.

### Feedback-Driven Relevance
- When users rate responses, the system adjusts the **relevance score** of the document chunks that contributed to that answer
- Positive feedback (3+ stars) increases chunk relevance; negative feedback decreases it
- The adjustment magnitude is controlled by **plasticity** — a value that determines how responsive each chunk is to new feedback

### Elastic Weight Consolidation (EWC)
Inspired by the EWC technique from neural network research, AdaptIQ uses a plasticity formula:

- **New/untested chunks** have high plasticity and adapt quickly to feedback
- **Well-established chunks** (high usage count) have low plasticity and change slowly
- This prevents a single piece of bad feedback from degrading well-validated knowledge

### Drift Detection
The system monitors the distribution of incoming queries over time:
- Compares recent query embeddings against historical ones using cosine similarity
- If the average similarity drops below a threshold (0.7), **concept drift** is detected
- During drift, plasticity is boosted by 50% so the knowledge base can adapt faster to new topics
- Admins can monitor drift status on the Analytics dashboard

### Replay Buffer
- The last 500 Q&A pairs are stored with their embeddings in a replay buffer
- This data feeds the drift detection system and can be sampled for future model updates
- The buffer automatically prunes old entries to maintain a fixed size
