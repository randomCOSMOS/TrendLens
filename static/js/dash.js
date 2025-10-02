let currentTrackingList = [];
let currentSortColumn = 'followers';
let currentSortDirection = 'desc';
let profilesData = window.profilesData;

class TableSorter {
    constructor(tableId) {
        this.table = document.getElementById(tableId);
        this.tbody = document.getElementById('profilesTableBody');
        this.data = [...profilesData];
        this.currentSort = { column: 'followers', direction: 'desc' };
        
        this.initSortHandlers();
        this.updateSortIndicators();
    }
    
    initSortHandlers() {
        const sortableHeaders = this.table.querySelectorAll('th.sortable');
        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-column');
                const type = header.getAttribute('data-type');
                this.sortTable(column, type);
            });
        });
    }
    
    sortTable(column, type) {
        if (this.currentSort.column === column) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.direction = type === 'number' ? 'desc' : 'asc';
        }
        
        this.currentSort.column = column;
        
        this.data.sort((a, b) => {
            let aVal = this.getValue(a, column);
            let bVal = this.getValue(b, column);
            
            if (type === 'number') {
                aVal = parseFloat(aVal) || 0;
                bVal = parseFloat(bVal) || 0;
            } else {
                aVal = aVal.toString().toLowerCase();
                bVal = bVal.toString().toLowerCase();
            }
            
            let result = 0;
            if (aVal < bVal) result = -1;
            if (aVal > bVal) result = 1;
            
            return this.currentSort.direction === 'desc' ? -result : result;
        });
        
        this.renderTable();
        this.updateSortIndicators();
    }
    
    getValue(obj, column) {
        switch (column) {
            case 'engagement':
                // Calculate posts per 1K followers
                return obj.followers > 0 ? (obj.total_posts / obj.followers) * 1000 : 0;
            case 'profile_name':
                return obj.profile_name || obj.username;
            default:
                return obj[column] || '';
        }
    }
    
    renderTable() {
        this.tbody.innerHTML = '';
        
        this.data.forEach((profile, index) => {
            const row = this.createTableRow(profile, index + 1);
            this.tbody.appendChild(row);
        });
        
        const rows = this.tbody.querySelectorAll('.table-row');
        rows.forEach((row, index) => {
            row.style.animationDelay = `${index * 30}ms`;
            row.classList.add('row-enter');
        });
    }
    
    createTableRow(profile, displayRank) {
        const row = document.createElement('tr');
        row.className = 'table-row';
        
        // Calculate posts per 1K followers
        const postsPerThousand = profile.followers > 0 ? (profile.total_posts / profile.followers) * 1000 : 0;
        
        // Use proxy for Instagram images
        const imageUrl = profile.profile_pic_url ? 
            `/proxy-image?url=${encodeURIComponent(profile.profile_pic_url)}` : null;
        
        row.innerHTML = `
            <td class="rank-cell">
                <div class="rank-badge rank-${displayRank <= 3 ? displayRank : 'other'}">
                    ${displayRank}
                </div>
            </td>
            <td>
                <div class="username-cell">
                    <div class="profile-pic-container">
                        ${imageUrl ? 
                            `<img src="${imageUrl}" alt="${profile.username}" class="profile-pic" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                            <div class="profile-avatar" style="display:none;">${profile.username[0].toUpperCase()}</div>` :
                            `<div class="profile-avatar">${profile.username[0].toUpperCase()}</div>`
                        }
                    </div>
                    <a href="/profile/${profile.username}" class="username-link">
                        <span class="username-text">@${profile.username}</span>
                        ${profile.is_verified ? '<span class="verified-badge">✓</span>' : ''}
                    </a>
                </div>
            </td>
            <td class="profile-name">${profile.profile_name || profile.username}</td>
            <td><span class="metric-number">${this.formatNumber(profile.followers)}</span></td>
            <td><span class="metric-number">${this.formatNumber(profile.following)}</span></td>
            <td><span class="metric-number">${this.formatNumber(profile.total_posts)}</span></td>
            <td>
                <span class="engagement-score">
                    ${postsPerThousand.toFixed(1)}
                </span>
            </td>
        `;
        
        return row;
    }



    
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }
    
    updateSortIndicators() {
        const indicators = this.table.querySelectorAll('.sort-indicator');
        indicators.forEach(indicator => {
            indicator.textContent = '⇅';
            indicator.classList.remove('sort-asc', 'sort-desc');
        });
        
        const currentHeader = this.table.querySelector(`th[data-column="${this.currentSort.column}"]`);
        if (currentHeader) {
            const indicator = currentHeader.querySelector('.sort-indicator');
            indicator.textContent = this.currentSort.direction === 'asc' ? '↑' : '↓';
            indicator.classList.add(this.currentSort.direction === 'asc' ? 'sort-asc' : 'sort-desc');
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    if (profilesData && profilesData.length > 0) {
        new TableSorter('profilesTable');
    }
});

function openManageModal() {
    document.getElementById('manageModal').style.display = 'block';
    loadTrackingList();
}

function closeManageModal() {
    document.getElementById('manageModal').style.display = 'none';
}

async function loadTrackingList() {
    try {
        const response = await fetch('/api/tracking');
        const data = await response.json();
        
        if (data.usernames) {
            currentTrackingList = data.usernames;
            renderTrackingList();
        }
    } catch (error) {
        console.error('Error loading tracking list:', error);
    }
}

function renderTrackingList() {
    const trackingList = document.getElementById('trackingList');
    const trackingCount = document.getElementById('trackingCount');
    
    trackingCount.textContent = currentTrackingList.length;
    
    trackingList.innerHTML = '';
    
    if (currentTrackingList.length === 0) {
        trackingList.innerHTML = '<p class="empty-message">No usernames in tracking list</p>';
        return;
    }
    
    currentTrackingList.forEach(username => {
        const item = document.createElement('div');
        item.className = 'tracking-item';
        item.innerHTML = `
            <div class="tracking-username">
                <span class="username-icon">@</span>
                <span>${username}</span>
            </div>
            <button class="btn-remove" onclick="removeUsername('${username}')" title="Remove">
                Remove
            </button>
        `;
        trackingList.appendChild(item);
    });
}

async function addUsername() {
    const input = document.getElementById('newUsername');
    const username = input.value.trim().toLowerCase();
    
    if (!username) {
        alert('Please enter a username');
        return;
    }
    
    if (username.includes('@') || username.includes(' ') || username.includes('/')) {
        alert('Please enter only the username without @, spaces, or special characters');
        return;
    }
    
    try {
        const response = await fetch('/api/tracking/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentTrackingList = data.usernames;
            renderTrackingList();
            input.value = '';
            showMessage('Username added successfully!', 'success');
        } else {
            showMessage(data.error || 'Error adding username', 'error');
        }
    } catch (error) {
        console.error('Error adding username:', error);
        showMessage('Network error. Please try again.', 'error');
    }
}

async function removeUsername(username) {
    if (!confirm(`Remove @${username} from tracking list?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/tracking/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentTrackingList = data.usernames;
            renderTrackingList();
            showMessage('Username removed successfully!', 'success');
        } else {
            showMessage(data.error || 'Error removing username', 'error');
        }
    } catch (error) {
        console.error('Error removing username:', error);
        showMessage('Network error. Please try again.', 'error');
    }
}

function refreshDashboard() {
    closeManageModal();
    window.location.reload();
}

function showMessage(message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `flash-message flash-${type}`;
    messageDiv.innerHTML = `
        <span>${message}</span>
        <button class="flash-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    const flashContainer = document.querySelector('.flash-container') || document.body;
    flashContainer.appendChild(messageDiv);
    
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 3000);
}

window.onclick = function(event) {
    const modal = document.getElementById('manageModal');
    if (event.target == modal) {
        closeManageModal();
    }
}

document.getElementById('newUsername').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        addUsername();
    }
})
