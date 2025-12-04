from scipy.stats import false_discovery_control


GOAL_FILE_PATH = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/goals/goal_tree.yaml"
TEST_CASE_PATH = "/Users/efeonal/py_envs/MESA_thesis/consent_abs/test_cases/test_011_02_alternative_r_conflict_counting.yaml"
TEST = False
MAX_STEP_COUNT = 1000
ConsentFirstAgent_COUNT = 5
FiftyFiftyAgent_COUNT = 5
GoalFirstAgent_COUNT = 5
MonitoringAgent_COUNT = 5
CO_exp_step = 5
AU_exp_step = 2
random_exp_times = True
max_random_AU_exp_step = 7
min_random_AU_exp_step = 3
max_random_CO_exp_step = 7
min_random_CO_exp_step = 3
print_state = False
print_execution = False
random_agent_execution = True