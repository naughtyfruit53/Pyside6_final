# TRITIQ ERP Frontend

A modern React-based frontend for the TRITIQ ERP system built with Next.js and Material-UI.

## 🚀 Turbopack Migration

This project has been upgraded to use **Turbopack** for development builds, providing significantly faster compilation and hot reload times.

### Turbopack Benefits
- ⚡ **Faster Development**: Up to 10x faster than Webpack in development
- 🔄 **Instant Hot Reload**: Changes reflect immediately without losing state
- 📦 **Optimized Bundling**: Incremental compilation for better performance
- 🛠️ **Better Developer Experience**: Improved error reporting and debugging

## 📋 Prerequisites

- Node.js 18.17 or later
- npm 9.0 or later
- Backend API server running (FastAPI)

## 🛠️ Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd fastapi_migration/frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env.local
   ```
   
   Update `.env.local` with your API endpoint:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## 🚀 Development

### Starting the Development Server (with Turbopack)

```bash
npm run dev
```

This will start the development server with Turbopack enabled on `http://localhost:3000`.

### Key Development Commands

```bash
# Start development server with Turbopack
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linting
npm run lint
```

## ⚙️ Turbopack Configuration

Turbopack is enabled via the `next.config.js` file:

```javascript
const nextConfig = {
  experimental: {
    turbo: true,  // Enables Turbopack for development
  },
  // ... other config
}
```

### Migration Notes

- **Compatibility**: Turbopack is highly compatible with existing Next.js applications
- **Incremental Adoption**: The change only affects development builds; production builds still use Webpack
- **Performance**: You should notice significantly faster startup times and hot reloads
- **Debugging**: Enhanced error reporting and stack traces in development

## 🏗️ Architecture

### Tech Stack
- **Framework**: Next.js 15.4.4 with Turbopack
- **UI Library**: Material-UI (MUI) 5.14.0
- **State Management**: React Query 3.39.0
- **Forms**: React Hook Form 7.47.0
- **HTTP Client**: Axios 1.6.0
- **Notifications**: React Toastify 9.1.0
- **PDF Generation**: jsPDF with AutoTable
- **Excel Export**: ExcelJS with FileSaver

### Project Structure
```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Next.js pages
│   ├── utils/         # Utility functions
│   ├── hooks/         # Custom React hooks
│   └── types/         # TypeScript type definitions
├── public/            # Static assets
├── next.config.js     # Next.js configuration (with Turbopack)
└── package.json       # Dependencies and scripts
```

## 🔌 API Integration

The frontend communicates with the FastAPI backend through:

- **Base URL**: Configured via `NEXT_PUBLIC_API_URL` environment variable
- **Authentication**: JWT tokens stored in localStorage
- **Error Handling**: Centralized error handling with toast notifications
- **Data Fetching**: React Query for efficient data management

### API Routes
- Authentication: `/api/v1/auth/`
- Organizations: `/api/v1/organizations/`
- Users: `/api/v1/users/`
- Vouchers: `/api/v1/vouchers/`
- Products: `/api/v1/products/`
- And more...

## 🎨 UI/UX Features

- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- **Dark/Light Theme**: Material-UI theming support
- **Data Grids**: Advanced data tables with sorting, filtering, and pagination
- **Form Validation**: Comprehensive form validation with real-time feedback
- **File Upload**: Support for document and image uploads
- **Export/Import**: Excel and PDF export capabilities

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Route Protection**: Protected routes for authenticated users
- **Role-Based Access**: Different UI components based on user roles
- **CORS Configuration**: Proper cross-origin resource sharing setup

## 📱 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🚀 Deployment

### Production Build
```bash
npm run build
npm run start
```

### Docker Support
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🐛 Troubleshooting

### Common Issues

1. **Turbopack build errors**: 
   - Ensure Node.js version is 18.17+
   - Clear `.next` folder and reinstall dependencies

2. **API connection issues**:
   - Verify `NEXT_PUBLIC_API_URL` is correctly set
   - Check backend server is running on the specified port

3. **Hot reload not working**:
   - With Turbopack, hot reload should be instant
   - If issues persist, restart the development server

### Performance Tips

- **Turbopack Optimization**: Already enabled for maximum performance
- **Bundle Analysis**: Use `npm run build` to analyze bundle size
- **Image Optimization**: Use Next.js Image component for optimized images

## 📄 License

This project is part of the TRITIQ ERP system and is proprietary software.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For technical support or questions about the frontend implementation, please contact the development team.

---

**Note**: This frontend has been optimized with Turbopack for the best possible development experience. Enjoy the faster build times! 🚀