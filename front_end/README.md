# Movie Recommendation App Prototype

This is a code bundle for Movie Recommendation App Prototype. The original project is available at https://www.figma.com/design/npBItSgNFaD9o7TEnAgFH4/Movie-Recommendation-App-Prototype.

## Features

- Movie recommendation interface with rating system
- Integration with OMDb API for real movie data
- Dummy data mode for development and debugging
- Responsive UI built with React and TypeScript
- Backend API for secure API key management

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

1. Copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` to configure your settings:
   ```
   VITE_API_BASE_URL=http://localhost:8000
   VITE_USE_DUMMY_DATA=true
   ```

   - `VITE_API_BASE_URL`: Backend API URL (default: http://localhost:8000)
   - `VITE_USE_DUMMY_DATA`: Set to `true` to use dummy data, `false` to use OMDb API

### 3. Start the backend API

Make sure the backend API is running. See `../back_end/README.md` for instructions.

### 4. Run the development server

**Option 1 - Use the start script (recommended):**

```powershell
.\start.ps1
```

**Option 2 - Manual start:**

```bash
npm run dev
```

The app will be available at http://localhost:5173

The start script will:
- Automatically install dependencies if needed
- Create `.env` from `.env.example` if it doesn't exist
- Start the Vite dev server
- Remind you to start the backend API

## Using the App

### Development Mode (Dummy Data)

Set `VITE_USE_DUMMY_DATA=true` in your `.env` file to use the built-in dummy movies. This is useful for:
- Development without API key
- Testing UI functionality
- Debugging without external dependencies

### Production Mode (OMDb API)

Set `VITE_USE_DUMMY_DATA=false` to fetch real movie data from OMDb API through the backend:
1. Ensure backend API is running
2. Backend must have a valid OMDb API key configured
3. Movies will be loaded lazily for better performance

## Project Structure

```
front_end/
├── src/
│   ├── components/        # React components
│   │   ├── ui/           # UI component library
│   │   └── ...
│   ├── services/         # API service layer
│   │   └── movieApi.ts   # OMDb API integration
│   ├── App.tsx           # Main application component
│   └── main.tsx          # Application entry point
├── .env                  # Environment variables (not in git)
├── .env.example          # Example environment file
└── package.json          # Dependencies and scripts
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## API Integration

The app uses a service layer (`src/services/movieApi.ts`) to communicate with the backend API. This provides:

- `searchMovies(query, page, type)` - Search for movies
- `getMovieById(imdbId, plot)` - Get movie details by IMDb ID
- `getMovieByTitle(title, year, plot)` - Get movie details by title
- `checkApiHealth()` - Check backend API status
- `isUsingDummyData()` - Check if using dummy data mode
