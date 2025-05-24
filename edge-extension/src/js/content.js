/**
 * Content script for JIRA Chatbot Assistant
 * This script runs in the context of web pages and creates a Monica AI-style hover icon
 */

console.log('JIRA Chatbot Assistant content script loaded');

// State management for hover icon
let hoverIcon = null;
let isIconVisible = false;
let hideTimeout = null;

// Styles for the hover icon and container
const iconStyles = `
    .jcai-hover-container {
        position: fixed;
        top: 50%;
        right: 20px;
        transform: translateY(-50%);
        z-index: 10000;
        pointer-events: none;
        transition: opacity 0.3s ease, transform 0.3s ease;
    }    .jcai-hover-icon {
        width: 48px;
        height: 48px;
        background: none;
        border: none;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        pointer-events: auto;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: visible;
    }    .jcai-hover-icon:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.2);
    }
    
    .jcai-hover-icon:active {
        transform: scale(0.95);
    }    .jcai-icon-symbol {
        color: white;
        font-size: 20px;
        font-weight: 600;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        /* Image-specific styles */
        width: 48px;
        height: 48px;
        object-fit: contain;
        border-radius: 12px;
    }
    
    .jcai-tooltip {
        position: absolute;
        right: 60px;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.2s ease;
        backdrop-filter: blur(10px);
    }
      .jcai-hover-icon:hover .jcai-tooltip {
        opacity: 1;
    }
    
    .jcai-hidden {
        opacity: 0;
        transform: translateY(-50%) translateX(20px);
        pointer-events: none;
    }
    
    @media (max-width: 768px) {
        .jcai-hover-container {
            right: 15px;
        }
        .jcai-hover-icon {
            width: 44px;
            height: 44px;
        }        .jcai-icon-symbol {
            font-size: 18px;
            width: 44px;
            height: 44px;
        }
    }
`;

// Create and inject styles
function injectStyles() {
    const styleElement = document.createElement('style');
    styleElement.textContent = iconStyles;
    document.head.appendChild(styleElement);
}

// Create the hover icon
function createHoverIcon() {
    if (hoverIcon) return;

    const container = document.createElement('div');
    container.className = 'jcai-hover-container jcai-hidden'; const icon = document.createElement('div');
    icon.className = 'jcai-hover-icon';

    const symbol = document.createElement('img');
    symbol.className = 'jcai-icon-symbol';
    symbol.src = chrome.runtime.getURL('images/icon128.png');
    symbol.alt = 'JIRA Assistant';
    symbol.style.width = '48px';
    symbol.style.height = '48px';
    symbol.style.objectFit = 'contain';
    symbol.style.borderRadius = '12px';// Fallback to text if image fails to load
    symbol.onerror = () => {
        console.log('JIRA icon image failed to load, using JC text as fallback');
        const textElement = document.createElement('div');
        textElement.className = 'jcai-icon-symbol';
        textElement.textContent = 'JC';
        textElement.style.color = '#333';
        textElement.style.fontSize = '20px';
        textElement.style.fontWeight = '600';
        textElement.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        textElement.style.textShadow = '0 1px 2px rgba(0, 0, 0, 0.1)';
        symbol.parentNode.replaceChild(textElement, symbol);
    }; const tooltip = document.createElement('div');
    tooltip.className = 'jcai-tooltip';
    tooltip.textContent = 'Open JIRA Assistant';

    icon.appendChild(symbol);
    icon.appendChild(tooltip);
    container.appendChild(icon);// Add click handler to open sidebar
    icon.addEventListener('click', () => {
        chrome.runtime.sendMessage({ action: 'openSidePanel' });
    });

    document.body.appendChild(container);
    hoverIcon = container;

    // Show icon after a short delay
    setTimeout(() => {
        showIcon();
    }, 1000);
}

// Show the icon
function showIcon() {
    if (!hoverIcon || isIconVisible) return;

    clearTimeout(hideTimeout);
    isIconVisible = true;
    hoverIcon.classList.remove('jcai-hidden');

    // Auto-hide after 5 seconds of no interaction
    hideTimeout = setTimeout(() => {
        hideIcon();
    }, 5000);
}

// Hide the icon
function hideIcon() {
    if (!hoverIcon || !isIconVisible) return;

    isIconVisible = false;
    hoverIcon.classList.add('jcai-hidden');
}

// Show icon on page interaction
function showIconOnInteraction() {
    if (!isIconVisible) {
        showIcon();
    } else {
        // Reset hide timer
        clearTimeout(hideTimeout);
        hideTimeout = setTimeout(() => {
            hideIcon();
        }, 5000);
    }
}

// Initialize when page is ready
function initialize() {
    // Skip on certain domains that might conflict
    const hostname = window.location.hostname;
    const skipDomains = ['chrome-extension://', 'moz-extension://', 'edge-extension://'];

    if (skipDomains.some(domain => window.location.href.startsWith(domain))) {
        return;
    }

    injectStyles();
    createHoverIcon();

    // Show icon on various user interactions
    document.addEventListener('mousemove', showIconOnInteraction);
    document.addEventListener('scroll', showIconOnInteraction);
    document.addEventListener('click', showIconOnInteraction);
    document.addEventListener('keydown', showIconOnInteraction);

    // Show icon when hovering near the right edge
    document.addEventListener('mousemove', (e) => {
        const windowWidth = window.innerWidth;
        const mouseX = e.clientX;

        // Show icon when mouse is within 100px of right edge
        if (windowWidth - mouseX < 100) {
            showIconOnInteraction();
        }
    });
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Content script received message:', message);

    if (message.action === 'showIcon') {
        showIcon();
    } else if (message.action === 'hideIcon') {
        hideIcon();
    }

    return true;
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}
