let trackedDownloads = {};

// Triggered when the browser determines the filename of a new download
chrome.downloads.onDeterminingFilename.addListener((downloadItem, suggest) => {
    console.log("Download started:", downloadItem);

    // Add the download to tracked downloads
    trackedDownloads[downloadItem.id] = {
        filename: downloadItem.filename || null,
        checked: false,
        popupShown: false,
        suggest: suggest, // Store the suggest callback
        canceled: false,
        etag: null, // Store the ETag
        savedPath: null, // Will store the saved path
    };

    console.log("Tracked downloads after update:", trackedDownloads);

    // Pause download until duplicate check is complete
    fetchEtag(downloadItem.id);
    return true; // Indicate that we will handle the filename assignment asynchronously
});

// Fetch the ETag for the file being downloaded
function fetchEtag(downloadId) {
    chrome.downloads.search({ id: downloadId }, (results) => {
        if (results.length > 0 && results[0].url) {
            const url = results[0].url;
            console.log(`Fetching ETag for URL: ${url}`);

            // Attempt to fetch the ETag using fetch (with HEAD method)
            fetch(url, { method: "HEAD" })
                .then((response) => {
                    if (response.ok && response.headers.has("etag")) {
                        const etag = response.headers.get("etag");
                        trackedDownloads[downloadId].etag = etag;
                        console.log(`ETag fetched for download ${downloadId}: ${etag}`);
                    } else {
                        console.log(`No ETag found for URL: ${url}`);
                    }
                    checkForDuplicate(downloadId); // Proceed to duplicate check
                })
                .catch((error) => {
                    console.log(`Error fetching ETag for download ${downloadId} with URL ${url}:`, error);
                    checkForDuplicate(downloadId); // Proceed without ETag if fetch fails
                });
        } else {
            console.log(`URL not found for download ${downloadId}`);
            resumeDownload(downloadId);
        }
    });
}

// Check for duplicate using filename and optional ETag
async function checkForDuplicate(downloadId) {
    const downloadItem = trackedDownloads[downloadId];
    if (!downloadItem.filename) {
        console.warn(`Filename not available for download ${downloadId}.`);
        return;
    }

    const filename = downloadItem.filename;
    const etag = downloadItem.etag; // Include the ETag if available

    try {
        const response = await fetch("http://localhost:5000/check-duplicate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename, etag }), // Send ETag along with filename
        });

        const result = await response.json();
        console.log("Duplicate check result:", result);

        downloadItem.checked = true;

        if (result.isDuplicate && !downloadItem.popupShown) {
            showPopup(filename, downloadId, result.duplicatePath);
        } else if (!result.isDuplicate) {
            console.log(`No duplicate found. Proceeding with download: ${filename}`);
            resumeDownload(downloadId);
        }
    } catch (error) {
        console.error("Error checking for duplicate:", error);
        resumeDownload(downloadId); // If error, resume the download
    }
}

// Show popup with duplicate path
function showPopup(filename, downloadId, duplicatePath) {
    chrome.windows.create({
        url: "popup.html",
        type: "popup",
        width: 400,
        height: 300,
        focused: true,
    }, (window) => {
        waitForPopup(window.id, () => {
            chrome.runtime.sendMessage({
                action: "showPopup",
                message: `Duplicate file '${filename}' detected.`,
                duplicatePath: duplicatePath, // Include the path
                downloadId: downloadId,
            });
        });
    });

    trackedDownloads[downloadId].popupShown = true;
}

// Capture file path once the download is complete
chrome.downloads.onChanged.addListener((delta) => {
    console.log("onChanged event:", delta);
    console.log("Tracked downloads:", trackedDownloads);

    const downloadId = delta.id;
    if (trackedDownloads[downloadId]) {
        console.log(`Matched download ID: ${downloadId}`);
        const savedPath = delta.filename?.current;

        if (savedPath) {
            trackedDownloads[downloadId].savedPath = savedPath;
            console.log(`Download ${downloadId} saved at: ${savedPath}`);
            sendFilePathToServer(savedPath, downloadId);
            // Schedule deletion of tracked download after 5 seconds
            setTimeout(() => {
                if (trackedDownloads[downloadId]) {
                    console.log(`Deleting tracked download ${downloadId} after delay.`);
                    delete trackedDownloads[downloadId];
                }
            }, 5000); // 5 seconds delay
        }
    } else {
        console.log(`Download ID ${downloadId} not found in trackedDownloads.`);
    }
});

// Send the file path to the server
function sendFilePathToServer(savedPath, downloadId) {
    filename = trackedDownloads[downloadId].filename;
    etag = trackedDownloads[downloadId].etag;
    fetch("http://localhost:5000/save-file-path", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, etag, savedPath }), // Send only the saved path
    })
        .then((response) => response.json())
        .then((data) => {
            console.log("Server response:", data);
        })
        .catch((error) => {
            console.error("Error sending file path to server:", error);
        });
}

// Resume the download
function resumeDownload(downloadId) {
    const downloadItem = trackedDownloads[downloadId];
    if (downloadItem && downloadItem.suggest) {
        // Use the stored suggest callback to allow the download to proceed
        downloadItem.suggest({ filename: downloadItem.filename });
        console.log(`Resuming download ${downloadId}`);
    }
}

// Cancel the download
function cancelDownload(downloadId) {
    const downloadItem = trackedDownloads[downloadId];
    if (downloadItem && downloadItem.suggest) {
        chrome.downloads.cancel(downloadId, () => {
            if (chrome.runtime.lastError) {
                console.error(`Error canceling download ${downloadId}: ${chrome.runtime.lastError.message}`);
            } else {
                console.log(`Download ${downloadId} canceled.`);
            }
        });
    }
    delete trackedDownloads[downloadId]
}

// Wait for the popup to load
function waitForPopup(windowId, callback) {
    chrome.tabs.query({ windowId }, (tabs) => {
        const popupTab = tabs[0];
        if (popupTab && popupTab.status === "complete") {
            callback();
        } else {
            setTimeout(() => waitForPopup(windowId, callback), 500);
        }
    });
}

// Listen for user actions from the popup
chrome.runtime.onMessage.addListener((message) => {
    const downloadId = message.downloadId;

    if (message.action === "keepDownload") {
        console.log(`User chose to keep download ${downloadId}.`);
        resumeDownload(downloadId);
    } else if (message.action === "cancelDownload") {
        console.log(`User chose to cancel download ${downloadId}.`);
        cancelDownload(downloadId);
    }
});
