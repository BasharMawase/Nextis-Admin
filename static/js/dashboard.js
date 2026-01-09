// File upload handling
const fileInput = document.getElementById('fileInput');
const uploadBox = document.getElementById('uploadBox');
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

// Sidebar Toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleIcon = document.getElementById('toggleIcon');

    sidebar.classList.toggle('collapsed');

    if (sidebar.classList.contains('collapsed')) {
        toggleIcon.textContent = '▶'; // Point right when collapsed
    } else {
        toggleIcon.textContent = '◀'; // Point left when expanded
    }
}

// Phone number formatting function
function formatPhoneDisplay(phone) {
    if (!phone || phone === 'אין' || phone === '' || phone === '-') {
        return 'אין';
    }

    // Remove all non-digit characters
    let digits = phone.replace(/\D/g, '');

    // Handle country code
    if (digits.startsWith('972')) {
        digits = '0' + digits.substring(3);
    }

    // If number doesn't start with 0 but is 9 digits, add 0
    if (!digits.startsWith('0') && digits.length === 9) {
        digits = '0' + digits;
    }

    // Format based on length and prefix
    if (digits.length === 10 && digits.startsWith('05')) {
        // Mobile: 05X-XXXXXXX
        return `${digits.substring(0, 3)}-${digits.substring(3)}`;
    } else if (digits.length === 9 && digits.startsWith('0') && !digits.startsWith('05')) {
        // Landline: 0X-XXXXXXX
        return `${digits.substring(0, 2)}-${digits.substring(2)}`;
    } else if (digits.length === 10 && digits.startsWith('0')) {
        // Generic 10-digit: 0XX-XXXXXXX
        return `${digits.substring(0, 3)}-${digits.substring(3)}`;
    }

    // Return original if doesn't match expected patterns
    return phone;
}


// City Search Logic
let currentCityClients = [];
const citySearchInput = document.getElementById('citySearchInput');

if (citySearchInput) {
    citySearchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (!currentCityClients) return;

        const filtered = currentCityClients.filter(c => {
            const name = (c.business_name || c['Business Name'] || '').toLowerCase();
            const phone = (c.phone || c.Phone || '').toLowerCase();
            return name.includes(query) || phone.includes(query);
        });

        const listContainer = document.getElementById('locationClientsList');
        displaySearchResults(filtered, listContainer);
    });
}

// Check if data already exists on load
document.addEventListener('DOMContentLoaded', () => {
    loadAnalytics();
    loadMatrix();
});

// Drag and drop
uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = '#e63946';
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.style.borderColor = '#2d3748';
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = '#2d3748';

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFiles(files);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadFiles(e.target.files);
    }
});

async function uploadFiles(files) {
    console.log('Starting upload of', files.length, 'files');
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        uploadBox.innerHTML = '<p>מעלה ומעבד...</p>';

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            loadAnalytics();
            resetUploadBox();
        } else {
            alert('שגיאה בהעלאת קובץ: ' + data.error);
            resetUploadBox();
        }
    } catch (error) {
        console.error('Upload error:', error);
        alert('שגיאה בהעלאת קובץ');
        resetUploadBox();
    }
}

function resetUploadBox() {
    uploadBox.innerHTML = `
        <p>גרור ושחרר קבצים כאן</p>
        <p class="file-limit">עד 200MB לקובץ • XLSX, XLS, CSV</p>
        <button class="btn-upload" onclick="document.getElementById('fileInput').click()">בחר קבצים</button>
    `;
}

// Search functionality
let searchTimeout;
searchInput.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    const query = e.target.value.trim();

    if (query.length < 2) {
        searchResults.innerHTML = '';
        return;
    }

    searchTimeout = setTimeout(() => search(query), 300);
});

async function search(query) {
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const results = await response.json();

        displaySearchResults(results, searchResults);
    } catch (error) {
        console.error('Search error:', error);
    }
}

function displaySearchResults(results, container) {
    container.innerHTML = '';

    if (!results || results.length === 0) {
        container.innerHTML = '<p style="color: #a0aec0;">לא נמצאו תוצאות.</p>';
        return;
    }

    if (container === searchResults) {
        container.innerHTML = `<p style="color: #48bb78; margin-bottom: 16px;">נמצאו ${results.length} תוצאות</p>`;
    } else {
        container.innerHTML = `<p style="color: #48bb78; margin-bottom: 16px;">מציג ${results.length} לקוחות</p>`;
    }

    results.forEach(business => {
        const card = document.createElement('div');
        card.className = 'business-card';
        // Handle both key formats (DB vs old DF) just in case, but prioritize DB keys
        const name = business.business_name || business['Business Name'] || 'לא ידוע';
        const location = business.location || business.Location || 'לא ידוע';
        const phone = business.phone || business.Phone || 'אין';
        const anydesk = business.anydesk || business.AnyDesk || 'אין';

        card.onclick = () => openClientDetails(business); // Click to open details
        card.innerHTML = `
            <div class="card-title">${name}</div>
            <div class="card-detail">📍 <strong>עיר:</strong> ${location}</div>
            <div class="card-detail" style="color: #2a9d8f; font-weight: 600;">
                📞 <strong>טלפון:</strong> ${formatPhoneDisplay(phone)}
            </div>
            <span class="anydesk-badge">💻 AnyDesk: ${anydesk}</span>
        `;
        container.appendChild(card);
    });
}

const clientDetailsModal = document.getElementById('clientDetailsModal');
let currentViewingClient = null;

function openClientDetails(client) {
    currentViewingClient = client;
    const name = client.business_name || client['Business Name'] || 'לא ידוע';

    document.getElementById('detailBusinessName').textContent = name;

    const container = document.getElementById('dynamicDetails');
    container.innerHTML = '';

    let extraData = {};
    let hasExtra = false;

    try {
        if (client.extra_data) {
            extraData = JSON.parse(client.extra_data);
            hasExtra = true;
        }
    } catch (e) {
        console.error('Error parsing extra_data:', e);
    }

    // Fallback for legacy records or empty extra_data
    if (!hasExtra || Object.keys(extraData).length === 0) {
        extraData = {
            '📍 מיקום': client.location || client.Location || 'לא ידוע',
            '📞 טלפון': client.phone || client.Phone || 'אין',
            '💻 AnyDesk': client.anydesk || client.AnyDesk || 'אין'
        };
    }

    // Create grid items
    Object.entries(extraData).forEach(([key, value]) => {
        if (key === 'extra_data') return;

        const item = document.createElement('div');
        item.className = 'detail-item';

        const label = document.createElement('span');
        label.className = 'detail-label';
        label.textContent = key; // Column name from Excel

        const text = document.createElement('span');
        text.className = 'detail-text';
        text.textContent = value || '-';

        item.appendChild(label);
        item.appendChild(text);
        container.appendChild(item);
    });

    clientDetailsModal.style.display = 'block';
}

function closeClientDetailsModal() {
    clientDetailsModal.style.display = 'none';
}

// Load analytics
async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        const data = await response.json();

        if (data && data.total > 0) {
            // Show content
            document.getElementById('welcomeMessage').style.display = 'none';
            document.getElementById('searchSection').style.display = 'block';
            document.getElementById('analyticsSection').style.display = 'block';

            // Update metrics
            document.getElementById('totalClients').textContent = data.total;
            document.getElementById('uniqueLocations').textContent = data.unique_locations;
            document.getElementById('topLocation').textContent = data.top_location;

            // Display location cards
            const grid = document.getElementById('locationsGrid');
            grid.innerHTML = '';

            data.locations.forEach(location => {
                const card = document.createElement('div');
                card.className = 'location-card';
                card.onclick = () => openLocationDetails(location.name);
                card.innerHTML = `
                    <div class="location-name">
                        <span>📍</span>
                        <span>${location.name}</span>
                    </div>
                    <div class="location-stats">
                        <div class="stat">
                            <div class="stat-label">לקוחות</div>
                            <div class="stat-value count">${location.count}</div>
                        </div>
                        <div class="stat">
                            <div class="stat-label">אחוז</div>
                            <div class="stat-value percentage">${location.percentage}%</div>
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }
    } catch (error) {
        console.error('Analytics error:', error);
    }
}

function closeLocationDetails() {
    document.getElementById('locationDetailsSection').style.display = 'none';
    document.getElementById('analyticsSection').style.display = 'block';
    document.getElementById('searchSection').style.display = 'block';
}

// Add Client Modal Logic
const modal = document.getElementById("addClientModal");

function openAddClientModal() {
    modal.style.display = "block";
    document.getElementById("addName").focus();
}

function closeAddClientModal() {
    modal.style.display = "none";
}

// Edit Client Logic
const editClientModal = document.getElementById('editClientModal');

function openEditClientModal(client) {
    const container = document.getElementById('dynamicEditFields');
    container.innerHTML = '';
    document.getElementById('editClientId').value = client.id;

    // We want to preserve specific fields at the top if they exist
    const priorityFields = ['business_name', 'location', 'phone', 'anydesk'];
    const labels = {
        'business_name': 'שם העסק',
        'location': 'עיר',
        'phone': 'מספר טלפון',
        'anydesk': 'AnyDesk'
    };

    // Add priority fields
    priorityFields.forEach(field => {
        const val = client[field] || '';
        const group = createEditFieldGroup(field, labels[field] || field, val, true);
        container.appendChild(group);
    });

    // Add extra fields (everything else in client object that isn't ID or created_at or priority)
    Object.keys(client).forEach(key => {
        if (priorityFields.includes(key) || ['id', 'created_at', 'extra_data', 'source_file'].includes(key)) return;
        const val = client[key];
        if (typeof val === 'object' || Array.isArray(val)) return; // Skip complex objects

        const group = createEditFieldGroup(key, key, val, false);
        container.appendChild(group);
    });

    editClientModal.style.display = "block";
}

function createEditFieldGroup(key, label, value, isFixed) {
    const div = document.createElement('div');
    div.className = 'form-group';
    div.dataset.key = key;
    div.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
            <label style="margin:0;">${label}</label>
            ${!isFixed ? `<button type="button" onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: #e63946; cursor: pointer; font-size: 0.8rem;">מחק שדה</button>` : ''}
        </div>
        <input type="text" class="modal-input field-value" value="${value}" ${isFixed && key === 'business_name' ? 'required' : ''}>
    `;
    return div;
}

function addNewFieldRow() {
    const nameInput = document.getElementById('newFieldName');
    const valueInput = document.getElementById('newFieldValue');
    const name = nameInput.value.trim();
    const value = valueInput.value.trim();

    if (!name) return alert("אנא הזן שם לשדה החדש");

    // Check if key already exists
    const container = document.getElementById('dynamicEditFields');
    const existing = Array.from(container.querySelectorAll('.form-group')).find(g => g.dataset.key === name);
    if (existing) return alert("שדה בשם זה כבר קיים");

    const group = createEditFieldGroup(name, name, value, false);
    container.appendChild(group);

    // Clear inputs and add a nice visual feedback
    nameInput.value = '';
    valueInput.value = '';

    // Scroll to the new field
    group.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Highlight the new field briefly
    group.style.animation = 'fadeIn 0.3s ease-in';
}

function openEditClientModalFromDetails() {
    if (currentViewingClient) {
        closeClientDetailsModal();
        openEditClientModal(currentViewingClient);
    }
}

function closeEditClientModal() {
    editClientModal.style.display = "none";
}

async function submitEditClient(event) {
    event.preventDefault();
    const id = document.getElementById('editClientId').value;

    // Collect all fields
    const clientData = {};
    const fieldGroups = document.querySelectorAll('#dynamicEditFields .form-group');
    fieldGroups.forEach(group => {
        const key = group.dataset.key;
        const val = group.querySelector('.field-value').value;
        clientData[key] = val;
    });

    const btn = event.target.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = 'שומר...';
    btn.disabled = true;

    try {
        const response = await fetch(`/api/clients/update/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(clientData)
        });

        const data = await response.json();
        if (data.success) {
            closeEditClientModal();
            loadAnalytics();
            loadMatrix();
            alert("הפרטים עודכנו בהצלחה!");
        } else {
            alert('שגיאה בעדכון הלקוח: ' + (data.error || 'שגיאה לא ידועה'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('שגיאה בעדכון הלקוח');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}


// Close if click outside
window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
    if (event.target == clientDetailsModal) {
        clientDetailsModal.style.display = "none";
    }
    if (event.target == editClientModal) {
        editClientModal.style.display = "none";
    }
}


async function submitAddClient(event) {
    event.preventDefault();

    const clientData = {
        business_name: document.getElementById("addName").value,
        location: document.getElementById("addLocation").value,
        phone: document.getElementById("addPhone").value,
        anydesk: document.getElementById("addAnyDesk").value
    };

    // Disable button to prevent double submit
    const btn = event.target.querySelector('button');
    const originalText = btn.textContent;
    btn.textContent = 'שומר...';
    btn.disabled = true;

    try {
        const response = await fetch('/api/clients/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(clientData)
        });

        const data = await response.json();

        if (data.success) {
            // Reset form
            document.getElementById("addClientForm").reset();
            closeAddClientModal();

            // Reload data
            loadAnalytics();
            alert("הלקוח נוסף בהצלחה!");
        } else {
            alert('שגיאה בהוספת הלקוח: ' + (data.error || 'שגיאה לא ידועה'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('שגיאה בהוספת הלקוח');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

// Location Details Drill-down
async function openLocationDetails(location) {
    document.getElementById('analyticsSection').style.display = 'none';
    document.getElementById('searchSection').style.display = 'none';
    const detailsSection = document.getElementById('locationDetailsSection');
    detailsSection.style.display = 'block';

    document.getElementById('locationDetailsTitle').textContent = `לקוחות ב-${location}`;
    const listContainer = document.getElementById('locationClientsList');
    listContainer.innerHTML = '<p>טוען...</p>';

    // Reset search
    if (citySearchInput) citySearchInput.value = '';

    try {
        const response = await fetch(`/api/clients?location=${encodeURIComponent(location)}`);
        const clients = await response.json();

        currentCityClients = clients; // Store for filtering
        displaySearchResults(clients, listContainer);

        // Render city data matrix
        renderCityMatrix(clients);

    } catch (error) {
        console.error('Error fetching clients:', error);
        listContainer.innerHTML = '<p style="color:red">שגיאה בטעינת לקוחות.</p>';
    }


}

function renderCityMatrix(clients) {
    const tableBody = document.getElementById('cityTableBody');
    const tableHeader = document.getElementById('cityTableHeader');

    if (!clients || clients.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="100%" style="text-align:center; padding: 20px;">אין נתונים להצגה</td></tr>';
        tableHeader.innerHTML = '';
        return;
    }

    // Collect ALL unique columns from all records
    const allColumns = new Set();

    // Priority columns that should appear first
    const priorityCols = ['business_name', 'location', 'phone', 'anydesk', 'source_file'];

    // Add all columns from all rows
    clients.forEach(r => {
        Object.keys(r).forEach(k => {
            if (k !== 'extra_data' && k !== 'id' && k !== 'created_at') {
                allColumns.add(k);
            }
        });
    });

    // Create ordered array: priority columns first, then others alphabetically
    const colArray = [];
    priorityCols.forEach(col => {
        if (allColumns.has(col)) {
            colArray.push(col);
            allColumns.delete(col);
        }
    });

    // Add remaining columns alphabetically
    const remainingCols = Array.from(allColumns).sort((a, b) => a.localeCompare(b, 'he'));
    colArray.push(...remainingCols);

    const headerMap = {
        'business_name': 'שם העסק',
        'location': 'עיר',
        'phone': 'מספר טלפון',
        'anydesk': 'AnyDesk',
        'source_file': 'קובץ מקור'
    };

    // Render Header
    tableHeader.innerHTML = '';
    colArray.forEach(col => {
        const th = document.createElement('th');
        th.textContent = headerMap[col] || col;
        th.title = col; // Tooltip
        tableHeader.appendChild(th);
    });

    // Render Body
    tableBody.innerHTML = '';
    clients.forEach(r => {
        const tr = document.createElement('tr');
        tr.onclick = () => openClientDetails(r);
        tr.style.cursor = 'pointer';

        colArray.forEach(col => {
            const td = document.createElement('td');
            let value = r[col];

            // Format phone numbers
            if (col === 'phone' || col.toLowerCase().includes('טלפון') || col.toLowerCase().includes('phone')) {
                td.textContent = formatPhoneDisplay(value) || '-';
            } else {
                td.textContent = (value !== null && value !== undefined && value !== '') ? value : '-';
            }

            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });

    console.log(`City matrix rendered with ${colArray.length} columns from ${clients.length} records`);
}

// Data Matrix Logic
let currentPage = 1;
const limit = 100;  // Increased to show more data per page

async function loadMatrix() {
    const tableBody = document.getElementById('tableBody');
    // Using innerHTML with a single row for loading message
    tableBody.innerHTML = '<tr><td colspan="100%" style="text-align:center; padding: 20px;">טוען נתונים...</td></tr>';

    try {
        const response = await fetch(`/api/clients/all?page=${currentPage}&limit=${limit}`);
        const data = await response.json();

        renderMatrix(data.data);

        // Update pagination
        const totalPages = Math.ceil(data.total / data.per_page) || 1;
        document.getElementById('pageInfo').textContent = `עמוד ${data.page} מתוך ${totalPages}`;
        document.getElementById('prevPage').disabled = data.page <= 1;
        document.getElementById('nextPage').disabled = data.page >= totalPages;

        // Show section if hidden
        document.getElementById('matrixSection').style.display = 'block';
    } catch (e) {
        console.error('Matrix error:', e);
        tableBody.innerHTML = '<tr><td colspan="100%" style="text-align:center; color: #e63946; padding: 20px;">שגיאה בטעינת נתונים</td></tr>';
    }
}

function renderMatrix(rows) {
    const tableBody = document.getElementById('tableBody');
    const tableHeader = document.getElementById('tableHeader');

    if (!rows || rows.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="100%" style="text-align:center; padding: 20px;">אין נתונים להצגה</td></tr>';
        return;
    }

    // 1. Collect ALL unique columns from all records
    const allColumns = new Set();

    // Priority columns that should appear first
    const priorityCols = ['business_name', 'location', 'phone', 'anydesk', 'source_file'];

    // First, add all columns from all rows to get complete picture
    rows.forEach(r => {
        Object.keys(r).forEach(k => {
            // Skip internal fields
            if (k !== 'extra_data' && k !== 'id' && k !== 'created_at') {
                allColumns.add(k);
            }
        });
    });

    // Create ordered array: priority columns first, then others alphabetically
    const colArray = [];
    priorityCols.forEach(col => {
        if (allColumns.has(col)) {
            colArray.push(col);
            allColumns.delete(col);
        }
    });

    // Add remaining columns alphabetically
    const remainingCols = Array.from(allColumns).sort((a, b) => a.localeCompare(b, 'he'));
    colArray.push(...remainingCols);

    // Hebrew header mappings
    const headerMap = {
        'business_name': 'שם העסק',
        'location': 'עיר',
        'phone': 'מספר טלפון',
        'anydesk': 'AnyDesk',
        'source_file': 'קובץ מקור'
    };

    // 2. Render Header
    tableHeader.innerHTML = '';
    colArray.forEach(col => {
        const th = document.createElement('th');
        th.textContent = headerMap[col] || col;
        th.title = col; // Tooltip showing original column name
        tableHeader.appendChild(th);
    });

    // 3. Render Body
    tableBody.innerHTML = '';
    rows.forEach(r => {
        const tr = document.createElement('tr');
        tr.onclick = () => openClientDetails(r); // Click to open modal
        tr.style.cursor = 'pointer';

        colArray.forEach(col => {
            const td = document.createElement('td');
            let value = r[col];

            // Format phone numbers
            if (col === 'phone' || col.toLowerCase().includes('טלפון') || col.toLowerCase().includes('phone')) {
                td.textContent = formatPhoneDisplay(value) || '-';
            } else {
                // Handle empty values
                td.textContent = (value !== null && value !== undefined && value !== '') ? value : '-';
            }

            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    });

    // Add info message about total columns
    console.log(`Matrix rendered with ${colArray.length} columns from ${rows.length} records`);
}

function changePage(delta) {
    currentPage += delta;
    if (currentPage < 1) currentPage = 1;
    loadMatrix();
}









