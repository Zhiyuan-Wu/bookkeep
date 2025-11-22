/**
 * 订单管理功能
 */

let ordersPage = 1;
let ordersPageSize = 20;

// 加载订单列表
async function loadOrders(page = 1) {
    ordersPage = page;
    
    const supplierId = document.getElementById('filterOrderSupplier').value;
    const content = document.getElementById('filterOrderContent').value;
    const status = document.getElementById('filterOrderStatus').value;
    
    const params = new URLSearchParams({
        page: page,
        page_size: ordersPageSize,
    });
    
    if (supplierId) params.append('supplier_id', supplierId);
    if (content) params.append('content', content);
    if (status) params.append('status', status);
    
    try {
        const response = await apiRequest(`/orders/?${params}`);
        renderOrdersTable(response.items);
        renderOrdersPagination(response.page, response.page_size, response.total);
    } catch (error) {
        showMessage('加载订单列表失败: ' + error.message, 'error');
    }
}

// 渲染订单表格
function renderOrdersTable(orders) {
    const tbody = document.getElementById('ordersTableBody');
    tbody.innerHTML = '';
    
    if (orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }
    
    orders.forEach(order => {
        const row = document.createElement('tr');
        
        // 解析订单内容以显示摘要
        let contentSummary = '无内容';
        try {
            const items = JSON.parse(order.content).items || [];
            if (items.length > 0) {
                contentSummary = items.map(item => `${item.name} x${item.quantity}`).join(', ');
                if (contentSummary.length > 50) {
                    contentSummary = contentSummary.substring(0, 50) + '...';
                }
            }
        } catch (e) {
            contentSummary = order.content.substring(0, 50) + '...';
        }
        
        const actions = `
            <div class="action-buttons">
                <button class="action-btn" onclick="viewOrderDetail(${order.id})" title="查看详情">
                    <i class="fas fa-eye"></i>
                </button>
                ${currentUser.user_type === '厂家' ? `
                    ${order.status === '发起' ? `
                        <button class="action-btn btn-success" onclick="confirmOrder(${order.id})" title="确认订单">
                            <i class="fas fa-check"></i>
                        </button>
                    ` : ''}
                ` : `
                    ${order.status === '暂存' ? `
                        <button class="action-btn btn-primary" onclick="submitOrder(${order.id})" title="发起订单">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    ` : ''}
                    <button class="action-btn btn-danger" onclick="deleteOrder(${order.id})" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>
                `}
            </div>
        `;
        
        row.innerHTML = `
            <td>${actions}</td>
            <td>#${order.id}</td>
            <td>${order.supplier_name || '-'}</td>
            <td>${contentSummary}</td>
            <td><span class="tag-item status-tag status-${getStatusClass(order.status)}">${order.status}</span></td>
            <td>${formatDate(order.created_at)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// 渲染分页
function renderOrdersPagination(page, pageSize, total) {
    const pagination = document.getElementById('ordersPagination');
    const totalPages = Math.ceil(total / pageSize);
    
    pagination.innerHTML = `
        <button class="btn btn-secondary" ${page <= 1 ? 'disabled' : ''} onclick="loadOrders(${page - 1})">
            <i class="fas fa-chevron-left"></i> 上一页
        </button>
        <span class="pagination-info">第 ${page} 页，共 ${totalPages} 页，共 ${total} 条</span>
        <button class="btn btn-secondary" ${page >= totalPages ? 'disabled' : ''} onclick="loadOrders(${page + 1})">
            下一页 <i class="fas fa-chevron-right"></i>
        </button>
    `;
}

// 查看订单详情
async function viewOrderDetail(orderId) {
    try {
        const order = await apiRequest(`/orders/${orderId}`);
        
        let itemsHtml = '<table class="data-table"><thead><tr>';
        itemsHtml += '<th>商品名</th><th>型号</th><th>规格</th>';
        if (currentUser.user_type !== '厂家') {
            itemsHtml += '<th>内部价格</th>';
        }
        itemsHtml += '<th>含税价格</th><th>数量</th></tr></thead><tbody>';
        
        order.items.forEach(item => {
            itemsHtml += '<tr>';
            itemsHtml += `<td>${item.name}</td>`;
            itemsHtml += `<td>${item.model || '-'}</td>`;
            itemsHtml += `<td>${item.specification || '-'}</td>`;
            if (currentUser.user_type !== '厂家') {
                itemsHtml += `<td>${formatCurrency(item.internal_price)}</td>`;
            }
            itemsHtml += `<td>${formatCurrency(item.tax_included_price)}</td>`;
            itemsHtml += `<td>${item.quantity}</td>`;
            itemsHtml += '</tr>';
        });
        
        itemsHtml += '</tbody></table>';
        
        const totalsHtml = `
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--color-border);">
                ${currentUser.user_type !== '厂家' ? `
                    <p><strong>总内部价格：</strong>${formatCurrency(order.total_internal_price)}</p>
                ` : ''}
                <p><strong>总含税价格：</strong>${formatCurrency(order.total_tax_included_price)}</p>
            </div>
            <div class="form-actions" style="margin-top: 20px;">
                <button class="btn btn-primary" onclick="exportOrder(${orderId})">
                    <i class="fas fa-download"></i> 导出订单
                </button>
            </div>
        `;
        
        const modal = createModal('orderDetailModal', '订单详情', itemsHtml + totalsHtml);
        document.getElementById('modalContainer').appendChild(modal);
        openModal('orderDetailModal');
    } catch (error) {
        showMessage('加载订单详情失败: ' + error.message, 'error');
    }
}

// 发起订单
async function submitOrder(orderId) {
    if (!await confirmDialog('确定要发起这个订单吗？')) {
        return;
    }
    
    try {
        await apiRequest(`/orders/${orderId}/status?new_status=发起`, { method: 'PUT' });
        showMessage('订单发起成功', 'success');
        loadOrders(ordersPage);
    } catch (error) {
        showMessage('发起订单失败: ' + error.message, 'error');
    }
}

// 确认订单
async function confirmOrder(orderId) {
    if (!await confirmDialog('确定要确认这个订单吗？')) {
        return;
    }
    
    try {
        await apiRequest(`/orders/${orderId}/status?new_status=确认`, { method: 'PUT' });
        showMessage('订单确认成功', 'success');
        loadOrders(ordersPage);
    } catch (error) {
        showMessage('确认订单失败: ' + error.message, 'error');
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

// 删除订单
async function deleteOrder(orderId) {
    if (!await confirmDialog('确定要删除这个订单吗？')) {
        return;
    }
    
    try {
        await apiRequest(`/orders/${orderId}`, { method: 'DELETE' });
        showMessage('订单删除成功', 'success');
        loadOrders(ordersPage);
    } catch (error) {
        showMessage('删除订单失败: ' + error.message, 'error');
    }
}

// 导出订单
async function exportOrder(orderId) {
    try {
        const order = await apiRequest(`/orders/${orderId}`);
        
        // 使用后端API导出Excel
        const response = await fetch(`/api/orders/${orderId}/export`, {
            method: 'GET',
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('导出失败');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `订单_${orderId}_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showMessage('订单导出成功', 'success');
    } catch (error) {
        showMessage('导出订单失败: ' + error.message, 'error');
    }
}

