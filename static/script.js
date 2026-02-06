document.addEventListener("DOMContentLoaded", () => {
    const gridContainer = document.getElementById("grid-container");
    const statusText = document.getElementById("status-text");
    const statusDot = document.querySelector(".dot");
    const startBtn = document.getElementById("start-btn");
    const stopBtn = document.getElementById("stop-btn");
    const galleryGrid = document.getElementById("gallery-grid");

    // Config Elements
    const elMotionThreshold = document.getElementById("motion_threshold");
    const elTimeLapseDuration = document.getElementById("time_lapse_duration");
    const elTimeBetweenSnaps = document.getElementById("time_between_snaps");
    const elImageQuality = document.getElementById("image_quality");
    const elQualityVal = document.getElementById("quality-val");
    const elTimezone = document.getElementById("timezone");

    let currentConfig = {};
    let activeCells = new Set();
    let isPolling = true;

    // --- CONFIG & GRID ---

    elImageQuality.addEventListener("input", () => {
        elQualityVal.textContent = elImageQuality.value;
    });

    async function fetchConfig() {
        try {
            const res = await fetch("/api/config");
            const config = await res.json();
            currentConfig = config;

            // Populate Inputs
            elMotionThreshold.value = config.motion_threshold;
            elTimeLapseDuration.value = config.time_lapse_duration;
            elTimeBetweenSnaps.value = config.time_between_snaps;
            elImageQuality.value = config.image_quality || 80;
            elQualityVal.textContent = elImageQuality.value;
            elTimezone.value = config.timezone;

            // Render Grid
            renderGrid(config.grid_rows, config.grid_cols, config.grid_mask);
        } catch (e) {
            console.error("Error fetching config", e);
        }
    }

    // --- CONTROLS ---

    startBtn.addEventListener("click", async () => {
        try {
            await fetch("/api/start", { method: "POST" });
            pollStatus(); // Immediate update
        } catch (e) {
            alert("Failed to start monitoring");
        }
    });

    stopBtn.addEventListener("click", async () => {
        try {
            await fetch("/api/stop", { method: "POST" });
            pollStatus(); // Immediate update
        } catch (e) {
            alert("Failed to stop monitoring");
        }
    });

    function renderGrid(rows, cols, mask) {
        // Calculate cell size based on camera resolution (640x480)
        // We want the grid to match the video aspect ratio.
        // Let's force the container to be 640x480 for now to match default cam.

        gridContainer.style.width = "640px";
        gridContainer.style.height = "480px";
        gridContainer.style.display = "grid";
        gridContainer.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
        gridContainer.style.gridTemplateRows = `repeat(${rows}, 1fr)`;

        gridContainer.innerHTML = `<img id="video-feed" src="/video_feed" alt="Live View">`;

        activeCells = new Set(mask);

        for (let i = 0; i < rows * cols; i++) {
            const cell = document.createElement("div");
            cell.classList.add("grid-cell");
            cell.dataset.index = i;

            if (activeCells.has(i)) {
                cell.classList.add("active");
            }

            cell.addEventListener("click", () => toggleCell(cell, i));
            gridContainer.appendChild(cell);
        }
    }

    function toggleCell(cell, index) {
        if (activeCells.has(index)) {
            activeCells.delete(index);
            cell.classList.remove("active");
        } else {
            activeCells.add(index);
            cell.classList.add("active");
        }
    }

    document.getElementById("save-btn").addEventListener("click", async () => {
        const newConfig = {
            ...currentConfig,
            motion_threshold: parseInt(elMotionThreshold.value),
            time_lapse_duration: parseInt(elTimeLapseDuration.value),
            time_between_snaps: parseFloat(elTimeBetweenSnaps.value),
            image_quality: parseInt(elImageQuality.value),
            timezone: elTimezone.value,
            grid_mask: Array.from(activeCells)
        };

        try {
            const res = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(newConfig)
            });
            if (res.ok) {
                alert("Configuration Saved!");
                fetchConfig(); // Refresh
            }
        } catch (e) {
            alert("Failed to save config");
        }
    });

    // --- STATUS ---

    async function pollStatus() {
        if (!isPolling) return;
        try {
            const res = await fetch("/api/status");
            const status = await res.json();

            let statusStr = "Ready";
            statusDot.classList.remove("active");

            if (status.recording) {
                statusStr = "RECORDING TIME-LAPSE";
                statusDot.classList.add("active");
                statusDot.style.backgroundColor = "#ff4757"; // Red for recording
                startBtn.style.display = "none";
                stopBtn.style.display = "inline-block";
            } else if (status.monitoring_enabled) {
                statusStr = "Monitoring Active";
                statusDot.classList.add("active");
                statusDot.style.backgroundColor = "#00ff9d"; // Green for monitoring
                startBtn.style.display = "none";
                stopBtn.style.display = "inline-block";
            } else {
                statusStr = "Idle (Monitoring Stopped)";
                statusDot.classList.remove("active");
                statusDot.style.backgroundColor = "#7f8c8d"; // Grey for idle
                startBtn.style.display = "inline-block";
                stopBtn.style.display = "none";
            }

            checkErrors(status);

            if (status.mock_mode) {
                statusStr += " (DEV/MOCK)";
            }

            statusText.textContent = statusStr;
        } catch (e) {
            statusText.textContent = "Disconnected";
        }
    }

    // --- GALLERY ---

    async function loadGallery() {
        try {
            const res = await fetch("/api/images");
            const images = await res.json();

            galleryGrid.innerHTML = "";
            images.forEach(img => {
                const card = document.createElement("div");
                card.classList.add("thumb-card");
                card.innerHTML = `
                    <div style="background-image: url('${img.url}?t=${Date.now()}')" class="thumb-img" style="height:100px; background-size:cover;"></div>
                    <img src="${img.url}" loading="lazy" style="display:none"> <!-- Preload for lightbox -->
                    <div class="thumb-caption">${img.filename}</div>
                `;
                // Use background image for grid for better fit, or img tag
                // Let's use img tag inside
                card.innerHTML = `
                    <img src="${img.url}" loading="lazy">
                    <div class="thumb-caption">${img.filename}</div>
                `;

                card.addEventListener("click", () => openLightbox(img.url, img.filename));
                galleryGrid.appendChild(card);
            });
        } catch (e) {
            console.error("Gallery load error", e);
        }
    }

    document.getElementById("delete-btn").addEventListener("click", async () => {
        if (!confirm("Delete ALL captured images?")) return;
        await fetch("/api/images/delete_all", { method: "POST" });
        loadGallery();
    });

    document.getElementById("download-btn").addEventListener("click", () => {
        window.location.href = "/api/images/download";
    });

    // --- LIGHTBOX ---
    const lightbox = document.getElementById("lightbox");
    const lightboxImg = document.getElementById("lightbox-img");
    const lightboxCaption = document.getElementById("lightbox-caption");
    const closeLightbox = document.querySelector(".close-lightbox");

    function openLightbox(url, caption) {
        lightboxImg.src = url;
        lightboxCaption.textContent = caption;
        lightbox.classList.remove("hidden");
    }

    closeLightbox.addEventListener("click", () => {
        lightbox.classList.add("hidden");
    });

    lightbox.addEventListener("click", (e) => {
        if (e.target === lightbox) lightbox.classList.add("hidden");
    });

    // --- INIT ---
    fetchConfig();
    pollStatus();
    loadGallery();

    setInterval(pollStatus, 2000);
    setInterval(loadGallery, 5000); // Poll gallery less frequently

    // --- LOGS & ERRORS ---
    const errorBanner = document.getElementById("error-banner");
    const errorText = document.getElementById("error-text");
    const logsBtn = document.getElementById("logs-btn");
    const logsModal = document.getElementById("logs-modal");
    const closeLogs = document.getElementById("close-logs");
    const logsContainer = document.getElementById("logs-container");
    const refreshLogsBtn = document.getElementById("refresh-logs");

    async function checkErrors(status) {
        if (status.camera_error) {
            errorBanner.classList.remove("hidden");
            errorText.textContent = `Camera Error: ${status.camera_error}`;
            // Disable start button if fatal error? or let user retry?
            // startBtn.disabled = true; 
        } else {
            errorBanner.classList.add("hidden");
        }
    }

    logsBtn.addEventListener("click", () => {
        logsModal.classList.remove("hidden");
        fetchLogs();
    });

    closeLogs.addEventListener("click", () => {
        logsModal.classList.add("hidden");
    });

    refreshLogsBtn.addEventListener("click", fetchLogs);

    async function fetchLogs() {
        try {
            const res = await fetch("/api/logs");
            const data = await res.json();
            logsContainer.innerHTML = data.logs.map(log => `<div class="log-entry">${log}</div>`).join("");
        } catch (e) {
            logsContainer.textContent = "Failed to load logs.";
        }
    }

    // Hook into pollStatus
    const originalPollStatus = pollStatus;
    pollStatus = async () => {
        // We modify pollStatus by redefining it or just updating the original function's logic inside.
        // Actually, let's just copy the logic or append to it. 
        // cleaner to just update the existing function.
        // Since I can't easily redefine inside this scope without rewriting the whole chunk, 
        // I will rely on the fact that I am replacing the whole file content or a block.
        // Wait, I am replacing a block.
        // Let's rewrite the pollStatus function completely in the big block replacement if possible.
        // But for minimal diff, I will just call checkErrors inside the existing pollStatus loop?
        // Ah, the tool allows replacing chunks.
        // Let's rewrite the pollStatus function logic in a separate replacement call to be clean.
        // For now, I'll just add the UI handlers here and assume I update pollStatus in next step.
    };
});
