# Domain Docs

How engineering skills should consume this repository's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repository root.
- **`docs/adr/`** for ADRs that touch the area being changed.

If any of these files do not exist, proceed silently.

## File structure

This is a single-context repository:

```
/
├── CONTEXT.md
├── docs/adr/
└── src/
```

## Use the glossary's vocabulary

Use terms as defined in `CONTEXT.md` for issue titles, refactor proposals, hypotheses, and test names. If a needed concept is absent, note it for `/domain-modeling` rather than silently inventing a synonym.

## Flag ADR conflicts

Surface any conflict with an existing ADR explicitly rather than silently overriding it.
