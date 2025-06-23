# RL Agent Q-value/Loss Explosion: Issues & Next Steps

## Summary of Observed Issues
- **Q-value and loss explosion**: During long training runs, both Q-values and target Q-values (min, mean, max) increase rapidly after ~200 episodes, reaching extremely high values (millions). Losses also become very large, indicating divergence.
- **Instability after initial stability**: The agent is stable for the first 100-200 episodes, but then diverges, as shown in wandb charts.
- **Agent performance**: The agent does not outperform random or simple heuristic baselines, likely due to instability.

## Suspected Causes
- Learning rate may still be too high for this environment.
- Overestimation bias in vanilla DQN (Double DQN may help).
- Lack of reward normalization (reward clipping is already used).
- Target network update frequency or batch size may be suboptimal.
- Network architecture or initialization may contribute.

## Next Steps
- Try further lowering the learning rate.
- Implement Double DQN to reduce overestimation.
- Consider Q-value clipping or reward normalization.
- Review target network update frequency and batch size.
- Explore architectural changes if needed.

---

*This summary documents the current issues and planned directions for stabilizing DQN training in Othello. See wandb charts for details.*
