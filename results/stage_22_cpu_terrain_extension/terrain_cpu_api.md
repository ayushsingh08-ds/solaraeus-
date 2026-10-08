# SOLARAEUS 2.1.0-cpu-terrain Reference API Documentation

## Overview
The `2.1.0-cpu-terrain` extension augments the frozen `2.0.0-cpu-ref` solver with digital terrain model awareness. When terrain is disabled, the solver executes an exact bypass guaranteeing 0.000000 discrepancy against the frozen reference.

## Usage
```python
from urban_comfort.terrain import TerrainGrid, TerrainAwareScene, TerrainAwareCPUSolver

# 1. Create Terrain
terrain = TerrainGrid.create_inclined(bounds, base_elevation=0.0, slope_x=0.03)

# 2. Wrap Scene
scene = TerrainAwareScene(base_scene=base_scene, terrain=terrain)

# 3. Simulate
result = TerrainAwareCPUSolver.simulate(scene, weather, config)
```
