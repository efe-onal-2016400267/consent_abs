# Requirements from Aperion's Paper

## Agents
- Each agent owns only 1 resource in the paper. We abandon this assumption.
- Goals of the agents are represented as propositional atoms in $\mathbb{G}$. For us, subgoals are represented likewise.
- An action: $t = <p, r>, where p \subseteq \Omega$ is the non-empty post condition (changes it makes in the state) of t and r is the affected resources.


## Norms
- There is a set of norms $\mathbb{L}$ in the STS, that are active even before any execution begins. (e.g. Prohibitions that keep agents from using others' resources.)
- Some norms might conflict. For such cases, a norm recency based priority ordering is used.
- 

## Consent
- A consent instance must be constrained to a specific agent, action, goal, and norms.
- $CI = <G, R, c, <p, r>>$ where $\mathbb{G}$ is the consent giver, $\mathbb{R}$ is the consent receiver, $c = c_det \land \lnot c_exp$, $<p, r>$ is the action $t$.
- Consent must be feasible. The agent need to be able to perform the stated goal if it acquires consent. (e.g., if G is lending their car, the car should not be broken.)
- $R$ requires consent from $G$ to use $r \in \mathbb{R}_G$
- $G$ and $R$ can negotiate to agree upon the details of consent. When negotiation begins, a consent instance is initialized. A negotiation ends when $G$ and $R$ come to an agreement about the norms in $\mathbb{N}$
- Agreed upon norms = $\mathbb{N} = \{AU, CO\} \cup \mathbb{N'}$, where $\mathbb{N'}$ includes any other norms that might have been invoked during the negotiation. E.g., Prohibitions to use $r$ for a goal different than $g_R$ Hence an agreement results in at least 1 CO and 1 AU (unsolicited consent is an exception to this rule).


### Unsolicited Consent



# consent_abs

Naming Convention for atoms:
<agent_id>-<goal_name>-<subgoal_name>-<resource_id>-<valid_tick_count>

What kind atoms will there be?
- agentX-make_rice---: AgentX made rice: TO BE IMPLEMENTED AFTER GOAL COMPLETION
- agentx--use_stove--: Agent x has acquired a stove, so we need to update the state about this
- agentX-make_rice---20: AgentX will make rice in 20 ticks. (Turns FALSE after 20 ticks passes from its creation): TO BE IMPLEMENTED AFTER NEGOTIATION.
- agentX-make_rice--resourceY-: AgentX made rice by using resourceY: TO BE IMPLEMENTED AFTER GOAL COMPLETION

- Do I need soverignty atoms like: AgentX--resourceY-: AgentX holds resourceY. I don't think so