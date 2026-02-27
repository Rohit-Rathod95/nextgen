// api.js — centralize HTTP calls to WorldSim backend

// prefer explicit base URL; fall back to legacy name and localhost for dev
const BASE =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8000';

// log the base on load (help debug 404s in production)
console.debug('[api] using BASE URL', BASE);

async function startSimulation() {
  try {
    const url = `${BASE}/start`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Start failed (url='+`${BASE}/start`+'):', error);
    return { error: error.message };
  }
}

async function pauseSimulation() {
  try {
    const url = `${BASE}/pause`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Pause failed (url='+`${BASE}/pause`+'):', error);
    return { error: error.message };
  }
}

async function resumeSimulation() {
  try {
    const url = `${BASE}/resume`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Resume failed (url='+`${BASE}/resume`+'):', error);
    return { error: error.message };
  }
}

async function stopSimulation() {
  try {
    const url = `${BASE}/stop`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Stop failed (url='+`${BASE}/stop`+'):', error);
    return { error: error.message };
  }
}

async function setSpeed(multiplier) {
  try {
    const url = `${BASE}/speed/${multiplier}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Set speed failed (url='+`${BASE}/speed/${multiplier}`+'):', error);
    return { error: error.message };
  }
}

async function getState() {
  try {
    const url = `${BASE}/state`;
    const response = await fetch(url, { method: 'GET' });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Get state failed (url='+`${BASE}/state`+'):', error);
    return { error: error.message };
  }
}

async function checkHealth() {
  try {
    const url = `${BASE}/health`;
    const response = await fetch(url, { method: 'GET' });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Health check failed (url='+`${BASE}/health`+'):', error);
    return { error: error.message };
  }
}

export {
  startSimulation,
  pauseSimulation,
  resumeSimulation,
  stopSimulation,
  setSpeed,
  getState,
  checkHealth,
};
