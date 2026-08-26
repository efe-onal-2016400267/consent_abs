#!/usr/bin/env python3
"""
Verify step normalization approach in analysis scripts.
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("NORMALIZATION VERIFICATION")
print("=" * 80)
print()

# Simulate the analysis approach
# Scenario: 3 seeds with different step counts
seeds_data = {
    'seed': [1, 2, 3],
    'rc': [100, 105, 95],
    'steps': [500, 510, 490],
}

df_seeds = pd.DataFrame(seeds_data)

print("Individual seed data:")
print(df_seeds)
print()

# Method 1: What the analysis script does (current)
# Average RC and average steps, then divide
mean_rc_all = df_seeds['rc'].mean()
mean_steps_all = df_seeds['steps'].mean()
per_step_method1 = mean_rc_all / mean_steps_all

print(f"METHOD 1 (Current Analysis Script):")
print(f"  Mean RC (across seeds): {mean_rc_all:.2f}")
print(f"  Mean Steps (across seeds): {mean_steps_all:.2f}")
print(f"  Per-step RC: {per_step_method1:.4f}")
print()

# Method 2: Compute per-seed per-step, then average
per_step_per_seed = df_seeds['rc'] / df_seeds['steps']
per_step_method2 = per_step_per_seed.mean()

print(f"METHOD 2 (Proper approach):")
print(f"  Per-seed per-step RC:")
for i, row in df_seeds.iterrows():
    print(f"    Seed {row['seed']}: {row['rc']} / {row['steps']} = {row['rc']/row['steps']:.4f}")
print(f"  Average per-step RC: {per_step_method2:.4f}")
print()

# Compare
difference = abs(per_step_method1 - per_step_method2)
pct_difference = (difference / per_step_method2 * 100) if per_step_method2 > 0 else 0

print(f"Difference: {difference:.6f} ({pct_difference:.3f}%)")
if pct_difference < 1:
    print("✓ Both methods are essentially equivalent (< 1% difference)")
elif pct_difference < 5:
    print("⚠ Methods differ by ~{:.1f}% - acceptable for most analyses".format(pct_difference))
else:
    print("✗ Methods differ significantly - statistical rigor concern")

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
The analysis script uses Method 1 (divide mean RC by mean steps).

For simulations where:
- Step counts don't vary too much between seeds
- Resource conflicts scale roughly linearly with steps

Method 1 is acceptable and much faster to compute.

However, for precise statistical error propagation:
- Standard deviations should be computed per-seed per-step first
- Then aggregated (not divided by mean steps directly)

Current error bars (SEM) are computed on the raw aggregated values,
not on the per-step normalized values. This could slightly underestimate
uncertainty in the "per step" normalized plots.
""")
