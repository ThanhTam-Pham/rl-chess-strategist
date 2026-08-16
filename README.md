# The Chess Strategist (RL Board Games Platform)

## Overview

This repository contains the source code for an integrated Artificial Intelligence platform featuring advanced Reinforcement Learning (RL) and heuristic search agents capable of playing three distinct board games: Chess, Xiangqi (Chinese Chess), and Go. 

## Key Technical Features

* **Multi-Game AI Engine:** Implemented specialized RL and rule-based agents tailored to handle the varying rules, move-generation logic, and massive state-space complexities of Chess, Xiangqi, and Go.
* **Reinforcement Learning (Q-Learning):** Developed adaptive agents utilizing Q-table updates (`q_learning.py`) with customizable reward logic (`reward_logic.py`) based on piece valuation dynamics and step penalties.
* **Stockfish Integration for Chess:** Integrated the Stockfish UCI engine (`chess_engine.py`) to support high-performance decision making, featuring both full-power execution and targeted ELO throttling/difficulty settings.
* **Dynamic Difficulty Tiers:** Designed multiple progression tiers (Easy, Medium/Normal, and Hard) by fine-tuning exploration-exploitation parameters ($\epsilon$-greedy) and heuristic search depths.
* **Interactive Graphical Interface:** Built an interactive platform using Pygame with dedicated game loops (`main.py`, `chess_game.py`, `xiangqi_game.py`, `go_game.py`) supporting Player vs Environment (PvE) and Environment vs Environment (EvE) modes.

## Difficulty Tiers Configuration

* **Easy Mode:** Utilizes baseline randomization combined with simple heuristic checks (e.g., prioritizing immediate captures or checking moves) for responsive and accessible gameplay.
* **Medium / Normal Mode:** Leverages Reinforcement Learning (Q-Learning) agents trained via Q-tables, balancing exploration and exploitation ($\epsilon \approx 0.10 - 0.15$) with reward shaping.
* **Hard Mode:** Features advanced configurations with very low exploration rates ($\epsilon \approx 0.03$), minimax/heuristic evaluation pruning, or Stockfish engine integration configured for high-level competitive play.

## Repository Structure

```text
rl-chess-strategist/
│
├── assets/                    # UI elements, fonts, and piece graphics for games
├── data/                      # Stored datasets, Q-tables, and JSON configurations
├── docs/                      # Official project documents and user manuals
├── engines/                   # Game engines and third-party binaries (e.g., Stockfish)
├── games/                     # Pygame UI and game loop implementations (chess, xiangqi, go)
├── rl_agents/                 # Core RL framework, Q-learning algorithms, and reward logic
│
├── main.py                    # Main entry point and menu runner
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation
