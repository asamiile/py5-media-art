# route_arbitration

Many autonomous decisions negotiate the same floor.

## Concept

The work abstracts a warehouse routing system as a field of negotiated intent, where every path is simple alone but dense conflicts emerge collectively.

## Technique

- **Obstacle Field**: Random rectangular blockers create aisles and unavailable floor zones.
- **Grid Shortest Paths**: Breadth-first routing finds Manhattan paths between distributed start and goal cells.
- **Conflict Heat**: Cells used by multiple routes glow amber, revealing arbitration pressure.
- **Reservation Ticks**: Small marks along paths suggest time-window reservations and route priority.

## Visual Impression

A dark operational map with steel-blue and green routes threading around matte blockers, amber conflict nodes, and crisp white priority markers.
