// web/static/audioManager.js
// (V1.1 - Removed Fallback to Browser's Speech Synthesis)

export function createAudioManager() {
    const state = {
        isSoundEnabled: true,
        audio: new Audio(),
        pollingIntervalId: null,
    };

    const toggleSoundBtn = document.getElementById('toggle-sound-btn');

    function setupEventListeners() {
        toggleSoundBtn?.addEventListener('click', () => {
            state.isSoundEnabled = !state.isSoundEnabled;
            toggleSoundBtn.textContent = state.isSoundEnabled ? '🔊' : '🔇';
            if (!state.isSoundEnabled) {
                stopAllAudio();
            }
        });
    }

    function stopAllAudio() {
        if (state.pollingIntervalId) {
            clearInterval(state.pollingIntervalId);
            state.pollingIntervalId = null;
        }
        state.audio.pause();
        state.audio.currentTime = 0;
    }

    function playAudio(voiceUrl) {
        if (!state.isSoundEnabled || !voiceUrl) return;
        
        stopAllAudio();

        state.audio.src = voiceUrl;
        state.audio.playbackRate = 1.15;
        state.audio.play().catch(e => console.error("Audio playback error:", e));
    }

    function pollForAudio(taskId, maxAttempts = 20, interval = 1500) {
        if (state.pollingIntervalId) {
            clearInterval(state.pollingIntervalId);
        }

        let attempts = 0;
        state.pollingIntervalId = setInterval(async () => {
            try {
                attempts++;
                const response = await fetch(`/audio_status/${taskId}`);
                
                if (response.status === 200) {
                    const data = await response.json();
                    if (data.status === 'done') {
                        clearInterval(state.pollingIntervalId);
                        state.pollingIntervalId = null;
                        playAudio(data.url);
                    } else if (data.status === 'failed') {
                        clearInterval(state.pollingIntervalId);
                        state.pollingIntervalId = null;
                        console.error(`Audio generation failed for task: ${taskId}`);
                    }
                }

                if (attempts >= maxAttempts) {
                    clearInterval(state.pollingIntervalId);
                    state.pollingIntervalId = null;
                    console.error(`Polling for audio timed out for task: ${taskId}`);
                }
            } catch (error) {
                clearInterval(state.pollingIntervalId);
                state.pollingIntervalId = null;
                console.error('Error polling for audio:', error);
            }
        }, interval);
    }

    setupEventListeners();

    return {
        startPolling: pollForAudio,
    };
}