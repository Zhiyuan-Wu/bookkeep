/**
 * 服务记录管理功能
 */

let servicesPage = 1;
let servicesPageSize = 20;

// 加载服务记录列表
async function loadServices(page = 1) {
    servicesPage = page;
    
    const supplierId = document.getElementById('filterServiceSupplier').value;
    const content = document.getElementById('filterServiceContent').value;
    const status = document.getElementById('filterServiceStatus').value;
    
    const params = new URLSearchParams({
        page: page,
        page_size: servicesPageSize,
    });
    
    if (supplierId) params.append('supplier_id', supplierId);
    if (content) params.append('content', content);
    if (status) params.append('status', status);
    
    try {
        const response = await apiRequest(`/services/?${params}`);
        renderServicesTable(response.items);
        renderServicesPagination(response.page, response.page_size, response.total);
    } catch (error) {
        showMessage('加载服务记录列表失败: ' + error.message, 'error');
    }
}

// 渲染服务记录表格
function renderServicesTable(services) {
    const tbody = document.getElementById('servicesTableBody');
    tbody.innerHTML = '';
    
    if (services.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }
    
    services.forEach(service => {
        const row = document.createElement('tr');
        
        const actions = `
            <div class="action-buttons">
                <button class="action-btn" onclick="viewServiceDetail(${service.id})" title="查看详情">
                    <i class="fas fa-eye"></i>
                </button>
                ${currentUser.user_type === '厂家' && service.status === '暂存' ? `
                    <button class="action-btn btn-primary" onclick="submitService(${service.id})" title="发起服务">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                ` : ''}
                ${(currentUser.user_type === '普通用户' || currentUser.user_type === '管理员') && service.status === '发起' && service.user_id === currentUser.id ? `
                    <button class="action-btn btn-success" onclick="confirmService(${service.id})" title="确认">
                        <i class="fas fa-check"></i>
                    </button>
                ` : ''}
                <button class="action-btn btn-danger" onclick="deleteService(${service.id})" title="删除">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        row.innerHTML = `
            <td>${actions}</td>
            <td>#${service.id}</td>
            <td>${service.username || '-'}</td>
            <td>${service.supplier_name || '-'}</td>
            <td>${service.content.length > 50 ? service.content.substring(0, 50) + '...' : service.content}</td>
            <td>${formatCurrency(service.amount)}</td>
            <td><span class="tag-item status-tag status-${getStatusClass(service.status)}">${service.status}</span></td>
            <td>${formatDate(service.created_at)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// 渲染分页
function renderServicesPagination(page, pageSize, total) {
    const pagination = document.getElementById('servicesPagination');
    const totalPages = Math.ceil(total / pageSize);
    
    pagination.innerHTML = `
        <button class="btn btn-secondary" ${page <= 1 ? 'disabled' : ''} onclick="loadServices(${page - 1})">
            <i class="fas fa-chevron-left"></i> 上一页
        </button>
        <span class="pagination-info">第 ${page} 页，共 ${totalPages} 页，共 ${total} 条</span>
        <button class="btn btn-secondary" ${page >= totalPages ? 'disabled' : ''} onclick="loadServices(${page + 1})">
            下一页 <i class="fas fa-chevron-right"></i>
        </button>
    `;
}

// 查看服务记录详情
async function viewServiceDetail(serviceId) {
    try {
        const service = await apiRequest(`/services/${serviceId}`);
        
        const content = `
            <div class="modal-section">
                <h4><i class="fas fa-info-circle"></i> 服务详情</h4>
                <div class="modal-richtext">
                    <p><strong>服务ID：</strong>${service.id}</p>
                    <p><strong>用户：</strong>${service.username || '-'}</p>
                    <p><strong>厂家：</strong>${service.supplier_name || '-'}</p>
                    <p><strong>服务内容：</strong>${service.content}</p>
                    <p><strong>金额：</strong>${formatCurrency(service.amount)}</p>
                    <p><strong>状态：</strong>${service.status}</p>
                    <p><strong>创建时间：</strong>${formatDate(service.created_at)}</p>
                </div>
            </div>
        `;
        
        const modal = createModal('serviceDetailModal', '服务记录详情', content);
        document.getElementById('modalContainer').appendChild(modal);
        openModal('serviceDetailModal');
    } catch (error) {
        showMessage('加载服务记录详情失败: ' + error.message, 'error');
    }
}

// 发起服务记录
async function submitService(serviceId) {
    if (!await confirmDialog('确定要发起这个服务记录吗？')) {
        return;
    }
    
    try {
        await apiRequest(`/services/${serviceId}/status?new_status=发起`, { method: 'PUT' });
        showMessage('服务记录发起成功', 'success');
        loadServices(servicesPage);
    } catch (error) {
        showMessage('发起服务记录失败: ' + error.message, 'error');
    }
}

// 确认服务记录
async function confirmService(serviceId) {
    if (!await confirmDialog('确定要确认这个服务记录吗？')) {
        return;
    }
    
    try {
        await apiRequest(`/services/${serviceId}/status?new_status=确认`, { method: 'PUT' });
        showMessage('服务记录确认成功', 'success');
        loadServices(servicesPage);
    } catch (error) {
        showMessage('确认服务记录失败: ' + error.message, 'error');
    }
}

// 获取状态样式类
function getStatusClass(status) {
    const statusMap = {
        '暂存': 'draft',
        '发起': 'submitted',
        '确认': 'confirmed',
        '无效': 'invalid'
    };
    return statusMap[status] || 'default';
}

// 删除服务记录
async function deleteService(serviceId) {
    if (!await confirmDialog('确定要删除这个服务记录吗？')) {
        return;
    }
    
    try {
        await apiRequest(`/services/${serviceId}`, { method: 'DELETE' });
        showMessage('服务记录删除成功', 'success');
        loadServices(servicesPage);
    } catch (error) {
        showMessage('删除服务记录失败: ' + error.message, 'error');
    }
}

// 打开服务记录新建/编辑模态框
async function openServiceModal(serviceId = null) {
    let service = null;
    let suppliers = [];
    
    // 如果是编辑模式，加载服务记录数据
    if (serviceId) {
        try {
            service = await apiRequest(`/services/${serviceId}`);
        } catch (error) {
            showMessage('加载服务记录信息失败: ' + error.message, 'error');
            return;
        }
    }
    
    // 厂家用户只能看到自己的厂家
    if (currentUser.user_type === '厂家') {
        // 重新获取用户信息以确保包含 supplier_id
        try {
            const userInfo = await apiRequest('/users/me');
            if (userInfo.supplier_id) {
                currentUser.supplier_id = userInfo.supplier_id;
            } else {
                showMessage('厂家用户未关联厂家，无法创建服务记录', 'error');
                return;
            }
        } catch (error) {
            console.error('获取用户信息失败:', error);
            showMessage('获取用户信息失败，请刷新页面重试', 'error');
            return;
        }
        
        // 厂家用户使用 supplier_id，而不是 user id
        if (!currentUser.supplier_id) {
            showMessage('厂家用户未关联厂家，无法创建服务记录', 'error');
            return;
        }
        try {
            const supplierResponse = await getSuppliers();
            const supplier = supplierResponse.find(s => s.id === currentUser.supplier_id);
            if (supplier) {
                suppliers = [supplier];
            } else {
                suppliers = [{ id: currentUser.supplier_id, name: '未知厂家' }];
            }
        } catch (error) {
            suppliers = [{ id: currentUser.supplier_id, name: '未知厂家' }];
        }
    } else {
        // 加载厂家列表
        try {
            const suppliersResponse = await getSuppliers();
            suppliers = suppliersResponse;
        } catch (error) {
            if (service && service.supplier_id) {
                suppliers = [{ id: service.supplier_id, name: service.supplier_name }];
            }
        }
    }
    
    const isSupplier = currentUser.user_type === '厂家';
    const isEdit = serviceId !== null;
    const canEdit = isSupplier && (!isEdit || service.status === '暂存');
    
    let formHtml = `
        <form id="serviceForm">
            ${!isSupplier || isEdit ? `
                <div class="form-group">
                    <label><i class="fas fa-building"></i> 厂家 *</label>
                    <select name="supplier_id" required ${isEdit ? 'disabled style="background: var(--color-surface-muted);"' : ''}>
                        <option value="">请选择厂家</option>
                        ${suppliers.map(s => `
                            <option value="${s.id}" ${service && service.supplier_id === s.id ? 'selected' : ''}>
                                ${s.name}
                            </option>
                        `).join('')}
                    </select>
                </div>
            ` : `<input type="hidden" name="supplier_id" value="${currentUser.supplier_id || ''}">`}
            ${isSupplier && !isEdit ? `
                <div class="form-group">
                    <label><i class="fas fa-user"></i> 服务接收用户名 *</label>
                    <input type="text" name="user_username" required 
                           placeholder="请输入服务接收用户名"
                           autocomplete="off">
                </div>
            ` : ''}
            <div class="form-group">
                <label><i class="fas fa-file-alt"></i> 服务内容 *</label>
                <textarea name="content" required maxlength="1000" ${!canEdit ? 'disabled style="background: var(--color-surface-muted);"' : ''}>${service ? service.content : ''}</textarea>
            </div>
            <div class="form-group">
                <label><i class="fas fa-money-bill"></i> 金额 *</label>
                <input type="text" name="amount" value="${service ? service.amount : ''}" 
                       placeholder="请输入金额" required ${!canEdit ? 'disabled style="background: var(--color-surface-muted);"' : ''}>
            </div>
            ${isEdit ? `
                <div class="form-group">
                    <label><i class="fas fa-info-circle"></i> 状态</label>
                    <input type="text" value="${service.status}" disabled style="background: var(--color-surface-muted);">
                </div>
            ` : ''}
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal('serviceModal')">取消</button>
                ${canEdit ? `
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-save"></i> 保存
                    </button>
                ` : ''}
            </div>
        </form>
    `;
    
    const modal = createModal('serviceModal', serviceId ? '服务记录详情' : '录入服务记录', formHtml);
    document.getElementById('modalContainer').appendChild(modal);
    openModal('serviceModal');
    
    // 绑定表单提交事件
    if (canEdit) {
        document.getElementById('serviceForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await saveService(serviceId);
        });
    }
}

// 加载厂家下拉框（服务记录页面）
async function loadServiceSuppliers() {
    try {
        const suppliers = await getSuppliers();
        const select = document.getElementById('filterServiceSupplier');
        // 保留"全部"选项
        select.innerHTML = '<option value="">全部</option>';
        suppliers.forEach(supplier => {
            const option = document.createElement('option');
            option.value = supplier.id;
            option.textContent = supplier.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('加载厂家列表失败:', error);
    }
}

// 重置服务记录筛选条件
function resetServiceFilters() {
    document.getElementById('filterServiceSupplier').value = '';
    document.getElementById('filterServiceContent').value = '';
    document.getElementById('filterServiceStatus').value = '';
    loadServices(1);
}

// 保存服务记录
async function saveService(serviceId) {
    const form = document.getElementById('serviceForm');
    const formData = getFormData(form);
    
        // 验证金额输入
        const amount = parseFloat(formData.amount);
        if (isNaN(amount) || amount < 0) {
            showMessage('金额必须是有效的正数', 'error');
            return;
        }
        
        // 验证 supplier_id
        let supplierId;
        if (currentUser.user_type === '厂家' && !serviceId) {
            // 厂家用户创建新服务记录时，使用 currentUser.supplier_id
            if (!currentUser.supplier_id) {
                showMessage('厂家用户未关联厂家，无法创建服务记录', 'error');
                return;
            }
            supplierId = currentUser.supplier_id;
        } else {
            // 其他情况从表单获取
            supplierId = parseInt(formData.supplier_id);
            if (isNaN(supplierId)) {
                showMessage('厂家ID无效', 'error');
                return;
            }
        }
        
        const data = {
            supplier_id: supplierId,
            content: formData.content,
            amount: amount,
        };
        
        // 如果是厂家用户创建新服务记录，需要包含 user_username
        if (currentUser.user_type === '厂家' && !serviceId) {
            if (!formData.user_username || formData.user_username.trim() === '') {
                showMessage('请输入服务对象用户名', 'error');
                return;
            }
            data.user_username = formData.user_username.trim();
        }
    
    try {
        if (serviceId) {
            // 更新服务记录
            await apiRequest(`/services/${serviceId}`, {
                method: 'PUT',
                body: JSON.stringify({
                    content: data.content,
                    amount: data.amount
                })
            });
            showMessage('服务记录更新成功', 'success');
        } else {
            // 创建服务记录
            await apiRequest('/services/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showMessage('服务记录创建成功', 'success');
        }
        
        closeModal('serviceModal');
        loadServices(servicesPage);
    } catch (error) {
        showMessage((serviceId ? '更新' : '创建') + '服务记录失败: ' + error.message, 'error');
    }
}

