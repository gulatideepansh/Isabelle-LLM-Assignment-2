# Planner-Fill-Repair Workflow

Use this as the basis for the report figure.

```mermaid
flowchart TD
    A["Input Isabelle/HOL goal"] --> B["LLM generates Isar outline"]
    B --> C["Run Isabelle checker"]
    C --> D{Verified and no sorry?}
    D -- yes --> E["Return final proof and log result"]
    D -- no --> F["Select earliest failure"]
    F --> G{Failure is a sorry hole?}
    G -- yes --> H["Extract local proof state"]
    H --> I["Stepwise prover searches tactics"]
    I --> J["Insert candidate only if Isabelle verifies"]
    J --> C
    G -- no --> K["Stage 1: repair local have/show block"]
    K --> L{Progress?}
    L -- yes --> C
    L -- no --> M["Stage 2: repair case or subproof"]
    M --> N{Progress?}
    N -- yes --> C
    N -- no --> O["Stage 3: regenerate whole proof"]
    O --> C
```

The loop is deliberately top-down: every iteration fixes the earliest Isabelle failure before touching later proof text.

