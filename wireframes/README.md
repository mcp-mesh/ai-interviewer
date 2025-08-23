# AI Careers Wireframes

Static HTML wireframes for the AI-enhanced careers page redesign. These wireframes demonstrate the complete user flow from landing page to interview scheduling.

## 🚀 Quick Start

1. **Start the wireframe server:**
   ```bash
   cd docker-compose
   docker-compose -f docker-compose.wireframes.yml up wireframe-server
   ```

2. **Access wireframes:**
   - Open: http://localhost
   - Clean, focused environment for wireframe development only

## 📱 Wireframe Pages

### Core Flow
- **Landing Page** (`/index.html`) - AI-enhanced careers hub with authentication states
- **Position Listing** (`/pages/positions/listing.html`) - Job search with AI matching
- **Position Detail** (`/pages/positions/detail.html`) - Job details with AI insights
- **Application Flow** (`/pages/careers/apply.html`) - Multi-step application process
- **Application Result** (`/pages/careers/application-result.html`) - Interview eligibility results

### Demo States
Each page supports different user states via URL parameters:

- `?state=` (guest user)
- `?state=logged-in` (authenticated, no resume)
- `?state=has-resume` (authenticated with resume)
- `?state=interview-ready` (eligible for interview)

### Example URLs
```
http://localhost/?state=has-resume
http://localhost/pages/positions/listing.html?state=logged-in
http://localhost/pages/positions/detail.html?state=has-resume&id=1
http://localhost/pages/careers/apply.html?id=1&quick=true
http://localhost/pages/careers/application-result.html?result=eligible
```

## 🎨 Design System

### Color Palette
- **Primary Blue**: #3b82f6 (buttons, links, brand)
- **Success Green**: #10b981 (positive actions, success states)
- **Warning Yellow**: #f59e0b (alerts, pending states)
- **Text Gray**: #1f2937 (primary text)
- **Secondary Gray**: #6b7280 (secondary text)
- **Background**: #f9fafb (page background)

### Typography
- **Font**: System font stack (-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', ...)
- **Headings**: Bold weights (600-700)
- **Body**: Regular weight (400)
- **Small text**: 0.875rem
- **Meta info**: 0.75rem, muted color

### Components
- **Cards**: White background, subtle border, rounded corners
- **Buttons**: Multiple variants (primary, secondary, success)
- **Match Scores**: Blue background, rounded pills
- **Progress Steps**: Numbered circles with connecting lines
- **Forms**: Clean inputs with focus states

## 🔧 Interactive Features

### Demo Controls
- **Alt+1-4**: Quick state switching
- **Floating Controls**: Bottom-left demo controls (localhost only)
- **Login Simulation**: Modal with OAuth provider selection
- **Form Simulation**: Auto-save indicators, progress tracking
- **File Upload**: Simulated resume upload with AI processing

### State Management
JavaScript handles:
- User authentication states
- UI component visibility
- Form progression
- Notification system
- Navigation simulation

## 📋 User Flow Testing

### Complete Flow Test
1. **Start as guest** → Browse positions → Select job → Login prompt
2. **Login simulation** → Upload resume → AI matching appears
3. **Browse with AI** → See match scores → Quick apply option
4. **Application flow** → Multi-step form → Auto-fill simulation
5. **Submit application** → AI analysis → Interview eligibility
6. **Interview scheduling** → Integration with existing interview system

### Critical Paths
- **Guest to Applied**: Landing → Browse → Detail → Login → Apply → Interview
- **Returning User**: Landing → Browse Matched → Quick Apply → Interview
- **Resume Update**: Profile → Upload → Updated Matching

## 🎯 AI Features Demonstrated

### Smart Matching
- **Match Percentages**: Visual indicators on job cards
- **Recommended Tab**: Separate view for AI-matched positions
- **Match Reasons**: "Why you're a good fit" explanations

### Auto-Fill Technology
- **Resume Parsing**: Simulated extraction of structured data
- **Form Population**: Pre-filled fields from resume analysis
- **Smart Validation**: Context-aware error checking

### Suitability Analysis
- **Background Screening**: AI evaluation of candidate fit
- **Interview Eligibility**: Binary decision with professional messaging
- **No Gaming Prevention**: Minimal feedback to prevent manipulation

## 🔒 Security & Privacy

### Demonstrated Concepts
- **No Real-time Feedback**: Prevents application gaming
- **Minimal Rejection Details**: Professional standard responses
- **Privacy Notices**: Clear AI usage disclosures
- **Consent Mechanisms**: Checkbox agreements for AI processing

## 📱 Responsive Design

### Breakpoints
- **Desktop**: 1200px+ (full layout with sidebar)
- **Tablet**: 768px-1199px (stacked layout)
- **Mobile**: <768px (single column, condensed navigation)

### Mobile Optimizations
- **Touch-friendly buttons**: Larger tap targets
- **Simplified navigation**: Collapsible user details
- **Stacked forms**: Single column layout
- **Condensed cards**: Optimized for smaller screens

## 🛠 Development Notes

### File Structure
```
wireframes/
├── index.html                     # Landing page
├── css/careers.css               # Main stylesheet
├── js/careers.js                 # Interactive behavior
├── nginx.conf                    # Static server config
└── pages/
    ├── positions/
    │   ├── listing.html          # Job search
    │   └── detail.html           # Job details
    └── careers/
        ├── apply.html            # Application form
        ├── application-result.html # Results page
        ├── interview.html        # Interview redirect
        └── my-applications.html  # Dashboard
```

### Tech Stack
- **Pure HTML/CSS/JS**: No frameworks for maximum compatibility
- **Modern CSS**: Grid, Flexbox, CSS Variables
- **ES6+ JavaScript**: Modern browser features
- **NGINX**: Static file serving

### Performance
- **Minimal Dependencies**: No external libraries
- **Optimized Assets**: Compressed CSS, efficient selectors
- **Fast Loading**: Static files with caching headers
- **Mobile First**: Progressive enhancement approach

## 🔄 Integration Points

### Backend APIs (for future implementation)
- `GET /api/user/profile` - User authentication state
- `GET /api/positions` - Job listings with AI matching
- `POST /api/applications` - Submit application
- `POST /api/interviews/schedule` - Schedule interview
- `POST /api/user/upload-resume` - Resume upload and processing

### Existing Interview System
- Wireframes link to existing interview flow
- Maintains current authentication system
- Preserves session management
- Compatible with current user roles

## 📈 Metrics & Analytics

### Key Interactions Tracked
- **Page Views**: Landing, listing, detail, application pages
- **User Actions**: Login, upload, apply, schedule interview
- **Conversion Points**: Guest→Login, Application→Interview
- **Drop-off Analysis**: Multi-step form completion rates

### A/B Testing Opportunities
- **CTA Button Text**: "Apply Now" vs "Quick Apply"
- **Match Score Display**: Percentage vs descriptive
- **AI Messaging**: Technical vs friendly tone
- **Application Length**: Single vs multi-step forms

---

## 🚀 Next Steps

1. **User Testing**: Validate flow with real users
2. **Backend Integration**: Connect to actual APIs
3. **Data Collection**: Implement analytics tracking
4. **Performance Optimization**: Production-ready optimization
5. **Accessibility**: WCAG compliance improvements