// background.js — service worker
// Handles messages between content script and popup

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'APPLICATION_LOGGED') {
    // Show a badge on the extension icon
    chrome.action.setBadgeText({ text: '✓' });
    chrome.action.setBadgeBackgroundColor({ color: '#00d4a0' });
    setTimeout(() => chrome.action.setBadgeText({ text: '' }), 3000);
  }
  return true;
});

// Clear badge when extension icon is clicked
chrome.action.onClicked.addListener(() => {
  chrome.action.setBadgeText({ text: '' });
});
