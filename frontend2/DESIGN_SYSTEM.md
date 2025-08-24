# AI Interviewer Design System

A comprehensive design system for the AI Interviewer platform built with Next.js, Tailwind CSS, and modern React patterns.

## Table of Contents

- [Colors](#colors)
- [Typography](#typography)
- [Components](#components)
- [Icons](#icons)
- [Spacing](#spacing)
- [Layouts](#layouts)
- [Forms](#forms)
- [States](#states)

## Colors

### Primary Palette
```css
/* Blue - Primary Actions */
--color-primary-50: #eff6ff;
--color-primary-500: #3b82f6;  /* Main brand blue */
--color-primary-600: #2563eb;
--color-primary-700: #1d4ed8;

/* Success - Positive Actions */
--color-success-500: #10b981;
--color-success-600: #059669;

/* Warning - Caution */
--color-warning-500: #f59e0b;

/* Error - Destructive Actions */
--color-error-500: #ef4444;
--color-error-600: #dc2626;
```

### Semantic Colors
```css
/* Glass/Overlay Effects */
--color-glass-bg: rgba(255, 255, 255, 0.1);
--color-glass-border: rgba(255, 255, 255, 0.2);
--color-glass-hover: rgba(255, 255, 255, 0.15);

/* Text Hierarchy */
--color-text-primary: #1f2937;
--color-text-secondary: #6b7280;
--color-text-muted: #9ca3af;
--color-text-on-dark: rgba(255, 255, 255, 0.9);
```

### Usage
- **Primary Blue**: Main CTAs, links, active states
- **Success Green**: Success messages, completed states
- **Warning Yellow**: Warning messages, pending states
- **Error Red**: Error messages, destructive actions

## Typography

### Font Stack
```css
--font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
```

### Scale
- **Heading 1**: `text-4xl` (36px) - Page titles
- **Heading 2**: `text-3xl` (30px) - Section titles  
- **Heading 3**: `text-xl` (20px) - Subsection titles
- **Body Large**: `text-lg` (18px) - Emphasis text
- **Body**: `text-base` (16px) - Default body text
- **Body Small**: `text-sm` (14px) - Secondary text
- **Caption**: `text-xs` (12px) - Captions, labels

### Clamp Utility
```css
.text-clamp-hero {
  font-size: clamp(2rem, 4vw, 3.5rem);
}
```

## Components

### Buttons

#### Variants
```tsx
// Primary - Main actions
<Button variant="primary" size="default">Apply Now</Button>

// Secondary - Supporting actions  
<Button variant="secondary" size="default">Learn More</Button>

// Success - Positive confirmations
<Button variant="success" size="default">Save</Button>

// Outline - Secondary actions with borders
<Button variant="outline" size="default">Cancel</Button>

// Ghost - Minimal actions
<Button variant="ghost" size="default">Skip</Button>

// Glass - Overlay contexts
<Button variant="glass" size="default">Continue</Button>
```

#### Sizes
- `sm`: Compact buttons (36px height)
- `default`: Standard buttons (44px height)  
- `lg`: Prominent buttons (48px height)
- `xl`: Hero buttons (56px height)
- `icon`: Square icon buttons (40x40px)

#### Features
- **Loading states**: Built-in spinner with `loading` prop
- **Accessibility**: ARIA labels, focus management
- **Animations**: Hover lift effects, shimmer on hover
- **Disabled states**: Proper visual feedback

### Cards

#### Basic Card
```tsx
<Card className="p-6">
  <CardContent>
    Content goes here
  </CardContent>  
</Card>
```

#### Feature Card (Wireframe Style)
```tsx
<WireframeCard className="animate-fade-in">
  <WireframeCardBody>
    <WireframeCardIcon color="blue">
      <ClipboardList className="w-6 h-6" />
    </WireframeCardIcon>
    <h3>Feature Title</h3>
    <p>Feature description</p>
  </WireframeCardBody>
</WireframeCard>
```

### Forms

#### Form Fields
```tsx
<FormField 
  label="Email Address" 
  required
  error={errors.email}
  description="We'll never share your email"
>
  <Input
    type="email"
    registration={register('email')}
    error={errors.email}
    placeholder="john@example.com"
  />
</FormField>
```

#### Validation
- Built with **Zod** schemas
- **React Hook Form** integration
- Real-time validation feedback
- Accessible error messages

### Loading States

#### Spinner Component
```tsx
// Different sizes
<LoadingSpinner size="sm" />
<LoadingSpinner size="md" text="Loading..." />
<LoadingSpinner size="lg" />

// Page-level loading
<LoadingPage text="Loading dashboard..." />

// Card-level loading  
<LoadingCard text="Fetching jobs..." />
```

### Error Boundaries

#### Usage
```tsx
<ErrorBoundary fallback={CustomErrorComponent}>
  <SomeComponent />
</ErrorBoundary>
```

## Icons

### Icon System
- **Library**: Lucide React
- **Sizes**: 16px, 20px, 24px, 32px
- **Semantic Usage**: Location (MapPin), Time (Clock), etc.

#### Common Icons
```tsx
import { 
  MapPin,        // Location
  Clock,         // Time/Schedule  
  Star,          // Rating/Favorite
  Search,        // Search functionality
  User,          // Profile/Account
  Mail,          // Email/Contact
  Phone,         // Phone/Contact
  Building,      // Company
  Briefcase,     // Job/Work
  DollarSign,    // Salary/Money
  Target,        // Goals/Matching
  Zap,           // Power/Quick actions
  CheckCircle,   // Success
  AlertCircle,   // Warning/Error
  Loader2        // Loading (spinning)
} from 'lucide-react'
```

## Spacing

### Scale
- `xs`: 4px (space-1)
- `sm`: 8px (space-2)  
- `md`: 16px (space-4)
- `lg`: 24px (space-6)
- `xl`: 32px (space-8)
- `2xl`: 48px (space-12)
- `3xl`: 64px (space-16)

### Usage
- **Component padding**: Use md (16px) as default
- **Section margins**: Use xl-2xl (32-48px) 
- **Element spacing**: Use sm-md (8-16px)

## Layouts

### Container Widths
```css
.container {
  max-width: 1400px;  /* Main content width */
  margin: 0 auto;
  padding: 0 24px;    /* Side gutters */
}
```

### Grid Systems
```tsx
// Job listings
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">

// Dashboard layout
<div className="grid lg:grid-cols-4 gap-8">
  <aside className="lg:col-span-1">Sidebar</aside>
  <main className="lg:col-span-3">Content</main>
</div>
```

### Responsive Breakpoints
- **sm**: 640px - Mobile landscape
- **md**: 768px - Tablet
- **lg**: 1024px - Desktop
- **xl**: 1280px - Large desktop
- **2xl**: 1536px - Extra large

## Forms

### Validation Schema Pattern
```tsx
// Define schema
const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password too short')
})

// Use in component
const { register, handleSubmit, formState: { errors } } = useForm({
  resolver: zodResolver(schema)
})
```

### Form Components
- **FormField**: Wrapper with label, error display
- **Input**: Text inputs with validation styling
- **Textarea**: Multi-line text inputs
- **Select**: Dropdown selectors
- **FormContainer**: Form wrapper with proper spacing
- **FormErrorSummary**: Aggregate error display

## States

### Loading States
- **Skeleton loading**: For predictable content shapes
- **Spinner loading**: For unpredictable durations
- **Button loading**: Inline loading with text

### Empty States  
- **Illustrations**: Use meaningful iconography
- **Messaging**: Clear, actionable messaging
- **CTAs**: Guide users to next steps

### Error States
- **Inline errors**: Field-level validation
- **Page errors**: Error boundaries with retry
- **Network errors**: Friendly error messages

## Animation

### Transitions
```css
/* Standard transition */
transition: all 300ms ease-in-out;

/* Hover effects */
hover:transform hover:-translate-y-1;

/* Focus states */  
focus:ring-2 focus:ring-blue-500 focus:ring-offset-2;
```

### Keyframes
```css
/* Fade in up */
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Shimmer effect */
@keyframes shimmer {
  0% { left: -100%; }
  100% { left: 100%; }
}
```

## Best Practices

### Component Development
1. **Composition over inheritance**
2. **Prop-based variants** using CVA
3. **Forward refs** for form components  
4. **Semantic HTML** with ARIA labels
5. **TypeScript** for all components

### Accessibility
1. **Semantic HTML** structure
2. **ARIA labels** and roles
3. **Focus management** with proper tabbing
4. **Screen reader** compatibility
5. **Color contrast** WCAG AA compliance

### Performance
1. **Next/Image** for all images
2. **React Query** for API state
3. **Lazy loading** for heavy components
4. **Code splitting** with dynamic imports
5. **Bundle optimization** with analysis

### State Management
1. **React Query** for server state
2. **useState/useReducer** for local state  
3. **Context** for global UI state
4. **LocalStorage** for persistence
5. **Optimistic updates** for UX

---

## Usage Examples

See individual component files in `/src/components/ui/` for detailed implementation examples and API documentation.