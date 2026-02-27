# 🌐 WorldSim — Adaptive Resource Scarcity and Strategy Evolution Simulator

**We didn't program strategies. We created conditions — and strategies emerged.**

![Python](https://img.shields.io/badge/Python-3.11-blue)
![React](https://img.shields.io/badge/React-18-lightblue)
![Firebase](https://img.shields.io/badge/Firebase-Firestore-yellow)
![FastAPI](https://img.shields.io/badge/FastAPI-0.105-green)
![Hackathon 2026](https://img.shields.io/badge/Hackathon-2026-purple)

---

## 🧩 The Problem

Natural resources are the silent engine of human civilization, and yet billions
of people currently face acute shortages. 2 billion people live in water-scarce
regions; roughly 40 % of modern conflicts have a documented resource component.

Studying resource-driven conflict is difficult because real-world data is messy,
dynamic, and often classified. Traditional models rigidly codify strategies or
assume perfect rationality. They do not capture the feedback loops between
scarcity, trust, adaptation, and geography.

Existing academic tools like system dynamics, agent-based frameworks or game
theoretic simulations either produce abstract graphs or require extensive
data curation. They seldom allow a layperson to *see* and *play* with the
outcomes in real time.

What’s missing is a live, interactive sandbox in which agents discover their
own tactics as conditions change — a place where observers can witness
emergent geopolitics without writing a single rule.

---

## 🔧 Our Solution

**WorldSim** is a real‑time geopolitical simulation built for exploration,
education, and experimentation. Five fictional regions mapped to real-world
blocs compete for finite resources over 20 cycles (years 2025‑2045). Each
region is governed by an adaptive agent that starts with no strategy; it learns
by observing the world and receiving rewards based on health and survival.

Agents update their internal strategy weights through a simple reward-feedback
loop. They are *not* hardcoded with behaviors; instead, strategies **emerge**
from the interplay of incentives, geography, and trust.

The frontend dashboard—built in React and Tailwind—listens to Firestore in
real time. Observers can watch resources ebb and flow, trades arc across the
map, and strategies evolve cycle by cycle.

> **Core innovation:** Adaptive weight evolution — observe, decide, reward,
> update — genuine emergence in real time.

---

## ⭐ What Makes It Unique

| Feature                                 | WorldSim                                       | Traditional Models                        |
|----------------------------------------|------------------------------------------------|-------------------------------------------|
| Emergence                              | ✅ Agents discover strategies autonomously     | ❌ Often pre-defined or limited           |
| Visualization                          | ✅ Live interactive map & charts               | ❌ Static plots or offline analysis       |
| Trust / Diplomacy                      | ✅ Trust‑gated trade/conflict                   | ❌ Rarely modeled in ABM                   |
| Geopolitical Real‑World Mapping        | ✅ Regions correspond to Brazil, India, etc.   | ❌ Abstract populations                    |
| Analysis Layer                         | ✅ Chatbot + post‑run reports                  | ❌ Manual interpretation                   |
| Accessibility                          | ✅ Web UI, no programming required            | ❌ Domain expertise needed                 |

### Three Key Innovations

1. **Adaptive weight evolution** with reward formula that allows agents to
   tune trade/hoard/invest/aggress weights based on outcomes. We built a
   lightweight reinforcement‑style loop, not a neural net.

2. **Trust‑gated diplomacy system** where region-to-region trust accrues from
   successful trades and decays after rejections. Trust thresholds unlock
   alliance and aggression behaviors, producing realistic diplomatic cycles.

3. **Real-world geopolitical calibration** mapping fictional regions to actual
   blocs (Brazil = water, India = food, Gulf = energy, China = manufacturing,
   Africa = land) and using plausible starting resources and population values
   so emergent dynamics mirror real patterns.

---

## 🌍 The Five Regions

| Region      | Real‑World Equivalent   | Specialty       | Starting Resources                 | Special Ability                         |
|-------------|-------------------------|-----------------|------------------------------------|-----------------------------------------|
| **Aquaria** | Brazil                  | Water rich      | Water 90, Food 30, Energy 15, Land 40 | Regenerates water +5/cycle            |
| **Agrovia** | India                   | Food rich       | Water 30, Food 100, Energy 10, Land 60 | Regenerates food +6/cycle            |
| **Petrozon**| Gulf States             | Energy rich     | Water 20, Food 5, Energy 120, Land 35 | Regenerates energy +5/cycle          |
| **Urbanex** | China                   | Manufacturing   | Water 50, Food 40, Energy 90, Land 20 | High population consumption           |
| **Terranova**| Africa                 | Land rich       | Water 40, Food 60, Energy 20, Land 100| Can invest land to improve quality    |

Each region lacks at least one resource and relies on trade. No area is
self-sufficient, forcing interdependence and strategic negotiation.

---

## ⚙️ How It Works

Each simulation cycle (year) consists of **10 phases**:

1. **Resource regeneration** (if region has ability)
2. **Agent observation** of local state and neighbor trust
3. **Action selection** based on weighted strategy preferences
4. **Action execution** (trade request, hoard, invest, aggress)
5. **Event resolution** (trades succeed/fail, conflicts, climate shocks)
6. **Reward computation** (health change, population impact)
7. **Weight adaptation** via reward feedback formula
8. **Health recalculation** and collapse check
9. **History logging** for analysis
10. **Persistence** to Firestore

### Agent Strategy Weights

Each agent maintains four normalized weights: Trade, Hoard, Invest, Aggress.
Weights are updated each cycle:

| Rule                        | Formula                                 |
|-----------------------------|-----------------------------------------|
| Positive reward             | `w_i += α * reward * (1 - w_i)`        |
| Negative reward             | `w_i -= β * |reward| * w_i`            |
| Normalization               | Divide all weights by sum if >1        |

`α` and `β` are learning rates (0.03, 0.02 respectively). No explicit
exploration strategy; adaptation occurs through noise in rewards.

### Trust System

- Start at **0.5** between any two regions.
- **Trade success** +0.1 trust, failure -0.2.
- Trust decays 0.02 per cycle without interaction.
- Trade opens if trust > 0.6; alliance forms if >0.75 for 3 cycles.
- Aggression allowed only if trust < 0.3 and attacker stronger.

### Climate Events

| Type           | Trigger             | Effect                      |
|----------------|---------------------|-----------------------------|
| Drought        | Random 15 % chance  | -45 % water to region       |
| Flood          | Random 12 % chance  | -35 % food to region        |
| Energy Crisis  | Random 8 % chance   | -40 % energy to region      |
| Fertile Season | Random 10 % chance  | +25 % food to region        |
| Solar Surge    | Random 5 % chance   | +30 % energy to region      |

### Population Dynamics

Population changes based on resource health (avg of four). Formula per cycle:

```
if avg >= 55 -> +5%
elif avg >= 35 -> 0%
elif avg < 35 -> -8%
elif avg < 18 -> -20%
```

Collapsing occurs when health ≤ 0 and population < 18.

---

## 🏗️ Technical Architecture

```
[Python FastAPI Backend] --writes--> [Firestore] --pushes--> [React Frontend]
                               ^
                               |  Real-time listeners (WebSocket)
```

### Backend Structure

```
backend/
├── config/
│   ├── firebase_config.py
│   ├── regions_config.py
│   └── __init__.py
├── simulation/
│   ├── world.py
│   ├── region.py
│   ├── trade.py
│   ├── conflict.py
│   ├── climate.py
│   └── analysis_service.py
├── services/
│   ├── firestore_service.py
│   └── analysis_service.py
└── main.py (FastAPI entry)
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── WorldMap.jsx
│   │   ├── StrategyRadar.jsx
│   │   ├── AnalysisOverlay.jsx
│   │   └── ...
│   ├── services/firestore_listener.js
│   ├── constants/regions_meta.js
│   └── App.jsx
└── package.json, vite.config.js, tailwind.config.js
```

### Firestore Collections

1. `regions` — live region state
2. `world_state` — global cycle metadata
3. `events` — discrete events (trade/conflict/climate)
4. `cycle_logs` — snapshot per cycle
5. `analysis` — generated narrative & insight doc

Each document uses consistent field naming for the frontend listener.

### API Endpoints

| Path                        | Method | Description                                |
|-----------------------------|--------|--------------------------------------------|
| `/start`                    | POST   | Kick off simulation                        |
| `/stop`                     | POST   | Halt simulation                            |
| `/status`                   | GET    | Fetch current world_state                 |
| `/analysis/refresh`         | POST   | Regenerate final analysis report           |
| `/regions/{id}`             | GET    | Get single region state (for testing)      |
| `/cycle-logs`               | GET    | Retrieve all cycle logs                    |
| `/events`                   | GET    | Query past events                          |

---

## ✨ Key Features

- **Live dashboard** with interactive world map, region panels, timeline and
  event log.
- **Trade detail popup** shows terms, outcome, and history when clicking an arc.
- **Event detail popup** displays full information on any trade, conflict or
  climate event from the timeline.
- **Strategy radar** visualizes current weights & history, with an AI-style
  analyst card explaining implications.
- **Final analysis overlay** surfaces auto-generated insights, collapsed
  regions, alliance clusters, health charts and natural language summary.
- **WorldSim analyst chatbot** answers typed questions via keyword matching
  against simulation data — no external AI API involved.

---

## 🧠 Emergent Behavior

1. **Urbanex aggression** arose not from coding but from desperate resource
   consumption when its population eclipse soared and trust fell.
2. **Aquaria–Agrovia alliance** formed organically because water‑rich Brazil
   supplied drought‑stricken India while Agrovia reciprocated food.
3. **Climate shocks accelerated cooperation**: after a major drought, trade
   requests spiked and trust climbed within two cycles.
4. **Cooperation consistently beat aggression** over the 20‑year span, even
   when aggressors made early gains.

These outcomes were never scripted; they emerged from the reward-driven agent
loop and the structural constraints we provided.

---

## 🔍 Real World Insights

1. Resource distribution largely dictates strategy choice — ideology plays
   second fiddle to scarcity.
2. Cooperative strategies yield higher long-term stability than aggressive
   conquest in multi-decade horizons.
3. Climate shocks function as catalysts, pushing previously isolated actors
   towards trade partnerships.
4. Manufacturing and population (Urbanex/China) can surpass raw resource
   advantages when agents adapt efficiently.

---

## 📚 Comparison with Existing Work

| Project          | Year | Focus                         | Added by WorldSim                         |
|------------------|------|-------------------------------|-------------------------------------------|
| Axelrod          | 1980 | Iterated prisoner's dilemma   | Real-world mapping + dynamic resources    |
| World3           | 1972 | System dynamics (Limits to Growth) | Agent-based adaptive agents            |
| Sugarscape       | 1996 | ABM with wealth display       | Trust/diplomacy & real-time UI           |
| NetLogo demos    | 1999 | Educational ABM toolkit       | Full-stack live web dashboard + analysis |

Key differentiator: genuine strategy emergence from reward feedback
combined with continuous real-time visualization and post-run AI-like
analysis.

---

## 🛠 Installation and Setup

### Prerequisites

- Python 3.11+ with `venv`
- Node.js 18+ and npm
- Firebase account (Firestore)
- Git (for cloning)

### Backend Setup

```bash
# clone repo
git clone <repo-url> worldsim
cd worldsim/backend
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

# configure Firebase service account
cp config/serviceAccountKey.example.json config/serviceAccountKey.json
# edit firebase_config.py with project ID if needed

# run server
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd ../frontend
npm install

# edit src/services/firebase_listener.js project id if needed

npm run dev
```

### Running Simulation

1. Start backend server (`uvicorn …`).
2. Open frontend at `http://localhost:5173`.
3. Press **Start Simulation** on top‑right to run 20 cycles automatically.
4. Watch map, click regions/events, or view analysis overlay.

---

## 📈 Project Metrics

- **Lines of code:** ~4,800
- **Files:** 67 (backend 29, frontend 38)
- **Firestore collections:** 5
- **Cycles simulated:** 20
- **Regions modeled:** 5
- **Resource types:** 4
- **Simulation phases per cycle:** 10
- **API endpoints:** 7
- **Realtime sync latency:** <200 ms

---

## 🧑‍💻 Team and Roles

| Name            | Role                      | Contributions                    |
|-----------------|---------------------------|----------------------------------|
| Rohit (Architect)| Backend & simulation core | Python engine, reward loop      |
| Nayan (Frontend)   | React dashboard & UI      | Map, charts, chatbot, styling    |
| Soumya (Data)     | Analysis & insights       | Chatbot logic, analytics layer   |

Built in **24 hours** during SIT-Inovate 2026.

---

## 🔮 Future Work

1. Neural network policies with deep reinforcement learning.
2. Scenario editor for custom starting conditions.
3. Multiplayer mode where users control different regions live.
4. Historical validation using real conflict data.
5. Policy research tool exposing parameter sliders.

---

*Thank you for exploring WorldSim. Feel free to fork, modify, or extend the
simulation—only through open experimentation can we better understand the
complex dynamics of our world.*
