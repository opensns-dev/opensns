# UI COMPONENTS

**Directory:** `frontend/src/components/ui/`
**Pattern:** shadcn/ui + Radix UI + Tailwind CSS + class-variance-authority

## OVERVIEW

Reusable UI component library. 15 components extending Radix UI primitives with Tailwind styling via cva variants. All components use `cn()` utility for class merging and support ref forwarding.

## STRUCTURE

Flat directory. One file per component. Each exports:
- Component function (forwardRef)
- Variants object (cva result)
- Props interface (extends React.ComponentProps)

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new component | `frontend/src/components/ui/{name}.tsx` | Copy button.tsx pattern |
| Modify variants | Edit cva call in component file | Keep variant/size pattern |
| Add utility helper | `frontend/src/lib/utils.ts` | cn() lives here |
| Form components | input.tsx, textarea.tsx, select.tsx, label.tsx | Use together |
| Overlay components | dialog.tsx, sheet.tsx, dropdown-menu.tsx, tooltip.tsx | Portal-based |
| Data display | table.tsx, card.tsx, skeleton.tsx, tabs.tsx | Layout building blocks |

## CONVENTIONS

**cva Pattern:**
```typescript
const variants = cva("base-classes", {
  variants: { variant: { default: "...", secondary: "..." }, size: { default: "...", sm: "..." } },
  defaultVariants: { variant: "default", size: "default" }
})
```

**Props Interface:**
```typescript
export interface XProps extends React.ComponentProps<"div">, VariantProps<typeof xVariants> {}
```

**Component Body:**
```typescript
function X({ className, variant, size, ...props }: XProps) {
  return <div className={cn(variants({ variant, size }), className)} {...props} />
}
```

## KEY FILES

| File | Purpose |
|------|---------|
| button.tsx | Primary/secondary/ghost variants, all CTAs |
| dialog.tsx, sheet.tsx | Modal/drawer patterns, mobile responsive |
| table.tsx | Data grids with header/body/cell structure |
| sidebar.tsx | App navigation shell |
| toast.tsx | Notification system (with sonner) |
| input.tsx, textarea.tsx | Form field primitives |
| select.tsx, dropdown-menu.tsx | Selection/menus |

## ANTI-PATTERNS

- **NEVER** use inline class strings without `cn()` wrapper
- **NEVER** skip cva for components with visual variants
- **NEVER** import Radix UI directly in pages (always use these wrappers)
- **NEVER** forget `forwardRef` on interactive elements (buttons, inputs)
- **NEVER** add business logic to UI components (keep them presentational)
