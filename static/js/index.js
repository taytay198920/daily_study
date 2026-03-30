// 全局变量
let optionsData = null;
let testGroups = [];
let isLoading = false;

// 页面加载时获取下拉框选项和已有测试组
document.addEventListener('DOMContentLoaded', async function() {
    await loadOptions();
    await loadTestGroups();

    // 绑定添加按钮事件
    document.getElementById('addNewGroupBtn').addEventListener('click', addNewGroup);
});

// 加载下拉框选项数据
async function loadOptions() {
    try {
        const response = await fetch('/api/options');
        const result = await response.json();

        if (result.success) {
            optionsData = result.data;
        } else {
            console.error('Failed to load options:', result.error);
        }
    } catch (error) {
        console.error('Error loading options:', error);
    }
}

// 加载已有的测试组
async function loadTestGroups() {
    try {
        const response = await fetch('/api/test_groups');
        const result = await response.json();

        if (result.success) {
            // 按创建时间升序排序
            testGroups = result.data.sort((a, b) => {
                return new Date(a.created_at) - new Date(b.created_at);
            });
            renderTestGroups();
            updateGroupCount();
        } else {
            console.error('Failed to load test groups:', result.error);
        }
    } catch (error) {
        console.error('Error loading test groups:', error);
    }
}

// 渲染所有测试组（只在初始加载时调用）
function renderTestGroups() {
    const tbody = document.getElementById('testGroupBody');
    tbody.innerHTML = '';

    if (testGroups.length === 0) {
        // 显示空状态
        const emptyRow = document.createElement('tr');
        emptyRow.id = 'emptyRow';
        emptyRow.innerHTML = '<td colspan="8" class="text-center text-muted py-4"><i class="bi bi-inbox"></i> There is no test group, click the "New group" button to add a new test group</td>';
        tbody.appendChild(emptyRow);
        return;
    }

    // 渲染每个测试组
    testGroups.forEach((group, index) => {
        const row = createGroupRow(group, index + 1);
        tbody.appendChild(row);
    });
}

// 创建测试组行（返回 DOM 元素）
function createGroupRow(group, rowNumber) {
    const tr = document.createElement('tr');
    tr.id = `group_${group.id}`;
    tr.setAttribute('data-group-id', group.id);

    // 生成唯一的模态框 ID
    const modalId = `configModal_${group.id}`;
    const modalLabelId = `${modalId}Label`;

    // 获取当前选中的值
    const selectedClientId = group.client_id || '';
    const selectedServerId = group.server_id || '';
    const selectedSwitchId = group.switch_id || '';
    const selectedCableId = group.cable_id || '';

    // 生成下拉框选项HTML
    const clientOptions = generateSelectOptions(optionsData.clients, selectedClientId, 'id', 'unit_no');
    const serverOptions = generateSelectOptions(optionsData.servers, selectedServerId, 'id', 'unit_no');
    const switchOptions = generateSelectOptions(optionsData.switches, selectedSwitchId, 'id', 'model');
    const cableOptions = generateSelectOptions(optionsData.cables, selectedCableId, 'id', 'description');

    // 状态徽章样式
    let statusClass = 'bg-secondary';
    if (group.status === 'pending') statusClass = 'bg-warning';
    else if (group.status === 'running') statusClass = 'bg-info';
    else if (group.status === 'passed') statusClass = 'bg-success';
    else if (group.status === 'failed') statusClass = 'bg-danger';

    tr.innerHTML = `
        <td class="row-number">${rowNumber}</td>
        <td>
            <select class="form-select form-select-sm client-select" data-group-id="${group.id}" data-field="client_id">
                <option value="" selected disabled>--- select ---</option>
                ${clientOptions}
            </select>
        </td>
        <td>
            <select class="form-select form-select-sm server-select" data-group-id="${group.id}" data-field="server_id">
                <option value="" selected disabled>--- select ---</option>
                ${serverOptions}
            </select>
        </td>
        <td>
            <select class="form-select form-select-sm switch-select" data-group-id="${group.id}" data-field="switch_id">
                <option value="" selected disabled>--- select ---</option>
                ${switchOptions}
            </select>
        </td>
        <td>
            <select class="form-select form-select-sm cable-select" data-group-id="${group.id}" data-field="cable_id">
                <option value="" selected disabled>--- select ---</option>
                ${cableOptions}
            </select>
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#${modalId}">
                Config
            </button>
            <div class="modal fade" id="${modalId}" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1"
                aria-labelledby="${modalLabelId}" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h1 class="modal-title fs-5" id="${modalLabelId}">
                                Test Configuration - Group ${rowNumber}
                            </h1>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <!-- 1. Basic Test -->
                            <div class="test-option-group">
                                <div class="group-title">Basic Test</div>
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" value="ping" id="pingTest_${group.id}">
                                    <label class="form-check-label" for="pingTest_${group.id}">
                                        Ping Test
                                    </label>
                                </div>
                            </div>
            
                            <!-- 2. PowerManagement 带全选/取消全选 -->
                            <div class="test-option-group">
                                <div class="group-title">
                                    PowerManagement
                                    <div class="group-actions">
                                        <button type="button" class="btn btn-outline-primary btn-sm select-all-power">Select All</button>
                                        <button type="button" class="btn btn-outline-secondary btn-sm deselect-all-power">Unselect All</button>
                                    </div>
                                </div>
                                <div class="power-group">
                                    <div class="form-check">
                                        <input class="form-check-input power-checkbox" type="checkbox" value="restart"
                                            id="restartTest_${group.id}">
                                        <label class="form-check-label" for="restartTest_${group.id}">
                                            Restart Test
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input power-checkbox" type="checkbox" value="shutdown"
                                            id="shutdownTest_${group.id}">
                                        <label class="form-check-label" for="shutdownTest_${group.id}">
                                            Shutdown Test
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input power-checkbox" type="checkbox" value="sleep" 
                                            id="sleepTest_${group.id}">
                                        <label class="form-check-label" for="sleepTest_${group.id}">
                                            Sleep Test
                                        </label>
                                    </div>
                                </div>
                            </div>
            
                            <!-- 3. Iperf Test -->
                            <div class="test-option-group">
                                <div class="group-title">Iperf Test</div>
            
                                <!-- MTU=1500 区块 -->
                                <div class="mtu-section">
                                    <div class="mtu-header">
                                        <span class="mtu-title">MTU = 1500</span>
                                        <div class="group-actions">
                                            <button type="button"
                                                class="btn btn-outline-primary btn-sm mtu1500-select-all">Select All</button>
                                            <button type="button"
                                                class="btn btn-outline-secondary btn-sm mtu1500-deselect-all">Unselect All</button>
                                        </div>
                                    </div>
            
                                    <div class="option-group">
                                        <div class="option-label">Protocol:</div>
                                        <div class="option-items">
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu1500-protocol-checkbox" type="checkbox"
                                                    id="mtu1500_tcp_${group.id}" value="TCP">
                                                <label class="form-check-label" for="mtu1500_tcp_${group.id}">TCP</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu1500-protocol-checkbox" type="checkbox"
                                                    id="mtu1500_udp_${group.id}" value="UDP">
                                                <label class="form-check-label" for="mtu1500_udp_${group.id}">UDP</label>
                                            </div>
                                        </div>
                                    </div>
            
                                    <div class="option-group">
                                        <div class="option-label">Speed:</div>
                                        <div class="option-items">
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu1500-speed-checkbox" type="checkbox"
                                                    id="mtu1500_100M_${group.id}" value="100M">
                                                <label class="form-check-label" for="mtu1500_100M_${group.id}">100M</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu1500-speed-checkbox" type="checkbox"
                                                    id="mtu1500_1000M_${group.id}" value="1000M">
                                                <label class="form-check-label" for="mtu1500_1000M_${group.id}">1000M</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu1500-speed-checkbox" type="checkbox"
                                                    id="mtu1500_2500M_${group.id}" value="2500M">
                                                <label class="form-check-label" for="mtu1500_2500M_${group.id}">2500M</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu1500-speed-checkbox" type="checkbox"
                                                    id="mtu1500_5000M_${group.id}" value="5000M">
                                                <label class="form-check-label" for="mtu1500_5000M_${group.id}">5000M</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu1500-speed-checkbox" type="checkbox"
                                                    id="mtu1500_10G_${group.id}" value="10G">
                                                <label class="form-check-label" for="mtu1500_10G_${group.id}">10G</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
            
                                <!-- MTU=9000 区块 -->
                                <div class="mtu-section">
                                    <div class="mtu-header">
                                        <span class="mtu-title">MTU = 9000</span>
                                        <div class="group-actions">
                                            <button type="button"
                                                class="btn btn-outline-primary btn-sm mtu9000-select-all">Select All</button>
                                            <button type="button"
                                                class="btn btn-outline-secondary btn-sm mtu9000-deselect-all">Unselect All</button>
                                        </div>
                                    </div>
            
                                    <div class="option-group">
                                        <div class="option-label">Protocol:</div>
                                        <div class="option-items">
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu9000-protocol-checkbox" type="checkbox"
                                                    id="mtu9000_tcp_${group.id}" value="TCP">
                                                <label class="form-check-label" for="mtu9000_tcp_${group.id}">TCP</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu9000-protocol-checkbox" type="checkbox"
                                                    id="mtu9000_udp_${group.id}" value="UDP">
                                                <label class="form-check-label" for="mtu9000_udp_${group.id}">UDP</label>
                                            </div>
                                        </div>
                                    </div>
            
                                    <div class="option-group">
                                        <div class="option-label">Speed:</div>
                                        <div class="option-items">
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu9000-speed-checkbox" type="checkbox"
                                                    id="mtu9000_100M_${group.id}" value="100M">
                                                <label class="form-check-label" for="mtu9000_100M_${group.id}">100M</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu9000-speed-checkbox" type="checkbox"
                                                    id="mtu9000_1000M_${group.id}" value="1000M">
                                                <label class="form-check-label" for="mtu9000_1000M_${group.id}">1000M</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu9000-speed-checkbox" type="checkbox"
                                                    id="mtu9000_2500M_${group.id}" value="2500M">
                                                <label class="form-check-label" for="mtu9000_2500M_${group.id}">2500M</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu9000-speed-checkbox" type="checkbox"
                                                    id="mtu9000_5000M_${group.id}" value="5000M">
                                                <label class="form-check-label" for="mtu9000_5000M_${group.id}">5000M</label>
                                            </div>
                                            <div class="form-check form-check-inline">
                                                <input class="form-check-input mtu9000-speed-checkbox" type="checkbox"
                                                    id="mtu9000_10G_${group.id}" value="10G">
                                                <label class="form-check-label" for="mtu9000_10G_${group.id}">10G</label>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="form-text text-muted small mt-2">
                                    Note: You can select multiple protocols and speeds simultaneously for each MTU configuration.
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                Close
                            </button>
                            <button type="button" class="btn btn-primary save-config-btn" data-group-id="${group.id}">Save</button>
                        </div>
                    </div>
                </div>
            </div>
        </td>
        <td>
            <span class="badge ${statusClass} status-badge" data-group-id="${group.id}">
                ${getStatusText(group.status)}
            </span>
        </td>
        <td>
            <button class="btn btn-sm btn-success me-1 run-test-btn" data-group-id="${group.id}" ${group.status === 'running' ? 'disabled' : ''}>
                <i class="bi bi-play-fill"></i> Run Test
            </button>
            <button class="btn btn-sm btn-danger delete-btn" data-group-id="${group.id}">
                <i class="bi bi-trash"></i> Delete
            </button>
        </td>
    `;

    // 绑定模态框内的事件
    bindModalEvents(tr, group.id);

    // 绑定其他事件...
    const clientSelect = tr.querySelector('.client-select');
    const serverSelect = tr.querySelector('.server-select');
    const switchSelect = tr.querySelector('.switch-select');
    const cableSelect = tr.querySelector('.cable-select');
    const runTestBtn = tr.querySelector('.run-test-btn');
    const deleteBtn = tr.querySelector('.delete-btn');

    // 所有更改立即保存
    clientSelect.addEventListener('change', (e) => updateTestGroup(group.id, 'client_id', e.target.value));
    serverSelect.addEventListener('change', (e) => updateTestGroup(group.id, 'server_id', e.target.value));
    switchSelect.addEventListener('change', (e) => updateTestGroup(group.id, 'switch_id', e.target.value));
    cableSelect.addEventListener('change', (e) => updateTestGroup(group.id, 'cable_id', e.target.value));
    runTestBtn.addEventListener('click', () => runTest(group.id));
    deleteBtn.addEventListener('click', () => deleteTestGroup(group.id));

    return tr;
}

// 绑定模态框事件
function bindModalEvents(row, groupId) {
    const modal = row.querySelector(`#configModal_${groupId}`);
    if (!modal) return;

    // PowerManagement 全选
    const selectAllPower = modal.querySelector('.select-all-power');
    if (selectAllPower) {
        selectAllPower.addEventListener('click', () => {
            const powerCheckboxes = modal.querySelectorAll('.power-checkbox');
            powerCheckboxes.forEach(cb => cb.checked = true);
        });
    }

    // PowerManagement 取消全选
    const deselectAllPower = modal.querySelector('.deselect-all-power');
    if (deselectAllPower) {
        deselectAllPower.addEventListener('click', () => {
            const powerCheckboxes = modal.querySelectorAll('.power-checkbox');
            powerCheckboxes.forEach(cb => cb.checked = false);
        });
    }

    // MTU1500 全选
    const mtu1500SelectAll = modal.querySelector('.mtu1500-select-all');
    if (mtu1500SelectAll) {
        mtu1500SelectAll.addEventListener('click', () => {
            const protocolCheckboxes = modal.querySelectorAll('.mtu1500-protocol-checkbox');
            const speedCheckboxes = modal.querySelectorAll('.mtu1500-speed-checkbox');
            protocolCheckboxes.forEach(cb => cb.checked = true);
            speedCheckboxes.forEach(cb => cb.checked = true);
        });
    }

    // MTU1500 取消全选
    const mtu1500DeselectAll = modal.querySelector('.mtu1500-deselect-all');
    if (mtu1500DeselectAll) {
        mtu1500DeselectAll.addEventListener('click', () => {
            const protocolCheckboxes = modal.querySelectorAll('.mtu1500-protocol-checkbox');
            const speedCheckboxes = modal.querySelectorAll('.mtu1500-speed-checkbox');
            protocolCheckboxes.forEach(cb => cb.checked = false);
            speedCheckboxes.forEach(cb => cb.checked = false);
        });
    }

    // MTU9000 全选
    const mtu9000SelectAll = modal.querySelector('.mtu9000-select-all');
    if (mtu9000SelectAll) {
        mtu9000SelectAll.addEventListener('click', () => {
            const protocolCheckboxes = modal.querySelectorAll('.mtu9000-protocol-checkbox');
            const speedCheckboxes = modal.querySelectorAll('.mtu9000-speed-checkbox');
            protocolCheckboxes.forEach(cb => cb.checked = true);
            speedCheckboxes.forEach(cb => cb.checked = true);
        });
    }

    // MTU9000 取消全选
    const mtu9000DeselectAll = modal.querySelector('.mtu9000-deselect-all');
    if (mtu9000DeselectAll) {
        mtu9000DeselectAll.addEventListener('click', () => {
            const protocolCheckboxes = modal.querySelectorAll('.mtu9000-protocol-checkbox');
            const speedCheckboxes = modal.querySelectorAll('.mtu9000-speed-checkbox');
            protocolCheckboxes.forEach(cb => cb.checked = false);
            speedCheckboxes.forEach(cb => cb.checked = false);
        });
    }

    // Save 按钮
    const saveBtn = modal.querySelector('.save-config-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            collectAndShowConfig(modal, groupId);
        });
    }
}

// 收集配置并显示
async function collectAndShowConfig(modal, groupId) {
    const config = {
        basic_test: {},
        power_management: {},
        iperf_test: {}
    }

    const pingTest = modal.querySelector(`#pingTest_${groupId}`)
    if (pingTest) {
        config.basic_test.ping = pingTest.checked
    }

    const restartTest = modal.querySelector(`#restartTest_${groupId}`)
    const shutdownTest = modal.querySelector(`#shutdownTest_${groupId}`)
    const sleepTest = modal.querySelector(`#sleepTest_${groupId}`)

    config.power_management = {
        restart: restartTest?.checked || false,
        shutdown: shutdownTest?.checked || false,
        sleep: sleepTest?.checked || false
    }

    // Iperf Test - MTU1500
    const mtu1500Protocols = [];
    const mtu1500ProtocolCheckboxes = modal.querySelectorAll('.mtu1500-protocol-checkbox');
    mtu1500ProtocolCheckboxes.forEach(cb => {
        if (cb.checked) mtu1500Protocols.push(cb.value);
    });

    const mtu1500Speeds = [];
    const mtu1500SpeedCheckboxes = modal.querySelectorAll('.mtu1500-speed-checkbox');
    mtu1500SpeedCheckboxes.forEach(cb => {
        if (cb.checked) mtu1500Speeds.push(cb.value);
    });

    // Iperf Test - MTU9000
    const mtu9000Protocols = [];
    const mtu9000ProtocolCheckboxes = modal.querySelectorAll('.mtu9000-protocol-checkbox');
    mtu9000ProtocolCheckboxes.forEach(cb => {
        if (cb.checked) mtu9000Protocols.push(cb.value);
    });

    const mtu9000Speeds = [];
    const mtu9000SpeedCheckboxes = modal.querySelectorAll('.mtu9000-speed-checkbox');
    mtu9000SpeedCheckboxes.forEach(cb => {
        if (cb.checked) mtu9000Speeds.push(cb.value);
    });

    config.iperf_test = {
        mtu1500: {
            protocols: mtu1500Protocols,
            speeds: mtu1500Speeds
        },
        mtu9000: {
            protocols: mtu9000Protocols,
            speeds: mtu9000Speeds
        }
    };

    try {
        // 保存配置到后端
        const response = await fetch(`/api/test_groups/${groupId}/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config: config })
        });

        const result = await response.json();

        if (result.success) {
            // 可选：显示成功提示
            const saveBtn = modal.querySelector('.save-config-btn');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '✓ Saved!';
            setTimeout(() => {
                saveBtn.textContent = originalText;
            }, 1500);

            // 可以关闭模态框或保持打开
            // const bsModal = bootstrap.Modal.getInstance(modal);
            // bsModal.hide();
        } else {
            alert('Failed to save configuration: ' + result.error);
        }
    } catch (error) {
        console.error('Error saving config:', error);
        alert('Failed to save configuration');
    }

    // 可选：在控制台显示配置
    console.log('Saved configuration for group', groupId, config);
}

// 添加新测试组（无闪烁）
async function addNewGroup() {
    if (isLoading) return;

    // 禁用按钮，防止重复点击
    // const addBtn = document.getElementById('addNewGroupBtn');
    // addBtn.disabled = true;
    // addBtn.classList.add('btn-loading');
    // addBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Adding...';

    try {
        // 创建空的测试组到后端
        const response = await fetch('/api/test_groups', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_id: null,
                server_id: null,
                switch_id: null,
                cable_id: null
            })
        });

        const result = await response.json();

        if (result.success) {
            // 创建新组对象
            const newGroup = {
                id: result.data.id,
                client_id: null,
                server_id: null,
                switch_id: null,
                cable_id: null,
                status: 'pending',
                created_at: new Date().toISOString()
            };

            // 添加到本地数组
            testGroups.push(newGroup);

            // 移除空行（如果存在）
            const emptyRow = document.getElementById('emptyRow');
            if (emptyRow) {
                emptyRow.remove();
            }

            // 创建新行
            const tbody = document.getElementById('testGroupBody');
            const newRow = createGroupRow(newGroup, testGroups.length);
            tbody.appendChild(newRow);

            // 添加动画效果
            newRow.classList.add('new-row-animation');
            setTimeout(() => {
                newRow.classList.remove('new-row-animation');
            }, 300);

            // 滚动到新行
            newRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

            // 更新计数
            updateGroupCount();

        } else {
            alert('Failed to add test group: ' + result.error);
        }
    } catch (error) {
        console.error('Error adding test group:', error);
        alert('Failed to add test group');
    }
    // finally {
    //     // 恢复按钮
    //     addBtn.disabled = false;
    //     addBtn.classList.remove('btn-loading');
    //     addBtn.innerHTML = '<i class="bi bi-plus-circle"></i> New group';
    // }
}

// 更新测试组（立即保存）
async function updateTestGroup(groupId, field, value) {
    try {
        const updateData = {};
        updateData[field] = value ? parseInt(value) : null;

        const response = await fetch(`/api/test_groups/${groupId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });

        const result = await response.json();

        if (result.success) {
            // 更新本地数据
            const group = testGroups.find(g => g.id === groupId);
            if (group) {
                group[field] = updateData[field];
            }
        } else {
            console.error('Failed to update test group:', result.error);
        }
    } catch (error) {
        console.error('Error updating test group:', error);
    }
}

// 运行测试
async function runTest(groupId) {
    const runBtn = document.querySelector(`.run-test-btn[data-group-id="${groupId}"]`);
    if (!runBtn || runBtn.disabled) return;

    try {
        runBtn.disabled = true;
        runBtn.innerHTML = '<span class="loading-spinner"></span> Testing...';

        const response = await fetch(`/api/test_groups/${groupId}/run`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            // 更新本地状态
            const group = testGroups.find(g => g.id === groupId);
            if (group) {
                group.status = 'running';
            }

            // 更新状态显示
            const statusSpan = document.querySelector(`.status-badge[data-group-id="${groupId}"]`);
            if (statusSpan) {
                statusSpan.className = 'badge bg-info status-badge';
                statusSpan.textContent = 'Running';
            }

            // 定期检查状态
            checkTestStatus(groupId);
        } else {
            alert('Failed to start test: ' + result.error);
            runBtn.disabled = false;
            runBtn.innerHTML = '<i class="bi bi-play-fill"></i> Run Test';
        }
    } catch (error) {
        console.error('Error running test:', error);
        alert('Failed to run test');
        runBtn.disabled = false;
        runBtn.innerHTML = '<i class="bi bi-play-fill"></i> Run Test';
    }
}

// 检查测试状态
async function checkTestStatus(groupId) {
    try {
        const response = await fetch('/api/test_groups');
        const result = await response.json();

        if (result.success) {
            const updatedGroup = result.data.find(g => g.id === groupId);
            if (updatedGroup && updatedGroup.status !== 'running') {
                // 更新本地数据
                const index = testGroups.findIndex(g => g.id === groupId);
                if (index !== -1) {
                    testGroups[index] = { ...testGroups[index], ...updatedGroup };

                    // 只更新状态显示，不重新创建整行
                    const row = document.getElementById(`group_${groupId}`);
                    if (row) {
                        const statusSpan = row.querySelector('.status-badge');
                        if (statusSpan) {
                            let statusClass = 'bg-secondary';
                            if (updatedGroup.status === 'pending') statusClass = 'bg-warning';
                            else if (updatedGroup.status === 'passed') statusClass = 'bg-success';
                            else if (updatedGroup.status === 'failed') statusClass = 'bg-danger';

                            statusSpan.className = `badge ${statusClass} status-badge`;
                            statusSpan.textContent = getStatusText(updatedGroup.status);
                        }

                        // 恢复运行按钮
                        const runBtn = row.querySelector('.run-test-btn');
                        if (runBtn) {
                            runBtn.disabled = false;
                            runBtn.innerHTML = '<i class="bi bi-play-fill"></i> Run Test';
                        }
                    }
                }
            } else if (updatedGroup && updatedGroup.status === 'running') {
                setTimeout(() => checkTestStatus(groupId), 1000);
            }
        }
    } catch (error) {
        console.error('Error checking test status:', error);
    }
}

// 删除测试组（无闪烁）
async function deleteTestGroup(groupId) {
    if (!confirm('Are you sure you want to delete this test group?')) {
        return;
    }

    const row = document.getElementById(`group_${groupId}`);
    if (!row) return;

    // 添加删除动画
    row.classList.add('delete-row-animation');

    try {
        const response = await fetch(`/api/test_groups/${groupId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            // 等待动画完成后再删除 DOM
            setTimeout(() => {
                // 从本地数组中删除
                const index = testGroups.findIndex(g => g.id === groupId);
                if (index !== -1) {
                    testGroups.splice(index, 1);
                }

                // 删除行
                if (row && row.parentNode) {
                    row.remove();
                }

                // 如果没有数据了，显示空状态
                if (testGroups.length === 0) {
                    const tbody = document.getElementById('testGroupBody');
                    const emptyRow = document.createElement('tr');
                    emptyRow.id = 'emptyRow';
                    emptyRow.innerHTML = '<td colspan="8" class="text-center text-muted py-4"><i class="bi bi-inbox"></i> There is no test group，click the "New group" button to add a new test group</td>';
                    tbody.appendChild(emptyRow);
                } else {
                    // 重新编号
                    updateRowNumbers();
                }

                updateGroupCount();
            }, 200);
        } else {
            alert('Failed to delete test group: ' + result.error);
            // 如果删除失败，移除动画类
            row.classList.remove('delete-row-animation');
        }
    } catch (error) {
        console.error('Error deleting test group:', error);
        alert('Failed to delete test group');
        // 如果删除失败，移除动画类
        row.classList.remove('delete-row-animation');
    }
}

// 更新所有行的序号（只更新数字，不重建行）
function updateRowNumbers() {
    const rows = document.querySelectorAll('#testGroupBody tr:not(#emptyRow)');
    rows.forEach((row, index) => {
        const rowNumberCell = row.querySelector('.row-number');
        if (rowNumberCell) {
            rowNumberCell.textContent = index + 1;
        }
    });
}

// 生成下拉框选项
function generateSelectOptions(items, selectedValue, valueField, textField) {
    if (!items || items.length === 0) return '';

    return items.map(item => {
        const value = item[valueField];
        const text = item[textField];
        const selected = value == selectedValue ? 'selected' : '';
        return `<option value="${value}" ${selected}>${escapeHtml(text)}</option>`;
    }).join('');
}

// 更新组数统计
function updateGroupCount() {
    const countSpan = document.getElementById('groupCount');
    if (countSpan) {
        countSpan.textContent = testGroups.length;
    }
}

// 辅助函数
function getStatusText(status) {
    const statusMap = {
        'pending': 'Pending',
        'running': 'Running',
        'passed': 'Passed',
        'failed': 'Failed'
    };
    return statusMap[status] || status;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
