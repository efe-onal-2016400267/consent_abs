# Consent-Based Agent-Based Simulation (ConsentRealm / consent_abs)

An Agent-Based Simulation (ABS) framework built on the **Mesa** library to model, simulate, and analyze **consent, norms, and resource sharing** in multi-agent systems. This implementation operationalizes a formal consent mechanism, demonstrating how consent-based reasoning facilitates responsible autonomy and system-wide transparency in Socio-Technical Systems (STSs).

---

## 📖 Table of Contents
- [Abstract](#-abstract)
- [Research Questions](#-research-questions)
- [Technical Background & Formalisms](#-technical-background--formalisms)
- [Consent Operationalization](#-consent-operationalization)
  - [Authorization ($AU$) Transitions](#authorization-au-transitions)
  - [Commitment ($CO$) Transitions](#commitment-co-transitions)
  - [Consent Life-Cycle Transitions](#consent-life-cycle-transitions)
  - [Implementation via Enriched Atoms](#implementation-via-enriched-atoms)
- [Simulation Design](#-simulation-design)
  - [Agent Persona Mapping](#-agent-persona-mapping)
  - [Agent Personas](#agent-personas)
  - [Simulation Parameters](#simulation-parameters)
- [Empirical Results & Validation](#-empirical-results--validation)
  - [Validating Agent-Side Inference (Scenario Analysis)](#validating-agent-side-inference-scenario-analysis)
  - [Validating System-Level Transparency (Population Dynamics)](#validating-system-level-transparency-population-dynamics)
- [Repository Structure](#-repository-structure)
- [Installation & Setup](#-installation--setup)
- [Running Simulations & Experiments](#-running-simulations--experiments)
- [Statistical Analysis & Plotting](#-statistical-analysis--plotting)

---

## 📝 Abstract

Autonomous agents serve as personal assistants, decision-support companions, and AI-driven development tools. With their frequent use, they are increasingly being integrated into socio-technical systems, collaborating with each other and humans intensively. This collaboration requires the agent to take actions on behalf of humans as well as use resources that pertain to these interactions. These resources vary from information to physical objects to computational power. How can agents ensure that these resources are shared and used in line with the expectations of the resource owners? We study this problem through the lens of normative multiagent systems, where we put *consent* at the center. We operationalize a formal consent mechanism and demonstrate its effectiveness in managing resource sharing within socio-technical systems through representative scenarios and large-scale simulations. We specifically show that consent provides agents with the structures necessary to infer their normative standing and act accordingly, while simultaneously ensuring the system-wide transparency required for effective governance.

**Keywords:** Responsible autonomy, Consent, Norms, Socio-Technical Systems.

---

## ❓ Research Questions

This framework is designed to empirically evaluate and answer three core research questions:

1. **RQ1 (Operationalization):** How can we operationalize consent as a mechanism that facilitates responsible autonomy in socio-technical systems?
2. **RQ2 (Agent-Side Inference):** Does the operationalized consent abstraction enable autonomous agents to deterministically infer and reason about their normative states at runtime?
3. **RQ3 (System-Level Transparency):** How effectively does the proposed mechanism provide a transparent environment that allows STS managers to audit resource circulation, track actions and goal achievements, and trace normative events (e.g., norm violations and fulfillments)?

---

## 📐 Technical Background & Formalisms

We adopt and extend a formal model of consent:

- $\mathbb{A}$: The set of agents operating in the STS.
- $\mathbb{R}_A$: The set of resources under the sovereignty of agent $A \in \mathbb{A}$.
- $\mathbb{G}$: The set of propositional atoms representing goals and actions. A goal expressed to another agent is a *stated goal* ($g_R \in \mathbb{G}$).
- $\Phi$: A propositional language with standard operators and atoms $\Omega \cup \mathbb{G}$.
- $\mathbb{T}_A$: The set of possible actions executed by agent $A \in \mathbb{A}$. An action $t \in \mathbb{T}_A$ is represented as $\langle p, r \rangle$, where $p \subseteq \Omega$ is the post-condition (effects) of $t$, and $r \in \mathbb{R}$ is the affected resource.
- $\mathbb{S}$: The state of the STS (a propositional assignment). $\mathbb{S} \models \phi$ indicates that formula $\phi$ is true in state $\mathbb{S}$.

A **Consent Instance (CI)** is defined as:
$$CI = \langle G, R, \mathbb{N}, g_R, t \rangle$$
where $G$ is the consent giver, $R$ is the consent receiver, $\mathbb{N}$ is the set of agreed-upon norms, $g_R$ is $R$'s stated goal, and $t$ is the action to be taken by $R$ to achieve $g_R$.

---

## ⚙️ Consent Operationalization

We refine the state transitions of authorization and commitment norms to enable deterministic runtime inference using Kripke transition models.

### Authorization ($AU$) Transitions
An authorization norm is represented as $AU = \langle G, R, c, t \rangle$, where $c = \langle c_{det}, c_{exp\_au} \rangle$ defines the valid window (detachment and expiration conditions).

```
                 [ c_det ∧ ¬c_exp_au ]
  (Not Active) ------------------------> (Active)
       |                                    |
       | [ p ∧ (¬c_det ∨ c_exp_au) ]        | [ p ∧ ¬c_exp_au ]
       |                                    v
       +--------------------------------> (Fulfilled)
       |                                    |
       |                                    | [ p ∧ c_exp_au ]
       v                                    v
   (Violated) <-----------------------------+
```

- **$Not\_active \to Active$**: Occurs when $\mathbb{S} \models c_{det} \land \neg c_{exp\_au}$.
- **$Not\_active \to Violated$**: Triggered by unauthorized usage: $\mathbb{S} \models p \land (\neg c_{det} \lor c_{exp\_au})$.
- **$Active \to Not\_active$**: Occurs if the expiration condition $c_{exp\_au}$ becomes true before the action is taken.
- **$Active \to Fulfilled$**: Occurs when the action is taken within the valid window: $\mathbb{S} \models p \land \neg c_{exp\_au}$.
- **$Active, Fulfilled \to Violated$**: Occurs if the agent fails to return resource $r$ after the authorization expires: $\mathbb{S} \models p \land c_{exp\_au}$.

### Commitment ($CO$) Transitions
A commitment is represented as $CO = \langle R, G, p, g_R, c_{exp\_co} \rangle$, where $c_{exp\_co}$ is an explicit expiration condition representing the finite interval allowed to achieve the stated goal.

- **$Not\_active \to Active$**: Triggered when the antecedent $p$ holds, provided the goal is not yet achieved and the deadline has not passed: $\mathbb{S} \models p \land \neg g_R \land \neg c_{exp\_co}$.
- **$Not\_active \to Fulfilled$**: Occurs if the goal $g_R$ is already satisfied before commitment activation: $\mathbb{S} \models g_R \land \neg c_{exp\_co}$.
- **$Active \to Fulfilled$**: Represents successful compliance: $\mathbb{S} \models g_R \land \neg c_{exp\_co}$.
- **$Active \to Violated$**: Occurs if the deadline passes without the goal being achieved: $\mathbb{S} \models \neg g_R \land c_{exp\_co}$.

### Consent Life-Cycle Transitions
A consent instance transitions through the following states:
- **$\sigma_a$ (Active)**: Agreed-upon norms are active.
- **$\sigma_h$ (Honored)**: All agreed-upon norms are fulfilled ($\forall n \in \mathbb{N} : Fulfilled(n, S)$).
- **$\sigma_v$ (Violated)**: At least one norm is violated ($\exists n \in \mathbb{N} : Violated(n, S)$).
- **$\sigma_u$ (Unrealized)**: An authorization expires before being exercised, or the resource is returned early without achieving the goal.

We introduce two key extensions to the original model:
1. **$\sigma_h \to \sigma_v$**: A previously honored consent transitions to violated if a post-fulfillment violation occurs (e.g., failing to return the resource after expiration).
2. **Early Release ($\Phi_{early-release}$)**:
   $$\Phi_{\text{early-release}} = (\forall n \in \mathbb{N} : \neg Violated(n, S)) \land Fulfilled(AU, S) \land Active(CO, S) \land Released(r)$$
   This captures scenarios where the receiver returns the resource on time but fails to achieve the goal, which is a more responsible outcome than a violation ($\sigma_h \succ \sigma_u \succ \sigma_v$).

### Implementation via Enriched Atoms
Rather than parsing complex temporal logic at every step, agents use bottom-up evaluation to resolve norm and consent states via logical operations on **Enriched Atoms** (implemented in `base_model/atom.py`). These class objects encapsulate metadata such as `valid_from`, `valid_to`, and `truth` values, allowing deterministic, efficient runtime lookups under the closed-world assumption.

---

## 🧪 Simulation Design

The simulation environment, **ConsentRealm**, models a kitchen where **Chef Agents** aim to cook dishes (goals) by acquiring ingredients and appliances (resources).

### 🔄 Agent Persona Mapping
To bridge the terminology used in the research paper with the actual implementation classes in the codebase, please refer to the following mapping:

| Paper Terminology | Codebase Implementation Class | Description |
| :--- | :--- | :--- |
| **Selfish Agent (SA)** | `GoalFirstAgent` | Prioritizes goals, ignores consent violations/expirations. |
| **Reactive Agent (RA)** | `ConsentFirstAgent` | Prioritizes consent, returns resources upon violation. |
| **Preemptive Agent (PA)** | `MonitoringAgent` | Proactively releases resources one step before AU expiration. |
| **Hybrid Agent** | `FiftyFiftyAgent` | Randomly behaves as either Selfish or Reactive. |

### Agent Personas
1. **Selfish Agent (SA / `GoalFirstAgent`)**: Prioritizes goal accomplishment above all else. It acquires resources through consent but never returns them unless it no longer requires them for any current or future goal, regardless of consent violations.
2. **Reactive Agent (RA / `ConsentFirstAgent`)**: Rule-following. It monitors its received consents and immediately returns a borrowed resource if the associated consent instance is found to be violated.
3. **Preemptive Agent (PA / `MonitoringAgent`)**: Proactive. It monitors its consents and preemptively returns resources if an authorization expiration is *about to* occur (one step before violation), avoiding the downtime of consent violations.

### Simulation Parameters
- **Population**: 1000 agents across 11 population distributions (e.g., SA-RA or SA-PA pairings).
- **Goals & Resources**: Each agent starts with 3 unique goals and 3 sovereigned resources.
- **Norm Expirations**: Sampled uniformly from the interval $[3, 7]$ steps.
- **Execution**: Up to 1000 steps, with an early stopping threshold of 50 consecutive steps without any accomplished goals.
- **Replications**: 10 independent runs per configuration using different random seeds to ensure statistical robustness.

---

## 📈 Empirical Results & Validation

### Validating Agent-Side Inference (Scenario Analysis)
We validate **RQ2** by tracing individual-level representative scenarios (defined in `test_cases/`):
- **Preemptive Scenario**: Agent1 (PA / `MonitoringAgent`) borrows an oven from Agent2 to make a cake, but cannot find eggs. Realizing its authorization is about to expire at Step 3, Agent1 preemptively releases the oven, transitioning the consent to `UNREALIZED` ($\sigma_u$). This allows Agent3 (SA / `GoalFirstAgent`) to immediately acquire the oven and accomplish its goal.
- **Selfish Scenario**: In an identical setup with SAs, Agent1 retains the oven indefinitely despite the impossibility of completing its goal, resulting in a deadlock, a consent violation ($\sigma_v$), and system-wide lock.

This demonstrates that the consent mechanism successfully provides the deterministic signals necessary for agents to infer their normative standing and act responsibly.

### Validating System-Level Transparency (Population Dynamics)
We validate **RQ3** through large-scale simulations:
- **Resource Collapse**: As the proportion of Selfish Agents increases, the system experiences severe resource collapse and deadlocks. Cumulative goal accomplishment drops significantly for all agent types (highly significant under one-way ANOVA tests: $p < 0.001$).
- **Selfishness Doesn't Pay**: SAs do not outperform consent-sensitive agents (RAs or PAs) in terms of goal accomplishment (confirmed via Mann-Whitney tests, $p > 0.05$).
- **Consent Violations**: As the SA ratio increases, consent violations increase dramatically due to resource hoarding. Conversely, higher proportions of PAs and RAs improve resource circulation, enabling higher system-wide goal completion rates.

---

## 📂 Repository Structure

```bash
consent_abs/
├── base_model/
│   ├── agent_personas/
│   │   ├── consent_first_agent.py               # Implements ConsentFirst / Reactive Agent
│   │   ├── goal_first_agent.py                  # Implements GoalFirst / Selfish Agent
│   │   ├── fifty_fifty_consent_and_goal_agent.py # Implements FiftyFifty Agent
│   │   └── monitoring_agent.py                  # Implements Monitoring / Preemptive Agent
│   ├── helpers/
│   │   ├── food_ontology_extractor.py
│   │   └── html_data_viewer.py                  # Visualizes simulation traces
│   ├── models/
│   │   ├── __init__.py
│   │   └── model.py                             # Core Mesa model implementation
│   ├── simulation_scripts/
│   │   ├── experiment_configs/                  # JSON configurations for batch runs
│   │   ├── experiment_runner.py                 # Runs custom experiments
│   │   └── simulator.py                         # Batch simulator across multiple seeds
│   ├── action.py                                # Action class <p, r>
│   ├── atom.py                                  # Enriched Atom implementation
│   ├── base_agent.py                            # Base Chef Agent class
│   ├── config.py                                # Global simulation configurations
│   ├── consent.py                               # ConsentInstance class and state logic
│   ├── norm.py                                  # Authorization and Commitment classes
│   ├── resource.py                              # Resource class
│   └── state.py                                 # EnvState (propositional assignment)
├── goals/
│   └── goal_tree.yaml                           # Recipe goal hierarchy
├── test_cases/                                  # YAML files for individual scenarios
└── analysis_scripts/                            # Statistical tests and plotting scripts
```

---

## ⚙️ Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd consent_abs
   ```

2. **Install Dependencies**:
   Install all required packages via the provided `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Paths**:
   Update the hardcoded paths in `base_model/config.py` to match your local directory structure:
   ```python
   GOAL_FILE_PATH = "/path/to/consent_abs/goals/goal_tree.yaml"
   TEST_CASE_PATH = "/path/to/consent_abs/test_cases/test_008_01_resource_conflict_counter_goal.yaml"
   ```

---

## 🚀 Running Simulations & Experiments

### Single Simulation Run
Run a single simulation with real-time console output:
```bash
python base_model/models/model.py
```
This saves the agent and model data as CSV files in `base_model/results/`.

### Batch Experiments
To run the full suite of experiments across all 10 seeds:
```bash
python base_model/simulation_scripts/simulator.py
```
This executes the configurations defined in `base_model/simulation_scripts/experiment_configs/` and saves the outputs under `simulation_results/`.

---

## 📊 Statistical Analysis & Plotting

To perform statistical analysis and generate plots, **separate analysis scripts must be run** depending on the specific agent personas being compared. Each script processes the corresponding batch simulation results, averages them across all 10 seeds, and saves high-resolution figures in the experiment's `figures/` directory.

### 1. Selfish Agent vs. Reactive Agent (Goal vs. Consent-Based)
To analyze the dynamics between `GoalFirstAgent` (Selfish) and `ConsentFirstAgent` (Reactive):
```bash
python analysis_scripts/goal_vs_consent_model_and_agent_level_analysis.py
```
*Generates combined plots for accomplished goals, remaining goals, consent violations, and resource conflicts.*

For separate, individual plots:
```bash
python analysis_scripts/goal_vs_consent_model_and_agent_level_analysis_separate_plots.py
```

### 2. Selfish Agent vs. Preemptive Agent (Goal vs. Monitoring-Based)
To analyze the dynamics between `GoalFirstAgent` (Selfish) and `MonitoringAgent` (Preemptive):
```bash
python analysis_scripts/goal_vs_monitoring_model_and_agent_level_analysis.py
```

For separate, individual plots:
```bash
python analysis_scripts/goal_vs_monitoring_model_and_agent_level_analysis_separate_plots.py
```

### 3. Reactive Agent vs. Preemptive Agent (Consent vs. Monitoring-Based)
To analyze the dynamics between `ConsentFirstAgent` (Reactive) and `MonitoringAgent` (Preemptive):
```bash
python analysis_scripts/consent_vs_monitoring_model_and_agent_level_analysis.py
```

For separate, individual plots:
```bash
python analysis_scripts/consent_vs_monitoring_model_and_agent_level_analysis_separate_plots.py
```

### 4. General Simulation Analysis
To run a general analysis across all simulation results:
```bash
python analysis_scripts/analyze_simulation_results.py
```
