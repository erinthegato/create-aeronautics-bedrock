# Registry Mapping (Java -> Bedrock)

`mapping/registry.json` is the machine-readable map. Each Bedrock identifier uses the
**same namespace + path** as the Java registry name.

| Java (NeoForge)              | Bedrock identifier            |
|------------------------------|-------------------------------|
| `aeronautics:wooden_propeller` | `aeronautics:wooden_propeller` |
| `simulated:altitude_sensor`    | `simulated:altitude_sensor`    |
| `offroad:wheel_mount`          | `offroad:wheel_mount`          |

## Texture resolution
- Block texture: `assets/<ns>/textures/block/<name>.png` -> atlas key `<ns>_<name>`.
- Item texture:  `assets/<ns>/textures/item/<name>.png`  -> atlas key `<ns>_<name>`.
- Fallback: first texture under `textures/block` (blocks) or `textures/item` (items).

## Languages
Java lang keys `block.<ns>.<name>` / `item.<ns>.<name>` / `entity.<ns>.<name>`
become Bedrock `tile.<ns>:<name>.name`, `item.<ns>:<name>.name`,
`entity.<ns>:<name>.name` in `texts/en_US.lang`.
