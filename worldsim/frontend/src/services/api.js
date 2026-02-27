// api.js — centralize HTTP calls to WorldSim backend

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function startSimulation() {
  try {
    const response = await fetch(`${BASE}/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Start failed:', error);
    return { error: error.message };
  }
}

async function pauseSimulation() {
  try {
    const response = await fetch(`${BASE}/pause`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Pause failed:', error);
    return { error: error.message };
  }
}

async function resumeSimulation() {
  try {
    const response = await fetch(`${BASE}/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Resume failed:', error);
    return { error: error.message };
  }
}

async function stopSimulation() {
  try {
    const response = await fetch(`${BASE}/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Stop failed:', error);
    return { error: error.message };
  }
}

async function setSpeed(multiplier) {
  try {
    const response = await fetch(`${BASE}/speed/${multiplier}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Set speed failed:', error);
    return { error: error.message };
  }
}

async function getState() {
  try {
    const response = await fetch(`${BASE}/state`, { method: 'GET' });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Get state failed:', error);
    return { error: error.message };
  }
}

async function checkHealth() {
  try {
    const response = await fetch(`${BASE}/health`, { method: 'GET' });
    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Health check failed:', error);
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
