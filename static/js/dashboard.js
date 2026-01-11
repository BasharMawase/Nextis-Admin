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
    loadUploadedFiles();
    loadContactMessages();
});

// Load uploaded files list
async function loadUploadedFiles() {
    try {
        const response = await fetch('/api/files/list');
        const data = await response.json();

        const container = document.getElementById('filesContainer');
        if (!container) return;

        if (!data.files || data.files.length === 0) {
            container.innerHTML = '<p style="color: #718096; font-size: 12px; font-style: italic;">אין קבצים</p>';
            return;
        }

        container.innerHTML = '';
        data.files.forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.style.cssText = `
                background: rgba(30, 35, 48, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            `;

            const fileInfo = document.createElement('div');
            fileInfo.style.flex = '1';
            fileInfo.innerHTML = `
                <div style="font-size: 12px; color: #e2e8f0; font-weight: 500; margin-bottom: 4px;">${file.name}</div>
                <div style="font-size: 10px; color: #a0aec0;">${formatFileSize(file.size)} • ${file.modified}</div>
            `;

            const deleteBtn = document.createElement('button');
            deleteBtn.innerHTML = '🗑️';
            deleteBtn.style.cssText = `
                background: rgba(220, 38, 38, 0.1);
                border: 1px solid rgba(220, 38, 38, 0.3);
                color: #dc2626;
                padding: 6px 10px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.2s;
            `;
            deleteBtn.onclick = () => deleteUploadedFile(file.name);
            deleteBtn.onmouseover = () => {
                deleteBtn.style.background = 'rgba(220, 38, 38, 0.2)';
            };
            deleteBtn.onmouseout = () => {
                deleteBtn.style.background = 'rgba(220, 38, 38, 0.1)';
            };

            fileItem.appendChild(fileInfo);
            fileItem.appendChild(deleteBtn);
            container.appendChild(fileItem);
        });
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
}

async function deleteUploadedFile(filename) {
    if (!confirm(`האם למחוק את הקובץ "${filename}"?`)) return;

    try {
        const response = await fetch('/api/files/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });

        const data = await response.json();
        if (data.success) {
            loadUploadedFiles();
            loadAnalytics();  // Refresh stats
            loadMatrix();     // Refresh table/matrix
            alert('הקובץ והנתונים נמחקו בהצלחה');
        } else {
            alert('שגיאה: ' + (data.error || 'לא ניתן למחוק'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('שגיאה במחיקת הקובץ');
    }
}

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
            loadUploadedFiles();
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
        // const anydesk = business.anydesk || business.AnyDesk || 'אין'; 

        // Parse extra_data to find specific Book_4 fields
        let extraFieldsHtml = '';
        let extraDataObj = {};
        let extraCount = 0;

        if (business.extra_data) {
            try {
                extraDataObj = JSON.parse(business.extra_data);
                extraCount = Object.keys(extraDataObj).length;
            } catch (e) { }
        }

        const targetFields = [
            { key: 'בעלים', label: '👤 בעלים' },
            { key: 'אופן תשלום', label: '💳 תשלום' },
            { key: "מס' מורשה", label: '🔢 מורשה' },
            { key: "מס' מסוף", label: '📠 מסוף' },
            { key: 'ציוד', label: '🛠️ ציוד' },
            { key: 'תראיך התחלה', label: '📅 התחלה' },
            { key: 'תאריך התחלה', label: '📅 התחלה' }
        ];

        targetFields.forEach(field => {
            if (extraDataObj[field.key]) {
                extraFieldsHtml += `
                    <div class="card-sub-detail">
                        <span class="sub-label">${field.label}:</span>
                        <span class="sub-value">${extraDataObj[field.key]}</span>
                    </div>
                 `;
            }
        });

        card.onclick = () => openClientDetails(business);
        card.innerHTML = `
            <div class="card-title">${name}</div>
            <div class="card-detail">📍 <strong>עיר:</strong> ${location}</div>
            <div class="card-detail" style="color: #2a9d8f; font-weight: 600;">
                📞 <strong>טלפון:</strong> ${formatPhoneDisplay(phone)}
            </div>
            
            ${extraFieldsHtml ? `<div class="card-extra-section">${extraFieldsHtml}</div>` : ''}

            ${extraCount > 0 ? `<div class="data-badge">+${extraCount} פרטים נוספים</div>` : ''}
        `;
        container.appendChild(card);
    });
}

const clientDetailsModal = document.getElementById('clientDetailsModal');
let currentViewingClient = null;

async function openClientDetails(client) {
    currentViewingClient = client;
    const clientDetailsModal = document.getElementById('clientDetailsModal');

    // Setup Modal Structure if not already upgraded
    const modalContent = clientDetailsModal.querySelector('.modal-content');
    // Force structure update to ensure buttons are present
    modalContent.innerHTML = `
        <div class="modal-header-custom">
            <span class="close" onclick="closeClientDetailsModal()">&times;</span>
            <h2 id="detailBusinessName" style="font-size: 2rem; margin-bottom: 8px; color: white;"></h2>
            <div style="display: flex; gap: 10px;">
                <button class="btn-primary" onclick="openEditClientModalFromDetails()" style="width: auto; padding: 8px 16px; font-size: 0.9rem;">✎ עריכה</button>
                <button class="btn-primary" onclick="printClientDetails()" style="width: auto; padding: 8px 16px; font-size: 0.9rem; background: #059669;">🖨️ הדפסה</button>
                <button class="btn-danger" onclick="confirmDeleteClient()" style="width: auto; padding: 8px 16px; font-size: 0.9rem;">🗑️ מחיקה</button>
            </div>
        </div>
        <div class="modal-body-custom">
            <div id="coreInfoGrid" class="core-info-grid"></div>
            
            <div id="businessDetailsSection" style="display:none;">
                <h3 style="font-size: 1.1rem; color: #a0aec0; margin: 24px 0 16px 0; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">פרטי עסק ומסוף</h3>
                <div id="businessDetailsGrid" class="core-info-grid" style="grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));"></div>
            </div>

            <h3 style="font-size: 1.1rem; color: #a0aec0; margin: 24px 0 16px 0; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">מידע נוסף</h3>
            <div id="extendedDetailsGrid" class="extended-details-grid"></div>
        </div>
    `;

    // Function to handle printing via hidden iframe (Seamless)
    window.printClientDetails = function () {
        if (!client) return;

        // Create hidden iframe
        let printFrame = document.getElementById('printFrame');
        if (!printFrame) {
            printFrame = document.createElement('iframe');
            printFrame.id = 'printFrame';
            printFrame.style.position = 'fixed';
            printFrame.style.right = '0';
            printFrame.style.bottom = '0';
            printFrame.style.width = '0';
            printFrame.style.height = '0';
            printFrame.style.border = '0';
            document.body.appendChild(printFrame);
        }

        const date = new Date().toLocaleDateString('he-IL');
        const coreInfo = document.getElementById('coreInfoGrid').innerHTML;
        const businessInfo = document.getElementById('businessDetailsGrid').innerHTML;
        const extendedInfo = document.getElementById('extendedDetailsGrid').innerHTML;
        const businessInfoDisplay = document.getElementById('businessDetailsSection').style.display !== 'none' ? businessInfo : '';

        const htmlContent = `
            <!DOCTYPE html>
            <html lang="he" dir="rtl">
            <head>
                <title>הדפסת פרטי לקוח - ${client.business_name || 'לקוח'}</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        color: #000;
                        background: #fff;
                        padding: 20px 40px; /* Adjusted padding for A4 */
                        direction: rtl;
                    }
                    .header {
                        text-align: center;
                        border-bottom: 2px solid #000;
                        padding-bottom: 20px;
                        margin-bottom: 30px;
                    }
                    h1 { margin: 0; font-size: 24pt; }
                    .meta { color: #666; font-size: 10pt; margin-top: 10px; }
                    
                    .section { margin-bottom: 25px; page-break-inside: avoid; }
                    .section-title {
                        font-size: 14pt;
                        font-weight: bold;
                        border-bottom: 1px solid #ccc;
                        padding-bottom: 5px;
                        margin-bottom: 15px;
                        display: flex;
                        align-items: center;
                    }
                    
                    .grid {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr); /* 2 columns for A4 */
                        gap: 15px;
                    }
                    
                    .item {
                        border: 1px solid #eee;
                        padding: 10px;
                        border-radius: 4px;
                        background-color: #f9f9f9; /* Subtle background for clarity */
                    }
                    .label { color: #666; font-size: 9pt; margin-bottom: 3px; }
                    .value { font-weight: 600; font-size: 11pt; }
                    
                    /* Mapping styles for existing HTML content */
                    .core-info-item, .detail-card {
                        border: 1px solid #ddd;
                        padding: 10px;
                        border-radius: 4px;
                        background: #f9f9f9;
                    }
                    .core-text h4, .detail-card-label {
                        margin: 0 0 5px 0;
                        font-size: 9pt;
                        color: #555;
                    }
                    .core-text p, .detail-card-value {
                        margin: 0;
                        font-weight: bold;
                        font-size: 11pt;
                    }
                    .core-icon { display: none; } /* Hide icons for print */
                    
                    @media print {
                        body { padding: 0.5cm; } /* Minimal padding for print */
                        .no-print { display: none; }
                        .item, .section { break-inside: avoid; }
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>${client.business_name || 'פרטי לקוח'}</h1>
                    <div class="meta">הודפס בתאריך: ${date}</div>
                </div>

                <div class="section">
                    <div class="section-title">פרטים ראשיים</div>
                    <div class="grid">
                        ${coreInfo}
                    </div>
                </div>

                ${businessInfoDisplay ? `
                <div class="section">
                    <div class="section-title">פרטי עסק ומסוף</div>
                    <div class="grid">
                        ${businessInfoDisplay}
                    </div>
                </div>` : ''}

                <div class="section">
                    <div class="section-title">מידע נוסף</div>
                    <div class="grid">
                        ${extendedInfo}
                    </div>
                </div>

                <div style="margin-top: 50px; text-align: center; font-size: 9pt; color: #999; border-top: 1px solid #eee; padding-top: 10px;">
                    Nextis Management System
                </div>
            </body>
            </html>
        `;

        // Write content to iframe
        const doc = printFrame.contentWindow.document;
        doc.open();
        doc.write(htmlContent);
        doc.close();

        // Print after image loading (if any) or slight delay
        printFrame.contentWindow.onload = function () {
            setTimeout(() => {
                printFrame.contentWindow.focus();
                printFrame.contentWindow.print();
            }, 500);
        };

        // Fallback if onload doesn't trigger (e.g. no external resources)
        setTimeout(() => {
            if (printFrame.contentWindow.document.readyState === 'complete') {
                printFrame.contentWindow.focus();
                printFrame.contentWindow.print();
            }
        }, 1000);
    };

    const name = client.business_name || client['Business Name'] || 'לא ידוע';
    document.getElementById('detailBusinessName').textContent = name;

    const coreContainer = document.getElementById('coreInfoGrid');
    const extendedContainer = document.getElementById('extendedDetailsGrid');

    // Loading State
    coreContainer.innerHTML = '<div style="color:white">טוען...</div>';
    extendedContainer.innerHTML = '';

    clientDetailsModal.style.display = 'block';

    try {
        // Fetch aggregated data
        const response = await fetch(`/api/clients/details/${client.id}`);
        const data = await response.json();

        if (data.error) {
            coreContainer.innerHTML = `<p style="color: red;">שגיאה: ${data.error}</p>`;
            return;
        }

        coreContainer.innerHTML = '';
        extendedContainer.innerHTML = '';

        // Prioritize and Categorize
        const coreFields = ['location', 'phone', 'anydesk', 'source_file'];
        const iconMap = {
            'location': '📍',
            'phone': '📞',
            'anydesk': '💻',
            'source_file': '📁'
        };
        const labelMap = {
            'location': 'מיקום',
            'phone': 'טלפון',
            'anydesk': 'AnyDesk',
            'source_file': 'מקור הנתונים'
        };

        // 1. Render Core Info
        coreFields.forEach(key => {
            const item = data.find(i => i.Field === key);
            let value = item ? item.Value : (client[key] || '-');

            if (key === 'phone') value = formatPhoneDisplay(value);

            const div = document.createElement('div');
            div.className = 'core-info-item';
            div.innerHTML = `
                <div class="core-icon">${iconMap[key]}</div>
                <div class="core-text">
                    <h4>${labelMap[key]}</h4>
                    <p>${value}</p>
                </div>
            `;
            coreContainer.appendChild(div);
        });

        // 2. Render Extended Info
        let extendedCount = 0;
        data.forEach(item => {
            if (coreFields.includes(item.Field) || ['id', 'created_at', 'business_name', 'extra_data'].includes(item.Field)) return;
            if (!item.Value && item.Value !== 0) return; // Skip empty

            const div = document.createElement('div');
            div.className = 'detail-card';
            div.innerHTML = `
                <span class="detail-card-label">${item.Field}</span>
                <div class="detail-card-value">${item.Value}</div>
            `;
            extendedContainer.appendChild(div);
            extendedCount++;
        });

        if (extendedCount === 0) {
            extendedContainer.innerHTML = '<p style="color: #4a5568; font-style: italic;">אין מידע נוסף להצגה</p>';
        }

    } catch (error) {
        console.error('Error fetching client details:', error);
        coreContainer.innerHTML = '<p style="color: red;">שגיאה בטעינת הנתונים</p>';
    }
}

function closeClientDetailsModal() {
    clientDetailsModal.style.display = 'none';
}

function confirmDeleteClient() {
    if (!currentViewingClient) return;

    const clientName = currentViewingClient.business_name || 'לקוח זה';
    const confirmed = confirm(`האם אתה בטוח שברצונך למחוק את ${clientName}?\nפעולה זו לא ניתנת לביטול.`);

    if (confirmed) {
        deleteClient(currentViewingClient.id);
    }
}

async function deleteClient(clientId) {
    try {
        const response = await fetch(`/api/clients/delete/${clientId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (data.success) {
            closeClientDetailsModal();
            loadAnalytics();
            loadMatrix();
            alert('הלקוח נמחק בהצלחה!');
        } else {
            alert('שגיאה במחיקת הלקוח: ' + (data.error || 'שגיאה לא ידועה'));
        }
    } catch (error) {
        console.error('Error:', error);
        alert('שגיאה במחיקת הלקוח');
    }
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

function toggleMatrix() {
    const container = document.getElementById('matrixContainer');
    if (container.style.display === 'none') {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

async function loadContactMessages() {
    const list = document.getElementById('messagesList');
    if (!list) return;

    try {
        const res = await fetch('/api/contact');
        const messages = await res.json();

        list.innerHTML = '';
        if (messages.length === 0) {
            list.innerHTML = '<p style="color: #a0aec0; font-style: italic;">אין הודעות חדשות</p>';
            return;
        }

        messages.forEach(msg => {
            const div = document.createElement('div');
            div.id = `message-${msg.id}`;
            div.style.cssText = 'background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1); position: relative; transition: all 0.3s ease;';
            div.innerHTML = `
                <button onclick="markMessageAsRead(${msg.id})" 
                    style="position: absolute; top: 10px; left: 10px; background: rgba(16, 185, 129, 0.2); border: 1px solid rgba(16, 185, 129, 0.5); color: #10b981; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s;"
                    onmouseover="this.style.background='rgba(16, 185, 129, 0.3)'"
                    onmouseout="this.style.background='rgba(16, 185, 129, 0.2)'">
                    ✓ סמן כנקרא
                </button>
                <div style="display:flex; justify-content:space-between; margin-bottom:5px; padding-left: 120px;">
                    <strong style="color: #e63946;">${msg.name}</strong>
                    <span style="color: #a0aec0; font-size: 0.8rem;">${msg.created_at}</span>
                </div>
                <div style="margin-bottom: 5px; color: #a0aec0; font-size: 0.9rem;">📞 ${msg.phone}</div>
                <div style="color: #e2e8f0;">${msg.message || ''}</div>
            `;
            list.appendChild(div);
        });

    } catch (e) {
        console.error(e);
        list.innerHTML = '<p style="color: red;">שגיאה בטעינת הודעות</p>';
    }
}

async function markMessageAsRead(messageId) {
    const messageDiv = document.getElementById(`message-${messageId}`);
    if (!messageDiv) return;

    try {
        const res = await fetch(`/api/contact/${messageId}`, {
            method: 'DELETE'
        });

        if (res.ok) {
            // Animate out
            messageDiv.style.opacity = '0';
            messageDiv.style.transform = 'translateX(20px)';

            setTimeout(() => {
                messageDiv.remove();

                // Check if no messages left
                const list = document.getElementById('messagesList');
                if (list && list.children.length === 0) {
                    list.innerHTML = '<p style="color: #a0aec0; font-style: italic;">אין הודעות חדשות</p>';
                }
            }, 300);
        } else {
            alert('שגיאה במחיקת ההודעה');
        }
    } catch (e) {
        console.error(e);
        alert('שגיאה בתקשורת');
    }
}