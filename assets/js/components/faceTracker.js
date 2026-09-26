// faceTracker.js – lightweight wrapper around MediaPipe FaceMesh
// This module is loaded dynamically only when the user starts the try‑on camera.
// It provides start(videoElement, onResults) and stop() functions.

/**
 * Dynamically import MediaPipe FaceMesh from CDN and start tracking.
 * @param {HTMLVideoElement} video - video element showing the webcam feed.
 * @param {(results: any) => void} onResults - callback receiving MediaPipe results.
 * @returns {Promise<void>} resolves when tracking loop has started.
 */
export async function start(video, onResults) {
  // Import FaceMesh class from CDN (ESM module).
  const { FaceMesh } = await import('https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js');

  const faceMesh = new FaceMesh({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
  });
  faceMesh.setOptions({
    maxNumFaces: 1,
    refineLandmarks: true,
    minDetectionConfidence: 0.7,
    minTrackingConfidence: 0.7,
  });
  faceMesh.onResults(onResults);

  // Run a simple requestAnimationFrame loop sending the current video frame to MediaPipe.
  let animId = null;
  const onFrame = async () => {
    if (video.readyState >= 2) { // HAVE_CURRENT_DATA
      await faceMesh.send({ image: video });
    }
    animId = requestAnimationFrame(onFrame);
  };
  animId = requestAnimationFrame(onFrame);

  // Store internal handle so stop() can cancel.
  _trackerHandle = { faceMesh, animId };
}

/**
 * Stops the face‑tracking loop and releases MediaPipe resources.
 */
export function stop() {
  if (_trackerHandle) {
    cancelAnimationFrame(_trackerHandle.animId);
    // MediaPipe FaceMesh does not expose an explicit dispose, but cancelling the loop is enough.
    _trackerHandle = null;
  }
}

// Private variable holding the current tracking session.
let _trackerHandle = null;
