const statusText = document.getElementById('statusText');
const statusBox = document.getElementById('statusBox');
const startBtn = document.getElementById('startRecognitionBtn');
const signOutBtn = document.getElementById('signOutBtn');
const tryAgainBtn = document.getElementById('tryAgainBtn');
const studentCard = document.getElementById('studentCard');
const studentName = document.getElementById('studentName');
const studentBranch = document.getElementById('studentBranch');
const studentRoll = document.getElementById('studentRoll');
const studentEnrollment = document.getElementById('studentEnrollment');
const studentYear = document.getElementById('studentYear');
const studentSection = document.getElementById('studentSection');
const studentDate = document.getElementById('studentDate');
const studentTime = document.getElementById('studentTime');
const video = document.getElementById('camera');

let stream = null;
let processing = false;
let recognitionAction = 'sign_in';

function setStatus(message, tone = 'info') {
  if (!statusText) return;
  statusText.textContent = message;
  if (!statusBox) return;
  statusBox.style.background = tone === 'success'
    ? 'rgba(31, 163, 109, 0.1)'
    : tone === 'error'
      ? 'rgba(214, 59, 59, 0.1)'
      : 'rgba(11, 94, 215, 0.08)';
  statusBox.style.color = tone === 'success'
    ? '#1fa36d'
    : tone === 'error'
      ? '#d63b3b'
      : '#0a3f9d';
  const dot = statusBox.querySelector('.status-dot');
  if (dot) {
    dot.style.background = tone === 'success'
      ? '#1fa36d'
      : tone === 'error'
        ? '#d63b3b'
        : '#f3b126';
    dot.style.boxShadow = tone === 'success'
      ? '0 0 0 6px rgba(31, 163, 109, 0.2)'
      : tone === 'error'
        ? '0 0 0 6px rgba(214, 59, 59, 0.2)'
        : '0 0 0 6px rgba(243, 177, 38, 0.18)';
  }
}

async function startCamera() {
  if (!video) return;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    video.srcObject = stream;
    video.play();
    setStatus('Scanning Face...');
    return true;
  } catch (error) {
    setStatus('Camera unavailable or permission denied.', 'error');
    return false;
  }
}

function captureFrame() {
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL('image/jpeg', 0.9);
}

async function recognizeFace() {
  if (processing) return;
  processing = true;
  if (startBtn) startBtn.disabled = true;
  if (signOutBtn) signOutBtn.disabled = true;
  setStatus('Face Detected');

  try {
    const imageData = captureFrame();
    const response = await fetch('/api/recognize-face', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_data: imageData, action: recognitionAction })
    });

    const result = await response.json();
    if (result.success) {
      setStatus(`✓ ${result.student.name}: ${result.message}`, 'success');
      if (studentCard) {
        studentCard.classList.remove('hidden');
      }
      if (studentName) studentName.textContent = result.student.name;
      if (studentBranch) studentBranch.textContent = result.student.branch;
      if (studentRoll) studentRoll.textContent = result.student.roll_number;
      if (studentEnrollment) studentEnrollment.textContent = result.student.enrollment_number;
      if (studentYear) studentYear.textContent = result.student.year;
      if (studentSection) studentSection.textContent = result.student.section;
      if (studentDate) studentDate.textContent = new Date().toLocaleDateString('en-GB');
      if (studentTime) studentTime.textContent = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      window.location.href = `/dashboard?student_id=${result.student.id}`;
    } else {
      setStatus(result.message || 'Student Not Found. Please Try Again.', 'error');
      if (tryAgainBtn) tryAgainBtn.classList.remove('hidden');
    }
  } catch (error) {
    setStatus('Face recognition failed. Please try again.', 'error');
  } finally {
    processing = false;
    if (startBtn) startBtn.disabled = false;
    if (signOutBtn) signOutBtn.disabled = false;
  }
}

async function beginRecognition(action) {
  recognitionAction = action;
  const actionLabel = action === 'sign_out' ? 'Signing Out' : 'Signing In';
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setStatus('Camera access is not supported in this browser.', 'error');
    return;
  }
  const ok = await startCamera();
  if (ok) {
    setStatus(`${actionLabel} with Face...`);
    setTimeout(recognizeFace, 1200);
  }
}

if (startBtn) {
  startBtn.addEventListener('click', () => beginRecognition('sign_in'));
}

if (signOutBtn) {
  signOutBtn.addEventListener('click', () => beginRecognition('sign_out'));
}

if (tryAgainBtn) {
  tryAgainBtn.addEventListener('click', async () => {
    tryAgainBtn.classList.add('hidden');
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus('Camera access is not supported in this browser.', 'error');
      return;
    }
    const ok = await startCamera();
    if (ok) {
      setStatus(recognitionAction === 'sign_out' ? 'Signing Out with Face...' : 'Signing In with Face...');
      setTimeout(recognizeFace, 1200);
    }
  });
}

const registerForm = document.getElementById('studentForm');
const registerCamera = document.getElementById('registerCamera');
const registerStatusText = document.getElementById('registerStatusText');
const captureFaceBtn = document.getElementById('captureFaceBtn');
const registerStudentBtn = document.getElementById('registerStudentBtn');
let capturedFaceData = null;
let registeredStudentId = null;

async function startRegisterCamera() {
  if (!registerCamera) return false;
  if (registerCamera.srcObject) return true;
  try {
    const streamObject = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    registerCamera.srcObject = streamObject;
    await registerCamera.play();
    if (registerCamera.readyState < 2) {
      await new Promise((resolve) => registerCamera.addEventListener('loadeddata', resolve, { once: true }));
    }
    if (registerStatusText) {
      registerStatusText.textContent = 'Camera ready. Capture student face.';
    }
    return true;
  } catch (error) {
    if (registerStatusText) {
      registerStatusText.textContent = 'Camera unavailable or permission denied.';
    }
    return false;
  }
}

function captureRegisterFace() {
  if (!registerCamera) return;
  const canvas = document.createElement('canvas');
  canvas.width = registerCamera.videoWidth || 640;
  canvas.height = registerCamera.videoHeight || 480;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(registerCamera, 0, 0, canvas.width, canvas.height);
  capturedFaceData = canvas.toDataURL('image/jpeg', 0.9);
  if (registerStatusText) {
    registerStatusText.textContent = 'Face captured. Now register the student.';
  }
}

if (captureFaceBtn) {
  captureFaceBtn.addEventListener('click', async () => {
    const ready = await startRegisterCamera();
    if (ready) captureRegisterFace();
  });
}

if (registerStudentBtn) {
  registerStudentBtn.addEventListener('click', async () => {
    if (!registerForm) return;
    const formData = new FormData(registerForm);
    const payload = Object.fromEntries(formData.entries());
    if (!payload.name || !payload.roll_number || !payload.enrollment_number || !payload.branch || !payload.year || !payload.section) {
      if (registerStatusText) {
        registerStatusText.textContent = 'Please fill all student details.';
      }
      return;
    }

    if (!capturedFaceData) {
      if (registerStatusText) {
        registerStatusText.textContent = 'Please capture the face first.';
      }
      return;
    }

    try {
      const studentResponse = await fetch('/api/register-student', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const studentResult = await studentResponse.json();
      if (!studentResult.success) {
        throw new Error(studentResult.message || 'Student registration failed.');
      }
      registeredStudentId = studentResult.student_id;
      const faceResponse = await fetch('/api/register-face', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: registeredStudentId, image_data: capturedFaceData })
      });
      const faceResult = await faceResponse.json();
      if (!faceResult.success) {
        throw new Error(faceResult.message || 'Face registration failed.');
      }
      if (registerStatusText) {
        registerStatusText.textContent = 'Face Registration Successful.';
      }
      setTimeout(() => {
        window.location.href = '/admin';
      }, 900);
    } catch (error) {
      if (registerStatusText) {
        registerStatusText.textContent = error.message || 'Registration failed.';
      }
    }
  });
}

window.addEventListener('load', () => {
  if (registerCamera) {
    startRegisterCamera();
  }
});
