const express = require('express');
const path = require('path');
const fetch = require('node-fetch');

const app = express();
// Default to localhost for local dev; overridden by env when running in Docker
const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://backend:8000/api';
const PORT = process.env.PORT || 3000;
const publicPath = path.join(__dirname, 'public');

// Parse JSON bodies from clients
app.use(express.json());

// Serve static HTML files from the public folder
app.use(express.static(publicPath));

// Proxy the backend /api GET request so the frontend can fetch data without CORS issues.
app.get('/api', async (req, res) => {
  try {
    const response = await fetch(BACKEND_API_URL);
    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('Error fetching backend data:', error);
    res.status(502).json({ error: 'Unable to fetch backend data' });
  }
});

// Proxy POST submissions from the browser to the backend API
app.post('/api', async (req, res) => {
  try {
    const response = await fetch(BACKEND_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });
    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    console.error('Error posting to backend:', error);
    res.status(502).json({ error: 'Unable to submit to backend' });
  }
});

app.listen(PORT, () => {
  console.log(`Express server running at http://localhost:${PORT}`);
});