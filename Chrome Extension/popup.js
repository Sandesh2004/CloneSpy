// Listen for messages from the background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'showPopup') {
        const { message: popupMessage, duplicatePath, downloadId } = message;

        // Display the message and file path in the popup
        document.getElementById('message').textContent = popupMessage;
        document.getElementById('filePath').textContent = `Existing file path: ${duplicatePath}`;

        // Add event listeners to buttons for user's response
        document.getElementById('keepBtn').onclick = () => {
            // Send message back to background script to keep the download
            chrome.runtime.sendMessage({ action: 'keepDownload', downloadId: downloadId });
            window.close(); // Close the popup after the choice is made
        };

        document.getElementById('cancelBtn').onclick = () => {
            // Send message back to background script to cancel the download
            chrome.runtime.sendMessage({ action: 'cancelDownload', downloadId: downloadId });
            window.close(); // Close the popup after the choice is made
        };
    }
});
