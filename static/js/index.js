let groupCounter = 0;
const testGroups = [];

// Get the tbody element
const tbody = document.getElementById('testGroupBody');

// Function to add a new test group
function addTestGroup() {
    groupCounter++;
    const groupId = groupCounter;

    // Sample data - you can replace this with actual form data
    const newGroup = {
        id: groupId,
        client: `Client ${groupId}`,
        server: `Server ${groupId}`,
        switch: `Switch ${groupId}`,
        cable: `CAT6 Cable ${groupId}`,
        status: 'Pending'
    };

    testGroups.push(newGroup);

    // Remove empty row if it exists
    const emptyRow = document.getElementById('emptyRow');
    if (emptyRow) {
        emptyRow.remove();
    }

    // Create new row
    const newRow = document.createElement('tr');
    newRow.id = `group_${groupId}`;
    newRow.innerHTML = `
        <td>${groupId}</td>
        <td>
            <input type="text" class="form-control form-control-sm client-input" 
                   value="${newGroup.client}" data-group-id="${groupId}" 
                   placeholder="Enter client name">
        </td>
        <td>
            <input type="text" class="form-control form-control-sm server-input" 
                   value="${newGroup.server}" data-group-id="${groupId}" 
                   placeholder="Enter server name">
        </td>
        <td>
            <select class="form-select form-select-sm switch-select" data-group-id="${groupId}">
                <option value="Switch A">Switch A</option>
                <option value="Switch B">Switch B</option>
                <option value="Switch C">Switch C</option>
                <option value="Switch D" selected>${newGroup.switch}</option>
            </select>
        </td>
        <td>
            <select class="form-select form-select-sm cable-select" data-group-id="${groupId}">
                <option value="CAT5e">CAT5e</option>
                <option value="CAT6" selected>CAT6</option>
                <option value="CAT6a">CAT6a</option>
                <option value="CAT7">CAT7</option>
            </select>
        </td>
        <td>
            <span class="badge bg-warning status-badge" data-group-id="${groupId}">${newGroup.status}</span>
        </td>
        <td>
            <button class="btn btn-sm btn-success me-1 run-test-btn" data-group-id="${groupId}">
                <i class="bi bi-play-fill"></i> Run Test
            </button>
            <button class="btn btn-sm btn-danger delete-btn" data-group-id="${groupId}">
                <i class="bi bi-trash"></i> Delete
            </button>
        </td>
    `;

    tbody.appendChild(newRow);
    updateRowNumbers();

    // Add event listeners for the new row's buttons
    const runTestBtn = newRow.querySelector('.run-test-btn');
    const deleteBtn = newRow.querySelector('.delete-btn');

    runTestBtn.addEventListener('click', () => runTest(groupId));
    deleteBtn.addEventListener('click', () => deleteTestGroup(groupId));

    // Add change listeners for inputs and selects
    const clientInput = newRow.querySelector('.client-input');
    const serverInput = newRow.querySelector('.server-input');
    const switchSelect = newRow.querySelector('.switch-select');
    const cableSelect = newRow.querySelector('.cable-select');

    clientInput.addEventListener('change', (e) => updateGroupData(groupId, 'client', e.target.value));
    serverInput.addEventListener('change', (e) => updateGroupData(groupId, 'server', e.target.value));
    switchSelect.addEventListener('change', (e) => updateGroupData(groupId, 'switch', e.target.value));
    cableSelect.addEventListener('change', (e) => updateGroupData(groupId, 'cable', e.target.value));
}

// Function to delete a test group
function deleteTestGroup(groupId) {
    if (confirm('Are you sure you want to delete this test group?')) {
        // Remove from array
        const index = testGroups.findIndex(group => group.id === groupId);
        if (index !== -1) {
            testGroups.splice(index, 1);
        }

        // Remove row from table
        const row = document.getElementById(`group_${groupId}`);
        if (row) {
            row.remove();
        }

        // If no groups left, show empty row message
        if (testGroups.length === 0) {
            const emptyRow = document.createElement('tr');
            emptyRow.id = 'emptyRow';
            emptyRow.innerHTML = '<td colspan="7" class="text-center text-muted py-4">暂无测试组，点击 "Add a new group" 添加新的测试组合</td>';
            tbody.appendChild(emptyRow);
        }

        updateRowNumbers();
    }
}

// Function to update group data
function updateGroupData(groupId, field, value) {
    const group = testGroups.find(g => g.id === groupId);
    if (group) {
        group[field] = value;
        console.log(`Group ${groupId} updated: ${field} = ${value}`);
    }
}

// Function to run test
function runTest(groupId) {
    const group = testGroups.find(g => g.id === groupId);
    if (group) {
        console.log(`Running test for group ${groupId}:`, group);

        // Update status to "Running"
        const statusSpan = document.querySelector(`.status-badge[data-group-id="${groupId}"]`);
        if (statusSpan) {
            statusSpan.className = 'badge bg-info status-badge';
            statusSpan.textContent = 'Running';
        }

        // Simulate test execution
        setTimeout(() => {
            if (statusSpan) {
                statusSpan.className = 'badge bg-success status-badge';
                statusSpan.textContent = 'Passed';
                group.status = 'Passed';
            }
        }, 2000);
    }
}

// Function to update row numbers
function updateRowNumbers() {
    const rows = tbody.querySelectorAll('tr:not(#emptyRow)');
    rows.forEach((row, index) => {
        const firstCell = row.querySelector('td:first-child');
        if (firstCell) {
            firstCell.textContent = index + 1;
        }
    });
}

// Add event listener to the "Add a new group" button
document.getElementById('addNewGroupBtn').addEventListener('click', addTestGroup);

// Optional: Add some initial demo data
// Uncomment the line below to add a few demo groups on page load
// setTimeout(() => { addTestGroup(); addTestGroup(); }, 500);