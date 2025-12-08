// Dynamically set API_BASE based on current host
const API_BASE = `http://${window.location.hostname}:16969`;
let currentTab = 'videos';
let videosPage = 0;
let shortsPage = 0;
const VIDEOS_PER_PAGE = 20;
const SHORTS_PER_PAGE = 10;
let isLoadingVideos = false;
let isLoadingShorts = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadVideos();
    loadShorts();
    setupSearch();
});

function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    currentTab = tabName;
    
    // Update active tab
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update active content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // If switching to shorts tab, open a random short
    if (tabName === 'shorts') {
        setTimeout(() => {
            openRandomShort();
        }, 100);
    }
}

async function openRandomShort() {
    // Load all shorts if not already loaded
    if (allShortsLoaded.length === 0) {
        try {
            const response = await fetch(`${API_BASE}/api/shorts?skip=0&limit=1000`);
            const shorts = await response.json();
            if (shorts && shorts.length > 0) {
                allShortsLoaded = shorts;
            }
        } catch (error) {
            console.error('Error loading shorts:', error);
            return;
        }
    }
    
    if (allShortsLoaded.length > 0) {
        // Pick a random short
        const randomIndex = Math.floor(Math.random() * allShortsLoaded.length);
        shortsData = allShortsLoaded;
        currentShortIndex = randomIndex;
        await openShortsModal(allShortsLoaded[randomIndex], true);
    }
}

async function loadVideos() {
    if (isLoadingVideos) return;
    isLoadingVideos = true;
    
    const btn = document.getElementById('load-more-videos');
    if (btn) btn.disabled = true;

    try {
        const skip = videosPage * VIDEOS_PER_PAGE;
        const response = await fetch(`${API_BASE}/api/videos?skip=${skip}&limit=${VIDEOS_PER_PAGE}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const videos = await response.json();
        
        if (videos && videos.length > 0) {
            renderVideos(videos);
            videosPage++;
            
            if (videos.length === VIDEOS_PER_PAGE && btn) {
                btn.style.display = 'block';
            }
        } else if (videosPage === 0) {
            document.getElementById('videos-grid').innerHTML = '<div class="no-content">No videos found</div>';
        }
    } catch (error) {
        console.error('Error loading videos:', error);
        if (videosPage === 0) {
            document.getElementById('videos-grid').innerHTML = `
                <div style="grid-column: 1/-1;">
                    <div class="error-message">
                        Error loading videos. Make sure the backend is running on <strong>http://localhost:16969</strong>
                        <br><small>${error.message}</small>
                    </div>
                </div>
            `;
        }
    } finally {
        isLoadingVideos = false;
        if (btn) btn.disabled = false;
    }
}

async function loadShorts() {
    // Shorts are now loaded on-demand when opening the modal
    // This function is kept for backward compatibility but does minimal work
    if (allShortsLoaded.length === 0) {
        try {
            const response = await fetch(`${API_BASE}/api/shorts?skip=0&limit=1000`);
            const shorts = await response.json();
            if (shorts && shorts.length > 0) {
                allShortsLoaded = shorts;
            }
        } catch (error) {
            console.error('Error loading shorts:', error);
        }
    }
}

function renderVideos(videos) {
    const container = document.getElementById('videos-grid');
    if (videosPage === 1) {
        container.innerHTML = '';
    }

    videos.forEach(video => {
        const card = document.createElement('div');
        card.className = 'video-card';
        card.innerHTML = `
            <div class="video-thumbnail">
                <video muted playsinline></video>
                <div class="play-icon">▶</div>
                <div class="duration">${formatDuration(video.duration)}</div>
            </div>
            <div class="video-info">
                <div class="video-title">${escapeHtml(video.title)}</div>
                <div class="video-channel">${escapeHtml(video.channel)}</div>
            </div>
        `;
        
        const videoElement = card.querySelector('video');
        videoElement.src = `${API_BASE}/api/video/${video.video_id}`;
        videoElement.addEventListener('click', (e) => e.stopPropagation());
        videoElement.addEventListener('loadedmetadata', () => {
            videoElement.currentTime = videoElement.duration * 0.3;
        });
        
        card.addEventListener('click', () => openVideoModal(video));
        container.appendChild(card);
    });
}

function renderShorts(shorts) {
    // Shorts are no longer rendered as a grid
    // They are displayed in a modal view only
}

async function openVideoModal(video) {
    const modal = document.getElementById('video-modal');
    const player = document.getElementById('video-player');
    
    player.src = `${API_BASE}/api/video/${video.video_id}`;
    document.getElementById('modal-title').textContent = video.title;
    document.getElementById('modal-channel').textContent = video.channel;
    document.getElementById('modal-duration').textContent = formatDuration(video.duration);

    // Load comments
    try {
        const response = await fetch(`${API_BASE}/api/comments/${video.video_id}`);
        const data = await response.json();
        renderComments(data.comments, false);
    } catch (error) {
        console.error('Error loading comments:', error);
        document.getElementById('comments-list').innerHTML = '<div class="no-content">No comments available</div>';
    }

    modal.classList.add('active');
    // Autoplay the video
    setTimeout(() => {
        player.play().catch(e => console.log('Autoplay prevented:', e));
    }, 100);
}

let shortsData = [];
let currentShortIndex = 0;
let allShortsLoaded = [];

async function openShortsModal(short, fromArray = false) {
    const modal = document.getElementById('shorts-modal');
    const player = document.getElementById('shorts-player');
    
    // Pause any currently playing video
    player.pause();
    
    // Load all shorts if not already loaded
    if (shortsData.length === 0) {
        shortsData = allShortsLoaded;
    }
    
    // Find the index of the clicked short
    if (!fromArray) {
        currentShortIndex = shortsData.findIndex(s => s.video_id === short.video_id);
        if (currentShortIndex === -1) {
            currentShortIndex = 0;
        }
    }
    
    const currentShort = shortsData[currentShortIndex];
    player.src = `${API_BASE}/api/video/${currentShort.video_id}`;
    
    // Set loop property and reset playback
    player.loop = true;
    player.currentTime = 0;

    // Load comments
    try {
        const response = await fetch(`${API_BASE}/api/comments/${currentShort.video_id}`);
        const data = await response.json();
        document.getElementById('shorts-comment-count').textContent = data.comments.length;
        renderShortsComments(data.comments);
    } catch (error) {
        console.error('Error loading comments:', error);
        document.getElementById('shorts-comments-list').innerHTML = '<div class="no-content">No comments available</div>';
    }

    modal.classList.add('active');
    
    // Autoplay the video
    setTimeout(() => {
        player.play().catch(e => console.log('Autoplay prevented:', e));
    }, 100);
    
    // Setup keyboard navigation
    setupShortsNavigation();
}

function setupShortsNavigation() {
    // Remove previous keyboard listener if any
    document.removeEventListener('keydown', handleShortsKeyboard);
    
    document.addEventListener('keydown', handleShortsKeyboard);
    
    // Setup swipe support on the modal
    const modal = document.getElementById('shorts-modal');
    let touchStartY = 0;
    let touchStartX = 0;
    
    // Remove old touch listeners
    modal.removeEventListener('touchstart', handleTouchStart);
    modal.removeEventListener('touchend', handleTouchEnd);
    
    // Add new touch listeners
    modal.addEventListener('touchstart', handleTouchStart, { passive: true });
    modal.addEventListener('touchend', handleTouchEnd, { passive: true });
    
    function handleTouchStart(e) {
        touchStartY = e.touches[0].clientY;
        touchStartX = e.touches[0].clientX;
    }
    
    function handleTouchEnd(e) {
        const touchEndY = e.changedTouches[0].clientY;
        const touchEndX = e.changedTouches[0].clientX;
        
        const diffY = touchStartY - touchEndY;
        const diffX = Math.abs(touchStartX - touchEndX);
        
        // Only respond to vertical swipes (ignore horizontal)
        if (Math.abs(diffY) > 50 && diffX < 100) {
            if (diffY > 0) {
                // Swiped up - next short
                nextShort();
            } else {
                // Swiped down - previous short
                previousShort();
            }
        }
    }
}

function toggleShortsComments() {
    const panel = document.getElementById('shorts-comments-panel');
    const button = document.getElementById('comment-toggle');
    
    if (panel.style.display === 'none') {
        panel.style.display = 'flex';
        button.style.backgroundColor = 'rgba(6, 95, 212, 0.8)';
    } else {
        panel.style.display = 'none';
        button.style.backgroundColor = 'rgba(255, 255, 255, 0.3)';
    }
}

function handleShortsKeyboard(e) {
    const modal = document.getElementById('shorts-modal');
    if (!modal.classList.contains('active')) {
        document.removeEventListener('keydown', handleShortsKeyboard);
        return;
    }
    
    if (e.key === 'ArrowUp') {
        e.preventDefault();
        previousShort();
    } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        nextShort();
    }
}

async function nextShort() {
    const player = document.getElementById('shorts-player');
    player.pause();
    
    if (currentShortIndex < shortsData.length - 1) {
        currentShortIndex++;
        await openShortsModal(shortsData[currentShortIndex], true);
        
        // Load more shorts if needed
        if (currentShortIndex >= shortsData.length - 5) {
            loadShorts();
        }
    }
}

async function previousShort() {
    const player = document.getElementById('shorts-player');
    player.pause();
    
    if (currentShortIndex > 0) {
        currentShortIndex--;
        await openShortsModal(shortsData[currentShortIndex], true);
    }
}

function closeVideoModal() {
    document.getElementById('video-modal').classList.remove('active');
    document.getElementById('video-player').pause();
}

function closeShortsModal() {
    document.getElementById('shorts-modal').classList.remove('active');
    document.getElementById('shorts-player').pause();
    document.removeEventListener('keydown', handleShortsKeyboard);
    shortsData = [];
    currentShortIndex = 0;
    
    // Switch back to videos tab
    switchTab('videos');
}

function renderComments(comments, isShorts = false) {
    const container = isShorts ? document.getElementById('shorts-comments-list') : document.getElementById('comments-list');
    
    if (!comments || comments.length === 0) {
        container.innerHTML = '<div class="no-content">No comments available</div>';
        return;
    }

    container.innerHTML = '';

    comments.slice(0, 50).forEach(comment => {
        const commentEl = document.createElement('div');
        commentEl.className = 'comment';
        const avatar = (comment.author || 'U').charAt(0).toUpperCase();
        
        let repliesHtml = '';
        if (comment.replies && comment.replies.length > 0) {
            const replyId = `replies-${Math.random().toString(36).substr(2, 9)}`;
            repliesHtml = `
                <div class="replies-toggle" onclick="toggleReplies('${replyId}')">
                    👁️ ${comment.replies.length} replies
                </div>
                <div id="${replyId}" style="display: none;">
                    ${comment.replies.slice(0, 5).map(reply => `
                        <div class="reply">
                            <div class="comment-author">${escapeHtml(reply.author || 'Anonymous')}</div>
                            <div class="comment-text">${escapeHtml(reply.text || '')}</div>
                            <div class="comment-meta">
                                <span>${formatDate(reply.timestamp)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        commentEl.innerHTML = `
            <div class="comment-avatar">${avatar}</div>
            <div class="comment-content">
                <div class="comment-author">${escapeHtml(comment.author || 'Anonymous')}</div>
                <div class="comment-text">${escapeHtml(comment.text || '')}</div>
                <div class="comment-meta">
                    <span>${formatDate(comment.timestamp)}</span>
                    <span>👍 ${comment.like_count || 0}</span>
                </div>
                ${repliesHtml}
            </div>
        `;
        container.appendChild(commentEl);
    });
}

function renderShortsComments(comments) {
    renderComments(comments, true);
}

function toggleReplies(id) {
    const el = document.getElementById(id);
    if (el) {
        el.style.display = el.style.display === 'none' ? 'block' : 'none';
    }
}

function formatDuration(seconds) {
    if (!seconds) return '0:00';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

function formatDate(timestamp) {
    if (!timestamp) return 'Unknown';
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Search functionality
let searchPage = 0;
let currentSearchQuery = '';
let isLoadingSearch = false;
const SEARCH_RESULTS_PER_PAGE = 20;

function setupSearch() {
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        if (query !== currentSearchQuery) {
            currentSearchQuery = query;
            searchPage = 0;
            
            if (!query) {
                document.getElementById('search-results').innerHTML = '<div class="search-no-results">Start typing to search for videos, shorts, or channels...</div>';
            } else {
                document.getElementById('search-results').innerHTML = '';
                loadSearchResults();
            }
        }
    });
}

async function loadSearchResults() {
    if (isLoadingSearch || !currentSearchQuery.trim()) return;
    isLoadingSearch = true;

    const resultsContainer = document.getElementById('search-results');
    const loadMoreBtn = document.querySelector('.search-load-more');

    try {
        const skip = searchPage * SEARCH_RESULTS_PER_PAGE;
        const response = await fetch(
            `${API_BASE}/api/videos/search?query=${encodeURIComponent(currentSearchQuery)}&skip=${skip}&limit=${SEARCH_RESULTS_PER_PAGE}`
        );
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const results = await response.json();
        
        if (results && results.length > 0) {
            renderSearchResults(results);
            searchPage++;
            
            // Show "Load More" button if we got a full page of results
            if (results.length === SEARCH_RESULTS_PER_PAGE) {
                loadMoreBtn.style.display = 'block';
            } else {
                loadMoreBtn.style.display = 'none';
            }
        } else if (searchPage === 0) {
            resultsContainer.innerHTML = '<div class="search-no-results">No results found for "' + escapeHtml(currentSearchQuery) + '"</div>';
            loadMoreBtn.style.display = 'none';
        } else {
            loadMoreBtn.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading search results:', error);
        if (searchPage === 0) {
            resultsContainer.innerHTML = `
                <div class="search-no-results">
                    Error loading search results. Make sure the backend is running.
                    <br><small>${error.message}</small>
                </div>
            `;
        }
        loadMoreBtn.style.display = 'none';
    } finally {
        isLoadingSearch = false;
    }
}

function renderSearchResults(results) {
    const resultsContainer = document.getElementById('search-results');
    
    results.forEach(item => {
        const card = document.createElement('div');
        card.className = 'search-result-item';
        card.innerHTML = `
            <div class="search-result-thumbnail">
                <video muted playsinline></video>
            </div>
            <div class="search-result-info">
                <div class="search-result-title">${escapeHtml(item.title)}</div>
                <div class="search-result-channel">${escapeHtml(item.channel)}</div>
                <div class="search-result-type">${item.type === 'video' ? '📹 Video' : '🎥 Short'}</div>
            </div>
        `;

        const videoElement = card.querySelector('video');
        videoElement.src = `${API_BASE}/api/video/${item.video_id}`;

        card.addEventListener('click', () => {
            if (item.type === 'video') {
                openVideoModal(item);
            } else {
                switchTab('shorts');
                setTimeout(() => {
                    shortsData = [item];
                    currentShortIndex = 0;
                    openShortsModal(item, true);
                }, 100);
            }
        });

        resultsContainer.appendChild(card);
    });
}

// Update switchTab to reset search when switching away
const originalSwitchTab = switchTab;
window.switchTab = function(tabName) {
    if (tabName !== 'search') {
        // Reset search state when leaving search tab
        searchPage = 0;
        currentSearchQuery = '';
    }
    originalSwitchTab(tabName);
};

