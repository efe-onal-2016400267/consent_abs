# consent_abs

Naming Convention for atoms:
<agent_id>-<goal_name>-<subgoal_name>-<resource_id>-<valid_tick_count>

What kind atoms will there be?
- agentX-make_rice---: AgentX made rice: TO BE IMPLEMENTED AFTER GOAL COMPLETION
- agentx--use_stove--: Agent x has acquired a stove, so we need to update the state about this
- agentX-make_rice---20: AgentX will make rice in 20 ticks. (Turns FALSE after 20 ticks passes from its creation): TO BE IMPLEMENTED AFTER NEGOTIATION.
- agentX-make_rice--resourceY-: AgentX made rice by using resourceY: TO BE IMPLEMENTED AFTER GOAL COMPLETION

- Do I need soverignty atoms like: AgentX--resourceY-: AgentX holds resourceY. I don't think so